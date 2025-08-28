#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, html, re
from typing import Dict, List

# ===== 後端：HTML 產出的小工具 =====
def esc(s: str) -> str:
    # HTML 文字轉義，避免字串被當作標籤注入：只處理 & < > "，不轉義單引號
    return html.escape(str(s), quote=False)

def cls_safe(s: str) -> str:
    # 將任意文字轉成可用於 CSS class 的安全字串：保留英數/底線/連字號，其餘改為 -
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", s)

def build_palette(labels: List[str]):
    # HTML 渲染輔助：依目前出現的 BIO 標籤產生「穩定配色」
    # 參數：
    #   labels: 例如 ["B-DISEASE","I-DISEASE","B-DRUG","I-DRUG","O"]
    # 流程：
    #   1) 抽出不含 B-/I- 前綴的實體名，去除 "O"
    #   2) 以實體名排序並均分色相（HSL），確保不同實體好區分且穩定
    #   3) B- 用同色相較深；I- 較淺；O 透明背景 + 淡虛線
    ents = [re.sub(r"^[BI]-", "", L) for L in labels if L and L != "O"]
    uniq = sorted(set(ents))
    total = max(1, len(uniq))
    css = {}
    for i, ent in enumerate(uniq):
        hue = int(360 * i / total)
        css[f"B-{ent}"] = (f"hsl({hue},85%,90%)", f"hsl({hue},70%,35%)")
        css[f"I-{ent}"] = (f"hsl({hue},85%,96%)", f"hsl({hue},70%,55%)")
    css["O"] = ("transparent", "rgba(0,0,0,.18)")
    return css

# ===== HTML 模板骨架（拆段便於維護） =====
HTML_HEAD = """<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<style>
  :root{{--bg:#fff;--ink:#1f2937;--muted:#64748b;--card:#f7fafc;--line:#e5e7eb;--accent:#0b5fff;--chip:#f2f4f8}}
  html,body{{background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,Segoe UI,Roboto,Helvetica,Arial,'Noto Sans',sans-serif;margin:0}}
  .wrap{{max-width:1280px;margin:28px auto;padding:0 18px}}
  h1{{margin:0 0 6px 0;font-size:28px;font-weight:800}}
  .intro{{color:var(--muted);margin:2px 0 14px 0}}

  /* 兩欄 */
  .layout{{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;margin-top:12px}}
  .aside{{position:sticky;top:64px;align-self:start;max-height:calc(100vh - 80px);overflow:auto;padding-right:4px}}
  @media (max-width:1100px){{ .layout{{grid-template-columns:1fr}} .aside{{position:static;max-height:none}} }}

  /* 卡片 */
  .file-block{{border:1px solid var(--line);border-radius:14px;margin:16px 0;background:#fff}}
  .file-head{{padding:12px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}}
  .file-title{{font-size:16px;font-weight:700}}
  .file-sub{{color:var(--muted);font-size:12px}}
  .file-body{{padding:8px 14px 14px 14px}}

  /* 區塊 */
  details.section{{margin:10px 0;border:1px solid var(--line);border-radius:10px;background:#fbfdff}}
  details>summary{{cursor:pointer;padding:8px 12px;font-weight:700;color:#374151;list-style:none;border-bottom:1px solid var(--line)}}
  details>summary::-webkit-details-marker{{display:none}}
  .sec-inner{{padding:8px 12px}}
  details.sentence{{margin:8px 0;border:1px dashed var(--line);border-radius:10px;background:var(--card)}}
  details.sentence>summary{{cursor:pointer;padding:8px 10px;color:var(--muted);font-size:12px;list-style:none}}
  .sent-body{{padding:8px 10px}}

  /* token */
  .tok{{display:inline-block;margin:1px 2px;padding:2px 4px;border-radius:6px;line-height:1.9}}
  .tok.O{{opacity:.85;border:1px dashed rgba(0,0,0,.18)}}

  /* 右欄 */
  .aside-card{{border:1px solid var(--line);border-radius:14px;background:#fff;margin:0 0 14px 0}}
  .aside-head{{padding:12px 14px;border-bottom:1px solid var(--line);font-weight:700;display:flex;justify-content:space-between;align-items:center}}
  .aside-body{{padding:10px 12px}}

  /* Legend */
  .legend{{display:flex;flex-direction:column;gap:6px}}
  .legend .chip{{display:flex;width:100%;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:var(--chip);border:1px solid var(--line);font-size:12px}}
  .legend .swatch{{width:12px;height:12px;border-radius:3px;border:1px solid rgba(0,0,0,.25);display:inline-block}}

  .panel{{display:flex;flex-wrap:wrap;gap:12px;align-items:center}}
  .chip.btn{{cursor:pointer}}
  .search{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:6px 10px;color:var(--ink)}}
  .ta{{width:100%;height:180px;border:1px solid var(--line);border-radius:10px;padding:10px}}

  /* TOC */
  .toc{{margin:14px 0 18px 0;display:flex;flex-wrap:wrap;gap:10px}}
  .toc a{{text-decoration:none;color:var(--accent);font-size:13px;border:1px solid var(--line);padding:4px 8px;border-radius:8px;background:#fff}}

  /* 動態 BIO 樣式（由 Python 產） */
  {css_rules}
</style>
</head>
<body>
<div class="wrap">
  <h1>{title}</h1>
  <div class="intro">{subtitle}</div>
"""

