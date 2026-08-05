import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from src.career_intelligence import CareerIntelligence
from src.file_loader import DocumentProcessor, LocalFile
from src.matching import build_skill_match


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RESUME = PROJECT_ROOT / "sample_data" / "sample_resume.txt"
SAMPLE_JOB = PROJECT_ROOT / "sample_data" / "sample_job_description.txt"


def _clean_document(file) -> tuple[str, str]:
    processor = DocumentProcessor()
    text = processor.clean_text(processor.read_file(file))
    document_id = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, document_id


def _extract_with_cache(engine, kind, file):
    text, document_id = _clean_document(file)
    cache = st.session_state.setdefault("career_extraction_cache", {})
    cache_key = f"{kind}:{engine.model}:{document_id}"

    if cache_key not in cache:
        if kind == "candidate":
            cache[cache_key] = engine.extract_candidate(text, file.name)
        else:
            cache[cache_key] = engine.extract_job(text, file.name)

    return cache[cache_key]


def _render_learning_plan(plan):
    st.write(f"**Strategy:** {plan.strategy}")
    st.caption(f"Success metric: {plan.success_metric}")

    for week in plan.weeks:
        with st.expander(
            f"Week {week.week_number}: {', '.join(week.focus_skills)}",
            expanded=week.week_number == 1,
        ):
            st.write("**Objectives**")
            for objective in week.objectives:
                st.write(f"- {objective}")
            st.write(f"**Practical task:** {week.practical_task}")
            st.write("**Practice questions**")
            for question in week.interview_questions:
                st.write(f"- {question}")


