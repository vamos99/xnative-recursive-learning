from __future__ import annotations


def run_app():
    try:
        import streamlit as st
    except Exception:
        print(
            "Streamlit is optional. Install streamlit to use UI, or run sample mode via CLI/tests."
        )
        return
    st.set_page_config(page_title="XNative MVP", layout="wide")
    st.title("XNative Recursive Learning - Local-first MVP")
    st.write("No X API, no mandatory paid LLM. Use fixture/manual import and human approval queue.")
