# 臨床 NER HTML 報告產生器

一款輕量級的 Python CLI 工具，用於生成獨立的雙欄式 HTML 報告頁面。使用者可在瀏覽器中貼上醫療文本，完成段落拆分、分詞，並可呼叫 Hugging Face 推論 API 進行實體識別（NER）。

<img width="1308" height="674" alt="image" src="https://github.com/user-attachments/assets/d37e56d4-ecdd-4db6-8ae0-0d3695203a26" />

# 使用教學（步驟）

# Hugging Face Token 申請

註冊或登入 Hugging Face：https://huggingface.co/join

前往 Access Tokens：https://huggingface.co/settings/tokens

建立 New token，權限選 Read。

複製顯示的 Token（格式 hf_xxx...），貼到網頁右上設定欄位（或輸入框）中。

注意：若 Token 無效或過期，呼叫 API 會回 401；頁面會顯示錯誤訊息。

# 技術棧
- Python 3.7+（僅使用標準函式庫：argparse、json、html、re、typing）
- HTML5、CSS3、現代 JavaScript (ES6+)
- Hugging Face 推論 API（瀏覽器端 fetch，需輸入 HF Token）

# 匯入模組
```
import argparse, json, html, re
from typing import Dict, List
```

## 說明：
這裡匯入了程式需要用到的標準模組。

argparse：用來處理命令列參數，例如輸出檔名、標題、副標。

json：用來把 Python 的資料結構轉成 JSON 格式，方便輸出到前端或寫入檔案。

html：提供 html.escape 等函式，用於 HTML 轉義。

re：正則表達式模組，用來做字串替換或模式比對。

typing 中的 Dict、List：型別標註用，幫助程式可讀性，說明函式參數與回傳的資料結構。

### 如果要改：

要增加新的外部功能，就在這裡多匯入需要的模組；要改正則或 JSON 格式相關的處理，也會跟這裡匯入的工具有關。

# 後端：HTML 產出的小工具
```python
def esc(s: str) -> str:
    return html.escape(str(s), quote=False)

def cls_safe(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", s)

def build_palette(labels: List[str]):
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
```


## 說明：
```python
def esc(s: str) -> str:
    return html.escape(str(s), quote=False)
```
這個函式的目的是將輸入的文字做 HTML 字元轉義，避免被當成 HTML 標籤或導致 XSS。

參數 s：傳入的任意資料，會先被轉成字串。

html.escape：將特殊字元轉換成 HTML 安全格式，例如 & 變成 &，< 變成 <，> 變成 >，" 變成 "。

quote=False：代表不轉換單引號與雙引號。

### 如果要改：

若想連引號也轉換，將 quote=False 改成 True。若想加入額外過濾，例如單引號變成 '，需要自己再加 replace。

## 說明：
```python
def cls_safe(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", s)
```
這個函式會把輸入的字串轉成安全可用於 CSS class 名稱的形式。

使用正則表達式 re.sub，將所有不是字母、數字、底線、連字號的字元，通通換成一個連字號。

例如輸入 "心臟病" 會變成 "---"，輸入 "B-DISEASE" 則保持不變。

### 如果要改：

如果需要支援中文 class 名稱，可以在正則裡加入中文 Unicode 範圍，例如 \u4e00-\u9fff。

## 說明：
```python
def build_palette(labels: List[str]):
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
```
這個函式用來生成 BIO 標籤的配色方案。

先把標籤去掉 B- 或 I- 前綴，只留下實體名稱，例如 DISEASE。

去掉 O，因為 O 代表非實體。

uniq = sorted(set(ents))，得到去重且排序後的實體清單。

total 是實體的數量，用來計算色相的分配。

hue = int(360 * i / total)，每個實體分配不同的顏色，平均分佈在色環上。

B- 開頭的標籤用較深顏色，I- 開頭的標籤用較淺顏色。

O 類型設成透明背景和淡灰色虛線邊框。

### 如果要改:

可以調整 HSL 裡面的亮度或飽和度，控制顏色深淺；或者對特定實體強制指定顏色，例如 "DISEASE" 永遠用紅色。

