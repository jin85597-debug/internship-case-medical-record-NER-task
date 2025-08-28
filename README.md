# 臨床 NER HTML 報告產生器
一款輕量級的 Python CLI 工具，用於生成獨立的雙欄式 HTML 報告頁面。使用者可在瀏覽器中貼上醫療文本，完成段落拆分、分詞，並可選擇呼叫 Hugging Face 推論 API 進行實體識別（NER）。報告頁面支援穩定色彩渲染、標籤顯示/隱藏、標註摘要，並可下載三種 JSONL 格式輸出：segments.jsonl / ner_token_rows.jsonl / ner_labeled.jsonl。
# 主要功能
- 一條命令生成可互動的 HTML 報告
- 離線段落拆分與分詞
- 選擇性呼叫 Hugging Face API 進行 BIO NER
- 基於實體類型的穩定 HSL 配色
- 雙欄佈局：主欄文件/章節/句子可折疊，側欄圖例與摘要
- 圖例開關：可顯示或隱藏特定實體
- 自動生成標註摘要列表
- 下載三種 JSONL 輸出：
- segments.jsonl（段落片段）
- ner_token_rows.jsonl（原始 token，預設標籤為 O）
- ner_labeled.jsonl（帶 BIO 標籤的 token）
# 技術棧
- Python 3.7+（僅使用標準函式庫：argparse、json、html、re、typing）
- HTML5、CSS3、現代 JavaScript (ES6+)
- Hugging Face 推論 API（瀏覽器端 fetch，需輸入 HF Token）

