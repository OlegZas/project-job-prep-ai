import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from src.analytics_models import InterviewMetricRecord, PipelineRunRecord
from src.career_intelligence import CareerIntelligence
from src.file_loader import DocumentProcessor, LocalFile
from src.matching import build_skill_match
from src.telemetry import record_event
from src.ui_components import render_section_intro


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RESUME = PROJECT_ROOT / "sample_data" / "sample_resume.txt"
SAMPLE_JOB = PROJECT_ROOT / "sample_data" / "sample_job_description.txt"


def _role_family(job_title: str) -> str:
    lowered = job_title.casefold()
    if "analytics engineer" in lowered:
        return "Analytics Engineer"
    if "machine learning" in lowered or "ml engineer" in lowered:
        return "Machine Learning Engineer"
    if "data engineer" in lowered:
        return "Data Engineer"
    return "Other Data Role"


def _clean_document(file) -> tuple[str, str]:
    processor = DocumentProcessor()
    text = processor.clean_text(processor.read_file(file))
    document_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, document_id


def _extract_with_cache(engine, kind, file):
    text, document_id = _clean_document(file)
    cache = st.session_state.setdefault("career_extraction_cache", {})
    cache_key = (
        f"{kind}:{engine.model}:{getattr(engine, 'extraction_version', 'v1')}:{document_id}"
    )

    if cache_key not in cache:
        if kind == "candidate":
            cache[cache_key] = engine.extract_candidate(text, file.name)
        else:
            cache[cache_key] = engine.extract_job(text, file.name)

    return cache[cache_key]


def _render_learning_plan(plan):
    st.write("#### Your four-week goal")
    st.write(plan.strategy)
    st.info(f"**A good result after four weeks:** {plan.success_metric}")

    for week in plan.weeks:
        focus = ", ".join(week.focus_skills[:3])
        with st.expander(
            f"Week {week.week_number} — {focus}",
            expanded=week.week_number == 1,
        ):
            st.write("**What to learn**")
            st.write("  •  ".join(week.objectives[:3]))
            st.write(f"**Build this:** {week.practical_task}")
            with st.expander("Questions to practice"):
                for number, question in enumerate(week.interview_questions[:3], 1):
                    st.write(f"{number}. {question}")


