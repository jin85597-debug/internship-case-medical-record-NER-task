# 臨床 NER HTML 報告產生器
一款輕量級的 Python CLI 工具，用於生成獨立的雙欄式 HTML 報告頁面。使用者可在瀏覽器中貼上醫療文本，完成段落拆分、分詞，並可呼叫 Hugging Face 推論 API 進行實體識別（NER）。
# 主要功能
單檔 HTML：城市碼執行後直接以瀏覽器開啟.HTML即可使用，不需額外伺服器。

離線可用：基本的斷段、分詞完全本地完成。

雲端 NER：若輸入 Hugging Face Token，會呼叫 Hugging Face API（預設模型：d4data/biomedical-ner-all）。

章節切割：自動辨識「診斷、主訴、過去病史、住院治療經過」等章節。

BIO 標註上色：B- 深色、I- 淺色、O 虛線框，不同實體採 HSL 均分色相，確保穩定配色。

右側控制面板：
Legend：一鍵全選/全不選、逐實體開關顯示。

摘要：自動彙總每個章節中的連續實體片段。

資料下載：介面可直接下載三種 JSONL：

分句結果:segments.jsonl

分詞結果:ner_token_rows.jsonl

BIO 標註結果:ner_labeled.jsonl
# 技術棧
- Python 3.7+（僅使用標準函式庫：argparse、json、html、re、typing）
- HTML5、CSS3、現代 JavaScript (ES6+)
- Hugging Face 推論 API（瀏覽器端 fetch，需輸入 HF Token）

