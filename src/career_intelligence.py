import json
import os

from src.career_models import (
    CandidateProfile,
    InterviewFeedback,
    InterviewQuestion,
    JobProfile,
    LearningPlan,
)
from src.openai_client import create_openai_client
from src.skill_taxonomy import category_for_skill, normalize_skill_name


class CareerIntelligence:
    max_document_characters = 30_000

    def __init__(self, client=None):
        self.client = client or create_openai_client()
        self.model = os.getenv("OPENAI_CAREER_MODEL", "gpt-5.6-luna")

    def _parse(self, schema, system_prompt, user_prompt):
        response = self.client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text_format=schema,
        )

        if response.output_parsed is None:
            raise RuntimeError("The model did not return a structured result")

        return response.output_parsed

    def extract_candidate(self, text: str, source_name: str) -> CandidateProfile:
        profile = self._parse(
            CandidateProfile,
            (
                "Extract a data engineering candidate profile. Use only explicit "
                "document evidence. Do not infer sensitive traits or unsupported skills. "
                "Evidence items must be short verbatim excerpts."
            ),
            f"Source: {source_name}\n\n{text[:self.max_document_characters]}",
        )

        for skill in profile.skills:
            skill.name = normalize_skill_name(skill.name)
            skill.category = category_for_skill(skill.name)

        return profile

    def extract_job(self, text: str, source_name: str) -> JobProfile:
        profile = self._parse(
            JobProfile,
            (
                "Extract a data engineering job profile. Separate required and preferred "
                "skills only when the document supports that distinction. Evidence items "
                "must be short verbatim excerpts."
            ),
            f"Source: {source_name}\n\n{text[:self.max_document_characters]}",
        )

        for skill in profile.skills:
            skill.name = normalize_skill_name(skill.name)
            skill.category = category_for_skill(skill.name)

        return profile

    def generate_learning_plan(
        self, candidate: CandidateProfile, job: JobProfile, missing_skills: list[str]
    ) -> LearningPlan:
        payload = {
            "candidate": candidate.model_dump(mode="json"),
            "job": job.model_dump(mode="json"),
            "missing_skills": missing_skills,
        }
        return self._parse(
            LearningPlan,
            (
                "Create a realistic four-week data engineering interview study plan. "
                "Prioritize missing required skills, hands-on evidence, and measurable outcomes."
            ),
            json.dumps(payload),
        )

    def generate_interview_question(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        question_type: str,
        difficulty: str,
    ) -> InterviewQuestion:
        payload = {
            "candidate_headline": candidate.headline,
            "candidate_skills": [skill.name for skill in candidate.skills],
            "job": job.model_dump(mode="json"),
            "question_type": question_type,
            "difficulty": difficulty,
        }
        return self._parse(
            InterviewQuestion,
            (
                "Create one role-specific data engineering interview question. "
                "Do not reveal the answer. Return concrete evaluation criteria."
            ),
            json.dumps(payload),
        )

    def score_interview_answer(
        self, question: InterviewQuestion, answer: str
    ) -> InterviewFeedback:
        payload = {
            "question": question.model_dump(mode="json"),
            "candidate_answer": answer,
        }
        feedback = self._parse(
            InterviewFeedback,
            (
                "Score the interview answer against the supplied criteria. Be rigorous, "
                "specific, and constructive. The four rubric subscores must align with "
                "the overall score."
            ),
            json.dumps(payload),
        )
        feedback.score = (
            feedback.technical_accuracy
            + feedback.clarity
            + feedback.tradeoff_reasoning
            + feedback.production_readiness
        )
        return feedback
