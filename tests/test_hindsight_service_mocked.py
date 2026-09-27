from unittest.mock import AsyncMock, MagicMock
import pytest

from customer_support_agent.core.settings import Settings
from customer_support_agent.integrations.hindsight.service import HindsightMemoryService


@pytest.fixture
def test_settings():
    return Settings(
        hindsight_api_url="http://localhost:8888",
        hindsight_api_key="secret-hindsight-token-123",
        groq_api_key="secret-groq-key-456",
        hindsight_enabled=True,
    )


@pytest.mark.anyio
async def test_health_check_success(test_settings):
    mock_client = MagicMock()
    mock_version = MagicMock()
    mock_version.version = "0.10.1"
    mock_client.aget_version = AsyncMock(return_value=mock_version)

    service = HindsightMemoryService(settings=test_settings, client=mock_client)
    result = await service.health_check()

    assert result["status"] == "ok"
    assert result["available"] is True
    assert result["version"] == "0.10.1"


@pytest.mark.anyio
async def test_health_check_unavailable_does_not_crash(test_settings):
    mock_client = MagicMock()
    mock_client.aget_version = AsyncMock(
        side_effect=ConnectionError(
            "Failed to connect to http://localhost:8888 with key secret-hindsight-token-123"
        )
    )

    service = HindsightMemoryService(settings=test_settings, client=mock_client)
    result = await service.health_check()

    assert result["status"] == "unavailable"
    assert result["available"] is False
    assert "error" in result
    # Secret must be redacted
    assert "secret-hindsight-token-123" not in result["error"]
    assert "[REDACTED_HINDSIGHT_KEY]" in result["error"]


@pytest.mark.anyio
async def test_aretain_success(test_settings):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.id = "mem-1"
    mock_client.aretain = AsyncMock(return_value=mock_response)

    service = HindsightMemoryService(settings=test_settings, client=mock_client)
    result = await service.aretain(
        bank_id="meow_customer_test",
        content="Customer increased timeout to 90s to resolve API issue.",
        context="API timeout incident",
        tags=["timeout", "resolved"],
    )

    assert result["status"] == "ok"
    assert result["bank_id"] == "meow_customer_test"
    mock_client.aretain.assert_awaited_once_with(
        bank_id="meow_customer_test",
        content="Customer increased timeout to 90s to resolve API issue.",
        context="API timeout incident",
        metadata=None,
        tags=["timeout", "resolved"],
        document_id=None,
    )


@pytest.mark.anyio
async def test_arecall_success(test_settings):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_item = MagicMock()
    mock_item.text = "Increased timeout to 90s."
    mock_item.score = 0.95
    mock_item.metadata = {"tag": "resolved"}
    mock_response.results = [mock_item]
    mock_response.to_prompt_string.return_value = "Formatted prompt context"
    mock_client.arecall = AsyncMock(return_value=mock_response)

    service = HindsightMemoryService(settings=test_settings, client=mock_client)
    result = await service.arecall(
        bank_id="meow_customer_test",
        query="What resolved the API timeout?",
    )

    assert result["status"] == "ok"
    assert result["bank_id"] == "meow_customer_test"
    assert result["text"] == "Formatted prompt context"
    assert len(result["results"]) == 1
    assert result["results"][0]["text"] == "Increased timeout to 90s."


@pytest.mark.anyio
async def test_areflect_success(test_settings):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.response = "Customer previously experienced API timeouts; clearing cache failed, increasing timeout worked."
    mock_client.areflect = AsyncMock(return_value=mock_response)

    service = HindsightMemoryService(settings=test_settings, client=mock_client)
    result = await service.areflect(
        bank_id="meow_customer_test",
        query="What should support know about API timeouts for this customer?",
    )

    assert result["status"] == "ok"
    assert result["bank_id"] == "meow_customer_test"
    assert "clearing cache failed" in result["response"]


@pytest.mark.anyio
async def test_validation_errors(test_settings):
    service = HindsightMemoryService(settings=test_settings, client=MagicMock())

    with pytest.raises(ValueError, match="bank_id cannot be empty"):
        await service.aretain(bank_id="", content="sample")

    with pytest.raises(ValueError, match="content cannot be empty"):
        await service.aretain(bank_id="test_bank", content="")

    with pytest.raises(ValueError, match="bank_id cannot be empty"):
        await service.arecall(bank_id="", query="what happened?")

    with pytest.raises(ValueError, match="query cannot be empty"):
        await service.arecall(bank_id="test_bank", query="")

    with pytest.raises(ValueError, match="bank_id cannot be empty"):
        await service.areflect(bank_id="", query="what to do?")


def test_sync_wrappers(test_settings):
    mock_client = MagicMock()
    mock_client.retain.return_value = {"id": "sync-1"}
    mock_client.recall.return_value = {"results": []}
    mock_client.reflect.return_value = {"response": "ok"}

    service = HindsightMemoryService(settings=test_settings, client=mock_client)

    ret = service.retain(bank_id="bank1", content="content1")
    assert ret["status"] == "ok"

    rec = service.recall(bank_id="bank1", query="query1")
    assert rec["status"] == "ok"

    ref = service.reflect(bank_id="bank1", query="query1")
    assert ref["status"] == "ok"
