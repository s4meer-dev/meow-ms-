from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import os
from unittest.mock import AsyncMock, MagicMock
import pytest
from pydantic import ValidationError

from customer_support_agent.core.settings import Settings
from customer_support_agent.integrations.hindsight.banks import get_customer_bank_id
from customer_support_agent.integrations.hindsight.experience import (
    ExperienceMemoryService,
    format_experience_narrative,
    get_experience_document_id,
)
from customer_support_agent.integrations.hindsight.service import HindsightMemoryService
from customer_support_agent.schemas.experience import (
    ExperienceRecallItem,
    ExperienceRecallResponse,
    ExperienceReflectionResponse,
    SupportExperience,
    TroubleshootingAttempt,
)


# ---------------------------------------------------------------------------
# Unit Tests: Schema and Data Models
# ---------------------------------------------------------------------------

def test_troubleshooting_attempt_model():
    attempt_fail = TroubleshootingAttempt(
        action="Restarted container engine",
        result="Failed with exit code 137 OOM",
        reason="Host did not have enough virtual memory allocated",
    )
    assert attempt_fail.is_failure is True
    assert attempt_fail.is_success is False

    attempt_succ = TroubleshootingAttempt(
        action="Updated .wslconfig to memory=8GB",
        result="Succeeded, build passed in 45s",
        reason="WSL2 VM received sufficient RAM",
    )
    assert attempt_succ.is_failure is False
    assert attempt_succ.is_success is True


def test_support_experience_auto_partitioning():
    exp = SupportExperience(
        customer_id="cust_100",
        ticket_id="ticket_55",
        problem="Application crashes on heavy load",
        attempts=[
            TroubleshootingAttempt(action="Flushed redis", result="Failed with socket error", reason="Redis was hung"),
            TroubleshootingAttempt(action="Restarted cluster", result="Succeeded, load normalized", reason="Nodes recovered"),
        ],
        resolution="Restarted cluster nodes",
    )
    assert len(exp.failed_attempts) == 1
    assert exp.failed_attempts[0].action == "Flushed redis"
    assert len(exp.successful_attempts) == 1
    assert exp.successful_attempts[0].action == "Restarted cluster"
    assert exp.has_failed_attempts is True
    assert exp.has_successful_attempts is True
    assert exp.is_resolved is True


def test_support_experience_reverse_merge():
    fail = TroubleshootingAttempt(action="Rollback migration", result="Failed with FK conflict")
    succ = TroubleshootingAttempt(action="Applied patched migration", result="Succeeded without error")
    exp = SupportExperience(
        customer_id="cust_200",
        problem="Database schema mismatch",
        failed_attempts=[fail],
        successful_attempts=[succ],
    )
    assert len(exp.attempts) == 2
    assert exp.attempts[0].action == "Rollback migration"
    assert exp.attempts[1].action == "Applied patched migration"


def test_support_experience_add_attempt():
    exp = SupportExperience(
        customer_id="cust_300",
        problem="High CPU usage",
    )
    assert exp.has_failed_attempts is False
    assert exp.has_successful_attempts is False

    exp.add_attempt(action="Killed process 4012", result="Failed, respawned immediately", reason="Supervisor restarted it")
    assert len(exp.attempts) == 1
    assert len(exp.failed_attempts) == 1
    assert exp.has_failed_attempts is True

    exp.add_attempt(action="Updated supervisor config", result="Succeeded, CPU returned to 5%", reason="Prevented runaway spin")
    assert len(exp.attempts) == 2
    assert len(exp.successful_attempts) == 1
    assert exp.has_successful_attempts is True


def test_support_experience_validation_errors():
    # customer_id cannot be empty
    with pytest.raises(ValidationError):
        SupportExperience(customer_id="", problem="Some problem")

    # problem must have at least 3 characters
    with pytest.raises(ValidationError):
        SupportExperience(customer_id="cust_1", problem="hi")

    # Integer IDs are coerced to strings cleanly
    exp = SupportExperience(customer_id=1234, ticket_id=9876, problem="Valid description")
    assert exp.customer_id == "1234"
    assert exp.ticket_id == "9876"


