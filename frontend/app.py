import streamlit as st
from utils.api_client import send_chat

st.set_page_config(page_title="DocuMind AI", layout="centered")

st.title("📄 DocuMind AI")
st.write("Chat with your AI (RAG coming soon 🚀)")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Input
user_input = st.text_input("Ask something")

if st.button("Send") and user_input:
    # Store user message
    st.session_state.messages.append(("You", user_input))

    # Call backend
    response = send_chat(user_input)

    # Store AI response
    st.session_state.messages.append(("AI", response))

# Display chat history
for sender, msg in st.session_state.messages:
    if sender == "You":
        st.markdown(f"**🧑 You:** {msg}")
    else:
        st.markdown(f"**🤖 AI:** {msg}")