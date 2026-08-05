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
