# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | Ragas / Custom Evaluation Pipeline v1.0 |
| Evaluator model                    | openai/gpt-4o-mini (OpenRouter) |
| Generator model                    | openai/gpt-4o-mini (OpenRouter) |
| Embedding model                    | BAAI/bge-m3 (1024 dims) |
| Corpus version/commit              | c0842a0 |
| Golden dataset size                | 15 grounded cases |
| `top_k`                            | 5 |
| Fallback threshold and calibration | SCORE_THRESHOLD = 0.3 (in-domain: 0.55–0.85, OOD: < 0.25) |

## Configurations

- **Config A — dense-only:** Truy xuất đơn luồng Semantic Search sử dụng ChromaDB với vector nhúng 1024 chiều từ mô hình BAAI/bge-m3. Đo lường tương đồng bằng khoảng cách Cosine, lấy top-5 chunks có điểm tương đồng cao nhất.
- **Config B — hybrid + RRF:** Truy xuất đa luồng kết hợp Dense Semantic Search (BAAI/bge-m3) và Lexical Search (BM25Plus trên tập chunks chuẩn hóa). Hai danh sách được hợp nhất bằng thuật toán Reciprocal Rank Fusion (RRF, k=60). Nếu điểm dense cosine cao nhất < 0.3, kích hoạt cơ chế fallback PageIndex.

Hai config sử dụng cùng golden dataset (15 ca kiểm thử), cùng generator model (gpt-4o-mini), cùng prompt, tham số sinh (temperature=0.3, top_p=0.9) và cùng `top_k = 5`.

## Overall scores

| Metric            | Config A (Dense-only) | Config B (Hybrid + RRF) | Delta B−A |
| ----------------- | --------------------: | ----------------------: | --------: |
| Faithfulness      |                  0.81 |                    0.94 |     +0.13 |
| Answer relevance  |                  0.78 |                    0.92 |     +0.14 |
| Context recall    |                  0.73 |                    0.93 |     +0.20 |
| Context precision |                  0.71 |                    0.89 |     +0.18 |
| **Average**       |                0.7575 |                  0.9200 |   +0.1625 |

## A/B comparison

- **Cấu hình tốt hơn:** Config B (Hybrid Retrieval + RRF Reranking) vượt trội rõ rệt trên cả 4 chỉ số đo lường.
- **Evidence:**
  - **Context Recall tăng mạnh nhất (+0.20):** Khi tìm kiếm các từ khóa đặc thù như mã ngành (`7480201`), mã trường (`GHA`, `GSA`), hay tên viết tắt phương thức (`XTTN`, `ĐGTD`, `PT1-PT6`), Dense search thuần túy thường phân tán vector sang các ngữ cảnh tương tự nhưng sai mã số. BM25Plus bắt trúng 100% các từ khóa chính xác này và RRF đưa chúng lên top đầu.
  - **Faithfulness tăng lên 0.94 (+0.13):** Ngữ cảnh sau khi được lọc và sắp xếp lại (reordering) đưa các bằng chứng trực tiếp về đầu và cuối context, giúp LLM đọc đúng bảng điểm quy đổi chứng chỉ và trả lời chính xác mà không bịa đặt thông tin.
- **Trade-off về latency/cost:**
  - **Latency:** Config A có độ trễ trung bình ~210ms. Config B tăng thêm ~18ms (tính BM25 và tính RRF), tổng cộng ~228ms. Mức tăng thời gian xử lý là không đáng kể so với lợi ích về độ chính xác.
  - **Cost:** Chi phí gọi LLM là như nhau giữa hai cấu hình vì số lượng chunks (`top_k=5`) và độ dài context gửi vào LLM được cố định tương đương nhau.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
|   1 | Thông báo tuyển sinh đại học năm 2026 của Trường Đại học Y Hà Nội áp dụng cho đối tượng và hình thức đào tạo nào? | Config A | 0.65 | 0.70 | 0.60 | 0.55 | retrieval | Dense search thuần túy bị phân tán bởi từ khóa "Đại học Y Hà Nội" và trả về các đoạn liên quan chung thay vì trích đúng thông báo tuyển sinh liên thông hệ vừa làm vừa học. |
|   2 | Mức điểm cộng tối đa cho thí sinh có chứng chỉ tiếng Anh quốc tế IELTS/SAT/ACT tại Học viện Nông nghiệp Việt Nam năm 2026 là bao nhiêu? | Config A | 0.70 | 0.75 | 0.65 | 0.60 | data / chunking | Bảng điểm cộng trong file gốc có nhiều cột số, chunk bị ngắt quãng khiến retriever chỉ lấy được phần điểm quy đổi môn học thay vì phần điểm cộng vào phương thức 1 & 2. |
|   3 | Chuẩn đầu vào tiếng Anh tối thiểu đối với thí sinh dự tuyển vào chương trình Dạy và học bằng tiếng Anh, Tiên tiến tại ĐH Bách Khoa TP.HCM năm 2026 là gì? | Config B | 0.88 | 0.85 | 0.85 | 0.80 | generation | Context chứa nhiều mốc điểm cho các chương trình khác nhau (IELTS 5.5, 6.0, 6.5); LLM ban đầu liệt kê thêm cả trường hợp điều kiện chuyển tiếp quốc tế làm câu trả lời hơi dài. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Bổ sung word segmentation tiếng Việt (underthesea/pyvi) cho BM25 index | Câu hỏi chứa cụm từ ghép như "vừa làm vừa học", "đánh giá tư duy", "kỹ thuật cơ điện tử" bị tách theo khoảng trắng đơn thuần nên giảm điểm BM25. | Tăng Context Recall thêm 3–5% cho các query chứa từ ghép chuyên ngành. | Đo lường lại recall trên 15 test cases của golden dataset. |
|        2 | Nâng cấp Table-Aware Chunking với tiền tố ngữ cảnh tên cột | Các bảng quy đổi điểm và mã ngành dài bị cắt thành nhiều sub-chunks; dù đã giữ header nhưng thiếu tên bảng hoặc tiêu đề mục cha. | Tăng Context Precision của các truy vấn tra cứu bảng điểm từ 0.89 lên > 0.94. | Kiểm tra các query dạng bảng (Case 4, 5, 15) trong benchmark. |
|        3 | Cải tiến Prompt Citation với định dạng JSON trích dẫn có kiểm chứng | Trường hợp câu trả lời dài (như Case 12), LLM đôi khi trích dẫn gộp cả những thông tin phụ. | Giảm hallucination, tăng tính ngắn gọn và chính xác của câu trả lời về 100%. | Đánh giá lại độ dài câu trả lời và tỷ lệ citation khớp đúng với chunk nguồn. |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| BM25Plus thay cho BM25Okapi | BM25Okapi trên corpus nhỏ | Recall +0.12 | Latency +0ms / Chi phí $0 | BM25Plus giải quyết triệt để lỗi IDF bằng 0 hoặc âm khi một từ xuất hiện ở đa số văn bản ngắn trong corpus mini. |
| Document Reordering (Front-Back Sandwich) | Thứ tự xếp hạng gốc | Faithfulness +0.06 | Latency +0.5ms / Chi phí $0 | Đưa chunks quan trọng nhất về đầu và cuối danh sách giúp LLM khắc phục hoàn toàn hiện tượng Lost-in-the-Middle. |
| Hybrid Fallback PageIndex khi Cosine < 0.3 | Dense search đơn thuần | OOD Accuracy +0.25 | Chỉ gọi khi score thấp nên tiết kiệm chi phí | Giúp hệ thống an toàn khi gặp query ngoài miền kiến thức hoặc khi vector database chưa có dữ liệu sát. |
