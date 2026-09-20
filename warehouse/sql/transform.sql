CREATE OR REPLACE VIEW staging.pipeline_runs AS
SELECT
    event_id AS run_id,
    occurred_at,
    CAST(occurred_at AS DATE) AS event_date,
    payload->>'operation' AS operation,
    payload->>'status' AS status,
    CAST(payload->>'duration_ms' AS BIGINT) AS duration_ms,
    CAST(payload->>'input_count' AS BIGINT) AS input_count,
    CAST(payload->>'output_count' AS BIGINT) AS output_count,
    CAST(payload->>'cache_hits' AS BIGINT) AS cache_hits,
    CAST(payload->>'cache_misses' AS BIGINT) AS cache_misses,
    payload->>'model' AS model,
    payload->>'error_type' AS error_type
FROM raw.events
WHERE event_type = 'pipeline_run';

CREATE OR REPLACE VIEW staging.interview_metrics AS
SELECT
    event_id AS attempt_id,
    occurred_at,
    CAST(occurred_at AS DATE) AS event_date,
    payload->>'role_family' AS role_family,
    payload->>'question_type' AS question_type,
    payload->>'difficulty' AS difficulty,
    CAST(payload->>'score' AS INTEGER) AS score,
    CAST(payload->>'technical_accuracy' AS INTEGER) AS technical_accuracy,
    CAST(payload->>'clarity' AS INTEGER) AS clarity,
    CAST(payload->>'tradeoff_reasoning' AS INTEGER) AS tradeoff_reasoning,
    CAST(payload->>'production_readiness' AS INTEGER) AS production_readiness
FROM raw.events
WHERE event_type = 'interview_metric';

CREATE OR REPLACE VIEW staging.retrieval_evaluations AS
SELECT
    event_id AS evaluation_id,
    occurred_at,
    CAST(occurred_at AS DATE) AS event_date,
    payload->>'evaluation_name' AS evaluation_name,
    CAST(payload->>'case_count' AS INTEGER) AS case_count,
    CAST(payload->>'top_k' AS INTEGER) AS top_k,
    CAST(payload->>'minimum_score' AS DOUBLE) AS minimum_score,
    CAST(payload->>'hit_rate' AS DOUBLE) AS hit_rate,
    CAST(payload->>'mean_reciprocal_rank' AS DOUBLE) AS mean_reciprocal_rank,
    CAST(payload->>'cold_seconds' AS DOUBLE) AS cold_seconds,
    CAST(payload->>'warm_seconds' AS DOUBLE) AS warm_seconds
FROM raw.events
WHERE event_type = 'retrieval_evaluation';

CREATE OR REPLACE TABLE marts.pipeline_daily AS
SELECT
    event_date,
    operation,
    count(*) AS run_count,
    count(*) FILTER (WHERE status = 'success') AS success_count,
    round(avg(duration_ms), 2) AS average_duration_ms,
    sum(input_count) AS input_count,
    sum(output_count) AS output_count,
    sum(cache_hits) AS cache_hits,
    sum(cache_misses) AS cache_misses,
    round(
        100.0 * sum(cache_hits) / nullif(sum(cache_hits) + sum(cache_misses), 0),
        2
    ) AS cache_hit_percent
FROM staging.pipeline_runs
GROUP BY event_date, operation;

CREATE OR REPLACE TABLE marts.interview_progress AS
SELECT
    event_date,
    role_family,
    question_type,
    difficulty,
    count(*) AS attempt_count,
    round(avg(score), 2) AS average_score,
    round(avg(technical_accuracy), 2) AS average_accuracy,
    round(avg(clarity), 2) AS average_clarity,
    round(avg(tradeoff_reasoning), 2) AS average_tradeoffs,
    round(avg(production_readiness), 2) AS average_production_readiness
FROM staging.interview_metrics
GROUP BY event_date, role_family, question_type, difficulty;

CREATE OR REPLACE TABLE marts.retrieval_quality AS
SELECT
    event_date,
    evaluation_name,
    case_count,
    top_k,
    minimum_score,
    hit_rate,
    mean_reciprocal_rank,
    cold_seconds,
    warm_seconds,
    round(cold_seconds / nullif(warm_seconds, 0), 2) AS cache_speedup
FROM staging.retrieval_evaluations;
