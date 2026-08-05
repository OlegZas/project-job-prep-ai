import os
import time

import streamlit as st
from dotenv import load_dotenv

from src.career_ui import render_career_match, render_interview_lab
from src.file_loader import DocumentProcessor
from src.document_store import DocumentStore
from src.rag_pipeline import RAGPipeline
from src.web_search import WebSearchAssistant

load_dotenv()

st.set_page_config(
    page_title="DataPrep AI",
    page_icon="⚙️",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1250px; padding-top: 2rem;}
    [data-testid="stMetric"] {background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.8rem; border-radius: 0.75rem;}
    [data-testid="stMetricLabel"] {font-weight: 600;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title(" DataPrep AI")
st.subheader("Data Engineering Career Intelligence Platform")

st.write(
    """
    Turn résumés, job descriptions, and study notes into cited answers, transparent
    skill-gap analysis, targeted learning plans, and role-specific interview practice.
    """
)

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(
    ["Document Q&A", "Career Match", "Interview Lab", "Market Knowledge"]
)


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

    if st.button("Clear session document index"):
        st.session_state.pop("document_store", None)
        st.session_state.pop("indexed_corpus_id", None)
        st.success("The document index and cached embeddings were cleared for this session.")

    processor = DocumentProcessor(chunk_size=180, overlap=30)

    sample_files = []
    if use_sample_docs:
        sample_files = processor.load_local_files("docs", allowed_extensions={".txt"})

    all_files = sample_files + list(uploaded_files or [])

    documents = []
    chunks = []

    if all_files:
        processing_result = processor.process_files_with_metadata(all_files)
        documents = processing_result["documents"]
        chunks = processing_result["chunks"]

        indexed_count = sum(
            document["status"] == "indexed" for document in documents
        )
        duplicate_count = sum(
            document["status"] == "duplicate" for document in documents
        )
        issue_count = sum(
            document["status"] in {"empty", "unsupported", "error"}
            for document in documents
        )

        summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
        summary_col1.metric("Files received", len(documents))
        summary_col2.metric("Unique documents", indexed_count)
        summary_col3.metric("Duplicates skipped", duplicate_count)
        summary_col4.metric("Processing issues", issue_count)

        st.write("### Document Catalog")
        catalog_rows = []

        for document in documents:
            catalog_rows.append(
                {
                    "File": document["file_name"],
                    "Source": document["source_type"].title(),
                    "Type": document["file_type"],
                    "Size (KB)": round(document["file_size_bytes"] / 1024, 1),
                    "Words": document["word_count"],
                    "Chunks": document["chunk_count"],
                    "Status": document["status"].title(),
                    "Content ID": (
                        document["document_id"][:12]
                        if document["document_id"]
                        else "—"
                    ),
                    "Duplicate of": document["duplicate_of"] or "—",
                }
            )

        st.dataframe(catalog_rows, width="stretch", hide_index=True)
        st.caption(
            "Document metadata and embeddings remain in this browser session; "
            "uploaded files are not written to a shared project database."
        )

        if duplicate_count:
            st.warning(
                f"Skipped {duplicate_count} duplicate file(s) with content that "
                "was already indexed."
            )

        failed_documents = [
            document for document in documents if document["status"] == "error"
        ]
        for document in failed_documents:
            st.error(f"Could not process {document['file_name']}: {document['error']}")

        st.write("### Document Processing Results")
        st.write(f"Total files: {len(all_files)}")
        st.write(f"Unique documents indexed: {indexed_count}")
        st.write(f"Total text chunks created: {len(chunks)}")

        if chunks:
            with st.expander("Preview document chunks"):
                for chunk in chunks[:5]:
                    st.write(f"**File:** {chunk['file_name']}")
                    st.write(f"**Chunk:** {chunk['chunk_number']}")
                    st.caption(
                        f"Document ID: {chunk['document_id'][:12]} | "
                        f"Chunk ID: {chunk['chunk_id'][:12]}"
                    )
                    st.write(chunk["text"][:500] + "...")
                    st.divider()
        else:
            st.warning("No readable text was found in the documents.")

    else:
        st.info("No files loaded yet. Upload files or use the sample docs.")

    st.subheader("Ask a question about your documents")

    history = st.session_state.setdefault("document_chat_history", [])
    if history:
        history_header, history_action = st.columns([4, 1])
        history_header.write("### Conversation")
        if history_action.button("Clear conversation"):
            st.session_state.document_chat_history = []
            st.rerun()

        for exchange in history:
            with st.chat_message("user"):
                st.write(exchange["question"])
            with st.chat_message("assistant"):
                st.write(exchange["answer"])
                st.caption(
                    f"Index: {'reused' if exchange['index_reused'] else 'updated'} | "
                    f"Search: {exchange['search_seconds']:.3f}s"
                )
                with st.expander("Sources"):
                    for result in exchange["results"]:
                        st.write(
                            f"**[{result['citation']}] {result['file_name']} — "
                            f"chunk {result['chunk_number']} — {result['score']:.3f}**"
                        )
                        st.write(result["text"])

    retrieval_col1, retrieval_col2 = st.columns(2)
    top_k = retrieval_col1.slider("Maximum sources", 1, 8, 4)
    min_score = retrieval_col2.slider(
        "Minimum cosine similarity", 0.0, 1.0, 0.25, 0.05
    )

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
                corpus_id = DocumentStore.create_corpus_id(chunks)
                desired_model = os.getenv(
                    "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
                )
                store = st.session_state.get("document_store")
                index_reused = (
                    store is not None
                    and store.embedding_model == desired_model
                    and st.session_state.get("indexed_corpus_id") == corpus_id
                )

                index_started_at = time.perf_counter()

                with st.spinner("Preparing the document index..."):
                    if not index_reused:
                        if store is None or store.embedding_model != desired_model:
                            store = DocumentStore()

                        store.reset_cache_stats()
                        store.add_chunks(chunks)
                        index_stats = store.get_cache_stats()
                        st.session_state.document_store = store
                        st.session_state.indexed_corpus_id = corpus_id
                    else:
                        index_stats = {
                            "hits": len(chunks),
                            "misses": 0,
                            "cached_embeddings": len(store.embedding_cache),
                        }

                index_seconds = time.perf_counter() - index_started_at

                store.reset_cache_stats()
                search_started_at = time.perf_counter()

                with st.spinner("Searching your documents..."):
                    results = store.search(
                        doc_question, top_k=top_k, min_score=min_score
                    )

                search_seconds = time.perf_counter() - search_started_at
                search_stats = store.get_cache_stats()

                if index_reused:
                    st.success(
                        f"Reused the {len(chunks)}-chunk index from this browser session."
                    )
                else:
                    st.info(
                        f"Index prepared: {index_stats['hits']} cached and "
                        f"{index_stats['misses']} new chunk embeddings."
                    )

                metric_col1, metric_col2, metric_col3 = st.columns(3)
                metric_col1.metric(
                    "Index",
                    "Reused" if index_reused else "Updated",
                    f"{index_seconds:.3f}s",
                )
                metric_col2.metric("Indexed chunks", len(store.items))
                metric_col3.metric(
                    "Query embedding",
                    "Cached" if search_stats["hits"] else "New",
                    f"{search_seconds:.3f}s search",
                )

                if not results:
                    st.warning(
                        "No source passed the similarity threshold. Lower the threshold "
                        "or ask a question covered by the documents."
                    )
                else:
                    with st.spinner("Generating a cited answer from your documents..."):
                        rag = RAGPipeline()
                        answer = rag.answer_question(doc_question, results)

                    history.append(
                        {
                            "question": doc_question.strip(),
                            "answer": answer,
                            "results": results,
                            "index_reused": index_reused,
                            "index_seconds": index_seconds,
                            "search_seconds": search_seconds,
                        }
                    )
                    st.session_state.document_chat_history = history[-10:]
                    st.rerun()

            except Exception as error:
                st.error("Something went wrong while generating the document answer.")
                st.write(error)


with tab2:
    render_career_match()


with tab3:
    render_interview_lab()


with tab4:
    st.header("Live Market Knowledge")

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

st.header("Ways to explore DataPrep AI")

col1, col2 = st.columns(2)

with col1:
    st.write("### Documents and career match")
    st.write(
        """
        - Based on my resume, what interview topics should I prepare for?
        - Explain Kafka consumer groups from my notes.
        - What SQL topics appear in this job description?
        - Which required skills are missing from my résumé?
        """
    )

with col2:
    st.write("### Interview and market practice")
    st.write(
        """
        - Generate a system-design question for this role.
        - Score my answer and suggest a follow-up.
        - What are the latest Kafka improvements?
        - What cloud skills are useful for current interviews?
        """
    )