def render_career_match():
    st.header("Compare your résumé with a job")
    render_section_intro(
        "What you will get",
        "See which job requirements your résumé already supports, what appears to be "
        "missing, and what to study next. Every result includes evidence you can review.",
    )
    st.markdown("**How to use it:** 1. Add one résumé  →  2. Add up to three jobs  →  3. Select **Compare résumé and job**")
    st.caption("No files ready? Keep the sample option selected to see a complete example.")

    use_sample = st.checkbox(
        "Use a safe sample résumé and job posting",
        value=True,
        help="Recommended for your first visit. The sample contains no personal information.",
    )
    resume_upload = st.file_uploader(
        "Your résumé",
        type=["txt", "md", "pdf", "docx"],
        key="career_resume",
        help="Accepted formats: Word (.docx), PDF, TXT, and Markdown.",
    )
    job_uploads = st.file_uploader(
        "Job posting(s) - up to 3",
        type=["txt", "md", "pdf", "docx"],
        accept_multiple_files=True,
        key="career_job_uploads",
    )

    resume_file = resume_upload
    job_files = list(job_uploads or [])

    if use_sample and resume_file is None:
        resume_file = LocalFile(SAMPLE_RESUME)
    if use_sample and not job_files:
        job_files = [LocalFile(SAMPLE_JOB)]

    if len(job_files) > 3:
        st.warning("Only the first three job descriptions will be analyzed.")
        job_files = job_files[:3]

    if st.button("Compare résumé and job", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is required for structured career extraction.")
        elif resume_file is None or not job_files:
            st.warning("Provide one résumé and at least one job description.")
        else:
            extraction_started_at = time.perf_counter()
            try:
                engine = CareerIntelligence()
                with st.status("Reading your résumé and job posting...", expanded=True) as status:
                    st.write(f"Reading résumé: {resume_file.name}")
                    candidate = _extract_with_cache(engine, "candidate", resume_file)
                    jobs = []
                    for job_file in job_files:
                        st.write(f"Reading job: {job_file.name}")
                        job = _extract_with_cache(engine, "job", job_file)
                        jobs.append(job)
                    status.update(label="Your comparison is ready", state="complete")

                st.session_state.career_candidate = candidate
                st.session_state.career_jobs = jobs
                st.session_state.career_job_sources = [file.name for file in job_files]
                st.session_state.career_selected_job = 0
                record_event(
                    PipelineRunRecord(
                        operation="career_extraction",
                        status="success",
                        duration_ms=round(
                            (time.perf_counter() - extraction_started_at) * 1000
                        ),
                        input_count=1 + len(job_files),
                        output_count=1 + len(jobs),
                        model=engine.model,
                    )
                )
            except Exception as error:
                record_event(
                    PipelineRunRecord(
                        operation="career_extraction",
                        status="error",
                        duration_ms=round(
                            (time.perf_counter() - extraction_started_at) * 1000
                        ),
                        input_count=1 + len(job_files),
                        error_type=type(error).__name__,
                    )
                )
                st.error(f"Career extraction failed: {error}")

    candidate = st.session_state.get("career_candidate")
    jobs = st.session_state.get("career_jobs", [])

    if candidate is None or not jobs:
        st.info("Select the sample or upload your files, then choose Compare résumé and job.")
        return

    job_labels = [
        f"{job.job_title} — {job.company or 'Company not listed'}" for job in jobs
    ]
    selected_index = st.selectbox(
        "Job to review",
        range(len(jobs)),
        format_func=lambda index: job_labels[index],
        key="career_selected_job",
    )
    job = jobs[selected_index]
    match = build_skill_match(candidate, job)
    st.session_state.current_match = match
    st.session_state.current_job = job

    st.subheader(job_labels[selected_index])
    metric1, metric2, metric3, metric4 = st.columns(4)
    metric1.metric("Overall match", f"{match['score']}%")
    metric2.metric(
        "Required skills", f"{match['required_matched']}/{match['required_total']}"
    )
    metric3.metric(
        "Preferred skills", f"{match['preferred_matched']}/{match['preferred_total']}"
    )
    metric4.metric("Skills to strengthen", len(match["missing_skills"]))

    st.caption(
        "How the score works: required skills count twice as much as preferred skills. "
        "The score is calculated with fixed rules so it is easy to explain and reproduce."
    )

    match_rows = [
        {
            "Skill": row["skill"],
            "Category": row["category"],
            "Job priority": row["importance"].title(),
            "Your coverage": row["status"].replace("missing", "Not shown").replace("matched", "Found").title(),
            "Résumé evidence": "; ".join(row["candidate_evidence"]) or "—",
            "Job evidence": "; ".join(row["job_evidence"]) or "—",
        }
        for row in match["rows"]
    ]
    st.dataframe(match_rows, width="stretch", hide_index=True)

    if match["category_summary"]:
        st.write("### Skills covered by category")
        st.bar_chart(
            match["category_summary"],
            x="category",
            y=["matched", "required"],
            color=["#16a34a", "#94a3b8"],
        )

    with st.expander("Technical details: extracted profiles"):
        profile_col1, profile_col2 = st.columns(2)
        profile_col1.write("**Candidate profile**")
        profile_col1.json(candidate.model_dump(mode="json"))
        profile_col2.write("**Job profile**")
        profile_col2.json(job.model_dump(mode="json"))

    st.write("### Build your four-week learning plan")
    st.caption("The plan focuses first on important skills that were not clearly shown in the résumé.")
    plan_key = f"{candidate.headline}:{job.job_title}:{','.join(match['missing_skills'])}"
    plans = st.session_state.setdefault("learning_plans", {})

    if st.button("Generate four-week plan", key="generate_learning_plan"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is required to generate a plan.")
        else:
            plan_started_at = time.perf_counter()
            try:
                with st.spinner("Building a prioritized learning plan..."):
                    engine = CareerIntelligence()
                    plans[plan_key] = engine.generate_learning_plan(
                        candidate, job, match["missing_skills"][:6]
                    )
                record_event(
                    PipelineRunRecord(
                        operation="learning_plan",
                        status="success",
                        duration_ms=round((time.perf_counter() - plan_started_at) * 1000),
                        input_count=len(match["missing_skills"]),
                        output_count=len(plans[plan_key].weeks),
                        model=engine.model,
                    )
                )
            except Exception as error:
                record_event(
                    PipelineRunRecord(
                        operation="learning_plan",
                        status="error",
                        duration_ms=round((time.perf_counter() - plan_started_at) * 1000),
                        input_count=len(match["missing_skills"]),
                        error_type=type(error).__name__,
                    )
                )
                st.error(f"Learning-plan generation failed: {error}")

    if plan_key in plans:
        _render_learning_plan(plans[plan_key])


def render_interview_lab():
    st.header("Practice an interview for your target role")
    render_section_intro(
        "Practice, answer, improve",
        "Choose a topic and difficulty. DataPrep AI creates a role-focused question, "
        "then gives clear feedback on your answer.",
    )
    candidate = st.session_state.get("career_candidate")
    job = st.session_state.get("current_job")

    if candidate is None or job is None:
        st.info("First open Resume & Job Match and complete a comparison. Then come back here for a question tailored to that role.")
        return

    st.success(f"Practice role: {job.job_title}")
    control1, control2 = st.columns(2)
    question_type = control1.selectbox(
        "Question type",
        ["SQL", "Python", "Data Modeling", "System Design", "Behavioral"],
    )
    difficulty = control2.selectbox(
        "Difficulty", ["Foundational", "Intermediate", "Advanced"], index=1,
        help="Foundational checks core knowledge. Advanced expects tradeoffs and production-level reasoning.",
    )

    if st.button("Create a practice question", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is required to generate a question.")
        else:
            question_started_at = time.perf_counter()
            try:
                with st.spinner("Creating a role-specific question..."):
                    engine = CareerIntelligence()
                    st.session_state.current_interview_question = (
                        engine.generate_interview_question(
                            candidate, job, question_type, difficulty
                        )
                    )
                    st.session_state.pop("latest_interview_feedback", None)
                record_event(
                    PipelineRunRecord(
                        operation="interview_generation",
                        status="success",
                        duration_ms=round(
                            (time.perf_counter() - question_started_at) * 1000
                        ),
                        input_count=1,
                        output_count=1,
                        model=engine.model,
                    )
                )
            except Exception as error:
                record_event(
                    PipelineRunRecord(
                        operation="interview_generation",
                        status="error",
                        duration_ms=round(
                            (time.perf_counter() - question_started_at) * 1000
                        ),
                        input_count=1,
                        error_type=type(error).__name__,
                    )
                )
                st.error(f"Question generation failed: {error}")

    question = st.session_state.get("current_interview_question")

    if question is None:
        return

    st.subheader(f"{question.question_type} — {question.difficulty}")
    st.write(question.question)
    if question.context:
        st.caption(f"Why this fits the role: {question.context}")

    with st.expander("What a strong answer should cover"):
        st.write("  •  ".join(question.evaluation_criteria[:5]))

    answer = st.text_area(
        "Your practice answer",
        height=180,
        placeholder="Explain your reasoning, tradeoffs, and production considerations...",
    )

    if st.button("Get feedback on my answer", type="primary"):
        if len(answer.strip()) < 20:
            st.warning("Write a more complete answer before requesting feedback.")
        else:
            scoring_started_at = time.perf_counter()
            try:
                with st.spinner("Scoring against the interview rubric..."):
                    engine = CareerIntelligence()
                    feedback = engine.score_interview_answer(
                        question, answer.strip()
                    )
                st.session_state.latest_interview_feedback = feedback
                history = st.session_state.setdefault("interview_history", [])
                history.append(
                    {
                        "attempted_at": datetime.now(timezone.utc).isoformat(),
                        "role": job.job_title,
                        "question_type": question.question_type,
                        "difficulty": question.difficulty,
                        "question": question.question,
                        "answer": answer.strip(),
                        **feedback.model_dump(mode="json"),
                    }
                )
                record_event(
                    PipelineRunRecord(
                        operation="interview_scoring",
                        status="success",
                        duration_ms=round(
                            (time.perf_counter() - scoring_started_at) * 1000
                        ),
                        input_count=1,
                        output_count=1,
                        model=engine.model,
                    )
                )
                record_event(
                    InterviewMetricRecord(
                        role_family=_role_family(job.job_title),
                        question_type=question.question_type,
                        difficulty=question.difficulty,
                        score=feedback.score,
                        technical_accuracy=feedback.technical_accuracy,
                        clarity=feedback.clarity,
                        tradeoff_reasoning=feedback.tradeoff_reasoning,
                        production_readiness=feedback.production_readiness,
                    )
                )
            except Exception as error:
                record_event(
                    PipelineRunRecord(
                        operation="interview_scoring",
                        status="error",
                        duration_ms=round(
                            (time.perf_counter() - scoring_started_at) * 1000
                        ),
                        input_count=1,
                        error_type=type(error).__name__,
                    )
                )
                st.error(f"Answer scoring failed: {error}")

    feedback = st.session_state.get("latest_interview_feedback")
    if feedback:
        st.write("### Feedback")
        score1, score2, score3, score4, score5 = st.columns(5)
        score1.metric("Overall", f"{feedback.score}/100")
        score2.metric("Accuracy", f"{feedback.technical_accuracy}/25")
        score3.metric("Clarity", f"{feedback.clarity}/25")
        score4.metric("Tradeoffs", f"{feedback.tradeoff_reasoning}/25")
        score5.metric("Production", f"{feedback.production_readiness}/25")

        feedback_col1, feedback_col2 = st.columns(2)
        with feedback_col1:
            st.write("**Strengths**")
            st.write("  •  ".join(feedback.strengths[:3]))
        with feedback_col2:
            st.write("**Improve next**")
            st.write("  •  ".join(feedback.improvements[:3]))

        with st.expander("Model answer and follow-up"):
            st.write(feedback.model_answer)
            st.write(f"**Follow-up:** {feedback.follow_up_question}")

    history = st.session_state.get("interview_history", [])
    if history:
        st.write("### Session progress")
        average = round(sum(item["score"] for item in history) / len(history))
        history_col1, history_col2 = st.columns(2)
        history_col1.metric("Attempts", len(history))
        history_col2.metric("Average score", f"{average}/100")
        st.dataframe(
            [
                {
                    "Time": item["attempted_at"],
                    "Type": item["question_type"],
                    "Difficulty": item["difficulty"],
                    "Score": item["score"],
                }
                for item in history
            ],
            width="stretch",
            hide_index=True,
        )
        st.download_button(
            "Download session history",
            data=json.dumps(history, indent=2),
            file_name="dataprep_interview_history.json",
            mime="application/json",
        )
