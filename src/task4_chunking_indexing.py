"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

from pathlib import Path
import re


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    # TODO: Dispatch theo EMBEDDING_PROVIDER trong .env.
    
    #Provider local gợi ý:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model.encode(texts).tolist()
    raise NotImplementedError("Implement embed_texts")


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    # TODO: Tạo hoặc mở persistent collection.
    
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    raise NotImplementedError("Implement get_collection")


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document với metadata đầy đủ."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        raw_text = path.read_text(encoding="utf-8")
        title = path.stem
        source = path.name
        doc_type = "legal" if "legal" in path.parts else "news"
        url = None

        lines = raw_text.split("\n")
        header_end_idx = -1
        for i, line in enumerate(lines[:15]):
            stripped = line.strip()
            if stripped.startswith("# ") and title == path.stem:
                title = stripped[2:].strip()
            elif stripped.startswith("**Source:**"):
                val = stripped.split("**Source:**", 1)[1].strip()
                source = val
                if val.startswith("http://") or val.startswith("https://"):
                    url = val
            elif stripped.startswith("**Doc-Type:**"):
                doc_type = stripped.split("**Doc-Type:**", 1)[1].strip()
            elif stripped == "---" and i > 0:
                header_end_idx = i
                break

        if header_end_idx != -1:
            content = "\n".join(lines[header_end_idx + 1:]).strip()
        else:
            content = raw_text.strip()

        documents.append({
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                "source": source,
                "title": title,
                "doc_type": doc_type,
                "url": url,
            },
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index, bảo toàn tính toàn vẹn của bảng biểu."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for document in documents:
        content = document["content"]
        blocks = re.split(r"(\n(?:\|[^\n]+\|\n?)+)", content)
        doc_chunks_text = []

        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            is_table = len(lines) >= 2 and all(l.startswith("|") and l.endswith("|") for l in lines)

            if is_table:
                if len(block) <= CHUNK_SIZE:
                    doc_chunks_text.append(block)
                else:
                    has_sep = len(lines) > 1 and all(set(c) <= {"-", ":", " "} for c in lines[1].split("|")[1:-1])
                    header_count = 2 if has_sep else 1
                    header_str = "\n".join(lines[:header_count])
                    data_rows = lines[header_count:]

                    curr_rows = []
                    curr_len = len(header_str)

                    for r in data_rows:
                        added_len = len(r) + 1
                        if len(header_str) + added_len > CHUNK_SIZE:
                            if curr_rows:
                                doc_chunks_text.append(header_str + "\n" + "\n".join(curr_rows))
                                curr_rows = []
                                curr_len = len(header_str)
                            doc_chunks_text.extend(splitter.split_text(r))
                        elif curr_len + added_len <= CHUNK_SIZE:
                            curr_rows.append(r)
                            curr_len += added_len
                        else:
                            if curr_rows:
                                doc_chunks_text.append(header_str + "\n" + "\n".join(curr_rows))
                            curr_rows = [r]
                            curr_len = len(header_str) + added_len

                    if curr_rows:
                        doc_chunks_text.append(header_str + "\n" + "\n".join(curr_rows))
            else:
                doc_chunks_text.extend(splitter.split_text(block))

        # Đảm bảo không chunk nào vượt quá CHUNK_SIZE * 1.1
        final_chunks_text = []
        for c in doc_chunks_text:
            c = c.strip()
            if not c:
                continue
            if len(c) > int(CHUNK_SIZE * 1.1):
                final_chunks_text.extend(splitter.split_text(c))
            else:
                final_chunks_text.append(c)

        for index, text in enumerate(final_chunks_text):
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    # TODO: Embed theo batch và giữ nguyên các field của chunk.
    
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks
    raise NotImplementedError("Implement embed_chunks")


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    # TODO: Upsert ids, documents, embeddings và metadatas.
    
    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )
    raise NotImplementedError("Implement index_to_vectorstore")


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
