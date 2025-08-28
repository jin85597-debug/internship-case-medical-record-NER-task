# 臨床 NER HTML 報告產生器
一款輕量級的 Python CLI 工具，用於生成獨立的雙欄式 HTML 報告頁面。使用者可在瀏覽器中貼上醫療文本，完成段落拆分、分詞，並可選擇呼叫 Hugging Face 推論 API 進行實體識別（NER）。報告頁面支援穩定色彩渲染、標籤顯示/隱藏、標註摘要，並可下載三種 JSONL 格式輸出：段落、原始 token，以及帶 BIO 標籤的 token。
