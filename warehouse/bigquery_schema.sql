-- DataPrep AI analytics schema (run after replacing YOUR_PROJECT_ID).
-- No resume text, document text, file names, user answers, or API keys are stored.

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.dataprep_analytics`
OPTIONS(location = "US");

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.dataprep_analytics.pipeline_runs` (
  run_id STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  operation STRING NOT NULL,
  status STRING NOT NULL,
  duration_ms INT64 NOT NULL,
  input_count INT64 NOT NULL,
  output_count INT64 NOT NULL,
  cache_hits INT64 NOT NULL,
  cache_misses INT64 NOT NULL,
  model STRING,
  error_type STRING,
  app_version STRING
)
PARTITION BY DATE(occurred_at)
CLUSTER BY operation, status;

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.dataprep_analytics.retrieval_evaluations` (
  evaluation_id STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  evaluation_name STRING NOT NULL,
  case_count INT64 NOT NULL,
  top_k INT64 NOT NULL,
  minimum_score FLOAT64 NOT NULL,
  hit_rate FLOAT64 NOT NULL,
  mean_reciprocal_rank FLOAT64 NOT NULL,
  cold_seconds FLOAT64 NOT NULL,
  warm_seconds FLOAT64 NOT NULL
)
PARTITION BY DATE(occurred_at);

CREATE TABLE IF NOT EXISTS `YOUR_PROJECT_ID.dataprep_analytics.interview_metrics` (
  attempt_id STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  role_family STRING NOT NULL,
  question_type STRING NOT NULL,
  difficulty STRING NOT NULL,
  score INT64 NOT NULL,
  technical_accuracy INT64 NOT NULL,
  clarity INT64 NOT NULL,
  tradeoff_reasoning INT64 NOT NULL,
  production_readiness INT64 NOT NULL
)
PARTITION BY DATE(occurred_at)
CLUSTER BY role_family, question_type, difficulty;
