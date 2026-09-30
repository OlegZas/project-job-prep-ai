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
    extraction_version = "v2-atomic-skills"

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
                "Extract a data engineering candidate profile using plain, atomic skill "
                "names such as Python, SQL, BigQuery, Data Modeling, Communication, or "
                "Production Data Engineering. Split combined tool lists into separate "
                "skills. Include broader capabilities only when the résumé explicitly "
                "supports them through work or project evidence. Use only document "
                "evidence, never infer sensitive traits, and keep evidence excerpts short."
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
                "Extract a data engineering job profile with concise, matchable skills. "
                "Do not use full requirement sentences as skill names. Split lists into "
                "atomic skills when every item is required. When a job asks for at least "
                "one option, such as one cloud platform or one programming language, keep "
                "it as one broader requirement and preserve the alternatives in evidence. "
                "Separate required and preferred only when supported by the document. "
                "Keep evidence excerpts short and verbatim."
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
                "Create a simple, realistic four-week interview plan. Prioritize at most "
                "six important gaps and build on the candidate's existing strengths. Use "
                "one short strategy paragraph and one short success metric. For each week, "
                "return no more than three focus skills, two or three objectives of at most "
                "15 words each, one practical task of at most two sentences, and two or "
                "three concise interview questions. Avoid long lists and repeated advice."
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
            "candidate_achievements": candidate.achievements[:6],
            "job": job.model_dump(mode="json"),
            "question_type": question_type,
            "difficulty": difficulty,
        }
        return self._parse(
            InterviewQuestion,
            (
                "Create one personalized data engineering interview question using the "
                "target job, its responsibilities, and the candidate's demonstrated skills. "
                "Keep the question to one or two sentences and do not list every technology. "
                "Use a short context explaining why it fits this candidate and role. Return "
                "three to five concrete criteria, each under 15 words. Do not reveal the answer."
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
                "Score the answer against the supplied criteria. Be fair, specific, and "
                "easy to understand. Give at most three short strengths and three short "
                "improvements. Keep the model answer concise and practical. The four rubric "
                "subscores must align with the overall score."
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
