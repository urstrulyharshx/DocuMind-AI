import streamlit as st

from utils.api_client import (
    delete_document,
    ingest_pdf,
    list_documents,
    query_document,
    upload_pdf,
)

st.set_page_config(page_title="DocuMind AI", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        max-width: 1180px;
    }
    [data-testid="stSidebar"] {
        min-width: 320px;
    }
    .doc-status {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 12px 14px;
        background: #fafafa;
    }
    .small-muted {
        color: #6b7280;
        font-size: 0.88rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_file_key(file_path: str):
    if file_path.startswith("s3://"):
        return "/".join(file_path.replace("s3://", "").split("/")[1:])
    return file_path


def reset_document_state():
    st.session_state.document_id = None
    st.session_state.file_key = None
    st.session_state.file_name = None
    st.session_state.chunks = None
    st.session_state.messages = []


def init_state():
    if "document_id" not in st.session_state:
        reset_document_state()
    if "documents" not in st.session_state:
        st.session_state.documents = []
    if "documents_error" not in st.session_state:
        st.session_state.documents_error = None


def refresh_documents():
    try:
        result = list_documents()
        st.session_state.documents = result.get("documents", [])
        st.session_state.documents_error = None
    except Exception as exc:
        st.session_state.documents = []
        st.session_state.documents_error = str(exc)


def select_document(document):
    st.session_state.document_id = document["document_id"]
    st.session_state.file_key = document.get("file_key")
    st.session_state.file_name = document_display_name(document)
    st.session_state.chunks = document.get("chunk_count")
    st.session_state.messages = []


def document_display_name(document):
    display_name = document.get("display_name")
    if display_name:
        return display_name

    file_name = document.get("file_name")
    if file_name and not is_uuid_like(file_name):
        return file_name

    file_key = document.get("file_key")
    if file_key and not is_uuid_like(file_key):
        return file_key.rstrip("/").split("/")[-1]

    return f"Document {document.get('document_id', '')[:8]}"


def is_uuid_like(value):
    parts = str(value).split("-")
    return len(parts) == 5 and all(parts)


def document_option_label(document):
    name = document_display_name(document)
    chunks = document.get("chunk_count", 0)
    short_id = document.get("document_id", "")[:8]
    return f"{name} | {chunks} chunks | id {short_id}"


def render_sources(sources):
    if not sources:
        return

    st.markdown("**Sources**")
    for index, source in enumerate(sources, start=1):
        file_name = source.get("file_name") or "Unknown file"
        page_number = source.get("page_number")
        chunk_index = source.get("chunk_index")
        score = source.get("similarity_score")
        retrieval_mode = source.get("retrieval_mode")
        hybrid_score = source.get("hybrid_score")

        details = [file_name]
        if page_number is not None:
            details.append(f"page {page_number}")
        if chunk_index is not None:
            details.append(f"chunk {chunk_index}")
        if retrieval_mode:
            details.append(retrieval_mode)
        if hybrid_score is not None:
            details.append(f"hybrid {hybrid_score}")
        if score is not None:
            details.append(f"semantic {score}")

        st.caption(f"{index}. " + " | ".join(details))


def render_metrics(metrics):
    if not metrics:
        return

    with st.expander("Run details"):
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Retrieved", metrics.get("retrieved_chunks", 0))
        col_b.metric("Mode", metrics.get("retrieval_mode", "hybrid"))
        col_c.metric("Generation", f"{metrics.get('generation_latency_ms', 0)} ms")
        col_d.metric("Total", f"{metrics.get('total_latency_ms', 0)} ms")
        st.caption(f"Retrieval latency: {metrics.get('retrieval_latency_ms', 0)} ms")
        st.caption(f"Embedding model: {metrics.get('embedding_model')}")
        st.caption(f"Chat model: {metrics.get('chat_model')}")


def render_document_status():
    if not st.session_state.document_id:
        st.info("Upload or select a PDF to start document-grounded chat.")
        return

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Selected document", st.session_state.file_name or "Document")
    col_b.metric("Indexed chunks", st.session_state.chunks or 0)
    col_c.metric("Mode", "Grounded RAG")
    st.caption(f"Document ID: {st.session_state.document_id}")


init_state()

if not st.session_state.documents and st.session_state.documents_error is None:
    refresh_documents()

st.title("DocuMind AI")
st.caption("Document-grounded RAG with pgvector retrieval, page-aware citations, and prompt-injection guardrails.")

with st.sidebar:
    st.header("Workspace")

    if st.button("Refresh document library", use_container_width=True):
        refresh_documents()

    if st.session_state.documents_error:
        st.warning(f"Document library unavailable: {st.session_state.documents_error}")

    documents = st.session_state.documents
    if documents:
        labels = [document_option_label(doc) for doc in documents]
        current_index = 0
        for idx, doc in enumerate(documents):
            if doc["document_id"] == st.session_state.document_id:
                current_index = idx
                break

        selected_idx = st.selectbox(
            "Select indexed document",
            range(len(documents)),
            index=current_index,
            format_func=lambda idx: labels[idx],
        )
        selected_doc = documents[selected_idx]

        if selected_doc["document_id"] != st.session_state.document_id:
            select_document(selected_doc)

        st.caption(f"Using: {document_display_name(selected_doc)}")
        st.caption(f"Document ID: {selected_doc.get('document_id')}")

        if st.button("Use selected document", use_container_width=True):
            select_document(selected_doc)
            st.success("Document selected")

        if st.button("Delete selected document", use_container_width=True):
            try:
                delete_document(selected_doc["document_id"])
                reset_document_state()
                refresh_documents()
                st.success("Document deleted")
            except Exception as exc:
                st.error(f"Delete failed: {exc}")
    else:
        st.caption("No indexed documents found.")

    st.divider()
    st.header("Upload")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        st.write(f"Selected: `{uploaded_file.name}`")

        if st.button("Upload and process", type="primary", use_container_width=True):
            try:
                with st.spinner("Uploading PDF..."):
                    upload_result = upload_pdf(uploaded_file)
                    file_path = upload_result["file_path"]
                    file_key = get_file_key(file_path)

                with st.spinner("Extracting text, embedding chunks, and indexing..."):
                    ingest_result = ingest_pdf(file_key)

                st.session_state.document_id = ingest_result["document_id"]
                st.session_state.file_key = ingest_result.get("file_key", file_key)
                st.session_state.file_name = uploaded_file.name
                st.session_state.chunks = ingest_result["chunks"]
                st.session_state.messages = []
                refresh_documents()
                st.success("Document ready")
            except Exception as exc:
                st.error(f"Failed to process document: {exc}")

    st.divider()
    st.header("Guardrails")
    st.caption("Answers are restricted to retrieved document context. The backend ignores document text that attempts to override system rules.")


render_document_status()

if not st.session_state.document_id:
    st.stop()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []))
            render_metrics(message.get("metrics", {}))
        if message["role"] == "assistant" and message.get("context"):
            with st.expander("Retrieved context"):
                for index, chunk in enumerate(message["context"], start=1):
                    st.markdown(f"**Chunk {index}**")
                    st.write(chunk)


question = st.chat_input("Ask a question about the selected PDF")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving evidence and generating answer..."):
                result = query_document(question, st.session_state.document_id)

            answer = result.get("answer", "")
            context = result.get("context_used", [])
            sources = result.get("sources", [])
            metrics = result.get("metrics", {})
            st.markdown(answer)
            render_sources(sources)
            render_metrics(metrics)

            if context:
                with st.expander("Retrieved context"):
                    for index, chunk in enumerate(context, start=1):
                        st.markdown(f"**Chunk {index}**")
                        st.write(chunk)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "context": context,
                    "sources": sources,
                    "metrics": metrics,
                }
            )
        except Exception as exc:
            error_message = f"Failed to query document: {exc}"
            st.error(error_message)
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                    "context": [],
                    "sources": [],
                    "metrics": {},
                }
            )
