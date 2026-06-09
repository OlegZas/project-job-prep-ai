import streamlit as st

st.set_page_config(
    page_title="DataPrep AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DataPrep AI")
st.subheader("A Data Engineering Interview Prep Assistant")

st.write(
    """
    DataPrep AI is a simple RAG-style interview prep assistant for data engineering.
    For this first version, the app lets you upload study files and type interview
    questions. Later, it will use those files to answer questions with an LLM.
    """
)

st.divider()

st.header("1. Upload Interview Prep Documents")

uploaded_files = st.file_uploader(
    "Upload TXT, MD, or PDF files",
    type=["txt", "md", "pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded.")
    for file in uploaded_files:
        st.write(f"- {file.name}")
else:
    st.info("No files uploaded yet. You can upload interview notes, job descriptions, or study guides.")

st.header("2. Ask an Interview Prep Question")

question = st.text_input(
    "Enter a data engineering interview question:",
    placeholder="Example: Explain Kafka consumer groups in simple terms."
)

if st.button("Submit Question"):
    if not uploaded_files:
        st.warning("Please upload at least one document first.")
    elif not question.strip():
        st.warning("Please enter a question.")
    else:
        st.write("### Your Question")
        st.write(question)

        st.write("### Demo Response")
        st.write(
            """
            This is where the AI answer will appear in the next version.
            The final app will search your uploaded files, find relevant notes,
            and generate an interview-focused answer.
            """
        )

st.divider()

st.header("Example Questions")
st.write(
    """
    - Explain the difference between batch and streaming pipelines.
    - What is a Kafka consumer group?
    - How do SQL window functions work?
    - What is BigQuery partitioning?
    - How would you design an ETL pipeline?
    """
)

