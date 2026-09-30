import re


SKILL_CATEGORIES = {
    "Languages": {"Python", "SQL", "Java", "Scala", "Bash", "R", "Groovy", "JavaScript"},
    "Cloud": {"GCP", "AWS", "Azure"},
    "Warehouses & Platforms": {
        "BigQuery",
        "Snowflake",
        "Redshift",
        "Databricks",
        "Synapse",
    },
    "Processing & Streaming": {"Spark", "Kafka", "Flink", "Beam", "Pub/Sub"},
    "Orchestration": {"Airflow", "Dagster", "Prefect"},
    "Transformation": {"dbt", "ETL", "ELT"},
    "Databases": {"PostgreSQL", "MySQL", "SQL Server", "MongoDB", "Redis"},
    "Infrastructure": {"Docker", "Kubernetes", "Terraform", "Git", "CI/CD"},
    "Data Engineering": {
        "Data Modeling",
        "Data Quality",
        "Data Governance",
        "Batch Processing",
        "Stream Processing",
        "Lakehouse",
        "Data Lakes",
        "Data Warehousing",
    },
    "Professional Skills": {
        "Communication",
        "Collaboration",
        "Problem Solving",
        "Consulting",
        "Learning Mindset",
    },
    "AI & Analytics": {"Machine Learning", "RAG", "LLM", "Vector Search", "Vertex AI"},
}


ALIASES = {
    "apache airflow": "Airflow",
    "apache beam": "Beam",
    "apache flink": "Flink",
    "apache kafka": "Kafka",
    "apache spark": "Spark",
    "pyspark": "Spark",
    "amazon redshift": "Redshift",
    "amazon web services": "AWS",
    "azure synapse": "Synapse",
    "big query": "BigQuery",
    "continuous integration": "CI/CD",
    "continuous delivery": "CI/CD",
    "confluent kafka": "Kafka",
    "cloud composer": "Airflow",
    "google cloud composer": "Airflow",
    "google cloud pub/sub": "Pub/Sub",
    "google pub/sub": "Pub/Sub",
    "pubsub": "Pub/Sub",
    "google cloud dataflow": "Beam",
    "dataflow": "Beam",
    "data lake": "Data Lakes",
    "data warehouse": "Data Warehousing",
    "data modelling": "Data Modeling",
    "docker containers": "Docker",
    "extract load transform": "ELT",
    "extract transform load": "ETL",
    "etl/elt": "ETL",
    "google bigquery": "BigQuery",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "k8s": "Kubernetes",
    "large language models": "LLM",
    "machine learning": "Machine Learning",
    "microsoft azure": "Azure",
    "ms sql server": "SQL Server",
    "postgres": "PostgreSQL",
    "retrieval augmented generation": "RAG",
    "structured query language": "SQL",
    "github actions": "CI/CD",
    "problem-solving": "Problem Solving",
    "problem solving": "Problem Solving",
    "client-facing": "Consulting",
    "growth-oriented mindset": "Learning Mindset",
}


CANONICAL_LOOKUP = {
    skill.casefold(): skill
    for skills in SKILL_CATEGORIES.values()
    for skill in skills
}


def normalize_skill_name(name: str) -> str:
    cleaned = " ".join(name.strip().split())
    lowered = cleaned.casefold()
    return ALIASES.get(lowered, CANONICAL_LOOKUP.get(lowered, cleaned))


def category_for_skill(name: str) -> str:
    canonical = normalize_skill_name(name)

    for category, skills in SKILL_CATEGORIES.items():
        if canonical in skills:
            return category

    return "Other"


def skills_mentioned(text: str) -> set[str]:
    """Return canonical taxonomy skills that are explicitly named in free text."""
    normalized_text = re.sub(r"[^a-z0-9+#/]+", " ", text.casefold()).strip()
    padded_text = f" {normalized_text} "
    phrase_map = {
        **{skill.casefold(): skill for skill in CANONICAL_LOOKUP.values()},
        **ALIASES,
    }
    found = set()

    for phrase, canonical in sorted(
        phrase_map.items(), key=lambda item: len(item[0]), reverse=True
    ):
        normalized_phrase = re.sub(r"[^a-z0-9+#/]+", " ", phrase).strip()
        if len(normalized_phrase) < 2:
            continue
        if f" {normalized_phrase} " in padded_text:
            found.add(canonical)

    return found
