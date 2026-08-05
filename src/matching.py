from src.career_models import CandidateProfile, JobProfile
from src.skill_taxonomy import category_for_skill, normalize_skill_name


def build_skill_match(candidate: CandidateProfile, job: JobProfile) -> dict:
    candidate_skills = {}

    for skill in candidate.skills:
        canonical = normalize_skill_name(skill.name)
        candidate_skills.setdefault(canonical.casefold(), skill)

    job_skills = {}

    for skill in job.skills:
        canonical = normalize_skill_name(skill.name)
        key = canonical.casefold()
        existing = job_skills.get(key)

        if existing is None or skill.importance == "required":
            job_skills[key] = skill

    rows = []
    earned_weight = 0
    available_weight = 0

    for key, job_skill in job_skills.items():
        canonical = normalize_skill_name(job_skill.name)
        candidate_skill = candidate_skills.get(key)
        weight = 2 if job_skill.importance == "required" else 1
        available_weight += weight

        if candidate_skill:
            earned_weight += weight

        rows.append(
            {
                "skill": canonical,
                "category": category_for_skill(canonical),
                "importance": job_skill.importance,
                "status": "matched" if candidate_skill else "missing",
                "proficiency": (
                    candidate_skill.proficiency if candidate_skill else "not evidenced"
                ),
                "candidate_evidence": (
                    candidate_skill.evidence if candidate_skill else []
                ),
                "job_evidence": job_skill.evidence,
            }
        )

    rows.sort(
        key=lambda row: (
            row["status"] != "missing",
            row["importance"] != "required",
            row["category"],
            row["skill"],
        )
    )

    category_counts = {}
    for row in rows:
        category = category_counts.setdefault(
            row["category"], {"required": 0, "matched": 0}
        )
        category["required"] += 1
        category["matched"] += row["status"] == "matched"

    category_summary = [
        {
            "category": category,
            "required": counts["required"],
            "matched": counts["matched"],
            "coverage": round(100 * counts["matched"] / counts["required"]),
        }
        for category, counts in sorted(category_counts.items())
    ]

    required_rows = [row for row in rows if row["importance"] == "required"]
    preferred_rows = [row for row in rows if row["importance"] == "preferred"]

    return {
        "score": round(100 * earned_weight / available_weight) if available_weight else 0,
        "rows": rows,
        "category_summary": category_summary,
        "required_matched": sum(row["status"] == "matched" for row in required_rows),
        "required_total": len(required_rows),
        "preferred_matched": sum(row["status"] == "matched" for row in preferred_rows),
        "preferred_total": len(preferred_rows),
        "missing_skills": [row["skill"] for row in rows if row["status"] == "missing"],
    }
