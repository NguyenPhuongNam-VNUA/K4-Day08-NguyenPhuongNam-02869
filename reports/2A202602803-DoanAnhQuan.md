# Individual contribution report

## Thông tin

- Họ và tên: Đoàn Anh Quân
- Mã học viên: 2A202602803
- Nhóm: JKL
- Repository/branch: K4-Day08-NguyenPhuongNam-02869 / DAQuan

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 8 - PageIndex vectorless fallback | Upload tài liệu standardized lên PageIndex, cache `doc_id`, chờ tree sẵn sàng (`is_retrieval_ready`), và hiện thực `pageindex_search()` trả về `SearchResult` với `retrieval_method = "pageindex"`. | `src/task8_pageindex_vectorless.py`; commit `0568682` | Done |
| Chuyển Markdown sang PDF cho PageIndex | Ưu tiên PDF gốc trong `data/landing/`; nếu không có thì convert Markdown sang PDF text-based bằng `fpdf2` với font Unicode để giữ dấu tiếng Việt, heading giữ bằng cỡ chữ lớn. | `_pdf_for()`, `_markdown_to_pdf()`, `_find_font()` trong file trên | Done |
| Xử lý lỗi/timeout dịch vụ ngoài | Timeout tổng 30s cho mỗi lần search, query song song theo document, bỏ qua document lỗi, trả kết quả một phần khi timeout. | `pageindex_search()`, `_query_document()` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Cache `source -> doc_id` vào `data/pageindex_doc_ids.json` và ghi ngay sau mỗi lần upload thành công.  
   **Lý do/evidence:** Upload và dựng tree trên PageIndex chậm (chờ tối đa 300s); ghi cache từng file giúp lần chạy sau không upload lại kể cả khi lần trước bị ngắt giữa chừng. File cache hỏng được coi như chưa có cache thay vì làm crash.  
   **Trade-off:** Nếu nội dung tài liệu đổi mà tên file giữ nguyên thì cache trả doc cũ; cần xóa entry thủ công.

2. **Quyết định:** Query các document song song, rồi xếp hạng bằng cách xen kẽ theo rank trong từng document và gán `score = 1 / (1 + vị trí)`.  
   **Lý do/evidence:** API PageIndex trả node theo từng document và không có score dùng chung giữa các document, nên không so sánh score trực tiếp được. Xen kẽ theo rank tránh một document chiếm hết `top_k`; song song hóa giữ tổng độ trễ trong giới hạn 30s.  
   **Trade-off:** Score chỉ phản ánh thứ hạng, không phải độ tương đồng thật, nên không dùng làm ngưỡng tuyệt đối khi so với score của dense/hybrid.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m py_compile src/task8_pageindex_vectorless.py`; chạy `python src/task8_pageindex_vectorless.py` để upload và cache document IDs.
- Kết quả trước/sau nếu có: Trước đó file chỉ là skeleton; sau commit `0568682` (+228/-10 dòng) module biên dịch không lỗi và có đủ luồng upload, cache, search, parse. Chưa có số liệu evaluation riêng cho PageIndex trong `reports/RESULT.md`.
- Lỗi đã phát hiện và cách xử lý: PDF sinh từ Markdown mất dấu tiếng Việt nếu thiếu font Unicode, nên thêm danh sách font ứng viên và biến môi trường `PAGEINDEX_FONT_PATH`. URL dài không có khoảng trắng làm PDF tràn dòng, xử lý bằng `wrapmode="CHAR"`. Thiếu `PAGEINDEX_API_KEY` thì báo lỗi rõ ràng.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: `pageindex_search()` phụ thuộc mạng và API key ngoài; khi timeout chỉ trả kết quả một phần, và `url` trong metadata luôn là `None` vì PDF upload không giữ URL nguồn của bài news.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Lưu metadata nguồn (URL, tiêu đề gốc) cùng `doc_id` trong cache, và đo độ trễ/recall của PageIndex so với dense/hybrid trên golden dataset.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Đoàn Anh Quân