#  HTML 頁首模板
```php-template
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
```

## 說明:
```php-template
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
```
### 目的：建立 HTML5 頁面骨架、設定語系與基礎 SEO/響應式標頭，並放入全域 CSS 變數與標題/副標題的基本樣式。

`<!doctype html>`：指定 HTML5，避免瀏覽器進怪異模式。

`<html lang="zh-Hant">`：主要語系為繁體中文，影響拼字檢查、螢幕閱讀器與搜尋引擎語言判定。

`<meta charset="utf-8"/>`：UTF-8 編碼，避免中文字亂碼。

`<meta name="viewport" content="width=device-width, initial-scale=1"/>`：mobile-first 響應式，寬度隨裝置，初始縮放 1。

`<title>{title}</title>`：頁面標題，{title} 是後端用 .format() 動態填入。

`:root{{--bg:#fff;--ink:#1f2937;--muted:#64748b;--card:#f7fafc;--line:#e5e7eb;--accent:#0b5fff;--chip:#f2f4f8}}`：定義全站 CSS 變數（背景、字色、輔助色、邊框色、強調色等），方便統一調色。

`html,body{{background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,Segoe UI,Roboto,Helvetica,Arial,'Noto Sans',sans-serif;margin:0}}`：套用全域字型與顏色、移除預設邊距。

`.wrap{{max-width:1280px;margin:28px auto;padding:0 18px}}`：中心容器，最大寬度 1280px，置中並留左右內距。

`h1{{margin:0 0 6px 0;font-size:28px;font-weight:800}}`：主標題字級、粗細、間距。

`.intro{{color:var(--muted);margin:2px 0 14px 0}}`：副標題的字色與間距，使用較 muted 的顏色變數。

### 如果要改：

改語系：把 <html lang="zh-Hant"> 換成 en、ja 等。

改標題：呼叫 render_html 時傳入不同 title。

改副標題：同上傳入不同 subtitle，或刪除 .intro 的輸出。

改整體配色：只需調整 :root 的變數值（例如 --bg, --ink, --accent）。

改版面寬度：調整 .wrap 的 max-width 或左右 padding。

改字型：在 html,body 的 font-family 裡增刪字體（注意字體回退順序）。

## 說明:
```php-template
/* 兩欄 */
.layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;margin-top:12px}
.aside{position:sticky;top:64px;align-self:start;max-height:calc(100vh - 80px);overflow:auto;padding:4px 0;padding-right:4px}
@media (max-width:1100px){ .layout{grid-template-columns:1fr} .aside{position:static;max-height:none;overflow:visible;padding:0} }
```

### 目的：建立主內容與側欄的兩欄排版，並在窄螢幕下自動轉為單欄，提升閱讀性與響應式體驗。

`.layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:16px;margin-top:12px}`：使用 CSS Grid 建立兩欄結構，左側主欄自動撐滿，右側側欄固定寬度 340px，欄間距 16px，與上方區塊間距 12px。

`.aside{position:sticky;top:64px;align-self:start;max-height:calc(100vh - 80px);overflow:auto;padding:4px 0;padding-right:4px}`：側欄 sticky 固定在視窗頂部 64px 處，並限制最大高度為視窗高度減 80px，內容可滾動，內距設定避免捲軸壓線。

`@media (max-width:1100px){ .layout{grid-template-columns:1fr} .aside{position:static;max-height:none;overflow:visible;padding:0} }`：當螢幕寬度小於 1100px 時，自動改為單欄排版，側欄取消 sticky 並移除高度限制與捲動，改為完整顯示。

### 如果要改：

改側欄寬度：調整 .layout 的 grid-template-columns。

改 sticky 高度：調整 .aside 的 top 值。

改響應式斷點：修改 @media 的 max-width 數值。

## 說明:
```php-template
/* 卡片 */
.file-block{border:1px solid var(--line);border-radius:14px;margin:16px 0;background:#fff}
.file-head{padding:12px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}
.file-title{font-size:16px;font-weight:700}
.file-sub{color:var(--muted);font-size:12px}
.file-body{padding:8px 14px 14px 14px}
```
### 目的：建立每個檔案區塊的卡片樣式，包含標題列與內容區，提升視覺分隔與可讀性。