HTML_INPUT = """
  <div class="layout">
    <div id="mainCol">
      <details open class="file-block">
        <summary class="file-head" style="cursor:pointer">
          <div class="file-title">➕ 貼上病歷文字並處理</div>
          <div class="file-sub">離線可用；填 Hugging Face Token 可直接 NER</div>
        </summary>
        <div class="file-body">
          <div class="panel" style="margin-bottom:8px">
            <span class="chip">工作表名稱 <input id="inFileName" class="search" style="width:180px" value="pasted.txt"/></span>
            <span class="chip">HF 模型 <input id="inModel" class="search" style="width:240px" value="d4data/biomedical-ner-all"/></span>
            <span class="chip">HF Token <input id="inToken" class="search" style="width:260px" placeholder="hf_xxx"/></span>
          </div>
          <textarea id="inText" class="ta" placeholder="在此貼上整段病歷文字…"></textarea>
          <div class="panel" style="margin-top:10px">
            <span class="chip btn" id="btnPreprocess">① 只斷段 + 分詞</span>
            <span class="chip btn" id="btnRunNER">② 斷段 + 分詞 + NER</span>
            <span class="chip btn" id="btnClear">清除貼上結果</span>
            <span class="chip">下載：
              <button type="button" id="dlSegments" class="btn" disabled style="margin-left:4px">segments.jsonl</button>
              <button type="button" id="dlTokens" class="btn" disabled>ner_token_rows.jsonl</button>
              <button type="button" id="dlLabeled" class="btn" disabled>ner_labeled.jsonl</button>
            </span>
          </div>
          <div id="inStatus" class="intro" style="margin-top:6px"></div>
        </div>
      </details>
      <div class="toc" id="toc"></div>
    </div>

    <aside class="aside">
      <div class="aside-card">
        <div class="aside-head">標籤
          <span>
            <button type="button" class="chip btn" id="selAll">全選</button>
            <button type="button" class="chip btn" id="selNone">全不選</button>
          </span>
        </div>
        <div class="aside-body"><div class="legend" id="legend"></div></div>
      </div>

      <div class="aside-card">
        <div class="aside-head">標註摘要</div>
        <div class="aside-body" id="annSummary"></div>
      </div>
    </aside>
  </div>
"""

HTML_INIT_JSON = """
<script id="__INIT__" type="application/json">{init_json}</script>
"""

