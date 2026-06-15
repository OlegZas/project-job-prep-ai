import os

import streamlit as st
from dotenv import load_dotenv

from src.file_loader import DocumentProcessor
from src.document_store import DocumentStore
from src.rag_pipeline import RAGPipeline
from src.web_search import WebSearchAssistant

load_dotenv()

st.set_page_config(
    page_title="DataPrep AI",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DataPrep AI")
st.subheader("Data Engineering Interview Prep Assistant")

st.write(
    """
    DataPrep AI helps data engineering candidates prepare for interviews using two modes:

    **Mode 1:** Search uploaded interview documents, resumes, job descriptions, and study notes.  
    **Mode 2:** Ask live market knowledge questions about data engineering tools, trends, and skills.
    """
)

st.divider()

tab1, tab2 = st.tabs(["📁 Interview Documents", "🌐 Live Market Knowledge"])


with tab1:
    st.header("Mode 1: Interview Documents")

    st.write(
        """
        Upload your resume, job description, interview notes, SQL notes, Kafka notes,
        or cloud study guides. This mode prepares documents for RAG by reading,
        cleaning, and splitting them into searchable chunks.
        """
    )

    use_sample_docs = st.checkbox(
        "Use sample interview notes from docs folder",
        value=True
    )

    uploaded_files = st.file_uploader(
        "Upload TXT, MD, or PDF files",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True
    )

    processor = DocumentProcessor(chunk_size=180, overlap=30)

    sample_files = []
    if use_sample_docs:
        sample_files = processor.load_local_files("docs")

    all_files = sample_files + list(uploaded_files or [])

    chunks = []

    if all_files:
        st.success(f"{len(all_files)} file(s) ready for processing.")

        st.write("Files being used:")
        for file in all_files:
            st.write(f"- {file.name}")

        chunks = processor.process_files(all_files)

        st.write("### Document Processing Results")
        st.write(f"Total files: {len(all_files)}")
        st.write(f"Total text chunks created: {len(chunks)}")

        if chunks:
            with st.expander("Preview document chunks"):
                for chunk in chunks[:5]:
                    st.write(f"**File:** {chunk['file_name']}")
                    st.write(f"**Chunk:** {chunk['chunk_number']}")
                    st.write(chunk["text"][:500] + "...")
                    st.divider()
        else:
            st.warning("No readable text was found in the documents.")

    else:
        st.info("No files loaded yet. Upload files or use the sample docs.")

    st.subheader("Ask a question about your documents")

    doc_question = st.text_input(
        "Document question:",
        placeholder="Example: Based on my notes, explain Kafka consumer groups."
    )

    if st.button("Ask Document Question"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OpenAI API key. Add OPENAI_API_KEY to your .env file.")
        elif not all_files:
            st.warning("Please upload documents or use the sample docs.")
        elif not chunks:
            st.warning("The documents did not create any text chunks.")
        elif not doc_question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                with st.spinner("Creating embeddings and searching your documents..."):
                    store = DocumentStore()
                    store.add_chunks(chunks)
                    results = store.search(doc_question, top_k=3)

                st.write("### Retrieved References")

                for result in results:
                    with st.expander(
                        f"{result['file_name']} | Chunk {result['chunk_number']} | Score: {result['score']:.3f}"
                    ):
                        st.write(result["text"])

                with st.spinner("Generating answer from your documents..."):
                    rag = RAGPipeline()
                    answer = rag.answer_question(doc_question, results)

                st.write("### Answer")
                st.write(answer)

            except Exception as error:
                st.error("Something went wrong while generating the document answer.")
                st.write(error)


with tab2:
    st.header("Mode 2: Live Market Knowledge")

    st.write(
        """
        Use this mode for current or general data engineering questions.
        This mode uses web search through the OpenAI API to answer questions about
        current tools, skills, trends, and interview expectations.
        """
    )

    st.info(
        """
        Good questions for this mode:
        - What are the latest Kafka improvements?
        - What skills are companies asking from data engineers?
        - What should I know about modern ETL tools?
        - What cloud skills are useful for data engineering interviews?
        """
    )

    market_question = st.text_input(
        "Market knowledge question:",
        placeholder="Example: What skills are most important for data engineers in 2026?"
    )

    if st.button("Ask Market Question"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OpenAI API key. Add OPENAI_API_KEY to your .env file.")
        elif not market_question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                with st.spinner("Searching the web and generating answer..."):
                    web_assistant = WebSearchAssistant()
                    market_answer = web_assistant.answer_market_question(market_question)

                st.write("### Answer")
                st.write(market_answer)

            except Exception as error:
                st.error("Something went wrong while generating the market knowledge answer.")
                st.write(error)


st.divider()

st.header("Example Questions")

col1, col2 = st.columns(2)

with col1:
    st.write("### Document Mode Examples")
    st.write(
        """
        - Based on my resume, what interview topics should I prepare for?
        - Explain Kafka consumer groups from my notes.
        - What SQL topics appear in this job description?
        - Quiz me on BigQuery partitioning.
        """
    )

with col2:
    st.write("### Market Mode Examples")
    st.write(
        """
        - What are the latest Kafka improvements?
        - What skills are companies asking from data engineers?
        - What should I know about modern ETL tools?
        - What cloud skills are useful for data engineering interviews?
        """
    )