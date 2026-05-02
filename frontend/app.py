# frontend/app.py

import streamlit as st

st.title("DocuMind AI")

st.write("Upload documents and ask questions")

uploaded_file = st.file_uploader("Upload a file")

if uploaded_file:
    st.success("File uploaded successfully!")

query = st.text_input("Ask a question")

if query:
    st.write(f"You asked: {query}")