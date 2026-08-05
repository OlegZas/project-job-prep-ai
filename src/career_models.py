from typing import Literal

from pydantic import BaseModel, Field


class CandidateSkill(BaseModel):
    name: str
    category: str
    proficiency: Literal["beginner", "intermediate", "advanced", "expert", "unknown"]
    years_experience: float | None
    evidence: list[str]


class CandidateProfile(BaseModel):
    candidate_name: str | None
    headline: str
    target_roles: list[str]
    skills: list[CandidateSkill]
    achievements: list[str]


class JobSkill(BaseModel):
    name: str
    category: str
    importance: Literal["required", "preferred"]
    evidence: list[str]


class JobProfile(BaseModel):
    job_title: str
    company: str | None
    seniority: str
    skills: list[JobSkill]
    responsibilities: list[str]


class LearningWeek(BaseModel):
    week_number: int = Field(ge=1, le=4)
    focus_skills: list[str]
    objectives: list[str]
    practical_task: str
    interview_questions: list[str]


class LearningPlan(BaseModel):
    target_role: str
    strategy: str
    weeks: list[LearningWeek] = Field(min_length=4, max_length=4)
    success_metric: str


class InterviewQuestion(BaseModel):
    question_type: Literal["SQL", "Python", "Data Modeling", "System Design", "Behavioral"]
    difficulty: Literal["Foundational", "Intermediate", "Advanced"]
    question: str
    context: str
    evaluation_criteria: list[str]


class InterviewFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    technical_accuracy: int = Field(ge=0, le=25)
    clarity: int = Field(ge=0, le=25)
    tradeoff_reasoning: int = Field(ge=0, le=25)
    production_readiness: int = Field(ge=0, le=25)
    strengths: list[str]
    improvements: list[str]
    model_answer: str
    follow_up_question: str
