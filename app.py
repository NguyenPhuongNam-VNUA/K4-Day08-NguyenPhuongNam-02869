import os
import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation

load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot - Tư Vấn Tuyển Sinh 2026",
    page_icon="🎓",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("⚙️ Cấu hình RAG")
    st.markdown("Hệ thống **Hybrid Retrieval** kết hợp Semantic Search (Dense) + BM25 (Lexical) + RRF Reranking.")

    top_k = st.slider("Số lượng Chunks (top_k)", min_value=3, max_value=10, value=5)

    provider = os.getenv("LLM_PROVIDER", "openai").upper()
    model_name = os.getenv("LLM_MODEL", "openai/gpt-4o-mini" if provider == "OPENROUTER" else "gpt-4o-mini")
    st.info(f"**LLM Provider:** {provider}\n\n**Model:** `{model_name}`")

    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 📚 Dữ liệu tuyển sinh 2026:")
    st.markdown("- **Chính sách:** ĐH Y Hà Nội, ĐH Giao thông Vận tải, ĐH Bách khoa HN")
    st.markdown("- **Thông báo & Đề án:** VNUA, HUST, VMU, ĐH Mỏ - Địa chất, ĐH Bách Khoa TP.HCM")

st.title("🎓 RAG Chatbot – Tư Vấn Tuyển Sinh Đại Học 2026")
st.caption("Tra cứu đề án tuyển sinh, phương thức xét tuyển, chỉ tiêu và quy đổi chứng chỉ ngoại ngữ.")

# Hiển thị lịch sử chat
for m_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        sources = message.get("sources", [])
        if sources:
            retrieval_source = message.get("retrieval_source", "hybrid")
            with st.expander(f"📚 Nguồn trích dẫn ({len(sources)} tài liệu) — Phương thức: `{retrieval_source}`"):
                for idx, src in enumerate(sources, 1):
                    meta = src.get("metadata", {})
                    title = meta.get("title") or meta.get("source") or f"Tài liệu {idx}"
                    url = meta.get("url")
                    method = src.get("retrieval_method", "dense")
                    score = src.get("score", 0.0)

                    st.markdown(f"**[{idx}] {f'[{title}]({url})' if url else title}**")
                    st.caption(f"File/Nguồn: `{meta.get('source')}` | Phương thức: `{method}` | Điểm: `{score:.4f}`")
                    st.markdown(f"> {src.get('content', '').strip()}")

query = st.chat_input("Hỏi về chỉ tiêu, phương thức tuyển sinh, điểm quy đổi IELTS...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm tài liệu và sinh câu trả lời..."):
            try:
                result = generate_with_citation(query, top_k=top_k)
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                retrieval_source = result.get("retrieval_source", "none")
            except Exception as error:
                answer = f"⚠️ Lỗi xử lý: {error}"
                sources = []
                retrieval_source = "none"

        st.markdown(answer)

        if sources:
            with st.expander(f"📚 Nguồn trích dẫn ({len(sources)} tài liệu) — Phương thức: `{retrieval_source}`"):
                for idx, src in enumerate(sources, 1):
                    meta = src.get("metadata", {})
                    title = meta.get("title") or meta.get("source") or f"Tài liệu {idx}"
                    url = meta.get("url")
                    method = src.get("retrieval_method", "dense")
                    score = src.get("score", 0.0)

                    st.markdown(f"**[{idx}] {f'[{title}]({url})' if url else title}**")
                    st.caption(f"File/Nguồn: `{meta.get('source')}` | Phương thức: `{method}` | Điểm: `{score:.4f}`")
                    st.markdown(f"> {src.get('content', '').strip()}")

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