`.file-block{border:1px solid var(--line);border-radius:14px;margin:16px 0;background:#fff}`：卡片容器，白底、圓角 14px、上下間距 16px，邊框使用全域線色。

`.file-head{padding:12px 16px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}`：卡片標題列，左右排版，內距 12px 上下、16px 左右，底部加一條分隔線。

`.file-title{font-size:16px;font-weight:700}`：主標題字級 16px，粗體。

`.file-sub{color:var(--muted);font-size:12px}`：副標題字級 12px，使用 muted 色系。

`.file-body{padding:8px 14px 14px 14px}`：卡片內容區，內距設定為上 8px、左右 14px、下 14px。

### 如果要改：

改圓角：調整 .file-block 的 border-radius。

改背景色：修改 .file-block 的 background。

改排版方式：可改 .file-head 的 display 為 grid 或 block。

改字級：調整 .file-title 與 .file-sub 的 font-size。

改間距：調整 .file-body 的 padding。

## 說明:
```php-template
/* 區塊 */
details.section{margin:10px 0;border:1px solid var(--line);border-radius:10px;background:#fbfdff}
details>summary{cursor:pointer;padding:8px 12px;font-weight:700;color:#374151;list-style:none;border-bottom:1px solid var(--line)}
details>summary::-webkit-details-marker{display:none}
.sec-inner{padding:8px 12px}
details.sentence{margin:8px 0;border:1px dashed var(--line);border-radius:10px;background:var(--card)}
details.sentence>summary{cursor:pointer;padding:8px 10px;color:var(--muted);font-size:12px;list-style:none}
.sent-body{padding:8px 10px}
```
### 目的:建立可展開的區塊與句子樣式，用於分段與逐句呈現 NER 標註結果，提升可讀性與互動性。

`details.section{margin:10px 0;border:1px solid var(--line);border-radius:10px;background:#fbfdff}`：主區塊容器，上下間距 10px，實線邊框、圓角 10px，背景色為淡藍色 #fbfdff。

`details>summary{cursor:pointer;padding:8px 12px;font-weight:700;color:#374151;list-style:none;border-bottom:1px solid var(--line)}`：區塊標題列，游標可點擊，內距 8px 上下、12px 左右，字重 700，字色 #374151，無項目符號，底部加一條分隔線。

`details>summary::-webkit-details-marker{display:none}`：隱藏預設展開箭頭，避免干擾自訂樣式。

`.sec-inner{padding:8px 12px}`：區塊內容區，內距 8px 上下、12px 左右。

`details.sentence{margin:8px 0;border:1px dashed var(--line);border-radius:10px;background:var(--card)}`：句子容器，上下間距 8px，虛線邊框、圓角 10px，背景色使用全域變數 --card。

`details.sentence>summary{cursor:pointer;padding:8px 10px;color:var(--muted);font-size:12px;list-style:none}`：句子標題列，游標可點擊，內距 8px 上下、10px 左右，字色使用 muted 色系，字級 12px，無項目符號。

`.sent-body{padding:8px 10px}`：句子內容區，內距 8px 上下、10px 左右。

### 如果要改：

改圓角：調整 border-radius。

改背景色：修改 section 或 sentence 的 background。

改標題字級與字色：調整 summary 的 font-size 與 color。

改展開箭頭樣式：可自行加入 ::after 或 SVG 元素。

### 如果要改：

改圓角：調整 section 的 border-radius。

改展開顏色：修改 [open] 狀態的 border-color。

改標題字級：調整 summary 的 font-size。

改展開箭頭樣式：自行加入 ::after 或 SVG 元素。

## 說明:
```php-template
/* token */
.tok{display:inline-block;margin:1px 2px;padding:2px 4px;border-radius:6px;line-height:1.9}
.tok.O{opacity:.85;border:1px dashed rgba(0,0,0,.18)}
```
### 目的：定義每個 token 的呈現方式，用於顯示 NER 標註後的文字單元，具備間距、邊框與可視性調整。

