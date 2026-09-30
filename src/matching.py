from src.career_models import CandidateProfile, JobProfile
from src.skill_taxonomy import (
    category_for_skill,
    normalize_skill_name,
    skills_mentioned,
)


def _candidate_evidence(candidate: CandidateProfile) -> list[str]:
    evidence = list(candidate.achievements)
    for skill in candidate.skills:
        evidence.extend(skill.evidence)
    return list(dict.fromkeys(item for item in evidence if item))


def _find_capability_match(candidate, job_skill, candidate_skills):
    job_text = " ".join([job_skill.name, *job_skill.evidence])
    named_options = skills_mentioned(job_text)
    named_matches = [
        candidate_skills[name.casefold()]
        for name in named_options
        if name.casefold() in candidate_skills
    ]
    if named_matches:
        evidence = [item for skill in named_matches for item in skill.evidence]
        return named_matches[0], list(dict.fromkeys(evidence)), [
            normalize_skill_name(skill.name) for skill in named_matches
        ]

    text = job_text.casefold()
    evidence = _candidate_evidence(candidate)
    evidence_text = " ".join(evidence).casefold()
    candidate_categories = {
        category_for_skill(normalize_skill_name(skill.name)) for skill in candidate.skills
    }
    canonical_names = {normalize_skill_name(skill.name) for skill in candidate.skills}

    category_rules = [
        (
            ("programming language", "programming with"),
            {"Languages"},
        ),
        (
            ("cloud or data platform", "cloud platform", "data platform experience"),
            {"Cloud", "Warehouses & Platforms"},
        ),
        (
            ("modern data engineering", "data engineering capabilities"),
            {"Data Engineering", "Processing & Streaming", "Orchestration", "Transformation"},
        ),
    ]
    for phrases, qualifying_categories in category_rules:
        if any(phrase in text for phrase in phrases) and candidate_categories & qualifying_categories:
            matches = [
                skill for skill in candidate.skills
                if category_for_skill(normalize_skill_name(skill.name)) in qualifying_categories
            ]
            matched_evidence = [item for skill in matches[:4] for item in skill.evidence]
            return matches[0], list(dict.fromkeys(matched_evidence)), [
                normalize_skill_name(skill.name) for skill in matches[:4]
            ]

    if any(phrase in text for phrase in ("multiple platforms", "additional cloud", "across multiple platforms")):
        platform_skills = [
            skill for skill in candidate.skills
            if category_for_skill(normalize_skill_name(skill.name))
            in {"Cloud", "Warehouses & Platforms"}
        ]
        if len({normalize_skill_name(skill.name) for skill in platform_skills}) >= 2:
            return platform_skills[0], [item for skill in platform_skills[:4] for item in skill.evidence], [
                normalize_skill_name(skill.name) for skill in platform_skills[:4]
            ]

    evidence_rules = [
        (
            ("production data engineering", "production data", "production-grade engineering"),
            ("build", "maintain", "deploy", "support"),
            ("pipeline", "warehouse", "data service", "workflow"),
            "Production Data Engineering",
        ),
        (
            ("communication", "explain technical", "different audiences"),
            ("translate", "business insight", "stakeholder", "reporting", "dashboard"),
            (),
            "Communication",
        ),
        (
            ("learning mindset", "growth-oriented", "willingness to learn"),
            ("training", "completed", "learn", "course", "education"),
            (),
            "Learning Mindset",
        ),
        (
            ("consulting", "client-facing"),
            ("client", "consulting"),
            (),
            "Consulting",
        ),
    ]
    for job_phrases, required_terms, object_terms, label in evidence_rules:
        if not any(phrase in text for phrase in job_phrases):
            continue
        if not any(term in evidence_text for term in required_terms):
            continue
        if object_terms and not any(term in evidence_text for term in object_terms):
            continue
        matching_evidence = [
            item for item in evidence
            if any(term in item.casefold() for term in required_terms)
            and (not object_terms or any(term in item.casefold() for term in object_terms))
        ]
        return None, matching_evidence[:3], [label]

    if "certification" in text and any("certif" in item.casefold() for item in evidence):
        matching_evidence = [item for item in evidence if "certif" in item.casefold()]
        return None, matching_evidence[:3], ["Certification"]

    return None, [], []


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
        matched_evidence = candidate_skill.evidence if candidate_skill else []
        matched_skills = [canonical] if candidate_skill else []
        if candidate_skill is None:
            candidate_skill, matched_evidence, matched_skills = _find_capability_match(
                candidate, job_skill, candidate_skills
            )
        is_matched = bool(candidate_skill or matched_evidence)
        weight = 2 if job_skill.importance == "required" else 1
        available_weight += weight

        if is_matched:
            earned_weight += weight

        rows.append(
            {
                "skill": canonical,
                "category": category_for_skill(canonical),
                "importance": job_skill.importance,
                "status": "matched" if is_matched else "missing",
                "proficiency": (
                    candidate_skill.proficiency if candidate_skill else (
                        "evidenced" if matched_evidence else "not evidenced"
                    )
                ),
                "candidate_evidence": matched_evidence,
                "matched_skills": matched_skills,
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