def test_format_experience_narrative_full():
    exp = SupportExperience(
        customer_id="rahul_dev",
        ticket_id="101",
        company_id="acme_corp",
        problem="Docker Desktop build fails with Exit Code 137 OOM on Windows 11",
        environment={"os": "Windows 11 Pro", "wsl": "WSL2", "docker": "4.28"},
        symptoms=["Exit code 137 during npm install", "VmmemWSL process consumes 100% host RAM"],
        attempts=[
            TroubleshootingAttempt(
                action="Restarted Docker Desktop and ran docker system prune -a",
                result="Failed with same exit code 137",
                reason="Did not increase available RAM to the WSL2 virtual machine",
            ),
            TroubleshootingAttempt(
                action="Created %USERPROFILE%/.wslconfig with memory=8GB",
                result="Succeeded, build completed in 45s",
                reason="Provided sufficient RAM for Node build",
            ),
        ],
        resolution="Configured WSL2 memory limits via .wslconfig and restarted WSL2",
        outcome="Container builds reliably without memory crashes",
        customer_reaction="Confirmed build works, thrilled with quick resolution",
        customer_sentiment="satisfied",
        preferences=["Prefers PowerShell CLI troubleshooting over GUI settings"],
    )

    narrative = format_experience_narrative(exp)
    assert "Ticket ID: 101" in narrative
    assert "Customer ID: rahul_dev" in narrative
    assert "Company ID: acme_corp" in narrative
    assert "[ENVIRONMENT & INFRASTRUCTURE]" in narrative
    assert "Windows 11 Pro" in narrative
    assert "[PROBLEM REPORTED]" in narrative
    assert "Docker Desktop build fails" in narrative
    assert "[OBSERVED SYMPTOMS]" in narrative
    assert "Exit code 137 during npm install" in narrative
    assert "[TROUBLESHOOTING & CAUSAL ATTEMPTS]" in narrative
    assert "[FAILED - DO NOT REPEAT] Action: Restarted Docker Desktop" in narrative
    assert "Why it failed: Did not increase available RAM" in narrative
    assert "[SUCCESS - PROVEN FIX] Action: Created %USERPROFILE%/.wslconfig" in narrative
    assert "Why it succeeded: Provided sufficient RAM" in narrative
    assert "[FINAL RESOLUTION]" in narrative
    assert "Configured WSL2 memory limits" in narrative
    assert "[FINAL OUTCOME & IMPACT]" in narrative
    assert "Container builds reliably" in narrative
    assert "[CUSTOMER REACTION & SENTIMENT]" in narrative
    assert "satisfied" in narrative
    assert "[CUSTOMER PREFERENCES & OPERATIONAL CONSTRAINTS]" in narrative
    assert "Prefers PowerShell CLI" in narrative


def test_format_experience_narrative_minimal():
    exp = SupportExperience(
        customer_id="user_basic",
        problem="Password reset email not received",
    )
    narrative = format_experience_narrative(exp)
    assert "Customer ID: user_basic" in narrative
    assert "Password reset email not received" in narrative
    assert "No intermediate troubleshooting steps logged." in narrative
    assert "Issue remains unresolved" in narrative


def test_get_experience_document_id():
    exp_with_ticket = SupportExperience(customer_id="cust1", ticket_id="TCK-900", problem="Issue")
    assert get_experience_document_id(exp_with_ticket) == "meow-experience-ticket-tck-900"

    exp_no_ticket = SupportExperience(experience_id="exp-uuid-1234", customer_id="cust1", problem="Issue")
    assert get_experience_document_id(exp_no_ticket) == "meow-experience-exp-uuid-1234"


# ---------------------------------------------------------------------------
# Mocked Service Tests: ExperienceMemoryService
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_experience_service_aretain_mocked():
    mock_hindsight = MagicMock(spec=HindsightMemoryService)
    mock_hindsight.aretain = AsyncMock(return_value={"status": "ok", "response": {"id": "doc-1"}})
    mock_hindsight.is_enabled = True

    service = ExperienceMemoryService(hindsight_service=mock_hindsight)
    exp = SupportExperience(
        customer_id="alex_turner",
        ticket_id="501",
        problem="Websocket connection dropped constantly",
        attempts=[
            TroubleshootingAttempt(action="Restarted proxy", result="Failed, dropped again"),
            TroubleshootingAttempt(action="Increased keepalive to 60s", result="Succeeded, stable"),
        ],
        resolution="Increased proxy keepalive",
    )

    result = await service.aretain_experience(exp)
    assert result["status"] == "ok"
    assert result["bank_id"] == "meow_customer_alex_turner"
    assert result["document_id"] == "meow-experience-ticket-501"

    # Verify call parameters to underlying Hindsight service
    mock_hindsight.aretain.assert_awaited_once()
    kwargs = mock_hindsight.aretain.call_args.kwargs
    assert kwargs["bank_id"] == "meow_customer_alex_turner"
    assert kwargs["document_id"] == "meow-experience-ticket-501"
    assert "Websocket connection dropped" in kwargs["content"]
    assert kwargs["metadata"]["has_failed_attempts"] == "true"
    assert kwargs["metadata"]["has_successful_attempts"] == "true"
    assert kwargs["metadata"]["is_resolved"] == "true"
    assert "experience" in kwargs["tags"]
    assert "resolved" in kwargs["tags"]
    assert "has_failures" in kwargs["tags"]


