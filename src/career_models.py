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
    focus_skills: list[str] = Field(min_length=1, max_length=3)
    objectives: list[str] = Field(min_length=1, max_length=3)
    practical_task: str = Field(max_length=320)
    interview_questions: list[str] = Field(min_length=1, max_length=3)


class LearningPlan(BaseModel):
    target_role: str
    strategy: str = Field(max_length=420)
    weeks: list[LearningWeek] = Field(min_length=4, max_length=4)
    success_metric: str = Field(max_length=280)


class InterviewQuestion(BaseModel):
    question_type: Literal["SQL", "Python", "Data Modeling", "System Design", "Behavioral"]
    difficulty: Literal["Foundational", "Intermediate", "Advanced"]
    question: str = Field(max_length=520)
    context: str = Field(max_length=300)
    evaluation_criteria: list[str] = Field(min_length=1, max_length=5)


class InterviewFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    technical_accuracy: int = Field(ge=0, le=25)
    clarity: int = Field(ge=0, le=25)
    tradeoff_reasoning: int = Field(ge=0, le=25)
    production_readiness: int = Field(ge=0, le=25)
    strengths: list[str] = Field(max_length=3)
    improvements: list[str] = Field(max_length=3)
    model_answer: str = Field(max_length=1600)
    follow_up_question: str = Field(max_length=300)