`.tok{display:inline-block;margin:1px 2px;padding:2px 4px;border-radius:6px;line-height:1.9}`：每個 token 使用 inline-block 排版，設定上下間距 1px、左右間距 2px，內距 2px 上下、4px 左右，圓角 6px，行高 1.9 提升可讀性。

`.tok.O{opacity:.85;border:1px dashed rgba(0,0,0,.18)}`：未標註類別的 token（BIO 標記為 "O"），透明度降低至 85%，並使用虛線邊框（rgba 灰色）區隔。

### 如果要改：

改 token 間距：調整 .tok 的 margin 或 padding。

改圓角：修改 border-radius。

改未標註樣式：調整 .tok.O 的 opacity 或 border 顏色／樣式。


## 說明:
```php-template
/* 右欄 */
.aside-card{border:1px solid var(--line);border-radius:14px;background:#fff;margin:0 0 14px 0}
.aside-head{padding:12px 14px;border-bottom:1px solid var(--line);font-weight:700;display:flex;justify-content:space-between;align-items:center}
.aside-body{padding:10px 12px}
```
### 目的：建立右側資訊卡片的樣式，用於顯示輔助說明、圖例或控制元件，具備視覺分隔與一致排版。

`.aside-card{border:1px solid var(--line);border-radius:14px;background:#fff;margin:0 0 14px 0}`：整體卡片容器，白底、圓角 14px、底部間距 14px，邊框使用全域線色。

`.aside-head{padding:12px 14px;border-bottom:1px solid var(--line);font-weight:700;display:flex;justify-content:space-between;align-items:center}`：卡片標題列，內距 12px 上下、14px 左右，底部加一條分隔線，字重 700，使用 flex 排版，左右對齊並垂直置中。

`.aside-body{padding:10px 12px}`：卡片內容區，內距 10px 上下、12px 左右。

### 如果要改：

改圓角：調整 .aside-card 的 border-radius。

改排版方式：可改 .aside-head 的 display 為 grid 或 block。

改間距：調整 padding 值以改變內部空間感。

改背景色：修改 .aside-card 的 background。

## 說明:
```php-template
/* Legend */
.legend{display:flex;flex-direction:column;gap:6px}
.legend .chip{display:flex;width:100%;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:var(--chip);border:1px solid var(--line);font-size:12px}
.legend .swatch{width:12px;height:12px;border-radius:3px;border:1px solid rgba(0,0,0,.25);display:inline-block}
.panel{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.chip.btn{cursor:pointer}
.search{background:#fff;border:1px solid var(--line);border-radius:8px;padding:6px 10px;color:var(--ink)}
.ta{width:100%;height:180px;border:1px solid var(--line);border-radius:10px;padding:10px}
```
### 目的：定義圖例區塊、控制面板、互動按鈕與輸入欄位的樣式，用於輔助標註操作與使用者互動。
`.legend{display:flex;flex-direction:column;gap:6px}`：圖例容器，使用 flex 垂直排列，每項間距 6px。

`.legend .chip{display:flex;width:100%;align-items:center;gap:8px;padding:6px 10px;border-radius:999px;background:var(--chip);border:1px solid var(--line);font-size:12px}`：每個圖例項目，橢圓形背景（border-radius:999px），左右內距 6px/10px，項目間距 8px，字級 12px，背景色使用全域 chip 色，邊框使用全域線色。

`.legend .swatch{width:12px;height:12px;border-radius:3px;border:1px solid rgba(0,0,0,.25);display:inline-block}`：色塊指示器，寬高 12px，圓角 3px，邊框為灰色半透明，inline-block 顯示。

`.panel{display:flex;flex-wrap:wrap;gap:12px;align-items:center}`：控制面板容器，使用 flex 排版，允許換行，項目間距 12px，垂直置中。

`.chip.btn{cursor:pointer}`：互動按鈕樣式，設定游標為 pointer。

