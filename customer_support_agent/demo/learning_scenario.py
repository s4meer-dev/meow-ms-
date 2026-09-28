"""
MEOW — Phase 7: End-to-End Hindsight Learning Demo Controller
Deterministic, reproducible closed-loop learning scenario state machine.

Flow:
NEW_CUSTOMER
  ↓
FIRST_TICKET (Clear cache proposed, 0 prior experience)
  ↓
REJECTED_FAILURE (Human rejects "Already tried" -> FAILURE retained)
  ↓
SECOND_TICKET (Hindsight recalls FAILURE -> AI avoids cache clearing, suggests 90s timeout)
  ↓
ACCEPTED_SUCCESS (Human accepts -> SUCCESS retained)
  ↓
THIRD_TICKET (Hindsight recalls SUCCESS + FAILURE + PREFERENCE + PATTERN)
  ↓
LEARNED_STATE
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class DemoEvent:
    timestamp: str
    component: str  # "SQLite", "Mem0", "RAG", "Hindsight", "Groq", "System"
    action: str
    status: str     # "ok", "info", "warn", "error"
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "component": self.component,
            "action": self.action,
            "status": self.status,
            "description": self.description,
        }


class DemoState(str, Enum):
    NEW_CUSTOMER = "NEW_CUSTOMER"
    FIRST_TICKET = "FIRST_TICKET"
    REJECTED_FAILURE = "REJECTED_FAILURE"
    SECOND_TICKET = "SECOND_TICKET"
    ACCEPTED_SUCCESS = "ACCEPTED_SUCCESS"
    THIRD_TICKET = "THIRD_TICKET"
    LEARNED_STATE = "LEARNED_STATE"


DEMO_CUSTOMER = {
    "id": 9999,
    "email": "alex.rivera@demo.meow",
    "name": "Alex Rivera",
    "company": "Acme Cloud Labs",
    "preference": "Concise technical instructions",
}

DEMO_TICKET_1 = {
    "id": 1001,
    "customer_id": 9999,
    "customer_email": "alex.rivera@demo.meow",
    "customer_name": "Alex Rivera",
    "customer_company": "Acme Cloud Labs",
    "subject": "Large report API timeout error 504",
    "description": "Exporting customer ledger reports with >500 rows returns 504 Gateway Timeout after 60s.",
    "priority": "high",
    "status": "pending",
}

DEMO_TICKET_2 = {
    "id": 1002,
    "customer_id": 9999,
    "customer_email": "alex.rivera@demo.meow",
    "customer_name": "Alex Rivera",
    "customer_company": "Acme Cloud Labs",
    "subject": "Large report API timeout error 504 (reopened/recurrence)",
    "description": "Still encountering 504 Gateway Timeout when running large report exports.",
    "priority": "high",
    "status": "pending",
}

DEMO_TICKET_3 = {
    "id": 1003,
    "customer_id": 9999,
    "customer_email": "alex.rivera@demo.meow",
    "customer_name": "Alex Rivera",
    "customer_company": "Acme Cloud Labs",
    "subject": "Large financial report export timeout",
    "description": "End-of-month financial report export timed out with 504.",
    "priority": "high",
    "status": "pending",
}


class DemoLearningController:
    """
    Deterministic state machine managing the Phase 7 demonstration scenario.
    Completely isolated from production customer data and live provider quotas.
    """

    def __init__(self) -> None:
        self.state: DemoState = DemoState.NEW_CUSTOMER
        self.rejection_reason: str | None = None
        self.events: list[DemoEvent] = []
        self._emit("System", "DEMO_INITIALIZED", "info", "Demo environment initialized (customer: Alex Rivera)")

    def _emit(self, component: str, action: str, status: str, description: str) -> None:
        now_str = datetime.now().strftime("%H:%M:%S")
        self.events.append(DemoEvent(
            timestamp=now_str,
            component=component,
            action=action,
            status=status,
            description=description,
        ))

    def reset(self) -> None:
        """Reset scenario back to NEW_CUSTOMER."""
        self.state = DemoState.NEW_CUSTOMER
        self.rejection_reason = None
        self.events.clear()
        self._emit("System", "DEMO_RESET", "info", "All demo state, tickets, and memory banks reset to clean state.")

    def advance_to_ticket_1(self) -> None:
        """Stage 1: Generate initial ticket with novel issue (0 prior experience)."""
        self.state = DemoState.FIRST_TICKET
        self._emit("SQLite", "TICKET_CREATED", "ok", "Ticket #1001 created: Large report API timeout error 504")
        self._emit("Mem0", "CUSTOMER_RECALLED", "ok", "Customer profile recalled: Alex Rivera (1 fact: Custom enterprise export pipeline)")
        self._emit("RAG", "KNOWLEDGE_RETRIEVED", "ok", "Documentation retrieved: kb_api_guide (relevance: 0.94)")
        self._emit("Hindsight", "EXPERIENCE_SEARCHED", "info", "Past experience searched in bank 'alex_rivera': 0 experiences found (clean slate)")
        self._emit("Groq", "DRAFT_GENERATED", "ok", "Initial draft #5001 generated based on documentation alone (Clear cache)")
        self._emit("SQLite", "DRAFT_SAVED", "ok", "Draft #5001 saved to SQLite repository (status: pending)")

    def reject_ticket_1(self, reason: str = "Already tried clearing cache without effect") -> None:
        """Stage 2: Human rejects initial draft -> FAILURE retained."""
        self.rejection_reason = reason
        self.state = DemoState.REJECTED_FAILURE
        self._emit("SQLite", "DRAFT_DISCARDED", "warn", f"Draft #5001 marked DISCARDED (Reason: {reason})")
        self._emit("Mem0", "MEM0_BYPASSED", "info", "Bypassed Mem0: Rejected solution is unconfirmed, NOT saved as customer fact")
        self._emit("Hindsight", "RETENTION_STARTED", "info", "Storing rejected troubleshooting attempt into bank 'alex_rivera'")
        self._emit("Hindsight", "FAILURE_RECORDED", "warn", "Failure experience recorded: [DO NOT REPEAT] Cache clearing failed")

    def advance_to_ticket_2(self) -> None:
        """Stage 3: Second ticket recalls FAILURE and avoids repeated mistake."""
        self.state = DemoState.SECOND_TICKET
        self._emit("SQLite", "TICKET_CREATED", "ok", "Ticket #1002 created: API 504 recurring timeout (status: open)")
        self._emit("Mem0", "CUSTOMER_RECALLED", "ok", "Customer profile recalled: Alex Rivera (1 fact)")
        self._emit("RAG", "KNOWLEDGE_RETRIEVED", "ok", "Documentation retrieved: kb_api_guide (API timeout threshold raised to 90s)")
        self._emit("Hindsight", "FAILURE_RECALLED", "warn", "Recalled 1 failure: Cache clearing previously failed (Do not repeat)")
        self._emit("Groq", "DRAFT_GENERATED", "ok", "Draft #5002 generated (Avoided cache clearing; proposed timeout: 90s)")
        self._emit("SQLite", "DRAFT_SAVED", "ok", "Draft #5002 saved to SQLite repository (status: pending)")

    def accept_ticket_2(self) -> None:
        """Stage 4: Human accepts proven fix -> SUCCESS retained."""
        self.state = DemoState.ACCEPTED_SUCCESS
        self._emit("SQLite", "DRAFT_ACCEPTED", "ok", "Draft #5002 marked ACCEPTED by human agent")
        self._emit("SQLite", "TICKET_RESOLVED", "ok", "Ticket #1002 marked RESOLVED")
        self._emit("Mem0", "FACT_SAVED", "ok", "Confirmed resolution stored in Mem0: Timeout raised 30s → 90s")
        self._emit("Hindsight", "RETENTION_STARTED", "info", "Storing verified resolution into bank 'alex_rivera'")
        self._emit("Hindsight", "SUCCESS_RECORDED", "ok", "Proven fix recorded: [PROVEN FIX] Increase timeout to 90s")

    def advance_to_ticket_3(self) -> None:
        """Stage 5: Third ticket recalls SUCCESS + FAILURE + PREFERENCE + PATTERN."""
        self.state = DemoState.THIRD_TICKET
        self._emit("SQLite", "TICKET_CREATED", "ok", "Ticket #1003 created: End-of-month batch export timeout (status: open)")
        self._emit("Mem0", "CUSTOMER_RECALLED", "ok", "Customer profile recalled: Alex Rivera (2 confirmed facts)")
        self._emit("RAG", "KNOWLEDGE_RETRIEVED", "ok", "Documentation retrieved: kb_api_guide")
        self._emit("Hindsight", "FULL_RECALL", "ok", "Full historical recall: 4 experiences found (Fix, Failure, Preference, Pattern)")
        self._emit("Groq", "DRAFT_GENERATED", "ok", "Personalized draft #5003 synthesized: 'Set export_timeout: 90s'")
        self._emit("SQLite", "DRAFT_SAVED", "ok", "Draft #5003 saved to SQLite repository (status: pending)")

    def complete_learned_state(self) -> None:
        """Stage 6: Final learned state overview."""
        self.state = DemoState.LEARNED_STATE

    def get_events(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Return chronological activity events with metadata."""
        evs = [e.to_dict() for e in self.events]
        if limit is not None:
            return evs[-limit:]
        return evs

    def get_current_payload(self) -> dict[str, Any]:
        """Produce the complete UI payload for the current demo state."""
        customer = dict(DEMO_CUSTOMER)

        if self.state == DemoState.NEW_CUSTOMER:
            return {
                "state": self.state.value,
                "stage_label": "Stage 0: New Customer (Clean Slate)",
                "customer": customer,
                "ticket": None,
                "draft": None,
                "context_used": None,
                "learned_card": None,
                "timeline": [],
            }

        elif self.state == DemoState.FIRST_TICKET:
            context_used = {
                "version": 2,
                "shadow_mode": False,
                "hindsight_context_injected": False,
                "hindsight_status": "DEMO_MODE",
                "mem0_status": "DEMO_MODE",
                "signals": {
                    "memory_hit_count": 1,
                    "knowledge_hit_count": 1,
                    "hindsight_hit_count": 0,
                    "tool_call_count": 0,
                    "knowledge_sources": ["kb_api_guide"],
                    "hindsight_status": "DEMO_MODE",
                    "mem0_status": "DEMO_MODE",
                },
                "memory_hits": [
                    {"memory": "Customer uses custom enterprise export pipeline", "metadata": {"created_at": "2026-09-20"}}
                ],
                "knowledge_hits": [
                    {"source": "kb_api_guide", "content": "API timeout handling and client retry thresholds"}
                ],
                "hindsight_hits": [],
                "tool_calls": [],
                "errors": [],
            }
            draft = {
                "id": 5001,
                "ticket_id": 1001,
                "content": (
                    "Hi Alex,\n\n"
                    "Thank you for reaching out. For large report export timeouts, please try clearing your local browser "
                    "and proxy cache, then retry generating the ledger report.\n\n"
                    "Let us know if the issue persists."
                ),
                "status": "pending",
                "context_used": context_used,
            }
            return {
                "state": self.state.value,
                "stage_label": "Stage 1: Novel Issue (No Prior Experience)",
                "customer": customer,
                "ticket": dict(DEMO_TICKET_1),
                "draft": draft,
                "context_used": context_used,
                "learned_card": None,
                "timeline": [
                    {"source": "mem0", "category": "FACT", "text": "Customer uses custom enterprise export pipeline", "timestamp": "2026-09-20"}
                ],
            }

        elif self.state == DemoState.REJECTED_FAILURE:
            context_used = {
                "version": 2,
                "shadow_mode": False,
                "hindsight_context_injected": False,
                "hindsight_status": "DEMO_MODE",
                "mem0_status": "DEMO_MODE",
                "signals": {
                    "memory_hit_count": 1,
                    "knowledge_hit_count": 1,
                    "hindsight_hit_count": 1,
                    "knowledge_sources": ["kb_api_guide"],
                    "hindsight_status": "DEMO_MODE",
                    "mem0_status": "DEMO_MODE",
                },
                "memory_hits": [
                    {"memory": "Customer uses custom enterprise export pipeline", "metadata": {"created_at": "2026-09-20"}}
                ],
                "knowledge_hits": [
                    {"source": "kb_api_guide", "content": "API timeout handling and client retry thresholds"}
                ],
                "hindsight_hits": [
                    {
                        "category": "FAILURE",
                        "text": "Proposed cache clearing failed: Already tried without effect",
                        "score": 0.90,
                        "metadata": {"timestamp": "2026-09-27", "ticket_id": "1001", "has_failed_attempts": "true"},
                    }
                ],
                "tool_calls": [],
                "errors": [],
            }
            draft = {
                "id": 5001,
                "ticket_id": 1001,
                "content": "Hi Alex, please try clearing your local cache...",
                "status": "discarded",
                "rejection_reason": self.rejection_reason or "Already tried clearing cache without effect",
                "context_used": context_used,
            }
            return {
                "state": self.state.value,
                "stage_label": "Stage 2: Draft Discarded → Failure Retained in Hindsight",
                "customer": customer,
                "ticket": dict(DEMO_TICKET_1),
                "draft": draft,
                "context_used": context_used,
                "learned_card": {
                    "type": "FAILURE",
                    "action": "Clear cache",
                    "reason": self.rejection_reason or "Already tried clearing cache without effect",
                    "note": "Previously unsuccessful approach — recorded in Hindsight to prevent repeating.",
                },
                "timeline": [
                    {
                        "source": "hindsight",
                        "category": "FAILURE",
                        "text": "Clear cache → unsuccessful (Already tried)",
                        "timestamp": "2026-09-27",
                    },
                    {
                        "source": "mem0",
                        "category": "FACT",
                        "text": "Customer uses custom enterprise export pipeline",
                        "timestamp": "2026-09-20",
                    },
                ],
            }

        elif self.state == DemoState.SECOND_TICKET:
            context_used = {
                "version": 2,
                "shadow_mode": False,
                "hindsight_context_injected": True,
                "hindsight_status": "DEMO_MODE",
                "mem0_status": "DEMO_MODE",
                "signals": {
                    "memory_hit_count": 1,
                    "knowledge_hit_count": 1,
                    "hindsight_hit_count": 1,
                    "knowledge_sources": ["kb_api_guide"],
                    "hindsight_status": "DEMO_MODE",
                    "mem0_status": "DEMO_MODE",
                },
                "memory_hits": [
                    {"memory": "Customer uses custom enterprise export pipeline", "metadata": {"created_at": "2026-09-20"}}
                ],
                "knowledge_hits": [
                    {"source": "kb_api_guide", "content": "API timeout threshold can be raised to 90s for batch reports"}
                ],
                "hindsight_hits": [
                    {
                        "category": "FAILURE",
                        "text": "Clear cache was previously rejected by customer (Already tried without effect)",
                        "score": 0.92,
                        "metadata": {"timestamp": "2026-09-27", "ticket_id": "1001"},
                    }
                ],
                "tool_calls": [],
                "errors": [],
            }
            draft = {
                "id": 5002,
                "ticket_id": 1002,
                "content": (
                    "Hi Alex,\n\n"
                    "We note that clearing cache was previously unsuccessful for this issue. "
                    "For large batch exports, please increase your API client timeout from 30 to 90 seconds "
                    "in your export configuration (`timeout: 90s`).\n\n"
                    "This provides sufficient window for the ledger compilation worker to complete."
                ),
                "status": "pending",
                "context_used": context_used,
            }
            return {
                "state": self.state.value,
                "stage_label": "Stage 3: Hindsight Recalls Failure → AI Proposes 90s Timeout",
                "customer": customer,
                "ticket": dict(DEMO_TICKET_2),
                "draft": draft,
                "context_used": context_used,
                "learned_card": None,
                "timeline": [
                    {
                        "source": "hindsight",
                        "category": "FAILURE",
                        "text": "Clear cache → unsuccessful (Already tried)",
                        "timestamp": "2026-09-27",
                    },
                    {
                        "source": "mem0",
                        "category": "FACT",
                        "text": "Customer uses custom enterprise export pipeline",
                        "timestamp": "2026-09-20",
                    },
                ],
            }

        elif self.state == DemoState.ACCEPTED_SUCCESS:
            context_used = {
                "version": 2,
                "shadow_mode": False,
                "hindsight_context_injected": True,
                "hindsight_status": "DEMO_MODE",
                "mem0_status": "DEMO_MODE",
                "signals": {
                    "memory_hit_count": 1,
                    "knowledge_hit_count": 1,
                    "hindsight_hit_count": 2,
                    "knowledge_sources": ["kb_api_guide"],
                    "hindsight_status": "DEMO_MODE",
                    "mem0_status": "DEMO_MODE",
                },
                "memory_hits": [
                    {"memory": "Customer uses custom enterprise export pipeline", "metadata": {"created_at": "2026-09-20"}}
                ],
                "knowledge_hits": [
                    {"source": "kb_api_guide", "content": "API timeout threshold can be raised to 90s"}
                ],
                "hindsight_hits": [
                    {
                        "category": "SUCCESS",
                        "text": "Increase API timeout from 30 to 90 seconds resolved large export timeout",
                        "score": 0.96,
                        "metadata": {"timestamp": "2026-09-27", "ticket_id": "1002", "is_resolved": "true"},
                    },
                    {
                        "category": "FAILURE",
                        "text": "Clear cache was previously rejected by customer (Already tried)",
                        "score": 0.90,
                        "metadata": {"timestamp": "2026-09-27", "ticket_id": "1001"},
                    },
                ],
                "tool_calls": [],
                "errors": [],
            }
            draft = {
                "id": 5002,
                "ticket_id": 1002,
                "content": "Increase API client timeout from 30 to 90 seconds...",
                "status": "accepted",
                "context_used": context_used,
            }
            return {
                "state": self.state.value,
                "stage_label": "Stage 4: Draft Accepted → Proven Fix Retained in Hindsight",
                "customer": customer,
                "ticket": dict(DEMO_TICKET_2),
                "draft": draft,
                "context_used": context_used,
                "learned_card": {
                    "type": "SUCCESS",
                    "action": "Increase timeout 30 → 90 sec",
                    "reason": "Confirmed effective resolution applied to customer ticket",
                    "note": "Previously successful experience — future tickets will recall this historical resolution.",
                },
                "timeline": [
                    {
                        "source": "hindsight",
                        "category": "SUCCESS",
                        "text": "Increase timeout 30 → 90 sec (Proven fix applied)",
                        "timestamp": "2026-09-27",
                    },
                    {
                        "source": "hindsight",
                        "category": "FAILURE",
                        "text": "Clear cache → unsuccessful (Already tried)",
                        "timestamp": "2026-09-27",
                    },
                    {
                        "source": "mem0",
                        "category": "FACT",
                        "text": "Customer uses custom enterprise export pipeline",
                        "timestamp": "2026-09-20",
                    },
                ],
            }

        else:  # THIRD_TICKET or LEARNED_STATE
            context_used = {
                "version": 2,
                "shadow_mode": False,
                "hindsight_context_injected": True,
                "hindsight_status": "DEMO_MODE",
                "mem0_status": "DEMO_MODE",
                "signals": {
                    "memory_hit_count": 1,
                    "knowledge_hit_count": 1,
                    "hindsight_hit_count": 4,
                    "knowledge_sources": ["kb_api_guide"],
                    "hindsight_status": "DEMO_MODE",
                    "mem0_status": "DEMO_MODE",
                },
                "memory_hits": [
                    {"memory": "Customer uses custom enterprise export pipeline", "metadata": {"created_at": "2026-09-20"}}
                ],
                "knowledge_hits": [
                    {"source": "kb_api_guide", "content": "API timeout handling"}
                ],
                "hindsight_hits": [
                    {
                        "category": "SUCCESS",
                        "text": "Increase API timeout from 30 to 90 seconds (Proven fix)",
                        "score": 0.96,
                        "metadata": {"timestamp": "2026-09-27", "ticket_id": "1002"},
                    },
                    {
                        "category": "FAILURE",
                        "text": "Clear cache was previously rejected by customer (Do not repeat)",
                        "score": 0.91,
                        "metadata": {"timestamp": "2026-09-27", "ticket_id": "1001"},
                    },
                    {
                        "category": "PREFERENCE",
                        "text": "Customer prefers concise technical instructions without generic greetings",
                        "score": 0.95,
                        "metadata": {"type": "preference"},
                    },
                    {
                        "category": "PATTERN",
                        "text": "Repeated report timeout issue occurs on end-of-month large batch exports",
                        "score": 0.88,
                        "metadata": {"type": "pattern"},
                    },
                ],
                "tool_calls": [],
                "errors": [],
            }
            draft = {
                "id": 5003,
                "ticket_id": 1003,
                "content": (
                    "Alex:\n\n"
                    "Set `export_timeout: 90s` in export config.\n\n"
                    "(Per account history: Cache clearing does not resolve this timeout; increasing client timeout to 90s is the verified fix for end-of-month batch runs)."
                ),
                "status": "pending",
                "context_used": context_used,
            }
            return {
                "state": self.state.value,
                "stage_label": "Stage 5: Full Learning Loop (Success + Failure + Preference + Pattern Recalled)",
                "customer": customer,
                "ticket": dict(DEMO_TICKET_3),
                "draft": draft,
                "context_used": context_used,
                "learned_card": None,
                "timeline": [
                    {
                        "source": "hindsight",
                        "category": "SUCCESS",
                        "text": "Increase timeout 30 → 90 sec (Proven fix)",
                        "timestamp": "2026-09-27",
                    },
                    {
                        "source": "hindsight",
                        "category": "FAILURE",
                        "text": "Clear cache → unsuccessful (Already tried)",
                        "timestamp": "2026-09-27",
                    },
                    {
                        "source": "hindsight",
                        "category": "PREFERENCE",
                        "text": "Concise technical instructions",
                        "timestamp": "2026-09-20",
                    },
                    {
                        "source": "hindsight",
                        "category": "PATTERN",
                        "text": "Repeated report timeout on end-of-month runs",
                        "timestamp": "2026-09-20",
                    },
                ],
            }
