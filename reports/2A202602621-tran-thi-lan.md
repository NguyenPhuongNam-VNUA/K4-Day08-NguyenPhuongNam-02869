# Individual contribution report

---

## Thông tin

- Họ và tên: Trần Thị Lan
- Mã học viên: 2A202602621
- Nhóm: JKL
- Repository/branch: task 4-5-6

## Phần việc đã thực hiện

| Module/deliverable           | Việc tôi trực tiếp làm                                                                                                                                                                  | File/commit/PR                   | Trạng thái |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | ---------- |
| Task 4 — Chunking & Indexing | Implement `chunk_documents()` với recursive splitter, bảo toàn bảng biểu; `embed_texts()` dùng BAAI/bge-m3 qua SentenceTransformer; `index_to_vectorstore()` upsert vào ChromaDB cosine | `src/task4_chunking_indexing.py` | Done       |
| Task 5 — Semantic Search     | Implement `semantic_search()`: embed query, query ChromaDB, convert cosine distance thành similarity, sort giảm dần                                                                     | `src/task5_semantic_search.py`   | Done       |
| Task 6 — Lexical Search      | Implement `build_bm25_index()` và `lexical_search()` dùng rank-bm25, tokenize lowercase, sort score giảm dần                                                                            | `src/task6_lexical_search.py`    | Done       |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng BAAI/bge-m3 (1024 chiều) làm embedding model thay vì OpenAI text-embedding-3-small.
   **Lý do/evidence:** bge-m3 hỗ trợ tiếng Việt tốt, chạy hoàn toàn local không cần API key, phù hợp với corpus tuyển sinh.
   **Trade-off:** Thời gian encode chậm hơn API (~2-3x với batch nhỏ) nhưng không phát sinh chi phí và không phụ thuộc kết nối mạng.

2. **Quyết định:** Tách block bảng Markdown trước khi chunk, giữ nguyên header row ở mỗi sub-chunk của bảng lớn.
   **Lý do/evidence:** Bảng tuyển sinh chứa thông tin điểm chuẩn, ngành học; nếu cắt ngang header thì retrieval trả về dữ liệu không có ngữ cảnh cột.
   **Trade-off:** Logic phức tạp hơn (re.split + loop thủ công) nhưng đảm bảo mỗi chunk bảng vẫn độc lập đọc được.

## Kiểm thử và kết quả

- Test query đã dùng: "điểm chuẩn ngành Y đa khoa năm 2026", "chỉ tiêu tuyển sinh Bách Khoa Hà Nội", "phương thức xét tuyển Đại học Giao thông Vận tải"
- Kết quả: semantic_search trả về top-5 chunk có score cosine > 0.55 cho query đúng domain; score < 0.25 cho query ngoài domain (dùng để calibrate SCORE_THRESHOLD = 0.3).
- Lỗi đã phát hiện: ChromaDB báo lỗi upsert khi metadata chứa giá trị None — xử lý bằng cách chuyển None thành chuỗi rỗng trước khi upsert.

## Điều còn hạn chế

- BM25 trong Task 6 tokenize đơn giản (lowercase split), chưa có tách từ tiếng Việt (underthesea/pyvi), nên bỏ sót một số trường hợp ghép từ như "chính quy", "xét tuyển thẳng".
- Nếu có thêm thời gian, sẽ tích hợp underthesea.word_tokenize vào build_bm25_index() và đo lại recall trên golden dataset để xác nhận cải thiện.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Trần Thị Lan