`.search{background:#fff;border:1px solid var(--line);border-radius:8px;padding:6px 10px;color:var(--ink)}`：搜尋框樣式，白底、圓角 8px、內距 6px/10px，字色使用 ink 色，邊框使用全域線色。

`.ta{width:100%;height:180px;border:1px solid var(--line);border-radius:10px;padding:10px}`：文字輸入框（textarea）樣式，寬度 100%、高度 180px，圓角 10px，內距 10px，邊框使用全域線色。


### 如果要改：

改 chip 外觀：調整 padding、border-radius 或背景色。

改色塊大小：修改 .swatch 的 width / height。

改 panel 排版：調整 flex-wrap 或 gap。

改輸入框尺寸：修改 .ta 的 width / height / padding。

改搜尋框字型與顏色：調整 .search 的 font-family 或 color。

## 說明:
```php-template
/* TOC */
.toc{margin:14px 0 18px 0;display:flex;flex-wrap:wrap;gap:10px}
.toc a{text-decoration:none;color:var(--accent);font-size:13px;border:1px solid var(--line);padding:4px 8px;border-radius:8px;background:#fff
```
### 目的：建立標註類型導覽區（TOC），用於快速跳轉至各類標註區塊，提升頁面導覽效率與使用者體驗。

`.toc{margin:14px 0 18px 0;display:flex;flex-wrap:wrap;gap:10px}`：TOC 容器，使用 flex 排版，允許換行（flex-wrap），項目間距 10px，上下外距分別為 14px 與 18px。

`.toc a{text-decoration:none;color:var(--accent);font-size:13px;border:1px solid var(--line);padding:4px 8px;border-radius:8px;background:#fff`：導覽連結樣式，移除底線（text-decoration:none），字色使用強調色 accent，字級 13px，白底、圓角 8px、內距 4px 上下 / 8px 左右，邊框使用全域線色。

### 如果要改：

改 TOC 排版：調整 .toc 的 flex-wrap、gap 或 margin。

改連結樣式：修改 .toc a 的 font-size、color、padding 或 border-radius。

改背景色或互動狀態：可加入 hover 或 active 樣式提升可點擊感。

## 說明:
```php-template
/* 動態 BIO 樣式（由 Python 產） */
{css_rules}
</style></head><body><div class="wrap"><h1>{title}</h1><div class="intro">{subtitle}</div>
```
### 目的：保留 CSS 插槽供 Python 動態產生 BIO 樣式，並建立 HTML 主體結構，包含容器、標題與副標題。

`{css_rules}`：插槽由後端 Python 產生，用於插入各類 BIO 標註樣式（例如 .tok.PER、.tok.ORG 等），支援多類型命名實體的視覺呈現。

`</style>`：結束 CSS 區塊。

`</head>`：結束 head 區塊，準備進入頁面主體。

`<body>`：開始 HTML 主體內容。

`<div class="wrap">`：主容器，控制整體寬度與左右內距，對應前面 CSS 中的 .wrap 樣式。

`<h1>{title}</h1>`：主標題，內容由後端以 .format() 動態填入。

`<div class="intro">{subtitle}</div>`：副標題區塊，使用 muted 色系，內容同樣由後端動態填入。
    
### 如果要改：
    
改 BIO 樣式：請在 Python 端定義 {css_rules} 的內容。

改標題文字：呼叫 render_html 時傳入不同 title。

改副標題樣式：調整 .intro 的 CSS 或移除該區塊。

改容器寬度與內距：修改 .wrap 的 max-width 或 padding。

# HTML 輸入模板
```php_template
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
```
## 說明:
```php-template
  <div class="layout">
    <div id="mainCol">
```
### 目的：建立輸入模板的主容器，包含左側主欄與右側 aside 區塊。

`<div class="layout">`:整體排版容器，負責左右欄配置

`<div id="mainCol">`:主欄容器，包含輸入卡片與標註類型導覽區

### 如果要改：
    
改排版方式：調整 .layout 的 display 或 flex 設定

改主欄寬度：修改 #mainCol 的 CSS

改欄位順序：調整 layout 下的子元素順序

