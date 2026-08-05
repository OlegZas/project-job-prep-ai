from datetime import datetime, timezone

from streamlit.testing.v1 import AppTest

from src.career_models import (
    CandidateProfile,
    CandidateSkill,
    InterviewFeedback,
    InterviewQuestion,
    JobProfile,
    JobSkill,
)


def candidate_profile():
    return CandidateProfile(
        candidate_name="Jordan",
        headline="Data Engineer",
        target_roles=["Senior Data Engineer"],
        skills=[
            CandidateSkill(
                name="Python",
                category="Languages",
                proficiency="advanced",
                years_experience=4,
                evidence=["Built Python pipelines"],
            )
        ],
        achievements=["Reduced processing time"],
    )


def job_profile():
    return JobProfile(
        job_title="Senior Data Engineer",
        company="Northstar",
        seniority="Senior",
        skills=[
            JobSkill(
                name="Python",
                category="Languages",
                importance="required",
                evidence=["Python required"],
            ),
            JobSkill(
                name="Kafka",
                category="Processing & Streaming",
                importance="required",
                evidence=["Kafka required"],
            ),
        ],
        responsibilities=["Build streaming pipelines"],
    )


def interview_question():
    return InterviewQuestion(
        question_type="System Design",
        difficulty="Intermediate",
        question="Design a reliable streaming pipeline.",
        context="Kafka role",
        evaluation_criteria=["Reliability", "Observability"],
    )


def interview_feedback():
    return InterviewFeedback(
        score=70,
        technical_accuracy=20,
        clarity=18,
        tradeoff_reasoning=17,
        production_readiness=15,
        strengths=["Clear partition strategy"],
        improvements=["Add recovery testing"],
        model_answer="Use replicated brokers and idempotent sinks.",
        follow_up_question="How would you handle replay?",
    )


def seeded_app():
    app = AppTest.from_file("app.py", default_timeout=20)
    app.session_state["career_candidate"] = candidate_profile()
    app.session_state["career_jobs"] = [job_profile()]
    app.session_state["career_job_sources"] = ["job.txt"]
    return app


def test_career_match_dashboard_renders_from_structured_profiles():
    app = seeded_app().run()

    assert not app.exception
    assert any(metric.value == "50%" for metric in app.metric)
    assert len(app.dataframe) >= 2


def test_interview_feedback_and_history_render():
    app = seeded_app()
    question = interview_question()
    feedback = interview_feedback()
    app.session_state["current_job"] = job_profile()
    app.session_state["current_interview_question"] = question
    app.session_state["latest_interview_feedback"] = feedback
    app.session_state["interview_history"] = [
        {
            "attempted_at": datetime.now(timezone.utc).isoformat(),
            "role": "Senior Data Engineer",
            "question_type": question.question_type,
            "difficulty": question.difficulty,
            "question": question.question,
            "answer": "Candidate answer",
            **feedback.model_dump(mode="json"),
        }
    ]

    app.run()

    assert not app.exception
    assert any(metric.value == "70/100" for metric in app.metric)
    assert len(app.download_button) == 1