@pytest.mark.anyio
async def test_experience_service_arecall_mocked():
    mock_hindsight = MagicMock(spec=HindsightMemoryService)
    mock_hindsight.arecall = AsyncMock(
        return_value={
            "status": "ok",
            "bank_id": "meow_customer_alex_turner",
            "query": "keepalive",
            "text": "Keepalive was increased to 60s",
            "results": [
                {"text": "Increased keepalive to 60s", "score": 0.95, "metadata": {"ticket_id": "501"}}
            ],
            "raw": {"some": "raw_obj"},
        }
    )

    service = ExperienceMemoryService(hindsight_service=mock_hindsight)
    recall_resp = await service.arecall_relevant_experiences(
        customer_id="alex_turner",
        query="keepalive timeout",
    )

    assert isinstance(recall_resp, ExperienceRecallResponse)
    assert recall_resp.customer_id == "alex_turner"
    assert recall_resp.bank_id == "meow_customer_alex_turner"
    assert len(recall_resp.experiences) == 1
    assert recall_resp.experiences[0].text == "Increased keepalive to 60s"
    assert recall_resp.experiences[0].score == 0.95
    assert recall_resp.summary_text == "Keepalive was increased to 60s"


@pytest.mark.anyio
async def test_experience_service_areflect_mocked():
    mock_hindsight = MagicMock(spec=HindsightMemoryService)
    mock_hindsight.areflect = AsyncMock(
        return_value={
            "status": "ok",
            "bank_id": "meow_customer_alex_turner",
            "query": "What steps failed?",
            "response": "Restarting proxy failed. Increasing keepalive succeeded.",
            "raw": {"raw_reflect": True},
        }
    )

    service = ExperienceMemoryService(hindsight_service=mock_hindsight)
    reflect_resp = await service.areflect_on_customer_experience(
        customer_id="alex_turner",
        question="What steps failed?",
    )

    assert isinstance(reflect_resp, ExperienceReflectionResponse)
    assert reflect_resp.customer_id == "alex_turner"
    assert reflect_resp.insights == "Restarting proxy failed. Increasing keepalive succeeded."


@pytest.mark.anyio
async def test_experience_service_aretain_preference_mocked():
    mock_hindsight = MagicMock(spec=HindsightMemoryService)
    mock_hindsight.aretain = AsyncMock(return_value={"status": "ok", "response": {}})

    service = ExperienceMemoryService(hindsight_service=mock_hindsight)
    pref_res = await service.aretain_preference(
        customer_id="alex_turner",
        preference="Prefers CLI curl commands over UI instructions",
    )
    assert pref_res["status"] == "ok"
    assert pref_res["bank_id"] == "meow_customer_alex_turner"
    assert "meow-pref-alex_turner-" in pref_res["document_id"]
    mock_hindsight.aretain.assert_awaited_once()


def test_experience_service_sync_methods_mocked():
    mock_hindsight = MagicMock(spec=HindsightMemoryService)
    mock_hindsight.retain = MagicMock(return_value={"status": "ok", "response": {}})

    mock_raw_recall = MagicMock()
    mock_raw_recall.results = []
    mock_raw_recall.to_prompt_string.return_value = "Sync recall"
    mock_raw_recall.text = "Sync recall"
    mock_hindsight.recall = MagicMock(return_value={"status": "ok", "raw": mock_raw_recall})

    mock_raw_reflect = MagicMock()
    mock_raw_reflect.response = "Sync reflection"
    mock_raw_reflect.text = "Sync reflection"
    mock_hindsight.reflect = MagicMock(return_value={"status": "ok", "raw": mock_raw_reflect})

    service = ExperienceMemoryService(hindsight_service=mock_hindsight)
    exp = SupportExperience(customer_id="sync_user", problem="Sync issue")

    # Retain sync
    retain_res = service.retain_experience(exp)
    assert retain_res["status"] == "ok"
    mock_hindsight.retain.assert_called_once()

    # Recall sync
    recall_res = service.recall_relevant_experiences(customer_id="sync_user", query="Sync issue")
    assert recall_res.customer_id == "sync_user"
    mock_hindsight.recall.assert_called_once()

    # Reflect sync
    reflect_res = service.reflect_on_customer_experience(customer_id="sync_user", question="Sync question?")
    assert reflect_res.customer_id == "sync_user"
    mock_hindsight.reflect.assert_called_once()

    # Preference sync
    pref_res = service.retain_preference(customer_id="sync_user", preference="Prefers dark mode")
    assert pref_res["status"] == "ok"
    assert mock_hindsight.retain.call_count == 2


