"""Tests for demo observability, event logging, and connected system state projections."""

import pytest
from customer_support_agent.demo import DemoEvent, DemoLearningController, DemoState


class TestDemoObservability:
    """Test suite for DemoEvent logging and observable system projections."""

    def test_demo_event_dataclass(self):
        """Verify DemoEvent fields and serialization properties."""
        event = DemoEvent(
            timestamp="10:00:00",
            component="Hindsight",
            action="EXPERIENCE_STORED",
            status="warn",
            description="Stored failure pattern: avoid cache wipe",
        )
        assert event.timestamp == "10:00:00"
        assert event.component == "Hindsight"
        assert event.action == "EXPERIENCE_STORED"
        assert event.status == "warn"
        assert event.description == "Stored failure pattern: avoid cache wipe"

        as_dict = event.to_dict()
        assert as_dict["component"] == "Hindsight"
        assert as_dict["status"] == "warn"

    def test_initial_state_events(self):
        """Verify initial state and ticket #1 emit properly sequenced event traces."""
        controller = DemoLearningController()
        assert controller.state == DemoState.NEW_CUSTOMER

        events_init = controller.get_events()
        assert len(events_init) >= 1
        assert events_init[0]["action"] == "DEMO_INITIALIZED"

        controller.advance_to_ticket_1()
        assert controller.state == DemoState.FIRST_TICKET

        events = controller.get_events()
        assert len(events) >= 6
        components = [e["component"] for e in events]
        assert "SQLite" in components
        assert "Mem0" in components
        assert "RAG" in components
        assert "Hindsight" in components
        assert "Groq" in components

        # Verify initial hindsight event shows clean slate
        hindsight_events = [e for e in events if e["component"] == "Hindsight"]
        assert any("0 experiences found" in e["description"] for e in hindsight_events)

    def test_rejected_failure_events_and_deltas(self):
        """Verify human rejection records event traces and state delta."""
        controller = DemoLearningController()
        controller.advance_to_ticket_1()
        controller.reject_ticket_1(reason="Do not clear cache, it causes timeouts")
        assert controller.state == DemoState.REJECTED_FAILURE

        events = controller.get_events()
        # Verify sqlite draft discard
        assert any(e["component"] == "SQLite" and "DISCARDED" in e["action"] for e in events)
        # Verify hindsight failure learning
        assert any(e["component"] == "Hindsight" and "FAILURE_RECORDED" in e["action"] for e in events)

        # Check deltas
        deltas = controller.get_deltas()
        assert "0 → 1 experience" in deltas["hindsight"]
        assert "DISCARDED" in deltas["sqlite"]
        assert "NOT stored as fact" in deltas["mem0"]

    def test_second_ticket_recall_events(self):
        """Verify second ticket recalls prior failure and emits recall event."""
        controller = DemoLearningController()
        controller.advance_to_ticket_1()
        controller.reject_ticket_1(reason="Do not clear cache")
        controller.advance_to_ticket_2()
        assert controller.state == DemoState.SECOND_TICKET

        events = controller.get_events()
        assert any(e["component"] == "Hindsight" and "FAILURE_RECALLED" in e["action"] for e in events)

        deltas = controller.get_deltas()
        assert "1 failure recalled" in deltas["hindsight"]

    def test_accepted_success_events_and_deltas(self):
        """Verify ticket acceptance writes to Hindsight, Mem0, and SQLite."""
        controller = DemoLearningController()
        controller.advance_to_ticket_1()
        controller.reject_ticket_1()
        controller.advance_to_ticket_2()
        controller.accept_ticket_2()
        assert controller.state == DemoState.ACCEPTED_SUCCESS

        events = controller.get_events()
        assert any(e["component"] == "SQLite" and "DRAFT_ACCEPTED" in e["action"] for e in events)
        assert any(e["component"] == "SQLite" and "TICKET_RESOLVED" in e["action"] for e in events)
        assert any(e["component"] == "Hindsight" and "SUCCESS_RECORDED" in e["action"] for e in events)
        assert any(e["component"] == "Mem0" and "FACT_SAVED" in e["action"] for e in events)

        deltas = controller.get_deltas()
        assert "1 → 2 experiences" in deltas["hindsight"]
        assert "1 → 2 facts" in deltas["mem0"]
        assert "RESOLVED" in deltas["sqlite"]

    def test_third_ticket_full_recall_events(self):
        """Verify third ticket executes full experiential recall."""
        controller = DemoLearningController()
        controller.advance_to_ticket_1()
        controller.reject_ticket_1()
        controller.advance_to_ticket_2()
        controller.accept_ticket_2()
        controller.advance_to_ticket_3()
        assert controller.state == DemoState.THIRD_TICKET

        events = controller.get_events()
        assert any("FULL_RECALL" in e["action"] for e in events)

        deltas = controller.get_deltas()
        assert "4 experiences recalled" in deltas["hindsight"]

    def test_reset_clears_events_to_initial(self):
        """Verify reset restores the event trace to clean state."""
        controller = DemoLearningController()
        controller.advance_to_ticket_1()
        controller.reject_ticket_1()
        assert controller.state == DemoState.REJECTED_FAILURE

        controller.reset()
        assert controller.state == DemoState.NEW_CUSTOMER
        events = controller.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "DEMO_RESET"

    def test_get_system_state_projections(self):
        """Verify projected database and memory tables reflect current scenario state."""
        controller = DemoLearningController()
        state_0 = controller.get_system_state()
        assert "sqlite" in state_0
        assert "mem0" in state_0
        assert "rag" in state_0
        assert "hindsight" in state_0
        assert len(state_0["hindsight"]["experiences"]) == 0

        # Advance to ticket 1 and reject
        controller.advance_to_ticket_1()
        controller.reject_ticket_1()
        state_rej = controller.get_system_state()
        assert len(state_rej["hindsight"]["experiences"]) == 1
        assert state_rej["hindsight"]["experiences"][0]["category"] == "FAILURE"
        assert state_rej["sqlite"]["drafts"][0]["status"] == "discarded"

        # Advance to ticket 2 and accept
        controller.advance_to_ticket_2()
        controller.accept_ticket_2()
        state_acc = controller.get_system_state()
        assert len(state_acc["hindsight"]["experiences"]) == 2
        assert len(state_acc["mem0"]["facts"]) == 2
        assert state_acc["sqlite"]["tickets"][1]["status"] == "resolved"
