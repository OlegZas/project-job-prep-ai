from types import SimpleNamespace

from src.career_intelligence import CareerIntelligence
from src.career_models import (
    CandidateProfile,
    CandidateSkill,
    InterviewFeedback,
    InterviewQuestion,
    JobProfile,
    JobSkill,
    LearningPlan,
    LearningWeek,
)


class FakeResponses:
    def __init__(self, parsed_results):
        self.parsed_results = list(parsed_results)
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed_results.pop(0))


class FakeClient:
    def __init__(self, parsed_results):
        self.responses = FakeResponses(parsed_results)


def candidate_profile():
    return CandidateProfile(
        candidate_name="Jordan",
        headline="Data Engineer",
        target_roles=["Senior Data Engineer"],
        skills=[
            CandidateSkill(
                name="Google BigQuery",
                category="Other",
                proficiency="advanced",
                years_experience=3,
                evidence=["Designed BigQuery tables"],
            )
        ],
        achievements=["Reduced cost"],
    )


def job_profile():
    return JobProfile(
        job_title="Senior Data Engineer",
        company="Northstar",
        seniority="Senior",
        skills=[
            JobSkill(
                name="Apache Kafka",
                category="Other",
                importance="required",
                evidence=["Kafka required"],
            )
        ],
        responsibilities=["Build streaming pipelines"],
    )


def test_structured_candidate_extraction_normalizes_taxonomy():
    client = FakeClient([candidate_profile()])
    intelligence = CareerIntelligence(client=client)

    result = intelligence.extract_candidate("resume text", "resume.txt")

    assert result.skills[0].name == "BigQuery"
    assert result.skills[0].category == "Warehouses & Platforms"
    assert client.responses.calls[0]["text_format"] is CandidateProfile


def test_structured_job_extraction_normalizes_taxonomy():
    client = FakeClient([job_profile()])
    intelligence = CareerIntelligence(client=client)

    result = intelligence.extract_job("job text", "job.txt")

    assert result.skills[0].name == "Kafka"
    assert result.skills[0].category == "Processing & Streaming"
    assert client.responses.calls[0]["text_format"] is JobProfile


def test_interview_feedback_schema_enforces_score_range():
    try:
        InterviewFeedback(
            score=101,
            technical_accuracy=25,
            clarity=25,
            tradeoff_reasoning=25,
            production_readiness=25,
            strengths=[],
            improvements=[],
            model_answer="answer",
            follow_up_question="follow up",
        )
        raise AssertionError("Expected score validation")
    except ValueError:
        pass


def test_question_schema_uses_supported_types():
    question = InterviewQuestion(
        question_type="System Design",
        difficulty="Advanced",
        question="Design a streaming platform.",
        context="Kafka role",
        evaluation_criteria=["Reliability"],
    )

    assert question.question_type == "System Design"


def test_overall_interview_score_is_sum_of_rubric_dimensions():
    feedback = InterviewFeedback(
        score=1,
        technical_accuracy=20,
        clarity=18,
        tradeoff_reasoning=16,
        production_readiness=14,
        strengths=["Clear"],
        improvements=["More detail"],
        model_answer="Model answer",
        follow_up_question="Follow up?",
    )
    client = FakeClient([feedback])
    intelligence = CareerIntelligence(client=client)
    question = InterviewQuestion(
        question_type="System Design",
        difficulty="Intermediate",
        question="Design a pipeline.",
        context="Streaming role",
        evaluation_criteria=["Reliability"],
    )

    result = intelligence.score_interview_answer(question, "A complete candidate answer")

    assert result.score == 68


def test_learning_plan_requires_exactly_four_weeks():
    week = LearningWeek(
        week_number=1,
        focus_skills=["Kafka"],
        objectives=["Explain consumer groups"],
        practical_task="Build a local producer and consumer",
        interview_questions=["How do offsets work?"],
    )

    try:
        LearningPlan(
            target_role="Data Engineer",
            strategy="Prioritize streaming",
            weeks=[week],
            success_metric="Complete a mock interview",
        )
        raise AssertionError("Expected four-week plan validation")
    except ValueError:
        pass