## 說明:
```php-template
 <details open class="file-block">
        <summary class="file-head" style="cursor:pointer">
          <div class="file-title">➕ 貼上病歷文字並處理</div>
          <div class="file-sub">離線可用；填 Hugging Face Token 可直接 NER</div>
        </summary>
```
### 目的:建立輸入卡片的標題區塊，顯示操作提示與模型使用說明。

`<details open class="file-block">`：輸入卡片容器，預設展開

`<summary class="file-head" style="cursor:pointer">`：卡片標題列，游標可點擊展開/收合

`<div class="file-title">`：主標題文字，顯示「➕ 貼上病歷文字並處理」

`<div class="file-sub">`：副標題文字，顯示「離線可用；填 Hugging Face Token 可直接 NER」

###如果要改：

改展開狀態：移除 open 屬性

改標題文字：修改 .file-title 的內容

改副標題文字：修改 .file-sub 的內容

改展開樣式：調整 .file-head 的 cursor 或 summary 樣式

改卡片命名：變更 class="file-block" 以符合語意

## 說明:
```php_template
 <div class="file-body">
          <div class="panel" style="margin-bottom:8px">
            <span class="chip">工作表名稱 <input id="inFileName" class="search" style="width:180px" value="pasted.txt"/></span>
            <span class="chip">HF 模型 <input id="inModel" class="search" style="width:240px" value="d4data/biomedical-ner-all"/></span>
            <span class="chip">HF Token <input id="inToken" class="search" style="width:260px" placeholder="hf_xxx"/></span>
          </div>
```
### 目的:建立模型設定區塊，提供使用者輸入檔名、指定 Hugging Face 模型與 Token。

`<div class="file-body">`：輸入卡片內容容器

`<div class="panel" style="margin-bottom:8px">`：輸入欄容器，下方間距 8px

`<span class="chip">`：欄位包裝單元，使用 chip 樣式

`<input id="inFileName" class="search" style="width:180px" value="pasted.txt"/>`：檔名輸入框，預設值 pasted.txt

`<input id="inModel" class="search" style="width:240px" value="d4data/biomedical-ner-all"/>`：模型名稱輸入框，預設值 d4data/biomedical-ner-all

`<input id="inToken" class="search" style="width:260px" placeholder="hf_xxx"/>`：Token 輸入框，提示文字 hf_xxx

## 說明:
```php_template
<textarea id="inText" class="ta" placeholder="在此貼上整段病歷文字…"></textarea>
          <div class="panel" style="margin-top:10px">
            <span class="chip btn" id="btnPreprocess">① 只斷段 + 分詞</span>
            <span class="chip btn" id="btnRunNER">② 斷段 + 分詞 + NER</span>
            <span class="chip btn" id="btnClear">清除貼上結果</span>
```
### 目的:建立病歷輸入區與執行操作按鈕，供使用者貼上文字並選擇處理方式。

`<textarea id="inText" class="ta" placeholder="在此貼上整段病歷文字…">`：多行文字輸入欄，使用 ta 樣式，提示文字為「在此貼上整段病歷文字…」

`<div class="panel" style="margin-top:10px">`：操作按鈕容器，頂部間距 10px
    
`<span class="chip btn" id="btnPreprocess">`：執行「只斷段 + 分詞」按鈕

`<span class="chip btn" id="btnRunNER">`：執行「斷段 + 分詞 + NER」按鈕

`<span class="chip btn" id="btnClear">`：清除貼上結果按鈕

### 如果要改：

改輸入欄高度：調整 .ta 的 CSS

改提示文字：修改 placeholder 屬性

改按鈕文字：直接修改 span 內容

改按鈕順序：調整 span 排列順序

改按鈕樣式：修改 .chip.btn 的 CSS 定義

改按鈕功能：調整 JS 綁定的事件處理邏輯

## 說明:
```php_template
<span class="chip">下載：
  <button type="button" id="dlSegments" class="btn" disabled style="margin-left:4px">segments.jsonl</button>
  <button type="button" id="dlTokens" class="btn" disabled>ner_token_rows.jsonl</button>
  <button type="button" id="dlLabeled" class="btn" disabled>ner_labeled.jsonl</button>
</span>
```
### 目的：建立下載區塊，提供使用者匯出處理後的 JSONL 結果檔案。