HTML_SCRIPT = """
<script>
/* ====== 基本工具/常數 ====== */
const $  = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
function htmlEscape(s){
  // 逐字元對照表：把可能形成 HTML 的字元轉義，避免 XSS 或破版
  return (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
function slug(s){
  // 轉成可用於錨點/ID 的字串：小寫 + 非中英數底線連字號改為 -
  return (s||'').toLowerCase()
    .replace(/[^a-z0-9\\u4e00-\\u9fff_-]+/g,'-') // 清掉不合法字元
    .replace(/^-|-$/g,'');                       // 去頭尾連字號
}
function natKey(s){
  // 產生「自然排序」鍵：數字部分轉成 Number，字母轉小寫
  // 例如 "file12a" -> ["file", 12, "a"]
  return (s+'').split(/(\\d+)/).map(p => /^\\d+$/.test(p) ? Number(p) : p.toLowerCase());
}
const natCmp = (a, b) => {
  // 自然排序比較器：逐段比較，數字比大小、字串比字典序
  const ka = natKey(a), kb = natKey(b);
  for (let i = 0; i < Math.max(ka.length, kb.length); i++) {
    if (ka[i] == null) return -1;             // a 比 b 短
    if (kb[i] == null) return 1;              // b 比 a 短
    if (ka[i] < kb[i]) return -1;
    if (ka[i] > kb[i]) return 1;
  }
  return 0;
};
function downloadText(filename, text){
  // 將字串打包成 Blob 供瀏覽器下載（避免伺服器 round-trip）
  // 1) 建立 Blob
  const blob = new Blob([text], {type:'application/json;charset=utf-8'});
  // 2) 建立暫時 URL 並觸發 a.click()
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  // 3) 釋放 URL，避免記憶體洩漏
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/* ====== 全域狀態 ====== */
let DATA = {};          // files[file][section][sidx] = [TokenRow...]
let LABELS = new Set(); // BIO 標籤集合（含 'O'）

/* ====== 常見章節優先排序 ====== */
const PREFERRED_SECTIONS = [
  "診斷","主訴","過去病史","住院治療經過",
  "Diagnosis","Impression","Chief_Complaint","Chief Complaint",
  "Past_History","Past History","Hospital_Course","Hospital Course"
];

/* ====== BIO 動態樣式（保底；Python 已輸出一版） ====== */
function dynBIO(){
  // 目的：依目前 LABELS 推導每個實體的 B-/I- 色票，寫進 <style id="dyn-label-css">
  // 步驟：
  // 1) 擷取實體名（去掉 B-/I-），去重排序
  const ents = Array.from(new Set(Array.from(LABELS)
                  .filter(l=>l!=='O')
                  .map(l=>l.replace(/^([BI]-)/,''))))
                .sort();
  // 2) 依實體數平均分配 HSL 色相，組 CSS 字串
  const total = Math.max(1, ents.length);
  let css = "";
  ents.forEach((ent,i)=>{
    const hue = Math.floor(360*i/total);
    const bbg = `hsl(${hue},85%,90%)`, bbd=`hsl(${hue},70%,35%)`;
    const ibg = `hsl(${hue},85%,96%)`, ibd=`hsl(${hue},70%,55%)`;
    const safe = ent.replace(/[^\\w-]/g,'-');
    css += `.lab-B-${safe}{background:${bbg};border:1px solid ${bbd};border-left:3px solid ${bbd};}`;
    css += `.lab-I-${safe}{background:${ibg};border:1px solid ${ibd};border-left:1px solid ${ibd};}`;
  });
  // 3) O 類型基礎樣式
  css += `.tok.O{opacity:.85;border:1px dashed rgba(0,0,0,.18)}`;
  // 4) 注入/覆寫到 head
  let st = document.getElementById('dyn-label-css');
  if(!st){ st=document.createElement('style'); st.id='dyn-label-css'; document.head.appendChild(st); }
  st.textContent = css;
}

/* ====== Legend / TOC ====== */
function renderLegend(){
  // 目的：右欄顏色圖例 + 勾選開關
  // 1) 蒐集實體清單（去掉 'O' 並統一成實體名）
  const ents = Array.from(new Set(Array.from(LABELS)
                  .filter(l=>l!=='O')
                  .map(l=>l.replace(/^([BI]-)/,''))))
                .sort();
  // 2) 依序產生每一列（顏色與主樣式一致）
  $('#legend').innerHTML = ents.length
    ? ents.map((ent, idx) => {
        const hue = Math.floor(360 * idx / Math.max(1, ents.length));
        return `<label class="chip">
          <input type="checkbox" class="entToggle" data-ent="${htmlEscape(ent)}" checked/>
          <span class="swatch" style="background:hsl(${hue},85%,90%);border-color:hsl(${hue},70%,35%)"></span>
          <span>${htmlEscape(ent)}</span>
        </label>`;
      }).join("")
    : '<span class="chip">No entities</span>';
}
function renderTOC(files){
  // 目的：頁面頂部 TOC，列出每個 file 的錨點連結
  // 1) 以自然排序排列檔名
  const names = Object.keys(files).sort(natCmp);
  // 2) 產生 anchor 連結，連到 #file-<slug>
  $('#toc').innerHTML = names.map(f => `<a href="#file-${slug(f)}">${htmlEscape(f)}</a>`).join("");
}
function bindLegendToggles(){
  // 目的：綁定 Legend 勾選行為，切換特定實體的視覺強度
  function apply(){
    // 1) 取得目前被勾選的實體集合（空集合 = 全部不著色但仍顯示）
    const enabled = new Set($$('.entToggle').filter(t=>t.checked).map(t=>t.dataset.ent));
    // 2) 對每個 token 判斷：O 不處理；其餘若未在 enabled，則去除背景與邊框
    $$('.tok').forEach(el=>{
      const ent = el.dataset.ent;
      if (ent === 'O') return;
      if (enabled.size === 0 || enabled.has(ent)) {
        el.style.display = 'inline-block';
        el.style.background = '';
        el.style.border = '';
      } else {
        el.style.display = 'inline-block';
        el.style.background = 'transparent';
        el.style.border = 'none';
      }
    });
  }
  // 3) 綁定勾選與全選/全不選
  $$('.entToggle').forEach(t => t.onchange = apply);
  $('#selAll')?.addEventListener('click',  () => { $$('.entToggle').forEach(t=>t.checked=true);  apply(); });
  $('#selNone')?.addEventListener('click', () => { $$('.entToggle').forEach(t=>t.checked=false); apply(); });
  // 4) 首次套用
  apply();
}

/* ====== 斷段/分詞 ====== */
const WORD_SECTIONS = new Set(["過去病史","Past_History","Past History","住院治療經過","Hospital_Course","Hospital Course"]);
const SECTION_TOKENS = [
  "診斷","主訴","過去病史","住院治療經過",
  "Diagnosis","Impression","Chief Complaint","CC",
  "Past Medical History","Past History","History of Present Illness","HPI",
  "Hospital Course","Hospitalization Course"
];
const SECTION_PATTERNS = [
  [/^\\s*(診斷\\s*[:：]|Diagnosis\\s*[:：]|Impression\\s*[:：])/i,"診斷"],
  [/^\\s*(主訴\\s*[:：]|Chief\\s*Complaint\\s*[:：]|CC\\s*[:：]?)/i,"主訴"],
  [/^\\s*(過去病史|既往史|Past\\s*(Medical\\s*)?History|History\\s*of\\s*Present\\s*Illness|HPI)\\s*[:：]?/i,"過去病史"],
  [/^\\s*(住院治療經過|住院經過|住院過程|Hospital\\s*Course|Hospitalization\\s*Course)\\s*[:：]?/i,"住院治療經過"],
];
const SENT_END = new Set(['.','。','．','!','?','！','？']);

function iterLines(raw){
  // 將原始字串依 \\n 逐行切出：(lineStartIdx, lineEndIdx, 行文字)
  const out=[]; let i=0;
  while(i<raw.length){
    const j = raw.indexOf('\\n', i);
    const end = j<0 ? raw.length : j+1;  // 保留行尾換行
    out.push([i, end, raw.slice(i, end)]);
    i = end;
  }
  return out;
}
function cleanCrossSection(text){
  // 清除一段文字中「下一個章節標頭之後的內容」，避免跨段落污染
  // 1) 如果整行只有「<章節>：」則視為空
  if(!text) return text;
  const stripped = text.trim();
  for(const tok of SECTION_TOKENS){
    const re = new RegExp(`^${tok.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')}\\s*[:：]\\s*$`, 'i');
    if(re.test(stripped)) return "";
  }
  // 2) 若段內遇到下一個章節標頭，截斷到標頭前
  const pattern = new RegExp(`(?:\\n|^)\\s*(?:${
    SECTION_TOKENS.map(t=>t.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')).join('|')
  })\\s*[:：]\\s*`, 'i');
  const m = text.match(pattern);
  if(m) return text.slice(0, m.index).replace(/\\s+$/,'');
  // 3) 否則只去掉尾端多餘空白
  return text.replace(/\\s+$/,'');
}
function findSections(raw){
  // 掃描全文，找出章節標頭出現位置：[標頭名, 起始索引, 內容起始索引]
  const hits=[];
  iterLines(raw).forEach(([i,_,line])=>{
    for(const [pat,norm] of SECTION_PATTERNS){
      const m = line.match(pat);
      if(m){
        // 內容起點：略過標頭 + 尾隨空白
        let k = m.index + m[0].length;
        while(k<line.length && /[ \\t]/.test(line[k])) k++;
        hits.push([norm, i + m.index, i + k]);
        break; // 一行只配一種章節
      }
    }
  });
  // 相同章節只保留第一次出現（避免重複）
  const uniq=[]; const seen=new Set();
  hits.sort((a,b)=>a[1]-b[1]);
  for(const h of hits){ if(!seen.has(h[0])){ uniq.push(h); seen.add(h[0]); } }
  return uniq;
}
function sliceBlocks(raw, labels){
  // 依章節標頭位置把全文切成區塊：每個章節 => [內容起點, 下一章節起點)
  const spans={};
  labels.forEach((t, idx)=>{
    const [lab, , contentStart] = t;
    const next = labels[idx+1] ? labels[idx+1][1] : raw.length; // 下一個標頭位置
    spans[lab] = [contentStart, next];
  });
  return spans;
}
function splitOnPeriods(raw, s, e){
  // 以句點/終止符號切句，避免小數點與數字被誤切
  const text = raw.slice(s, e);
  const cuts=[]; let last=0; let i=0;
  const at = k => (k>=0 && k<text.length) ? text[k] : '';
  while(i<text.length){
    const ch = text[i];
    if (SENT_END.has(ch)){
      // 若是數字 . 數字（小數/編號），則跳過
      if ((ch==='.'||ch==='．') && /\\d/.test(at(i-1))){
        let k=i+1; while(k<text.length && /[ \\t\\r\\n]/.test(text[k])) k++;
        if (k<text.length && /\\d/.test(text[k])) { i++; continue; }
      }
      // 切一段
      const segEnd = i+1; cuts.push([last, segEnd]); last = segEnd;
      // 忽略段後空白
      while(last<text.length && /[ \\t\\r\\n]/.test(text[last])) last++;
    }
    i++;
  }
  if (last < text.length) cuts.push([last, text.length]);
  // 回到全文座標
  return cuts.map(([a,b]) => [s+a, s+b]);
}
function mergeTinyForward(raw, spans, tiny){
  // 合併過短且未以終止符號結尾的分段，往後黏到下一段（直到遇到終止段）
  if(!spans.length) return spans;
  const out=[]; let i=0;
  while(i<spans.length){
    let [a,b] = spans[i];
    const frag = raw.slice(a,b);
    const endCh = frag.slice(-1);
    if ((b-a) <= tiny && !SENT_END.has(endCh)){
      // 過短且非終止：一路往後合併
      let j=i+1;
      while(j<spans.length){
        const [a2,b2] = spans[j];
        const frag2 = raw.slice(a2,b2);
        const end2  = frag2.slice(-1);
        b = b2; j++;
        if (SENT_END.has(end2)) break;
      }
      out.push([a,b]); i=j;
    } else {
      out.push([a,b]); i++;
    }
  }
  return out;
}
function mergeEnumerators(raw, spans){
  // 合併被編號符號切斷的片段：
  // 1) 單獨一行只有「數字.」接下一段
  // 2) 前一段以「數字.」收尾
  // 3) 下一段以「(數字)」或「數字) / 數字. / 數字)」開頭且前段很短
  const FULL = /^\\s*\\d+\\.\\s*$/;
  const TAILEND = /\\d+\\.\\s*$/;
  const TAILSTART = /^\\s*\\(?\\d+\\)?[.)]\\s+/;
  const out=[]; let i=0;
  while(i<spans.length){
    let [a,b] = spans[i];
    const frag = raw.slice(a,b);
    if (FULL.test(frag.trim()) && i+1<spans.length){ const [,b2]=spans[i+1]; out.push([a,b2]); i+=2; continue; }
    if (TAILEND.test(frag) && i+1<spans.length){ const [,b2]=spans[i+1]; out.push([a,b2]); i+=2; continue; }
    if (i+1<spans.length){
      const [a2,b2] = spans[i+1];
      const nxt = raw.slice(a2,b2);
      if (TAILSTART.test(nxt) && (b-a)<=12){ out.push([a,b2]); i+=2; continue; }
    }
    out.push([a,b]); i++;
  }
  return out;
}
function cutDiagnosis(raw, s, e){
  // 「診斷」段：依 # 或 's/p' 類分隔符切段，並移除下一章節以後的內容
  const out=[];
  iterLines(raw.slice(s,e)).forEach(([li,lj,line])=>{
    if(!line.trim()) return;
    // 使用分隔符群組保留：split 後再手動組裝
    const pieces = line.split(/(#+|- ?s\\/p)/ig).filter(Boolean);
    let acc='';
    pieces.forEach(p=>{
      acc += p;
      if (p.match(/(#+|- ?s\\/p)/i)) {
        // 遇到分隔符，將前半段（去掉分隔符）推入
        const frag = acc.replace(/(#+|- ?s\\/p)/ig,'').trim();
        if (frag){
          out.push([
            s + li + (acc.length - p.length - frag.length),
            s + li + (acc.length - p.length) + frag.length
          ]);
        }
        acc = '';
      }
    });
    if (acc.trim()){ out.push([s+li, s+lj]); }
  });
  // 清理跨段內容
  const cleaned=[];
  out.forEach(([a,b])=>{
    const frag = raw.slice(a,b);
    const c = cleanCrossSection(frag);
    if(c) cleaned.push([a, a + c.length]);
  });
  return cleaned;
}
function cutBlock(raw, s, e, name){
  // 依章節名稱分派對應切法；其餘採通用規則
  if (name === "診斷") return cutDiagnosis(raw, s, e);
  if (name === "主訴"){
    let spans = splitOnPeriods(raw, s, e);
    spans = mergeTinyForward(raw, spans, 18);
    spans = mergeEnumerators(raw, spans);
    return spans;
  }
  if (name === "過去病史" || name === "住院治療經過"){
    // 行為單位切句（避免長行塞太多），再合併細碎
    let acc=[];
    iterLines(raw.slice(s,e)).forEach(([li,lj,line])=>{
      if(line.trim()){
        acc = acc.concat(splitOnPeriods(raw, s+li, s+lj));
      }
    });
    acc = mergeTinyForward(raw, acc, 28);
    acc = mergeEnumerators(raw, acc);
    return acc;
  }
  // 通用：先句號切，再合併細碎與編號
  let spans = splitOnPeriods(raw, s, e);
  spans = mergeTinyForward(raw, spans, 24);
  spans = mergeEnumerators(raw, spans);
  return spans;
}
function computeOffsets(sentence, token, startPos){
  // 在 sentence 中自 startPos 起尋找 token，回傳 [start, end]
  // 若空白數量差異，改以「壓縮空白後的匹配」補救
  const idx = sentence.indexOf(token, startPos);
  if (idx >= 0) return [idx, idx + token.length];
  const ns = sentence.replace(/\\s+/g,' ');
  const nt = token.replace(/\\s+/g,' ');
  const j = ns.indexOf(nt);
  if (j >= 0) return [j, j + nt.length];
  // 最後退路：假設緊接 startPos
  return [startPos, startPos + token.length];
}
function splitOutsideParens(text){
  // 分詞（通用）：以逗號/分號/ and 分割，但括號內不切
  // 1) depth 計數括號層級
  // 2) 在 depth==0 時，遇到 , ; 或 " and " 才切
  let depth=0, cur='', toks=[];
  const flush = () => { const t = cur.trim(); if(t) toks.push(t); cur=''; };
  for(let i=0;i<text.length;i++){
    const ch = text[i];
    if (ch==='('){ depth++; cur+=ch; continue; }
    if (ch===')'){ depth=Math.max(depth-1,0); cur+=ch; continue; }
    if (depth===0){
      if (text.slice(i,i+5).toLowerCase()===' and '){ flush(); toks.push('and'); i+=4; continue; }
      if (ch===',' || ch===';'){ flush(); continue; }
    }
    cur += ch;
  }
  flush();
  return toks;
}
function tokenizeSentence(file, section, sidx, text){
  // 將一句文字切成 token_rows：{text, start, end, label, meta}
  // 規則：
  // - WORD_SECTIONS（如過去病史等）使用「空白」切，保留緊貼
  // - 其餘使用 splitOutsideParens
  let toks=[];
  if (WORD_SECTIONS.has(section)){
    let i=0, n=text.length;
    while(i<n){
      let j=i; while(j<n && !/ /.test(text[j])) j++;
      while(j<n && text[j]===' ') j++;
      const token = text.slice(i,j);
      if (token) toks.push(token);
      i = j;
    }
  } else {
    toks = splitOutsideParens(text);
  }
  // 依原句定位每個 token 的 start/end，並包 meta
  const recs=[]; let cursor=0;
  toks.forEach((t,k)=>{
    const [s,e] = computeOffsets(text, t, cursor);
    recs.push({
      id: `${file}:${section}:${sidx}:${k}`,
      meta: {file, section, source_span:[null,null], sentence_index:sidx, token_index:k},
      text: t, start: s, end: e, label: "O"
    });
    cursor = e;
  });
  return recs;
}
function preprocessRawToData(raw, fileLabel){
  // 原始病歷文字 → {files, segments, tokenRows}
  // 步驟：
  // 1) findSections：找章節標頭
  const labels = findSections(raw);
  // 2) 依標頭切區塊；若無標頭，改走逐行切
  const blocks = labels.length ? sliceBlocks(raw, labels) : {};
  let segments=[];
  if (!labels.length){
    // 無章節：逐行取非空白內容（並清跨段落尾巴）
    iterLines(raw).forEach(([i,j,t])=>{
      if (t.trim()){
        const c = cleanCrossSection(t);
        if (c) segments.push({file:fileLabel, section:"全文", start:i, end:i+c.length, text:c});
      }
    });
  } else {
    // 有章節：每個章節用對應 cut* 規則切成句片段
    Object.entries(blocks).forEach(([lab,[bs,be]])=>{
      cutBlock(raw, bs, be, lab).forEach(([a,b])=>{
        const frag = raw.slice(a,b);
        const c = cleanCrossSection(frag);
        if (c) segments.push({file:fileLabel, section:lab, start:a, end:a+c.length, text:c});
      });
    });
  }
  // 3) 以 file+section 分桶，維持句序
  const buckets = {};
  segments.forEach(seg=>{
    const key = seg.file + "||" + seg.section;
    (buckets[key] = buckets[key] || []).push(seg.text);
  });
  // 4) 產生 files 映射與 tokenRows 平鋪表
  const files = {}; const tokenRows=[];
  Object.entries(buckets).forEach(([key, arr])=>{
    const [file, section] = key.split("||");
    arr.forEach((sent,i)=>{
      const recs = tokenizeSentence(file, section, i, sent);
      (files[file] = files[file] || {});
      (files[file][section] = files[file][section] || {});
      files[file][section][i] = recs.map(r => ({
        text:r.text, start:r.start, end:r.end, label:r.label, meta:r.meta
      }));
      recs.forEach(r => tokenRows.push(r));
    });
  });
  // 5) 回傳渲染所需三份資料
  return {files, segments, tokenRows};
}

/* ====== HF NER ====== */
async function runNEROnFiles(files, model, token){
  // 對 files 中每一句文字呼叫 HF Inference API 做 NER，並把 BIO 標籤寫回 token
  async function inferText(text){
    // 以 simple aggregation 拿 span，回傳陣列：[{start,end, entity_group, score, word}, ...]
    const resp = await fetch(`https://api-inference.huggingface.co/models/${encodeURIComponent(model)}`, {
      method:'POST',
      headers:{'Authorization':`Bearer ${token}`,'Content-Type':'application/json'},
      body: JSON.stringify({inputs:text, parameters:{aggregation_strategy:"simple"}})
    });
    if(!resp.ok) throw new Error(`HF API ${resp.status}`);
    return await resp.json();
  }
  function assignBIO(tokens, spans){
    // 將 HF 回傳的 spans 對齊本地 tokens，產生 BIO 序列
    // 原則：
    // - 計算 token 與 span 的重疊長度，取每個 token 最佳匹配
    // - 第一個重疊記 B-<ENT>，延續記 I-<ENT>
    const labels = new Array(tokens.length).fill('O');
    const best = new Array(tokens.length).fill(0);
    spans.forEach(p=>{
      const s = +p.start, e = +p.end, lab = String(p.entity_group||p.entity||'ENT');
      const idxs=[];
      tokens.forEach((t,i)=>{
        const ts=+t.start, te=+t.end;
        const ov = Math.max(0, Math.min(te,e) - Math.max(ts,s));
        if (ov > 0) idxs.push([i, ov]);
      });
      if(!idxs.length) return;
      idxs.sort((a,b)=>a[0]-b[0]);
      idxs.forEach(([i,ov],j)=>{
        const tag = (j===0?'B-':'I-') + lab;
        if (ov > best[i]){ labels[i] = tag; best[i] = ov; }
      });
    });
    return labels;
  }
  // 逐 file / section / sentence 進行推論與回填
  for(const file of Object.keys(files)){
    for(const section of Object.keys(files[file])){
      for(const sidx of Object.keys(files[file][section]).map(Number).sort((a,b)=>a-b)){
        const toks = files[file][section][sidx];
        // WORD_SECTIONS 以「直連」組句，其餘以空白連接
        const sentText = (WORD_SECTIONS.has(section) ? toks.map(t=>t.text).join("") : toks.map(t=>t.text).join(" "));
        const ents = await inferText(sentText);
        const labs = assignBIO(toks, ents);
        toks.forEach((t,i)=>{ t.label = labs[i]; LABELS.add(labs[i]); });
      }
    }
  }
}

/* ====== 渲染 ====== */
function rebuildSummary(){
  // 目的：依 DATA 聚合每 file/section 的連續實體片段，產出右欄摘要清單
  const box = $('#annSummary'); if(!box) return;
  let html = '';
  const orderedFiles = Object.keys(DATA).sort(natCmp);
  orderedFiles.forEach(file=>{
    const sections = DATA[file] || {};
    const buckets = {}; // section -> [{ent,text}, ...]
    Object.keys(sections).forEach(sec=>{
      (buckets[sec] = buckets[sec] || []);
      Object.keys(sections[sec]).map(Number).sort((a,b)=>a-b).forEach(sidx=>{
        const toks = sections[sec][sidx] || [];
        // 將連續 I-* 與前一個 B-* 併為片段
        let cur=null; const groups=[];
        toks.forEach(t=>{
          const lab = String(t.label||'O');
          if (lab==='O'){ cur=null; return; }
          const ent = lab.replace(/^([BI]-)/,'');
          const piece = t.text;
          const joiner = (sec==="過去病史"||sec==="住院治療經過") ? '' : ' ';
          if (lab.startsWith('B-') || !cur || cur.ent!==ent){
            cur = {ent, text: piece};
            groups.push(cur);
          } else {
            cur.text += joiner + piece;
          }
        });
        groups.forEach(g => buckets[sec].push({ent:g.ent, text:g.text}));
      });
    });
    // 章節排序：常見章節優先，其餘依字母序
    const orderedSecs = [
      ...new Set([
        ...PREFERRED_SECTIONS.filter(n => buckets[n]?.length),
        ...Object.keys(buckets).sort().filter(n => !PREFERRED_SECTIONS.includes(n))
      ])
    ];
    // 總片段數
    let total = 0; orderedSecs.forEach(s => total += (buckets[s]||[]).length);
    // 組 HTML
    html += `<div class="sum-file"><div class="name">${htmlEscape(file)} · 標註片段 <b>${total}</b></div>`;
    orderedSecs.forEach(cs=>{
      const arr = buckets[cs]||[]; if(!arr.length) return;
      html += `<div class="sum-sec"><div class="sec-title">[${htmlEscape(cs)}]</div><ul class="sum-list">`;
      arr.forEach(r=>{
        html += `<li>${htmlEscape(r.text)}<span class="tag-badge" style="margin-left:8px;font-size:11px;padding:1px 6px;border:1px solid var(--line);border-radius:999px;background:#f9fafb;color:#111">${htmlEscape(r.ent)}</span></li>`;
      });
      html += `</ul></div>`;
    });
    html += `</div>`;
  });
  box.innerHTML = html || '<div class="intro">（尚無標註可摘要）</div>';
}
function rebuildPage(){
  // 整體重繪：樣式 → Legend/TOC → 主體檔案/章節/句子 → 摘要 → 綁定 Legend
  dynBIO();             // 更新/覆寫 BIO 樣式
  renderLegend();       // 重繪圖例
  renderTOC(DATA);      // 重繪 TOC
  $$('.file-block.rendered').forEach(e=>e.remove()); // 清掉舊內容

  const orderedFiles = Object.keys(DATA).sort(natCmp);
  orderedFiles.forEach(file=>{
    const sections = DATA[file];
    // 統計 token/section 數供標頭顯示
    let tokCnt = 0, secNames = Object.keys(sections);
    Object.values(sections).forEach(sentmap=>Object.values(sentmap).forEach(toks=>tokCnt+=toks.length));
    // 建立容器
    const block = document.createElement('div');
    block.className = 'file-block rendered'; block.id = `file-${slug(file)}`;
    block.innerHTML = `
      <div class="file-head"><div class="file-title">${htmlEscape(file)}</div>
        <div class="file-sub">tokens: <b>${tokCnt}</b> · sections: <b>${secNames.length}</b></div>
      </div>
      <div class="file-body"></div>`;
    const body = block.querySelector('.file-body');

    // 章節排序：常見優先，其餘字母序
    const seen=new Set(); const orderedSecs=[];
    PREFERRED_SECTIONS.forEach(n=>{ if(sections[n] && !seen.has(n)){ orderedSecs.push(n); seen.add(n);} });
    Object.keys(sections).sort().forEach(n=>{ if(!seen.has(n)){ orderedSecs.push(n); seen.add(n);} });

    // 逐章節、逐句子、逐 token 渲染
    orderedSecs.forEach(sec=>{
      const secEl = document.createElement('details');
      secEl.className='section'; secEl.open=true;
      secEl.innerHTML = `<summary>${htmlEscape(sec)}</summary><div class="sec-inner"></div>`;
      const inner = secEl.querySelector('.sec-inner');

      const sentIdx = Object.keys(sections[sec]).map(Number).sort((a,b)=>a-b);
      sentIdx.forEach(sidx=>{
        const toks = sections[sec][sidx];
        const sent = document.createElement('details');
        sent.className='sentence'; sent.open=true;
        sent.innerHTML = `<summary>tokens: ${toks.length}</summary><div class="sent-body"></div>`;
        const sbody = sent.querySelector('.sent-body');

        // token span：套上 lab-<BIO> 與 ent-<實體> 兩種 class
        toks.forEach(rec=>{
          const lab = String(rec.label||'O');
          const ent = lab==='O' ? 'O' : lab.replace(/^([BI]-)/,'');
          LABELS.add(lab);
          const labCls = lab==='O' ? 'O' : `lab-${lab.replace(/[^\\w-]/g,'-')}`;
          const span = document.createElement('span');
          span.className = `tok ${labCls} ent-${ent.replace(/[^\\w-]/g,'-')} ${lab==='O'?'O':''}`;
          span.dataset.ent = ent; span.dataset.label = lab;
          span.innerHTML = htmlEscape(rec.text).replace(/ /g,'&nbsp;'); // 保留空白視覺
          sbody.appendChild(span);
        });
        inner.appendChild(sent);
      });
      body.appendChild(secEl);
    });

    document.querySelector('#mainCol').appendChild(block);
  });

  rebuildSummary();     // 右欄摘要
  bindLegendToggles();  // 綁定圖例切換
}

/* ====== 下載 ====== */
function enableDownloads(obj){
  // 依是否有資料啟用下載按鈕；點擊時動態產生 JSONL 文字檔
  $('#dlSegments').disabled = !obj.segments;
  $('#dlTokens').disabled   = !obj.tokenRows;
  $('#dlLabeled').disabled  = !obj.labeled;
  if (obj.segments) $('#dlSegments').onclick = () =>
    downloadText('segments.jsonl', obj.segments.map(o=>JSON.stringify(o)).join('\\n'));
  if (obj.tokenRows) $('#dlTokens').onclick   = () =>
    downloadText('ner_token_rows.jsonl', obj.tokenRows.map(o=>JSON.stringify(o)).join('\\n'));
  if (obj.labeled)   $('#dlLabeled').onclick  = () =>
    downloadText('ner_labeled.jsonl', obj.labeled.map(o=>JSON.stringify(o)).join('\\n'));
}

/* ====== 事件 ====== */
$('#btnPreprocess').addEventListener('click', ()=>{
  // 只做斷段+分詞（不呼叫 HF）
  const txt   = $('#inText').value || '';
  const fname = $('#inFileName').value || 'pasted.txt';
  if (!txt.trim()){ $('#inStatus').textContent='請先貼上文字'; return; }
  $('#inStatus').textContent='處理中（斷段 + 分詞）…';
  const {files, segments, tokenRows} = preprocessRawToData(txt, fname);
  DATA[fname] = files[fname];   // 寫入全域 DATA
  LABELS.add('O');              // 至少有 O
  rebuildPage();                // 重新渲染
  $('#inStatus').textContent='完成（未做 NER）';
  // 下載：segments / tokenRows（labeled 先以 tokenRows 佔位）
  enableDownloads({segments, tokenRows, labeled: tokenRows});
});
$('#btnRunNER').addEventListener('click', async ()=>{
  // 斷段+分詞後，呼叫 HF API 產生 BIO 並回填，再渲染
  const txt   = $('#inText').value || '';
  const fname = $('#inFileName').value || 'pasted.txt';
  const model = $('#inModel').value || 'd4data/biomedical-ner-all';
  const token = $('#inToken').value.trim();
  if (!txt.trim()){ $('#inStatus').textContent='請先貼上文字'; return; }
  if (!token){     $('#inStatus').textContent='請填 Hugging Face Token'; return; }
  $('#inStatus').textContent='處理中（斷段 + 分詞 + NER）…';
  const {files, segments, tokenRows} = preprocessRawToData(txt, fname);
  DATA[fname] = files[fname];
  LABELS = new Set(['O']);      // 重新計算 LABELS
  try{
    await runNEROnFiles(DATA, model, token);
    // 平鋪含 BIO 的 labeled rows（多句多 token）
    const labeledRows=[];
    Object.keys(DATA).forEach(file=>{
      Object.keys(DATA[file]).forEach(sec=>{
        Object.keys(DATA[file][sec]).forEach(sidx=>{
          DATA[file][sec][sidx].forEach((t,i)=>{
            labeledRows.push({
              id: `${file}:${sec}:${sidx}:${i}`,
              meta: {file, section:sec, source_span:[null,null], sentence_index:+sidx, token_index:i},
              text: t.text, start: t.start, end: t.end, label: t.label
            });
          });
        });
      });
    });
    rebuildPage();
    $('#inStatus').textContent='完成：已套用 NER';
    enableDownloads({segments, tokenRows, labeled: labeledRows});
  }catch(err){
    console.error(err);
    $('#inStatus').textContent='HF API 失敗：' + err.message;
  }
});
$('#btnClear').addEventListener('click', ()=>{
  // 清空輸入與下載狀態（不動 DATA）
  $('#inText').value = '';
  $('#inStatus').textContent = '';
  $('#dlSegments').disabled = $('#dlTokens').disabled = $('#dlLabeled').disabled = true;
});

/* ====== 啟動 ====== */
(function init(){
  // 從內嵌 JSON 初始化（通常是空資料啟動）
  try{
    const init = JSON.parse(document.getElementById('__INIT__').textContent || "{}");
    DATA   = init.files  || {};
    LABELS = new Set((init.labels||['O']).length ? init.labels : ['O']);
  }catch(_){
    DATA = {}; LABELS = new Set(['O']);
  }
  rebuildPage();
})();
</script>
"""

