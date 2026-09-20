"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
import re
from pathlib import Path
from markitdown import MarkItDown

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"

LEGAL_TITLES = {
    "dai_hoc_y": "Thông báo Tuyển sinh trình độ Đại học năm 2026 – Trường Đại học Y Hà Nội",
    "gtvt": "Đề án Tuyển sinh Đại học hệ chính quy năm 2026 – Trường Đại học Giao thông Vận tải",
    "hust_ts": "Đề án Tuyển sinh Đại học năm 2026 – Đại học Bách khoa Hà Nội",
}


def clean_markdown_tables(text: str) -> str:
    """Chuẩn hóa bảng biểu Markdown và loại bỏ các dòng lặp rác từ quá trình bóc tách."""
    lines = text.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            # Thu thập các dòng của bảng
            table_rows = []
            while i < len(lines):
                cur = lines[i].strip()
                if cur.startswith("|") and cur.endswith("|"):
                    cells = [c.strip() for c in cur.split("|")[1:-1]]
                    # Bỏ qua các dòng rỗng toàn pipe
                    if any(cells):
                        table_rows.append(cells)
                    # Bỏ qua các dòng text lặp lại các ô trong hàng này
                    cell_set = set(cells) - {""}
                    j = i + 1
                    while j < len(lines):
                        nxt = lines[j].strip()
                        if not nxt or nxt in cell_set:
                            j += 1
                        else:
                            break
                    i = j
                elif not cur:
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
                        i += 1
                    else:
                        break
                else:
                    break

            if table_rows:
                max_cols = max(len(r) for r in table_rows)
                # Kiểm tra nếu chưa có dòng phân cách header thì tự tạo
                has_separator = any(all(set(c) <= {"-", ":", " "} for c in r) for r in table_rows)
                norm_rows = [r + [""] * (max_cols - len(r)) for r in table_rows]
                md_table = []
                if not has_separator:
                    md_table.append("| " + " | ".join(norm_rows[0]) + " |")
                    md_table.append("| " + " | ".join([":---"] * max_cols) + " |")
                    for r in norm_rows[1:]:
                        md_table.append("| " + " | ".join(r) + " |")
                else:
                    for r in norm_rows:
                        md_table.append("| " + " | ".join(r) + " |")
                cleaned.append("\n" + "\n".join(md_table) + "\n")
        else:
            cleaned.append(line)
            i += 1

    result = "\n".join(cleaned)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


def convert_legal_docs() -> None:
    """Convert PDF/DOCX sang Markdown chuẩn hóa với Header Metadata."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)
    converter = MarkItDown()

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        result = converter.convert(str(path))
        content = str(result.text_content or "").strip()
        if not content:
            print(f"Skipped empty document: {path}")
            continue

        title = LEGAL_TITLES.get(path.stem, path.stem.replace("_", " ").title())
        header = (
            f"# {title}\n\n"
            f"**Source:** {path.name}\n\n"
            f"**Doc-Type:** legal\n\n---\n\n"
        )
        clean_content = clean_markdown_tables(content)
        destination = output_dir / f"{path.stem}.md"
        destination.write_text(header + clean_content + "\n", encoding="utf-8")
        print(f"Converted Legal: {destination.name} ({len(clean_content)} chars)")


def convert_news_articles() -> None:
    """Convert JSON bài viết sang Markdown chuẩn hóa với Header Metadata và bảng sạch."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    required = {"url", "title", "date_crawled", "content_markdown"}

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not required <= data.keys():
            print(f"Skipped incomplete article: {path}")
            continue
        content = str(data["content_markdown"] or "").strip()
        if not content:
            print(f"Skipped empty article: {path}")
            continue

        clean_content = clean_markdown_tables(content)
        title = str(data["title"]).strip()
        if title.startswith("#"):
            title = title.lstrip("#").strip()

        header = (
            f"# {title}\n\n"
            f"**Source:** {str(data['url']).strip()}\n\n"
            f"**Doc-Type:** news\n\n"
            f"**Crawled:** {str(data['date_crawled']).strip()}\n\n---\n\n"
        )
        destination = output_dir / f"{path.stem}.md"
        destination.write_text(header + clean_content + "\n", encoding="utf-8")
        print(f"Converted News: {destination.name} ({len(clean_content)} chars)")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing sang standardized."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"\nSaved standardized Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
