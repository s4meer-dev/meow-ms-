import asyncio
from unittest.mock import MagicMock
import os
import pytest
from hindsight_client import Hindsight

from customer_support_agent.core.settings import Settings
from customer_support_agent.integrations.hindsight.banks import get_customer_bank_id
from customer_support_agent.integrations.hindsight.service import HindsightMemoryService


@pytest.fixture
async def hindsight_service():
    url = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")
    settings = Settings(
        hindsight_api_url=url,
        hindsight_timeout=120.0,
        hindsight_enabled=True,
    )
    service = HindsightMemoryService(settings=settings)
    try:
        yield service
    finally:
        await service.aclose()


@pytest.mark.anyio
async def test_failure_modes_invalid_url():
    """Verify that an invalid URL fails gracefully with a sanitized error."""
    bad_settings = Settings(
        hindsight_api_url="http://invalid-host-that-does-not-exist:8888",
        hindsight_timeout=2.0,
        hindsight_api_key="super-secret-key-999",
    )
    service = HindsightMemoryService(settings=bad_settings)
    try:
        # Health check must not crash
        health = await service.health_check()
        assert health["status"] == "unavailable"
        assert health["available"] is False
        assert "super-secret-key-999" not in str(health)

        # aretain on bad server raises sanitized RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            await service.aretain(bank_id="test_bank", content="sample content")
        assert "super-secret-key-999" not in str(exc_info.value)
    finally:
        await service.aclose()


@pytest.mark.anyio
async def test_failure_modes_empty_or_malformed_bank_id():
    """Verify input validation rejects empty and malformed bank identifiers."""
    service = HindsightMemoryService(client=MagicMock())
    with pytest.raises(ValueError, match="bank_id cannot be empty"):
        await service.aretain(bank_id="  ", content="content")

    with pytest.raises(ValueError, match="bank_id cannot be empty"):
        await service.arecall(bank_id="", query="query")

    with pytest.raises(ValueError, match="bank_id cannot be empty"):
        await service.areflect(bank_id="", query="query")


@pytest.mark.anyio
async def test_live_hindsight_retain_recall_reflect_and_isolation(hindsight_service):
    """
    End-to-end integration test against a live Hindsight instance:
    1. Retain synthetic support experience in Customer A's bank.
    2. Retain different support experience in Customer B's bank.
    3. Verify bank isolation: Customer B recall does NOT return Customer A's memory.
    4. Recall Customer A's experience and verify semantic keywords.
    5. Reflect on Customer A's bank and verify grounded advice.
    """
    health = await hindsight_service.health_check()
    if not health.get("available"):
        pytest.skip(f"Hindsight server is not reachable at {hindsight_service._settings.hindsight_api_url}. Skipping live integration test.")

    bank_a = get_customer_bank_id("live_test_customer_a")
    bank_b = get_customer_bank_id("live_test_customer_b")

    # Retain synthetic experience for Customer A
    content_a = (
        "Customer test-001 experienced API request timeouts in production while generating large reports. "
        "Clearing the cache did not resolve the problem. "
        "Increasing the API request timeout from 30 seconds to 90 seconds resolved the issue."
    )
    retain_a = await hindsight_service.aretain(
        bank_id=bank_a,
        content=content_a,
        context="API timeout incident report",
        tags=["timeout", "api", "resolved"],
    )
    assert retain_a["status"] == "ok"

    # Allow token bucket breathing room between sequential retains on free provider tier
    await asyncio.sleep(6)

    # Retain synthetic experience for Customer B
    content_b = (
        "Customer test-002 encountered an authentication 401 error. "
        "Rotating the client secret and re-authorizing resolved the authentication failure."
    )
    retain_b = await hindsight_service.aretain(
        bank_id=bank_b,
        content=content_b,
        context="Auth failure incident report",
        tags=["auth", "401", "resolved"],
    )
    assert retain_b["status"] == "ok"

    # Recall Customer A memory
    recall_a = await hindsight_service.arecall(
        bank_id=bank_a,
        query="What previously resolved the API timeout for generating large reports?",
    )
    assert recall_a["status"] == "ok"
    recalled_text_a = recall_a.get("text", "") + " " + " ".join(r.get("text", "") for r in recall_a.get("results", []))
    recalled_lower_a = recalled_text_a.lower()

    # Verify semantic concepts in recall
    assert any(term in recalled_lower_a for term in ["timeout", "90", "seconds", "report"])

    # Verify Bank Isolation: Customer B bank recall must NOT return Customer A timeout content
    recall_b = await hindsight_service.arecall(
        bank_id=bank_b,
        query="What previously resolved the API timeout?",
    )
    recalled_text_b = recall_b.get("text", "") + " " + " ".join(r.get("text", "") for r in recall_b.get("results", []))
    assert "90 seconds" not in recalled_text_b

    # Allow token bucket breathing room on free provider tier before multi-turn reflect
    await asyncio.sleep(12)

    # Reflect on Customer A's bank
    reflect_a = await hindsight_service.areflect(
        bank_id=bank_a,
        query="What should a support agent know if this customer reports another API timeout?",
    )
    assert reflect_a["status"] == "ok"
    response_lower = reflect_a.get("response", "").lower()
    assert any(term in response_lower for term in ["timeout", "cache", "90", "report", "increase"])
