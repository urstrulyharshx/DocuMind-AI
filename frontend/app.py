import streamlit as st

from utils.api_client import ingest_pdf, query_document, upload_pdf

st.set_page_config(page_title="DocuMind AI", layout="centered")

st.title("DocuMind AI")
st.caption("Upload a PDF, process it, then ask questions from that document.")


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


if "document_id" not in st.session_state:
    reset_document_state()


with st.sidebar:
    st.header("Document")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file and uploaded_file.name != st.session_state.file_name:
        reset_document_state()

    if uploaded_file:
        st.write(f"Selected: `{uploaded_file.name}`")

        if st.button("Upload and process", type="primary"):
            try:
                with st.spinner("Uploading PDF..."):
                    upload_result = upload_pdf(uploaded_file)
                    file_path = upload_result["file_path"]
                    file_key = get_file_key(file_path)

                with st.spinner("Extracting text and building vector index..."):
                    ingest_result = ingest_pdf(file_key)

                st.session_state.document_id = ingest_result["document_id"]
                st.session_state.file_key = ingest_result.get("file_key", file_key)
                st.session_state.file_name = uploaded_file.name
                st.session_state.chunks = ingest_result["chunks"]
                st.session_state.messages = []
                st.success("Document ready")
            except Exception as exc:
                st.error(f"Failed to process document: {exc}")

    if st.session_state.document_id:
        st.divider()
        st.write("Status: Ready")
        st.write(f"File: `{st.session_state.file_name}`")
        st.write(f"Chunks: `{st.session_state.chunks}`")
        st.caption(f"Document ID: {st.session_state.document_id}")
    else:
        st.info("Upload and process a PDF to enable document chat.")


if not st.session_state.document_id:
    st.info("Start by uploading a PDF from the sidebar.")
    st.stop()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("context"):
            with st.expander("Retrieved context"):
                for index, chunk in enumerate(message["context"], start=1):
                    st.markdown(f"**Chunk {index}**")
                    st.write(chunk)


question = st.chat_input("Ask a question about this PDF")

if question:
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Searching document..."):
                result = query_document(question, st.session_state.document_id)

            answer = result.get("answer", "")
            context = result.get("context_used", [])
            st.markdown(answer)

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
                }
            )
