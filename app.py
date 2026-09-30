import os
import time

import streamlit as st
from dotenv import load_dotenv

from src.analytics_models import PipelineRunRecord
from src.analytics_ui import render_engineering_metrics
from src.career_ui import render_career_match, render_interview_lab
from src.file_loader import DocumentProcessor
from src.document_store import DocumentStore
from src.rag_pipeline import RAGPipeline
from src.telemetry import record_event
from src.ui_components import (
    apply_app_style,
    render_document_flow,
    render_example_questions,
    render_getting_started,
    render_hero,
    render_section_intro,
)
from src.web_search import WebSearchAssistant

load_dotenv()

st.set_page_config(
    page_title="DataPrep AI",
    page_icon="🎯",
    layout="wide"
)

apply_app_style()
render_hero()

with st.expander("New here? See how to use DataPrep AI", expanded=True):
    render_getting_started()
    st.caption(
        "Start with Resume & Job Match if you have a specific role. Start with "
        "Ask My Documents if you want answers from your résumé or notes."
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Ask My Documents",
        "Resume & Job Match",
        "Practice Interview",
        "Current Trends",
        "Project Metrics",
    ]
)


with tab1:
    st.header("Ask questions about your documents")
    render_section_intro(
        "What this tool does",
        "Add a résumé, job posting, or study notes. DataPrep AI finds the most useful "
        "passages and answers using only those files, with sources you can open.",
    )
    render_document_flow()
    render_example_questions(
        [
            "What interview topics should I prepare from my résumé?",
            "Which skills does this job require?",
            "Summarize my strongest data engineering projects.",
        ]
    )

    st.subheader("1. Choose your documents")

    use_sample_docs = st.checkbox(
        "Try the sample study notes when I have not uploaded files",
        value=True,
        help="Safe example notes about SQL, Kafka, and Google Cloud. Your own uploads automatically take priority.",
    )

    uploaded_files = st.file_uploader(
        "Upload your résumé, job posting, or notes",
        type=["txt", "md", "pdf", "docx"],
        accept_multiple_files=True,
        help="Accepted formats: Word (.docx), PDF, TXT, and Markdown. Your files stay in this browser session on the public app.",
    )

    if st.button("Start over with documents", help="Use this after replacing documents or if you want to start fresh."):
        st.session_state.pop("document_store", None)
        st.session_state.pop("indexed_corpus_id", None)
        st.success("The document index and cached embeddings were cleared for this session.")

    processor = DocumentProcessor(chunk_size=180, overlap=30)

    sample_files = []
    if use_sample_docs and not uploaded_files:
        sample_files = processor.load_local_files("docs", allowed_extensions={".txt"})

    if uploaded_files and use_sample_docs:
        st.caption("Your uploaded files are being used. Sample notes are paused so they do not distract from your question.")

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

        st.write("### Files ready to use")
        catalog_rows = []

        for document in documents:
            catalog_rows.append(
                {
                    "File": document["file_name"],
                    "Source": document["source_type"].title(),
                    "Type": document["file_type"],
                    "Size (KB)": round(document["file_size_bytes"] / 1024, 1),
                    "Words": document["word_count"],
                    "Sections": document["chunk_count"],
                    "Status": {
                        "indexed": "Ready",
                        "duplicate": "Skipped duplicate",
                        "empty": "No readable text",
                        "unsupported": "Unsupported",
                        "error": "Problem",
                    }.get(document["status"], document["status"].title()),
                }
            )

        st.dataframe(catalog_rows, width="stretch", hide_index=True)
        st.caption(
            "Your uploaded files and prepared search data stay in this browser session; "
            "they are not written to a shared project database."
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

        if chunks:
            st.success(
                f"Ready: {indexed_count} document(s) organized into {len(chunks)} searchable sections."
            )
            with st.expander("Preview how the documents were divided (optional)"):
                for chunk in chunks[:5]:
                    st.write(f"**File:** {chunk['file_name']}")
                    st.write(f"**Section:** {chunk['chunk_number']}")
                    st.write(chunk["text"][:500] + "...")
                    st.divider()
        else:
            st.warning("No readable text was found in the documents.")

    else:
        st.info("Upload a file above, or keep the sample notes selected to try the tool.")

    st.subheader("2. Ask a question")

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
                with st.expander("See the supporting passages"):
                    for result in exchange["results"]:
                        st.write(
                            f"**[{result['citation']}] {result['file_name']} — "
                            f"section {result['chunk_number']}**"
                        )
                        st.write(result["text"])

    doc_question = st.text_input(
        "What would you like to know?",
        placeholder="Example: Based on my résumé, what interview topics should I prepare?",
        key="document_question_input",
    )

    with st.expander("Answer settings (optional)"):
        st.caption("The recommended defaults work well for most résumés and notes.")
        retrieval_col1, retrieval_col2 = st.columns(2)
        top_k = retrieval_col1.slider(
            "Supporting passages to review",
            2,
            8,
            6,
            help="More passages give the assistant broader context, but may make the answer less focused.",
        )
        search_style = retrieval_col2.select_slider(
            "How closely should a passage match?",
            options=["Broad", "Balanced", "Strict"],
            value="Balanced",
            help="Broad finds more possible matches. Strict only uses passages that are very closely related to your question.",
        )
        min_score = {"Broad": 0.05, "Balanced": 0.12, "Strict": 0.25}[search_style]

    if st.button("Find an answer", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OpenAI API key. Add OPENAI_API_KEY to your .env file.")
        elif not all_files:
            st.warning("Please upload documents or use the sample docs.")
        elif not chunks:
            st.warning("The documents did not create any text chunks.")
        elif not doc_question.strip():
            st.warning("Please enter a question.")
        else:
            active_operation = "document_index"
            operation_started_at = time.perf_counter()
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
                record_event(
                    PipelineRunRecord(
                        operation="document_index",
                        status="success",
                        duration_ms=round(index_seconds * 1000),
                        input_count=len(chunks),
                        output_count=len(store.items),
                        cache_hits=index_stats["hits"],
                        cache_misses=index_stats["misses"],
                        model=store.embedding_model,
                    )
                )

                store.reset_cache_stats()
                active_operation = "document_search"
                operation_started_at = time.perf_counter()
                search_started_at = time.perf_counter()

                with st.spinner("Searching your documents..."):
                    results = store.search(
                        doc_question, top_k=top_k, min_score=min_score
                    )

                search_seconds = time.perf_counter() - search_started_at
                search_stats = store.get_cache_stats()
                record_event(
                    PipelineRunRecord(
                        operation="document_search",
                        status="success" if results else "no_result",
                        duration_ms=round(search_seconds * 1000),
                        input_count=1,
                        output_count=len(results),
                        cache_hits=search_stats["hits"],
                        cache_misses=search_stats["misses"],
                        model=store.embedding_model,
                    )
                )

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
                        "I could not find a useful passage for that question. Try choosing "
                        "Broad in Answer settings, reword the question, or add a more relevant file."
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
                record_event(
                    PipelineRunRecord(
                        operation=active_operation,
                        status="error",
                        duration_ms=round(
                            (time.perf_counter() - operation_started_at) * 1000
                        ),
                        error_type=type(error).__name__,
                    )
                )
                st.error("Something went wrong while generating the document answer.")
                st.write(error)


with tab2:
    render_career_match()


with tab3:
    render_interview_lab()


with tab4:
    st.header("Explore current data engineering trends")
    render_section_intro(
        "When to use this tool",
        "Use it for questions that may have changed recently, such as popular tools, "
        "hiring expectations, and market trends. For questions about your own files, "
        "use Ask My Documents instead.",
    )
    render_example_questions(
        [
            "How is AI affecting data engineering careers and job searches?",
            "What should I know about modern ETL tools?",
            "Which cloud skills are useful for interviews?",
        ]
    )

    market_question = st.text_input(
        "What current topic would you like to explore?",
        placeholder="Example: How is AI affecting data engineering careers and job searches?"
    )

    if st.button("Search current information", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Missing OpenAI API key. Add OPENAI_API_KEY to your .env file.")
        elif not market_question.strip():
            st.warning("Please enter a question.")
        else:
            market_started_at = time.perf_counter()
            try:
                with st.spinner("Searching the web and generating answer..."):
                    web_assistant = WebSearchAssistant()
                    market_answer = web_assistant.answer_market_question(market_question)

                st.write("### Answer")
                st.write(market_answer)
                record_event(
                    PipelineRunRecord(
                        operation="market_knowledge",
                        status="success",
                        duration_ms=round(
                            (time.perf_counter() - market_started_at) * 1000
                        ),
                        input_count=1,
                        output_count=1,
                        model=os.getenv("OPENAI_WEB_MODEL", "gpt-5.6-luna"),
                    )
                )

            except Exception as error:
                record_event(
                    PipelineRunRecord(
                        operation="market_knowledge",
                        status="error",
                        duration_ms=round(
                            (time.perf_counter() - market_started_at) * 1000
                        ),
                        input_count=1,
                        error_type=type(error).__name__,
                        model=os.getenv("OPENAI_WEB_MODEL", "gpt-5.6-luna"),
                    )
                )
                st.error("Something went wrong while generating the market knowledge answer.")
                st.write(error)


with tab5:
    render_engineering_metrics()
