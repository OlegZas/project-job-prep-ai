import pytest

from src.openai_client import _positive_float


def test_positive_float_uses_default(monkeypatch):
    monkeypatch.delenv("TEST_TIMEOUT", raising=False)
    assert _positive_float("TEST_TIMEOUT", 60.0) == 60.0


@pytest.mark.parametrize("value", ["0", "-1", "not-a-number"])
def test_positive_float_rejects_invalid_values(monkeypatch, value):
    monkeypatch.setenv("TEST_TIMEOUT", value)
    with pytest.raises(ValueError):
        _positive_float("TEST_TIMEOUT", 60.0)