def render_career_match():
    st.header("Career Match Intelligence")
    st.write(
        "Compare a résumé with up to three job descriptions. The AI extracts "
        "schema-validated skills and evidence; the match score itself is calculated "
        "with transparent deterministic rules."
    )

    use_sample = st.checkbox("Use synthetic sample résumé and job", value=True)
    resume_upload = st.file_uploader(
        "Résumé (TXT, MD, or PDF)",
        type=["txt", "md", "pdf"],
        key="career_resume",
    )
    job_uploads = st.file_uploader(
        "Job descriptions — maximum 3",
        type=["txt", "md", "pdf"],
        accept_multiple_files=True,
        key="career_jobs",
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

    if st.button("Analyze career match", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is required for structured career extraction.")
        elif resume_file is None or not job_files:
            st.warning("Provide one résumé and at least one job description.")
        else:
            try:
                engine = CareerIntelligence()
                with st.status("Extracting structured career data...", expanded=True) as status:
                    st.write(f"Analyzing résumé: {resume_file.name}")
                    candidate = _extract_with_cache(engine, "candidate", resume_file)
                    jobs = []
                    for job_file in job_files:
                        st.write(f"Analyzing job: {job_file.name}")
                        job = _extract_with_cache(engine, "job", job_file)
                        jobs.append(job)
                    status.update(label="Career analysis complete", state="complete")

                st.session_state.career_candidate = candidate
                st.session_state.career_jobs = jobs
                st.session_state.career_job_sources = [file.name for file in job_files]
                st.session_state.career_selected_job = 0
            except Exception as error:
                st.error(f"Career extraction failed: {error}")

    candidate = st.session_state.get("career_candidate")
    jobs = st.session_state.get("career_jobs", [])

    if candidate is None or not jobs:
        st.info("Analyze the sample documents or upload your own files to see the match dashboard.")
        return

    job_labels = [
        f"{job.job_title} — {job.company or 'Company not listed'}" for job in jobs
    ]
    selected_index = st.selectbox(
        "Compare against",
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
    metric1.metric("Weighted match", f"{match['score']}%")
    metric2.metric(
        "Required skills", f"{match['required_matched']}/{match['required_total']}"
    )
    metric3.metric(
        "Preferred skills", f"{match['preferred_matched']}/{match['preferred_total']}"
    )
    metric4.metric("Priority gaps", len(match["missing_skills"]))

    match_rows = [
        {
            "Skill": row["skill"],
            "Category": row["category"],
            "Importance": row["importance"].title(),
            "Status": row["status"].title(),
            "Résumé evidence": "; ".join(row["candidate_evidence"]) or "—",
            "Job evidence": "; ".join(row["job_evidence"]) or "—",
        }
        for row in match["rows"]
    ]
    st.dataframe(match_rows, width="stretch", hide_index=True)

    if match["category_summary"]:
        st.write("### Coverage by skill category")
        st.bar_chart(
            match["category_summary"],
            x="category",
            y=["matched", "required"],
            color=["#16a34a", "#94a3b8"],
        )

    with st.expander("Inspect extracted structured profiles"):
        profile_col1, profile_col2 = st.columns(2)
        profile_col1.write("**Candidate profile**")
        profile_col1.json(candidate.model_dump(mode="json"))
        profile_col2.write("**Job profile**")
        profile_col2.json(job.model_dump(mode="json"))

    st.write("### Personalized learning plan")
    plan_key = f"{candidate.headline}:{job.job_title}:{','.join(match['missing_skills'])}"
    plans = st.session_state.setdefault("learning_plans", {})

    if st.button("Generate four-week plan", key="generate_learning_plan"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is required to generate a plan.")
        else:
            try:
                with st.spinner("Building a prioritized learning plan..."):
                    plans[plan_key] = CareerIntelligence().generate_learning_plan(
                        candidate, job, match["missing_skills"]
                    )
            except Exception as error:
                st.error(f"Learning-plan generation failed: {error}")

    if plan_key in plans:
        _render_learning_plan(plans[plan_key])


def render_interview_lab():
    st.header("Role-Specific Interview Lab")
    candidate = st.session_state.get("career_candidate")
    job = st.session_state.get("current_job")

    if candidate is None or job is None:
        st.info("Complete a Career Match analysis first so questions can target the selected role.")
        return

    st.caption(f"Target role: {job.job_title} | Candidate: {candidate.headline}")
    control1, control2 = st.columns(2)
    question_type = control1.selectbox(
        "Question type",
        ["SQL", "Python", "Data Modeling", "System Design", "Behavioral"],
    )
    difficulty = control2.selectbox(
        "Difficulty", ["Foundational", "Intermediate", "Advanced"], index=1
    )

    if st.button("Generate interview question", type="primary"):
        if not os.getenv("OPENAI_API_KEY"):
            st.error("OPENAI_API_KEY is required to generate a question.")
        else:
            try:
                with st.spinner("Creating a role-specific question..."):
                    st.session_state.current_interview_question = (
                        CareerIntelligence().generate_interview_question(
                            candidate, job, question_type, difficulty
                        )
                    )
                    st.session_state.pop("latest_interview_feedback", None)
            except Exception as error:
                st.error(f"Question generation failed: {error}")

    question = st.session_state.get("current_interview_question")

    if question is None:
        return

    st.subheader(f"{question.question_type} — {question.difficulty}")
    st.write(question.question)
    if question.context:
        st.caption(question.context)

    with st.expander("What the interviewer will evaluate"):
        for criterion in question.evaluation_criteria:
            st.write(f"- {criterion}")

    answer = st.text_area(
        "Your answer",
        height=180,
        placeholder="Explain your reasoning, tradeoffs, and production considerations...",
    )

    if st.button("Score my answer"):
        if len(answer.strip()) < 20:
            st.warning("Write a more complete answer before requesting feedback.")
        else:
            try:
                with st.spinner("Scoring against the interview rubric..."):
                    feedback = CareerIntelligence().score_interview_answer(
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
            except Exception as error:
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
            for strength in feedback.strengths:
                st.write(f"- {strength}")
        with feedback_col2:
            st.write("**Improve next**")
            for improvement in feedback.improvements:
                st.write(f"- {improvement}")

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