`<span class="chip">`：下載區容器，使用 chip 樣式

`<button type="button" id="dlSegments" class="btn" disabled style="margin-left:4px">`：下載斷段結果 segments.jsonl，左側間距 4px，預設 disabled

`<button type="button" id="dlTokens" class="btn" disabled>`：下載分詞結果 ner_token_rows.jsonl，預設 disabled

`<button type="button" id="dlLabeled" class="btn" disabled>`：下載標註結果 ner_labeled.jsonl，預設 disabled

### 如果要改：

改檔案名稱：修改 button 顯示文字

改啟用狀態：移除 disabled 或由 JS 控制

改按鈕順序：調整 button 排列順序

改按鈕樣式：修改 .btn 的 CSS 定義

改間距設定：調整 style="margin-left:..." 或使用 CSS 類別

## 說明:
```php_template
  </div>
          <div id="inStatus" class="intro" style="margin-top:6px"></div>
        </div>
      </details>
      <div class="toc" id="toc"></div>
    </div>
```
### 目的：結束輸入卡片區塊並建立標註類型導覽區，供使用者快速跳轉至各類標註結果。

`</div>`：結束下載區塊容器

`<div id="inStatus" class="intro" style="margin-top:6px">`：狀態提示容器，使用 intro 樣式，頂部間距 6px

`</div>`：結束 file-body 區塊

`</details>`：結束輸入卡片容器

`<div class="toc" id="toc">`：標註類型導覽容器，使用 toc 樣式，由 JS 動態填入

`</div>`：結束主欄容器 mainCol

### 如果要改：

改狀態提示樣式：修改 .intro 的 CSS

改導覽區排版：調整 .toc 的 flex 或 gap 設定

改導覽內容：由 JS 控制 toc 的填入邏輯

改容器結構：調整結束順序或包裝層級

改導覽命名：變更 id="toc" 以符合語意

## 說明:
```php_template
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
```
### 目的：建立右欄標籤選擇區，提供使用者快速選取或取消所有標註類型，並顯示標籤圖例。

`<aside class="aside">`：右欄容器，包含標籤與摘要卡片

`<div class="aside-card">`：標籤選擇卡片容器

`<div class="aside-head">`：卡片標題列，顯示「標籤」文字

`<span>`：按鈕群組容器

`<button type="button" class="chip btn" id="selAll">`：全選按鈕，id 為 selAll

`<button type="button" class="chip btn" id="selNone">`：全不選按鈕，id 為 selNone

`<div class="aside-body">`：卡片內容容器

`<div class="legend" id="legend">`：標籤圖例容器，由 JS 動態填入

###如果要改：

改按鈕文字：直接修改 button 內容

改按鈕功能：調整 JS 綁定邏輯

改圖例內容：由 JS 控制 legend 的填入方式

改卡片樣式：修改 .aside-card 的 CSS

改按鈕排列方式：調整 span 的排版設定

改右欄寬度：修改 .aside 的 CSS 定義

## 說明:
```php_template
   <div class="aside-card">
        <div class="aside-head">標註摘要</div>
        <div class="aside-body" id="annSummary"></div>
      </div>
    </aside>
  </div>
```
### 目的：建立右欄標註摘要區塊，顯示目前標註結果的統計或彙整資訊。

`<div class="aside-card">`：標註摘要卡片容器
    
`<div class="aside-head">`：卡片標題列，顯示「標註摘要」文字
    
`<div class="aside-body" id="annSummary">`：摘要內容容器，id 為 annSummary，由 JS 動態填入

`</aside>`：結束右欄容器

`</div>`：結束整體 layout 容器

### 如果要改：

改標題文字：修改 .aside-head 的內容

改摘要樣式：調整 .aside-body 或 #annSummary 的 CSS

改填入邏輯：修改 JS 對 annSummary 的更新方式

改卡片順序：調整 aside-card 的排列順序

改右欄排版：修改 .aside 的寬度或位置設定



