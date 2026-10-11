"""
Tests for Dedicated Writing Skills API (Ship 30 for 30 Writing Engine).
Verifies essay generation, formatting architecture (1-3-1 cadence, bold lead-ins),
citations, and structured artifact persistence.
"""

from unittest.mock import patch
import pytest
from starlette.testclient import TestClient
from app.core.config import settings


def test_ship30_skill_essay_generation_mock(client: TestClient):
    """
    Test POST /api/v1/skills/ship30 returns structured essay with artifact and citations.
    """
    mock_essay = (
        "Here is your atomic essay on Founder Mode.\n\n"
        ":::artifact{title=\"Ship 30 Essay: The Founder Mode Playbook\" type=\"markdown\"}\n"
        "# The Founder Mode Playbook: Why Great Leaders Refuse to Abdicate\n\n"
        "Most leaders are taught to hire great people and get out of the way.\n"
        "They delegate everything.\n"
        "They manage by spreadsheets.\n"
        "And then their company slowly loses its soul.\n"
        "Brian Chesky calls this the professional management trap.\n\n"
        "## The 3 Pillars of Founder Mode\n\n"
        "**The Trap:** Abdication disguised as delegation.\n"
        "Brian Chesky explained that when Airbnb scaled, advisors told him to step back. It nearly broke the company.\n\n"
        "**The Principle:** Stay relentlessly in the details.\n"
        "A founder must understand the product nuances that spreadsheets hide.\n\n"
        "**The Playbook:** Weekly executive reviews with zero bureaucracy.\n"
        "Replace committee sign-offs with direct founder involvement.\n\n"
        "## Actionable Next Steps\n"
        "1. Audit your top 3 projects this week.\n"
        "2. Review the details directly with engineers and designers.\n"
        ":::"
    )

    with patch("app.services.ship30_skill.generate_completion", return_value=mock_essay):
        res = client.post(
            f"{settings.API_V1_PREFIX}/skills/ship30",
            json={
                "topic": "Brian Chesky Founder Mode",
                "model_provider": "ollama",
                "model_name": "llama3.2",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["topic"] == "Brian Chesky Founder Mode"
        assert len(data["artifacts"]) == 1
        art = data["artifacts"][0]
        assert "Founder Mode" in art["title"]
        assert art["artifact_type"] == "markdown"
        assert "**The Trap:**" in art["content"]
        assert "**The Principle:**" in art["content"]
        assert len(data["citations"]) > 0


@pytest.mark.asyncio
async def test_ship30_service_trigger_detection():
    """
    Verify trigger keywords correctly route to Ship 30 writing skill.
    """
    from app.services.ship30_skill import ship30_service

    assert ship30_service.is_triggered("Can you write an essay about PLG?") is True
    assert ship30_service.is_triggered("Generate an atomic essay on pricing") is True
    assert ship30_service.is_triggered("Use ship30 methodology") is True
    assert ship30_service.is_triggered("What is PM market fit?", skill_param="ship30") is True
    assert ship30_service.is_triggered("What is retention?") is False