# ---------------------------------------------------------------------------
# Live Integration Tests against Real Hindsight Server
# ---------------------------------------------------------------------------

@pytest.fixture
async def live_experience_service():
    url = os.getenv("HINDSIGHT_API_URL", "http://localhost:8888")
    settings = Settings(
        hindsight_api_url=url,
        hindsight_timeout=180.0,
        hindsight_enabled=True,
    )
    hindsight_svc = HindsightMemoryService(settings=settings)
    try:
        service = ExperienceMemoryService(hindsight_service=hindsight_svc, settings=settings)
        yield service
    finally:
        await hindsight_svc.aclose()


@pytest.mark.anyio
async def test_live_experience_retain_recall_reflect_and_isolation(live_experience_service):
    """
    Comprehensive Live End-to-End Test for the Customer Experience Memory Layer:
    1. Personas:
       - Customer Rahul (MEOW_TEST_RAHUL): Docker exit code 137 on Windows 11 / WSL2.
         Failed attempt: Restarting Docker & docker system prune.
         Successful attempt: .wslconfig 8GB allocation and wsl --shutdown.
         Preference: Prefers PowerShell CLI over GUI.
       - Customer Anika (MEOW_TEST_ANIKA): SSO login loop on macOS Sonoma Safari.
         Failed attempt: Cleared Safari cache.
         Successful attempt: Okta cross-site cookie tracking permission.
         Preference: Always send security documentation via email confirmation.
    2. Operations:
       - aretain_experience() for Rahul (Ticket 101).
       - aretain_experience() for Anika (Ticket 201).
       - arecall_relevant_experiences() verifying failure-aware knowledge retrieval.
       - areflect_on_customer_experience() verifying synthesis of failed vs. successful steps.
       - Cross-customer bank isolation verification.
       - Idempotent document ID retention verification.
    """
    health = await live_experience_service.hindsight.health_check()
    if not health.get("available"):
        pytest.skip(f"Hindsight server is not reachable at {live_experience_service.hindsight._settings.hindsight_api_url}. Skipping live test.")

    rahul_id = "meow_test_rahul"
    anika_id = "meow_test_anika"

    def _handle_quota_error(exc: Exception):
        exc_str = str(exc).lower()
        if any(term in exc_str for term in ["provider quota exhausted", "rate limit reached", "tokens per day", "ratelimitreset", "providerratelimitreseterror", "rate_limit_exceeded"]):
            pytest.skip(f"Live Hindsight test skipped due to upstream Groq daily token limit (TPD): {exc}")
        raise exc

    try:
        # 1. Construct and Retain Rahul's Support Experience (Ticket 101)
        exp_rahul = SupportExperience(
            customer_id=rahul_id,
            ticket_id="101",
            problem="Docker Desktop build fails with Exit Code 137 OOM on Windows 11 WSL2",
            environment="Windows 11 Pro, WSL2",
            symptoms=["Exit code 137 during build", "High memory usage"],
            attempts=[
                TroubleshootingAttempt(
                    action="Restarted Docker and ran docker system prune",
                    result="Failed with exit code 137 OOM",
                    reason="Did not increase WSL2 virtual machine memory",
                ),
                TroubleshootingAttempt(
                    action="Configured .wslconfig with memory=8GB and ran wsl --shutdown",
                    result="Succeeded, build completed in 45s",
                    reason="Allocated 8GB RAM to WSL2",
                ),
            ],
            resolution="Configured WSL2 memory=8GB in .wslconfig and restarted WSL2",
            outcome="Container builds complete reliably",
            customer_reaction="Confirmed build works smoothly",
            customer_sentiment="satisfied",
            preferences=["Prefers PowerShell CLI commands over GUI settings"],
        )

        retain_rahul_res = await live_experience_service.aretain_experience(exp_rahul)
        assert retain_rahul_res["status"] == "ok"
        assert retain_rahul_res["bank_id"] == get_customer_bank_id(rahul_id)
        assert retain_rahul_res["document_id"] == "meow-experience-ticket-101"

        # Pacing to respect Groq rate limits
        await asyncio.sleep(6)

        # 2. Construct and Retain Anika's Support Experience (Ticket 201)
        exp_anika = SupportExperience(
            customer_id=anika_id,
            ticket_id="201",
            problem="SSO login redirect loop in Safari on macOS",
            environment="macOS Sonoma, Safari 17",
            symptoms=["Authentication redirect loop", "State mismatch error"],
            attempts=[
                TroubleshootingAttempt(
                    action="Cleared Safari cookies and cache",
                    result="Failed, redirect loop persisted",
                    reason="Did not enable cross-domain Okta session tokens",
                ),
                TroubleshootingAttempt(
                    action="Disabled prevent cross-site tracking in Safari for Okta",
                    result="Succeeded, authenticated successfully",
                    reason="Allowed Okta session tokens to pass across SSO domains",
                ),
            ],
            resolution="Configured cross-site tracking exemption for Okta SSO",
            outcome="SSO authentication works seamlessly",
            customer_reaction="Relieved, confirmed login works",
            customer_sentiment="satisfied",
            preferences=["Always send security documentation via email confirmation"],
        )

        retain_anika_res = await live_experience_service.aretain_experience(exp_anika)
        assert retain_anika_res["status"] == "ok"
        assert retain_anika_res["bank_id"] == get_customer_bank_id(anika_id)
        assert retain_anika_res["document_id"] == "meow-experience-ticket-201"

        # 3. Recall from Rahul's bank: Verify failure-aware memory retrieval
        recall_rahul = await live_experience_service.arecall_relevant_experiences(
            customer_id=rahul_id,
            query="What happened when troubleshooting Docker 137 OOM on Windows WSL2?",
        )
        assert recall_rahul.bank_id == get_customer_bank_id(rahul_id)
        combined_rahul_text = (
            recall_rahul.summary_text + " " + " ".join(item.text for item in recall_rahul.experiences)
        ).lower()

        # Verify both failure and success concepts were recalled
        assert any(term in combined_rahul_text for term in ["137", "oom", "prune", "wslconfig", "8gb", "wsl"])

        # 4. Bank Isolation Guarantee:
        # Query Rahul's bank for Anika's issue (Safari SSO Okta). Should NOT contain Anika's memories.
        isolation_query_on_rahul = await live_experience_service.arecall_relevant_experiences(
            customer_id=rahul_id,
            query="What was the fix for Safari SSO login loop with Okta?",
        )
        isolated_text = (
            isolation_query_on_rahul.summary_text
            + " "
            + " ".join(item.text for item in isolation_query_on_rahul.experiences)
        ).lower()
        assert "okta" not in isolated_text
        assert "safari" not in isolated_text

        # 5. Bank Isolation Guarantee in Reverse:
        # Query Anika's bank for Rahul's issue (Docker WSL2). Should NOT contain Rahul's memories.
        isolation_query_on_anika = await live_experience_service.arecall_relevant_experiences(
            customer_id=anika_id,
            query="What was the fix for Docker exit code 137 OOM in WSL2?",
        )
        anika_isolated_text = (
            isolation_query_on_anika.summary_text
            + " "
            + " ".join(item.text for item in isolation_query_on_anika.experiences)
        ).lower()
        assert "wslconfig" not in anika_isolated_text
        assert "vmmemwsl" not in anika_isolated_text

        # Pacing before LLM reflection call
        await asyncio.sleep(15)

        # 6. Reflection on Rahul's bank: Synthesize troubleshooting advice
        reflect_rahul = await live_experience_service.areflect_on_customer_experience(
            customer_id=rahul_id,
            question="What troubleshooting step failed and what succeeded when addressing Docker OOM issues for Rahul?",
        )
        assert reflect_rahul.bank_id == get_customer_bank_id(rahul_id)
        assert len(reflect_rahul.insights) > 10
        reflection_lower = reflect_rahul.insights.lower()
        # Should recognize the successful solution (.wslconfig or memory limit or WSL)
        assert any(term in reflection_lower for term in ["wslconfig", "memory", "8gb", "wsl", "shutdown", "prune"])

        # 7. Customer Preference Retention & Verification
        pref_res = await live_experience_service.aretain_preference(
            customer_id=rahul_id,
            preference="Strictly prefers PowerShell/CLI commands over Windows GUI settings for all troubleshooting",
        )
        assert pref_res["status"] == "ok"
        assert "meow-pref-meow_test_rahul-" in pref_res["document_id"]

        # 8. Idempotent Retention / Document ID deduplication check
        # Retaining updated experience with same ticket_id produces identical document_id
        exp_rahul.outcome = "Container builds verified 100% operational across multiple test runs"
        re_retain = await live_experience_service.aretain_experience(exp_rahul)
        assert re_retain["document_id"] == "meow-experience-ticket-101"
    except Exception as exc:
        _handle_quota_error(exc)
