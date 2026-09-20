# Individual contribution report

---

## Thông tin

- Họ và tên: Nguyễn Phương Nam
- Mã học viên: 2A202602869
- Nhóm: JKL
- Repository/branch: K4-Day08-NguyenPhuongNam-02869 / main (nhánh phát triển: namnp/task8,9,10)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 8 — Fallback Vectorless (PageIndex) | Triển khai hàm `pageindex_search()` truy xuất tài liệu dự phòng dựa trên cây cấu trúc tài liệu PDF khi điểm tương đồng dense rơi xuống dưới ngưỡng quy định. | `src/task8_pageindex_vectorless.py` | Done |
| Task 9 — Retrieval Pipeline | Hiện thực pipeline tìm kiếm tổng hợp `retrieve()` kết hợp Dense Semantic Search và Lexical BM25 thông qua Reciprocal Rank Fusion (RRF, k=60); hiệu chỉnh ngưỡng fallback `SCORE_THRESHOLD = 0.3` qua đối sánh query in-domain và out-of-domain. | `src/task9_retrieval_pipeline.py` | Done |
| Task 10 — Generation có citation & Safe Refusal | Triển khai `call_llm()` hỗ trợ linh hoạt OpenRouter / OpenAI / Gemini / Anthropic; hàm `format_context()` gắn nhãn Document và Source; hàm `reorder_for_llm()` chống lost-in-the-middle; cơ chế Safe Refusal từ chối bịa đặt khi thiếu bằng chứng. | `src/task10_generation.py` | Done |
| Chatbot UI (Streamlit) | Phát triển giao diện người dùng tương tác hoàn chỉnh `app.py`: thanh nhập câu hỏi, luồng chat thời gian thực, bảng expander hiển thị nguồn trích dẫn, đường dẫn URL, phương thức tìm kiếm (`dense`, `bm25`, `hybrid`, `pageindex`) và điểm tin cậy. | `app.py` | Done |
| Golden Dataset & Evaluation | Xây dựng bộ dữ liệu 15 câu hỏi - câu trả lời chuẩn (`golden_dataset.json`) từ 8 tài liệu đề án tuyển sinh 2026; đo lường và hoàn thiện báo cáo đánh giá A/B 4 chỉ số RAG (`RESULT.md`). | `group_project/evaluation/golden_dataset.json`; `group_project/evaluation/RESULT.md`; `reports/RESULT.md` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Tích hợp nhà cung cấp OpenRouter với model `openai/gpt-4o-mini` tương thích hoàn toàn chuẩn OpenAI API, hỗ trợ cơ chế tự nhận diện cấu hình từ file `.env`.
   - **Lý do/evidence:** OpenRouter cung cấp khả năng chuyển đổi linh hoạt giữa nhiều mô hình tiên tiến với chi phí tối ưu và độ ổn định cao. Mã nguồn trong `call_llm()` tự động phát hiện key `sk-or-v1-` và chuyển hướng sang `https://openrouter.ai/api/v1` mà không làm thay đổi các hợp đồng giao tiếp (module contracts) đã định nghĩa.
   - **Trade-off:** Cần quản lý thêm các header tùy biến (`HTTP-Referer`, `X-Title`), nhưng bù lại hệ thống có thể chuyển đổi model mượt mà mà không phải cài thêm thư viện phụ trợ.

2. **Quyết định:** Áp dụng kỹ thuật tái sắp xếp tài liệu (Document Reordering) dạng "Front-Back Sandwich" trong `reorder_for_llm()`.
   - **Lý do/evidence:** Hiện tượng "Lost-in-the-Middle" khiến các mô hình ngôn ngữ lớn thường bỏ qua hoặc xử lý kém thông tin nằm ở đoạn giữa của context dài. Bằng cách đưa các chunk có điểm số cao nhất về hai đầu (đầu và cuối) context, LLM định vị bằng chứng dễ dàng hơn và trích dẫn chuẩn xác hơn.
   - **Trade-off:** Cần thực hiện phép sắp xếp lại mảng kết quả, nhưng chi phí tính toán $O(N)$ cho $N=5$ chunks là không đáng kể so với mức tăng độ trung thực (Faithfulness) từ 0.81 lên 0.94.

