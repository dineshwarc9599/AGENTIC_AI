import streamlit as st
import requests

st.set_page_config(page_title="AI Knowledge Assistant")

st.title("AI Knowledge Assistant")

query = st.text_area(
    "Enter Your Requirement",
    placeholder="Generate test cases for login module"
)

if st.button("Generate Document"):

    if query:

        response = requests.post(
            "http://127.0.0.1:8000/generate",
            json={"query": query}
        )

        data = response.json()

        st.success(data["message"])

        download_url = (
            "http://127.0.0.1:8000"
            + data["download_url"]
        )

        st.markdown(
            f"[Download DOCX File]({download_url})"
        )