import streamlit as st
from src.file_loader import DocumentProcessor

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
        or cloud study guides. This mode will prepare your documents for RAG by
        reading, cleaning, and splitting them into searchable chunks.
        """
    )

    uploaded_files = st.file_uploader(
        "Upload TXT, MD, or PDF files",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True
    )

    chunks = []

    if uploaded_files:
        st.success(f"{len(uploaded_files)} file(s) uploaded.")

        st.write("Uploaded files:")
        for file in uploaded_files:
            st.write(f"- {file.name}")

        processor = DocumentProcessor(chunk_size=180, overlap=30)
        chunks = processor.process_files(uploaded_files)

        st.write("### Document Processing Results")
        st.write(f"Total files uploaded: {len(uploaded_files)}")
        st.write(f"Total text chunks created: {len(chunks)}")

        if chunks:
            with st.expander("Preview document chunks"):
                for chunk in chunks[:5]:
                    st.write(f"**File:** {chunk['file_name']}")
                    st.write(f"**Chunk:** {chunk['chunk_number']}")
                    st.write(chunk["text"][:500] + "...")
                    st.divider()
        else:
            st.warning("No readable text was found in the uploaded files.")

    else:
        st.info("No files uploaded yet.")

    st.subheader("Ask a question about your documents")

    doc_question = st.text_input(
        "Document question:",
        placeholder="Example: Based on my notes, explain Kafka consumer groups."
    )

    if st.button("Ask Document Question"):
        if not uploaded_files:
            st.warning("Please upload at least one document first.")
        elif not chunks:
            st.warning("The uploaded documents did not create any text chunks.")
        elif not doc_question.strip():
            st.warning("Please enter a question.")
        else:
            st.write("### Question")
            st.write(doc_question)

            st.write("### Demo Retrieval Result")
            st.write(
                """
                The app has successfully loaded and chunked your documents.
                In the next step, we will add embeddings and similarity search so the app
                can find the most relevant chunks for your question.
                """
            )

            st.write("### First Available Chunk")
            st.write(chunks[0]["text"][:700])


with tab2:
    st.header("Mode 2: Live Market Knowledge")

    st.write(
        """
        Use this mode for current or general data engineering questions.
        Later, this mode can connect to a web search API or live data source
        before sending the question to the LLM.
        """
    )

    market_question = st.text_input(
        "Market knowledge question:",
        placeholder="Example: What skills are most important for data engineers in 2026?"
    )

    if st.button("Ask Market Question"):
        if not market_question.strip():
            st.warning("Please enter a question.")
        else:
            st.write("### Question")
            st.write(market_question)

            st.write("### Demo Answer")
            st.write(
                """
                This is a placeholder answer. In the final version, this mode will search
                live or recent sources and return an answer about current data engineering
                tools, trends, and interview expectations.
                """
            )

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