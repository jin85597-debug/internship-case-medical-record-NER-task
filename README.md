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

說明：
這裡匯入了程式需要用到的標準模組。

argparse：用來處理命令列參數，例如輸出檔名、標題、副標。

json：用來把 Python 的資料結構轉成 JSON 格式，方便輸出到前端或寫入檔案。

html：提供 html.escape 等函式，用於 HTML 轉義。

re：正則表達式模組，用來做字串替換或模式比對。

typing 中的 Dict、List：型別標註用，幫助程式可讀性，說明函式參數與回傳的資料結構。

如果要改：
要增加新的外部功能，就在這裡多匯入需要的模組；要改正則或 JSON 格式相關的處理，也會跟這裡匯入的工具有關。

# 後端：HTML 產出的小工具

```python
def esc(s: str) -> str:
    return html.escape(str(s), quote=False)
```

說明：
這個函式的目的是將輸入的文字做 HTML 字元轉義，避免被當成 HTML 標籤或導致 XSS。

參數 s：傳入的任意資料，會先被轉成字串。

html.escape：將特殊字元轉換成 HTML 安全格式，例如 & 變成 &，< 變成 <，> 變成 >，" 變成 "。

quote=False：代表不轉換單引號與雙引號。

如果要改：
若想連引號也轉換，將 quote=False 改成 True。若想加入額外過濾，例如單引號變成 '，需要自己再加 replace。

```python
def cls_safe(s: str) -> str:
return re.sub(r"[^a-zA-Z0-9_-]+", "-", s)
```
說明：
這個函式會把輸入的字串轉成安全可用於 CSS class 名稱的形式。

使用正則表達式 re.sub，將所有不是字母、數字、底線、連字號的字元，通通換成一個連字號。

例如輸入 "心臟病" 會變成 "---"，輸入 "B-DISEASE" 則保持不變。

如果要改：
如果需要支援中文 class 名稱，可以在正則裡加入中文 Unicode 範圍，例如 \u4e00-\u9fff。
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
說明：
這個函式用來生成 BIO 標籤的配色方案。

先把標籤去掉 B- 或 I- 前綴，只留下實體名稱，例如 DISEASE。

去掉 O，因為 O 代表非實體。

uniq = sorted(set(ents))，得到去重且排序後的實體清單。

total 是實體的數量，用來計算色相的分配。

hue = int(360 * i / total)，每個實體分配不同的顏色，平均分佈在色環上。

B- 開頭的標籤用較深顏色，I- 開頭的標籤用較淺顏色。

O 類型設成透明背景和淡灰色虛線邊框。

如果要改：
可以調整 HSL 裡面的亮度或飽和度，控制顏色深淺；或者對特定實體強制指定顏色，例如 "DISEASE" 永遠用紅色。