HTML_TAIL = "</div></body></html>"

# ===== 產出 HTML =====
def render_html(init_files_map: Dict[str, Dict[str, Dict[int, list]]],
                labels_list: List[str],
                out_path: str,
                title: str,
                subtitle: str) -> None:
    palette = build_palette(labels_list or ["O"])
    # 後端先產 BIO 對應 CSS（前端仍會保底覆寫）
    css_rules = []
    for lab,(bg,bd) in palette.items():
        left = "3px" if lab.startswith("B-") else "1px"
        css_rules.append(f".lab-{cls_safe(lab)}{{background:{bg};border:1px solid {bd};border-left:{left} solid {bd};}}")
    css_rules = "\\n  ".join(css_rules)

    init_json = json.dumps(
        {"files": init_files_map or {}, "labels": sorted(set(labels_list or ["O"]))},
        ensure_ascii=False
    )

    html_out = []
    html_out.append(HTML_HEAD.format(title=esc(title), subtitle=esc(subtitle), css_rules=css_rules))
    html_out.append(HTML_INPUT)
    html_out.append(HTML_INIT_JSON.format(init_json=init_json))
    html_out.append(HTML_SCRIPT)
    html_out.append(HTML_TAIL)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("".join(html_out))

# ===== CLI =====
def build_argparser():
    ap = argparse.ArgumentParser(description="Paste text → segment/tokenize → optional HF NER → HTML")
    ap.add_argument("--out", default="ner_report.html", help="輸出 HTML 檔名")
    ap.add_argument("--title", default="臨床 NER 標註報告", help="頁面標題")
    ap.add_argument("--subtitle", default="貼上病歷文字 → 斷段/分詞 → 可套用 Hugging Face NER → 下載三種 JSONL", help="副標")
    return ap

def main():
    args = build_argparser().parse_args()
    # 空資料啟動；使用者貼文字後產生內容
    render_html(init_files_map={}, labels_list=["O"], out_path=args.out, title=args.title, subtitle=args.subtitle)
    print(f"[OK] wrote {args.out}")

if __name__ == "__main__":
    main()
