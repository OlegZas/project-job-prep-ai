SKILL_CATEGORIES = {
    "Languages": {"Python", "SQL", "Java", "Scala", "Bash"},
    "Cloud": {"GCP", "AWS", "Azure"},
    "Warehouses & Platforms": {
        "BigQuery",
        "Snowflake",
        "Redshift",
        "Databricks",
        "Synapse",
    },
    "Processing & Streaming": {"Spark", "Kafka", "Flink", "Beam"},
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
    "AI & Analytics": {"Machine Learning", "RAG", "LLM", "Vector Search"},
}


ALIASES = {
    "apache airflow": "Airflow",
    "apache beam": "Beam",
    "apache flink": "Flink",
    "apache kafka": "Kafka",
    "apache spark": "Spark",
    "amazon redshift": "Redshift",
    "amazon web services": "AWS",
    "azure synapse": "Synapse",
    "big query": "BigQuery",
    "continuous integration": "CI/CD",
    "continuous delivery": "CI/CD",
    "data lake": "Data Lakes",
    "data warehouse": "Data Warehousing",
    "data modelling": "Data Modeling",
    "docker containers": "Docker",
    "extract load transform": "ELT",
    "extract transform load": "ETL",
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
