"""
Task 8 — PageIndex vectorless fallback.

Hướng dẫn:
    1. Đọc PAGEINDEX_API_KEY từ .env.
    2. Upload tài liệu ở định dạng PageIndex hỗ trợ.
    3. Cache document IDs để không upload lại.
    4. Parse kết quả thành SearchResult có method pageindex.

PageIndex là dịch vụ ngoài: cần timeout và xử lý lỗi để pipeline không crash.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout, as_completed
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
DOC_IDS_PATH = Path(__file__).parent.parent / "data" / "pageindex_doc_ids.json"
PDF_DIR = Path(__file__).parent.parent / "data" / "pageindex_pdfs"

READY_TIMEOUT_SECONDS = 300  # PageIndex cần thời gian dựng tree sau khi upload.
SEARCH_TIMEOUT_SECONDS = 30  # Tổng thời gian tối đa cho một lần pageindex_search.
POLL_INTERVAL_SECONDS = 1.0

# PDF của PageIndex cần font Unicode để không mất dấu tiếng Việt.
FONT_CANDIDATES = [
    os.getenv("PAGEINDEX_FONT_PATH", ""),
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _get_client():
    from pageindex import PageIndexClient

    if not PAGEINDEX_API_KEY:
        raise RuntimeError("PAGEINDEX_API_KEY is not set")
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def _load_doc_ids() -> dict[str, str]:
    """Đọc cache source -> doc_id; file hỏng thì coi như chưa có cache."""
    try:
        data = json.loads(DOC_IDS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_doc_ids(doc_ids: dict[str, str]) -> None:
    DOC_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_IDS_PATH.write_text(
        json.dumps(doc_ids, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _find_font() -> str:
    for candidate in FONT_CANDIDATES:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError(
        "No Unicode TTF font found for PDF conversion; "
        "set PAGEINDEX_FONT_PATH to a .ttf file that supports Vietnamese"
    )


def _markdown_to_pdf(markdown_path: Path, pdf_path: Path) -> None:
    """Convert Markdown sang PDF text-based; heading được giữ bằng cỡ chữ lớn."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("Body", "", _find_font())
    pdf.add_page()

    sizes = {1: 18, 2: 15, 3: 13}
    for raw in markdown_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip():
            pdf.ln(3)
            continue
        stripped = line.lstrip("#")
        level = len(line) - len(stripped)
        is_heading = 0 < level <= 6 and stripped.startswith(" ")
        pdf.set_font("Body", size=sizes.get(level, 11) if is_heading else 10)
        pdf.multi_cell(
            0,
            7 if is_heading else 5.5,
            stripped.strip() if is_heading else line,
            wrapmode="CHAR",  # URL dài không có khoảng trắng vẫn xuống dòng được
            new_x="LMARGIN",
            new_y="NEXT",
        )
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(pdf_path))


def _pdf_for(markdown_path: Path) -> Path:
    """Ưu tiên PDF gốc trong landing/legal, nếu không có thì convert từ Markdown."""
    relative = markdown_path.relative_to(STANDARDIZED_DIR)
    original = LANDING_DIR / relative.with_suffix(".pdf")
    if original.is_file():
        return original
    pdf_path = PDF_DIR / relative.with_suffix(".pdf")
    _markdown_to_pdf(markdown_path, pdf_path)
    return pdf_path


def _wait_until_ready(client, doc_id: str, timeout: float = READY_TIMEOUT_SECONDS) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if client.is_retrieval_ready(doc_id):
            return True
        time.sleep(POLL_INTERVAL_SECONDS * 3)
    return False


