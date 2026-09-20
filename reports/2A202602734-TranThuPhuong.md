# Individual contribution report

## Thông tin

- Họ và tên: Tran Thu Phuong
- Mã học viên: 2A202602734
- Nhóm: JKL
- Repository/branch: K4-Day08-NguyenPhuongNam-02869 / phuong

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 - Thu thập tài liệu legal | Thu thập tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai và lưu vào thư mục dữ liệu legal. | `src/task1_collect_legal_docs.py`; `data/landing/legal/` | Done |
| Task 2 - Crawl bài viết/news | Cấu hình 5 URL công khai, crawl bài viết bằng Crawl4AI và lưu JSON với `url`, `title`, `date_crawled`, `content_markdown`. | `src/task2_crawl_news.py`; `data/landing/news/` | Done |
| Task 3 - Chuẩn hóa Markdown | Chuyển tài liệu legal và bài viết news sang Markdown, giữ metadata ở đầu file và duy trì hai thư mục output tương ứng. | `src/task3_convert_markdown.py`; `data/standardized/legal/`, `data/standardized/news/` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Giữ cấu trúc thư mục riêng cho `legal` và `news` từ landing đến standardized.  
   **Lý do/evidence:** Các module Task 1-3 dùng chung cấu trúc `data/landing/` và `data/standardized/`, giúp các task sau đọc dữ liệu theo đúng loại tài liệu.  
   **Trade-off:** Cần duy trì hai luồng xử lý riêng thay vì dùng một hàm convert cho mọi loại đầu vào.

2. **Quyết định:** Lưu metadata nguồn trong JSON news và phần đầu Markdown.  
   **Lý do/evidence:** Giữ được URL, tiêu đề, thời gian crawl và loại tài liệu để truy xuất nguồn ở các bước chunking và generation.  
   **Trade-off:** File Markdown có thêm phần header, nhưng dữ liệu có thể kiểm chứng nguồn rõ ràng hơn.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m py_compile src/task1_collect_legal_docs.py src/task2_crawl_news.py src/task3_convert_markdown.py`.
- Kết quả trước/sau nếu có: Ba module Task 1-3 không có lỗi cú pháp; dữ liệu đầu ra được tổ chức theo đúng thư mục legal/news.
- Lỗi đã phát hiện và cách xử lý: Quá trình crawl/convert phụ thuộc mạng, Crawl4AI, Playwright và MarkItDown; các lỗi từng URL được xử lý riêng để không làm dừng toàn bộ quá trình crawl.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: Nguồn công khai có thể thay đổi hoặc chặn crawler, khiến việc thu thập cần chạy lại hoặc thay URL.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: Bổ sung kiểm tra kích thước, MIME type và báo cáo tổng hợp số file thành công/thất bại sau mỗi lần chạy.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Tran Thu Phuong
