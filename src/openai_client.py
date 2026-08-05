import os

from openai import OpenAI


def _positive_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")

    return value


def create_openai_client() -> OpenAI:
    """Create a bounded client so UI requests cannot wait indefinitely."""
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=_positive_float("OPENAI_TIMEOUT_SECONDS", 60.0),
        max_retries=int(_positive_float("OPENAI_MAX_RETRIES", 1)),
    )