def upload_documents() -> None:
    """Upload tài liệu và lưu document IDs để tái sử dụng."""
    client = _get_client()
    doc_ids = _load_doc_ids()

    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        source = path.relative_to(STANDARDIZED_DIR).as_posix()
        if source in doc_ids:
            print(f"Cached: {source} -> {doc_ids[source]}")
            continue
        try:
            pdf_path = _pdf_for(path)
            doc_id = client.submit_document(str(pdf_path))["doc_id"]
        except Exception as exc:
            print(f"Upload failed for {source}: {exc}")
            continue
        # Lưu ngay để lần chạy sau không upload lại nếu bị ngắt giữa chừng.
        doc_ids[source] = doc_id
        _save_doc_ids(doc_ids)
        print(f"Uploaded: {source} -> {doc_id}")

    for source, doc_id in doc_ids.items():
        if not _wait_until_ready(client, doc_id):
            print(f"Not ready yet (still processing): {source} -> {doc_id}")
    print(f"Saved document IDs to: {DOC_IDS_PATH}")


def _query_document(client, doc_id: str, query: str, deadline: float) -> list[dict]:
    """Chạy một retrieval trên một document, trả về danh sách node đã retrieve."""
    retrieval_id = client.submit_query(doc_id, query)["retrieval_id"]
    while time.monotonic() < deadline:
        response = client.get_retrieval(retrieval_id)
        status = response.get("status")
        if status == "completed":
            return response.get("retrieved_nodes") or []
        if status == "failed":
            return []
        time.sleep(POLL_INTERVAL_SECONDS)
    return []


def _node_text(node: dict) -> str:
    """Ghép nội dung từ relevant_contents; fallback sang các field text thường gặp."""
    parts = [
        str(item.get("relevant_content", "")).strip()
        for item in node.get("relevant_contents") or []
        if isinstance(item, dict)
    ]
    text = "\n\n".join(part for part in parts if part)
    if not text:
        text = str(node.get("text") or node.get("content") or "").strip()
    return text


def _source_metadata(source: str) -> dict:
    path = Path(source)
    return {
        "source": path.name,
        "title": path.stem,
        "doc_type": "legal" if "legal" in path.parts else "news",
        "url": None,
    }


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Trả về pageindex SearchResult."""
    if not query.strip() or top_k <= 0:
        return []

    doc_ids = _load_doc_ids()
    if not doc_ids:
        return []

    deadline = time.monotonic() + SEARCH_TIMEOUT_SECONDS
    client = _get_client()

    # Query các document song song; tài liệu nào lỗi thì bỏ qua, không làm hỏng cả search.
    per_doc: dict[str, list[dict]] = {}
    executor = ThreadPoolExecutor(max_workers=min(8, len(doc_ids)))
    try:
        futures = {
            executor.submit(_query_document, client, doc_id, query, deadline): source
            for source, doc_id in doc_ids.items()
        }
        try:
            for future in as_completed(futures, timeout=SEARCH_TIMEOUT_SECONDS):
                try:
                    per_doc[futures[future]] = future.result()
                except Exception as exc:
                    print(f"PageIndex query failed for {futures[future]}: {exc}")
        except FutureTimeout:
            print("PageIndex search timed out; using partial results")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    # API không trả score chung giữa các document: xen kẽ theo rank trong từng
    # document rồi gán score giảm dần theo thứ hạng.
    candidates = []
    for source in sorted(per_doc):
        for rank, node in enumerate(per_doc[source]):
            text = _node_text(node)
            if text:
                candidates.append((rank, source, node, text))
    candidates.sort(key=lambda item: (item[0], item[1]))

    results, seen, chunk_counts = [], set(), {}
    for rank, source, node, text in candidates:
        node_key = str(node.get("node_id") or len(seen))
        result_id = f"{source}::pageindex-{node_key}"
        if result_id in seen:
            continue
        seen.add(result_id)
        chunk_index = chunk_counts.get(source, 0)
        chunk_counts[source] = chunk_index + 1
        metadata = _source_metadata(source)
        if node.get("title"):
            metadata["section"] = str(node["title"])
        results.append({
            "id": result_id,
            "content": text,
            "score": 1.0 / (1 + len(results)),
            "metadata": {**metadata, "chunk_index": chunk_index},
            "retrieval_method": "pageindex",
        })
        if len(results) >= top_k:
            break
    return results


if __name__ == "__main__":
    upload_documents()
