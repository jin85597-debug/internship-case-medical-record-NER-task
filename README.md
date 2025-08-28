# 臨床 NER HTML 報告產生器

一款輕量級的 Python CLI 工具，用於生成獨立的雙欄式 HTML 報告頁面。使用者可在瀏覽器中貼上醫療文本，完成段落拆分、分詞，並可呼叫 Hugging Face 推論 API 進行實體識別（NER）。

<img width="1308" height="674" alt="image" src="https://github.com/user-attachments/assets/d37e56d4-ecdd-4db6-8ae0-0d3695203a26" />

# 架構說明

# 維護者在修改任一段程式碼前，應先確認此架構原則。

# 任何引入外部依賴、改變執行模式的行為，都可能破壞 SCRIPT 的獨立性與可攜性。

這份 SCRIPT 是設計成可完全在本機 HTML 環境中執行的標註工具。除了標註階段需要呼叫 NER API，其餘所有功能（資料處理、渲染、切割、斷詞、匯出、下載）皆可在瀏覽器中離線完成，不依賴任何外部服務。

整體程式碼採用純 JavaScript，無框架、無編譯流程，所有邏輯直接嵌入 HTML 中，確保部署簡單、維護透明、操作穩定。

此架構原則影響所有模組與工具函式的設計方式，包括：

- 所有 DOM 操作統一透過 $ / $$ 處理

- 所有資料處理皆在前端完成，不依賴後端轉換
  
- 所有匯出皆透過 downloadText() 直接觸發下載
  
- 除了 API 呼叫外，不使用 async/await
  
- 不使用任何第三方函式庫或框架

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

#  HTML 頁首模版
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

# JSON初始化模板
```php_template
HTML_INIT_JSON = """
<script id="__INIT__" type="application/json">{init_json}</script>
"""
```
### 目的：建立初始化資料的嵌入區塊，將 JSON 結構注入頁面供前端程式讀取。

`<script id="__INIT__" type="application/json">`：嵌入型 JSON 區塊，使用 application/json MIME 類型，id 為 INIT

`{init_json}`：佔位符，用於插入初始化 JSON 字串內容

### 如果要改：

改資料來源：調整 {init_json} 的生成方式

改 script 標籤位置：移動至 head 或 body 其他區段

改識別名稱：變更 id="INIT"

改 MIME 類型：僅限於 application/json，不可改為 text/javascript

改嵌入方式：改用 data-* 屬性或其他 DOM 注入策略

# HTML_SCRIPT函式部分
```php_template
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
          span.innerHTML = htmlEscape(rec.text).replace(/ /g,'&bsp;'); // 保留空白視覺
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
```
 #  基本工具/常數 
```php_template
const $  = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
function htmlEscape(s){
  return (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
function slug(s){
  return (s||'').toLowerCase()
    .replace(/[^a-z0-9\\u4e00-\\u9fff_-]+/g,'-')
    .replace(/^-|-$/g,'');                      
}
function natKey(s){
  return (s+'').split(/(\\d+)/).map(p => /^\\d+$/.test(p) ? Number(p) : p.toLowerCase());
}
const natCmp = (a, b) => {
  const ka = natKey(a), kb = natKey(b);
  for (let i = 0; i < Math.max(ka.length, kb.length); i++) {
    if (ka[i] == null) return -1;            
    if (kb[i] == null) return 1;             
    if (ka[i] < kb[i]) return -1;
    if (ka[i] > kb[i]) return 1;
  }
  return 0;
};
function downloadText(filename, text){

  const blob = new Blob([text], {type:'application/json;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
```
## 解釋
 ```php_template
const $  = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
```


```php_template
function htmlEscape(s){
  return (s||'').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
```

 ```php_template
function slug(s){
  return (s||'').toLowerCase()
    .replace(/[^a-z0-9\\u4e00-\\u9fff_-]+/g,'-')
    .replace(/^-|-$/g,'');                      
}
```

 ```php_template
function natKey(s){
  return (s+'').split(/(\\d+)/).map(p => /^\\d+$/.test(p) ? Number(p) : p.toLowerCase());
}
```

 ```php_template
const natCmp = (a, b) => {
  const ka = natKey(a), kb = natKey(b);
  for (let i = 0; i < Math.max(ka.length, kb.length); i++) {
    if (ka[i] == null) return -1;            
    if (kb[i] == null) return 1;             
    if (ka[i] < kb[i]) return -1;
    if (ka[i] > kb[i]) return 1;
  }
  return 0;
};
```

 ```php_template
function downloadText(filename, text){
  const blob = new Blob([text], {type:'application/json;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
```




