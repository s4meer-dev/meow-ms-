"""MEOW: Automated End-to-End Demo Lifecycle Verification Tool.

Simulates the complete 3-ticket experiential learning demonstration:
1. Novel issue intake (Ticket #1) -> Clean slate
2. Human rejection -> Failure experience retained
3. Recurring issue (Ticket #2) -> Failure recalled & avoided
4. Human acceptance -> Success experience & Mem0 fact stored
5. Multi-memory synthesis (Ticket #3) -> Fix + Failure + Preference + Pattern recalled
"""

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from customer_support_agent.demo import DemoLearningController, DemoState


def verify_scenario():
    print("=" * 60)
    print("MEOW: Connected Observable Demo Lifecycle Verification")
    print("=" * 60)

    controller = DemoLearningController()
    assert controller.state == DemoState.NEW_CUSTOMER, "Initial state must be NEW_CUSTOMER"
    print("[PASS] [Init] Scenario initialized with clean slate for Alex Rivera")

    # Step 1: Advance to Ticket 1
    controller.advance_to_ticket_1()
    assert controller.state == DemoState.FIRST_TICKET
    events = controller.get_events()
    assert any(e["component"] == "Hindsight" and "0 experiences found" in e["description"] for e in events)
    deltas = controller.get_deltas()
    assert "Clean slate" in deltas["hindsight"]
    print("[PASS] [Stage 1] Ticket #1 intake: 0 past experiences verified")

    # Step 2: Reject Ticket 1 Draft
    controller.reject_ticket_1(reason="Already cleared cache without effect")
    assert controller.state == DemoState.REJECTED_FAILURE
    events = controller.get_events()
    assert any(e["component"] == "Hindsight" and "FAILURE_RECORDED" in e["action"] for e in events)
    assert any(e["component"] == "SQLite" and "DISCARDED" in e["action"] for e in events)
    deltas = controller.get_deltas()
    assert "0 → 1 experience" in deltas["hindsight"]
    assert "NOT stored as fact" in deltas["mem0"]
    print("[PASS] [Stage 2] Rejection captured: Failure experience committed to Hindsight; Mem0 bypassed")

    # Step 3: Advance to Ticket 2
    controller.advance_to_ticket_2()
    assert controller.state == DemoState.SECOND_TICKET
    events = controller.get_events()
    assert any(e["component"] == "Hindsight" and "FAILURE_RECALLED" in e["action"] for e in events)
    deltas = controller.get_deltas()
    assert "1 failure recalled" in deltas["hindsight"]
    print("[PASS] [Stage 3] Ticket #2 intake: Failure recalled; avoided repeating cache wipe mistake")

    # Step 4: Accept Ticket 2 Draft
    controller.accept_ticket_2()
    assert controller.state == DemoState.ACCEPTED_SUCCESS
    events = controller.get_events()
    assert any(e["component"] == "Hindsight" and "SUCCESS_RECORDED" in e["action"] for e in events)
    assert any(e["component"] == "Mem0" and "FACT_SAVED" in e["action"] for e in events)
    assert any(e["component"] == "SQLite" and "TICKET_RESOLVED" in e["action"] for e in events)
    deltas = controller.get_deltas()
    assert "1 → 2 experiences" in deltas["hindsight"]
    assert "1 → 2 facts" in deltas["mem0"]
    print("[PASS] [Stage 4] Acceptance captured: Proven fix committed to Hindsight & Mem0; Ticket #1002 resolved")

    # Step 5: Advance to Ticket 3
    controller.advance_to_ticket_3()
    assert controller.state == DemoState.THIRD_TICKET
    events = controller.get_events()
    assert any(e["component"] == "Hindsight" and "FULL_RECALL" in e["action"] for e in events)
    deltas = controller.get_deltas()
    assert "4 experiences recalled" in deltas["hindsight"]

    sys_state = controller.get_system_state()
    assert len(sys_state["hindsight"]["experiences"]) == 4
    categories = [exp["category"] for exp in sys_state["hindsight"]["experiences"]]
    assert "SUCCESS" in categories
    assert "FAILURE" in categories
    assert "PREFERENCE" in categories
    assert "PATTERN" in categories
    print("[PASS] [Stage 5] Ticket #3 synthesis: Recalled all 4 experience types (Success, Failure, Preference, Pattern)")

    # Step 6: Reset
    controller.reset()
    assert controller.state == DemoState.NEW_CUSTOMER
    assert len(controller.get_system_state()["hindsight"]["experiences"]) == 0
    print("[PASS] [Stage 6] Scenario reset: All demo state and memory banks restored to clean baseline")

    print("\n" + "=" * 60)
    print("ALL DEMO VERIFICATION CHECKS PASSED (100% OPERATIONAL)")
    print("=" * 60)


if __name__ == "__main__":
    verify_scenario()
