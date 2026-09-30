"""Tests for SANS maturity model scoring (vkr-frz)."""
import pytest
from tests.conftest import BASE_ENV
from unittest.mock import patch


@pytest.mark.anyio
async def test_high_metrics_give_high_level():
    """Near-perfect metrics → SANS level 4 or 5."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from app.services.maturity import compute_maturity

        overview = {
            "completion_rate": 0.95,
            "avg_score": 0.90,
            "phishing_click_rate": 0.05,
            "phishing_report_rate": 0.60,
            "phishing_submit_rate": 0.02,
        }
        result = compute_maturity(overview)
        assert result["level"] >= 4
        assert result["score"] >= 80


@pytest.mark.anyio
async def test_zero_metrics_give_level_1():
    """No progress → SANS level 1."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from app.services.maturity import compute_maturity

        overview = {
            "completion_rate": 0.0,
            "avg_score": 0.0,
            "phishing_click_rate": 1.0,
            "phishing_report_rate": 0.0,
            "phishing_submit_rate": 0.8,
        }
        result = compute_maturity(overview)
        assert result["level"] == 1
        assert result["score"] < 30


@pytest.mark.anyio
async def test_maturity_has_required_fields():
    """Result contains level, score, label, and indicators."""
    with patch.dict("os.environ", BASE_ENV, clear=True):
        from app.services.maturity import compute_maturity

        result = compute_maturity({
            "completion_rate": 0.5,
            "avg_score": 0.5,
            "phishing_click_rate": 0.3,
            "phishing_report_rate": 0.1,
            "phishing_submit_rate": 0.1,
        })
        assert "level" in result
        assert "score" in result
        assert "label" in result
        assert "indicators" in result
        assert isinstance(result["indicators"], list)
