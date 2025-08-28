# 臨床 NER HTML 報告產生器
一款輕量級的 Python CLI 工具，用於生成獨立的雙欄式 HTML 報告頁面。使用者可在瀏覽器中貼上醫療文本，完成段落拆分、分詞，並可呼叫 Hugging Face 推論 API 進行實體識別（NER）。
<img width="1308" height="674" alt="image" src="https://github.com/user-attachments/assets/d37e56d4-ecdd-4db6-8ae0-0d3695203a26" />

使用教學（步驟）

在瀏覽器開啟 ner_report.html。

在頁面左欄的「➕ 貼上病歷文字並處理」區塊：

輸入「工作表名稱」（檔名標籤，預設 pasted.txt）

（可選）輸入「HF 模型」，預設 d4data/biomedical-ner-all

（可選）輸入「HF Token」（格式 hf_xxx...）

貼上整段病歷文字到 textarea。

選擇：

① 只斷段 + 分詞：離線處理，僅切章節/分句/分詞，不做 NER。

② 斷段 + 分詞 + NER：在分詞後呼叫 HF API 做 NER（需要 Token）。

右側 Legend 可一鍵全選/全不選；也可逐一切換實體顯示強度。

右側「標註摘要」會自動彙總每章節連續實體片段。

可下載三種 JSONL：segments.jsonl、ner_token_rows.jsonl、ner_labeled.jsonl。

Hugging Face Token 申請

註冊或登入 Hugging Face：https://huggingface.co/join

前往 Access Tokens：https://huggingface.co/settings/tokens

建立 New token，權限選 Read。

複製顯示的 Token（格式 hf_xxx...），貼到網頁右上設定欄位（或輸入框）中。

注意：若 Token 無效或過期，呼叫 API 會回 401；頁面會顯示錯誤訊息。

# 技術棧
- Python 3.7+（僅使用標準函式庫：argparse、json、html、re、typing）
- HTML5、CSS3、現代 JavaScript (ES6+)
- Hugging Face 推論 API（瀏覽器端 fetch，需輸入 HF Token）

# 安裝

確認系統已安裝 Python 3.8+

python3 --version

下載程式碼

git clone 
cd repo

不需額外安裝套件，程式僅使用 Python 標準函式庫。