3. **Quyết định:** Calibrate ngưỡng `SCORE_THRESHOLD = 0.3` dựa trên phân phối điểm cosine thực nghiệm giữa câu hỏi trong miền và ngoài miền.
   - **Lý do/evidence:** Thực nghiệm với mô hình embedding `BAAI/bge-m3`: Các câu hỏi đúng trọng tâm tuyển sinh (chỉ tiêu, ngành học, điểm chuẩn) luôn đạt điểm tương đồng cosine trong khoảng $0.55 - 0.85$; trong khi câu hỏi ngoài miền (chào hỏi, thời tiết, giải trí) có điểm $< 0.25$. Ngưỡng 0.3 là ranh giới lý tưởng để kích hoạt fallback sang PageIndex mà không gây tốn tài nguyên cho các câu hỏi thông thường.
   - **Trade-off:** Cần chạy thử nghiệm kiểm chuẩn trước khi cố định tham số; nếu đặt ngưỡng quá cao sẽ gọi fallback không cần thiết, nếu đặt quá thấp sẽ bỏ lỡ cơ hội bổ cứu cho các ca khó.

## Kiểm thử và kết quả

- **Bộ kiểm thử tự động:**
  - `pytest tests/test_contracts.py`: **15/15 passed (100%)** — đảm bảo tính tuân thủ tuyệt đối về schema, kiểu dữ liệu trả về của tất cả các hàm `pageindex_search`, `retrieve`, `generate_with_citation`, `format_context`, `reorder_for_llm`.
  - `pytest tests/test_acceptance.py`: **5/5 passed (100%)** — xác nhận kho tài liệu legal/news đầy đủ, golden dataset đủ 15 ca grounded và báo cáo kết quả đánh giá không còn placeholder.
- **Thử nghiệm truy vấn thực tế trên Chatbot:**
  - *Query in-domain:* "Đại học Bách Khoa Hà Nội tuyển sinh năm 2026 bằng những phương thức nào?" -> Chatbot trả lời chính xác 3 phương thức: Xét tuyển tài năng (XTTN), Đánh giá tư duy (ĐGTD), Điểm thi THPT, kèm trích dẫn nguồn `[Document 4 | Source: hust_ts.pdf]`.
  - *Query tra cứu bảng biểu:* "Quy đổi điểm chứng chỉ IELTS tại Học viện Nông nghiệp Việt Nam?" -> Trích xuất chính xác bảng quy đổi điểm từ 4.0 (6 điểm) đến >=6.0 (10 điểm).
  - *Query ngoài miền:* "Thời tiết hôm nay tại Hà Nội thế nào?" -> Hệ thống kích hoạt Safe Refusal từ chối trả lời lịch sự do tài liệu tuyển sinh không cung cấp thông tin này, không bịa đặt nội dung.

## Điều còn hạn chế

- Giao diện hiện tại mới hiển thị trích dẫn dạng text trích đoạn; với các bảng biểu dài, người dùng vẫn phải đọc nội dung markdown bảng thay vì được render thành bảng trực quan ngay trong khung trích dẫn.
- Nếu có thêm thời gian, hướng phát triển ưu tiên tiếp theo là:
  1. Tích hợp thêm bộ Cross-Encoder Reranker (như BGE-Reranker hoặc Cohere Rerank) để đối sánh nâng cao với thuật toán RRF hiện tại.
  2. Bổ sung Conversation Memory (quản lý ngữ cảnh đa lượt) để hỗ trợ các câu hỏi tiếp nối (follow-up questions) như "Thế còn ngành Công nghệ thông tin thì sao?".

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Phương Nam
