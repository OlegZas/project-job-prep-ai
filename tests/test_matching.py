from src.career_models import CandidateProfile, CandidateSkill, JobProfile, JobSkill
from src.matching import build_skill_match
from src.skill_taxonomy import category_for_skill, normalize_skill_name


def make_candidate():
    return CandidateProfile(
        candidate_name="Jordan",
        headline="Data Engineer",
        target_roles=["Senior Data Engineer"],
        skills=[
            CandidateSkill(
                name="Google BigQuery",
                category="Cloud",
                proficiency="advanced",
                years_experience=3,
                evidence=["Designed BigQuery tables"],
            ),
            CandidateSkill(
                name="Python",
                category="Languages",
                proficiency="advanced",
                years_experience=4,
                evidence=["Built Python pipelines"],
            ),
        ],
        achievements=["Reduced query cost"],
    )


def make_job():
    return JobProfile(
        job_title="Senior Data Engineer",
        company="Northstar",
        seniority="Senior",
        skills=[
            JobSkill(
                name="Big Query",
                category="Warehouses",
                importance="required",
                evidence=["BigQuery required"],
            ),
            JobSkill(
                name="Python",
                category="Languages",
                importance="required",
                evidence=["Python required"],
            ),
            JobSkill(
                name="Terraform",
                category="Infrastructure",
                importance="preferred",
                evidence=["Terraform preferred"],
            ),
        ],
        responsibilities=["Build pipelines"],
    )


def test_taxonomy_normalizes_aliases():
    assert normalize_skill_name("google cloud platform") == "GCP"
    assert normalize_skill_name("Big Query") == "BigQuery"
    assert category_for_skill("Apache Kafka") == "Processing & Streaming"


def test_match_is_weighted_and_evidence_based():
    result = build_skill_match(make_candidate(), make_job())

    assert result["score"] == 80
    assert result["required_matched"] == 2
    assert result["required_total"] == 2
    assert result["preferred_matched"] == 0
    assert result["missing_skills"] == ["Terraform"]
    assert result["rows"][0]["status"] == "missing"


def test_duplicate_job_skill_prefers_required_importance():
    job = make_job()
    job.skills.append(
        JobSkill(
            name="google bigquery",
            category="Other",
            importance="preferred",
            evidence=["BigQuery is also preferred"],
        )
    )

    result = build_skill_match(make_candidate(), job)

    bigquery_rows = [row for row in result["rows"] if row["skill"] == "BigQuery"]
    assert len(bigquery_rows) == 1
    assert bigquery_rows[0]["importance"] == "required"


def test_broad_job_requirements_match_named_resume_evidence():
    candidate = CandidateProfile(
        candidate_name="Oleg",
        headline="Data Engineer",
        target_roles=["Data Engineer"],
        skills=[
            CandidateSkill(name="Python", category="Languages", proficiency="advanced", years_experience=None, evidence=["Built Python pipelines"]),
            CandidateSkill(name="SQL", category="Languages", proficiency="advanced", years_experience=None, evidence=["Developed SQL transformations"]),
            CandidateSkill(name="GCP", category="Cloud", proficiency="intermediate", years_experience=None, evidence=["Designed workflows on Google Cloud"]),
            CandidateSkill(name="BigQuery", category="Warehouses & Platforms", proficiency="intermediate", years_experience=None, evidence=["Built BigQuery tables"]),
            CandidateSkill(name="Airflow", category="Orchestration", proficiency="intermediate", years_experience=None, evidence=["Orchestrated Airflow jobs"]),
        ],
        achievements=[
            "Build and maintain production data pipelines and reporting workflows.",
            "Completed intensive data engineering training.",
        ],
    )
    job = JobProfile(
        job_title="Data Engineer",
        company="Slalom",
        seniority="Mid-level",
        skills=[
            JobSkill(
                name="Programming with SQL, Python, Java, or Scala",
                category="Other",
                importance="required",
                evidence=["Proficiency in programming languages such as SQL, Python, Java or Scala."],
            ),
            JobSkill(
                name="Cloud or data platform experience",
                category="Other",
                importance="required",
                evidence=["Experience with AWS, Azure, GCP, Databricks, or Snowflake."],
            ),
            JobSkill(
                name="Production data engineering experience",
                category="Other",
                importance="required",
                evidence=["Build, deploy, or support production data engineering solutions."],
            ),
            JobSkill(
                name="Learning mindset",
                category="Other",
                importance="preferred",
                evidence=["A growth-oriented mindset and willingness to learn."],
            ),
        ],
        responsibilities=["Build reliable data platforms"],
    )

    result = build_skill_match(candidate, job)

    assert result["score"] == 100
    assert result["required_matched"] == 3
    assert result["preferred_matched"] == 1
    assert all(row["candidate_evidence"] for row in result["rows"])


def test_unproven_consulting_requirement_stays_missing():
    job = make_job()
    job.skills = [
        JobSkill(
            name="Consulting or client-facing delivery",
            category="Professional Skills",
            importance="required",
            evidence=["Experience in consulting or client-facing teams."],
        )
    ]

    result = build_skill_match(make_candidate(), job)

    assert result["score"] == 0
    assert result["missing_skills"] == ["Consulting or client-facing delivery"]
