"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF/DOCX từ nguồn công khai."""
    # TODO: Có thể tải thủ công hoặc dùng requests.
    #
    # Ví dụ:
    # import requests
    #
    # sources = {
    #     "policy-a.pdf": "https://example.edu/policy-a.pdf",
    # }
    # for filename, url in sources.items():
    #     response = requests.get(url, timeout=30)
    #     response.raise_for_status()
    #     (DATA_DIR / filename).write_bytes(response.content)
    import requests

    sources = {
        "qghn.pdf": (
            "https://cdnportal.vnu.edu.vn/data/0/documents/2026/03/20/upload_2/955-qd-dhqghn-2026.pdf"
        ),
        "dai_hoc_y.pdf": (
            "https://apiwebhmu.hmu.edu.vn/Upload/Images/ba09fde5-4e13-4e03-83c9-62592a5a4404.pdf"
        ),
        "gtvt.pdf": (
            "https://tuyensinh.utc2.edu.vn/uploads/img/files/414-Thong%20tin%20TS%20Dai%20hoc%20chinh%20quy%202026%20cap%20nhat.pdf"
        ),
    }

    setup_directory()
    for filename, url in sources.items():
        destination = DATA_DIR / filename
        if destination.exists() and destination.stat().st_size > 0:
            print(f"Exists: {destination}")
            continue

        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "k4-day08-rag-pipeline/0.1"},
        )
        response.raise_for_status()
        if not response.content:
            raise ValueError(f"Empty response for {url}")
        destination.write_bytes(response.content)
        print(f"Downloaded: {destination}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
