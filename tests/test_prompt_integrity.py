"""Unit tests for recall query builder, memory evaluation, and support experience schemas."""

import pytest
from customer_support_agent.schemas.experience import (
    HindsightEvidence,
    MemoryCategory,
    MemoryEvaluation,
    SupportExperience,
    build_hindsight_recall_query,
    evaluate_memory_overlap,
)


def test_build_hindsight_recall_query():
    """Verify recall query combines ticket subject and description cleanly."""
    ticket = {
        "subject": "Large report API timeout error 504",
        "description": "Batch exports with >500 rows fail after 60s timeout.",
    }
    customer = {
        "name": "Alex Rivera",
        "company": "Acme Cloud Labs",
    }
    query = build_hindsight_recall_query(ticket=ticket, customer=customer)
    assert "Large report API timeout error 504" in query
    assert "Batch exports with >500 rows fail after 60s timeout." in query


def test_evaluate_memory_overlap_empty():
    """Verify memory evaluation handles empty input sets gracefully."""
    eval_result = evaluate_memory_overlap(
        customer_id="9999",
        ticket_id="1001",
        mem0_results=[],
        hindsight_results=[],
    )
    assert isinstance(eval_result, MemoryEvaluation)
    assert eval_result.overlap_ratio == 0.0
    assert eval_result.customer_id == "9999"
    assert eval_result.ticket_id == "1001"


def test_evaluate_memory_overlap_with_items():
    """Verify memory evaluation classifies distinct items across Mem0 and Hindsight."""
    mem0_items = [{"memory": "Customer uses custom enterprise export pipeline"}]
    hindsight_items = [
        HindsightEvidence.from_raw_item(
            text="[SUCCESS] Increase timeout to 90s for large reports",
            score=0.95,
            metadata={"ticket_id": "1002"},
        )
    ]
    eval_result = evaluate_memory_overlap(
        customer_id="9999",
        ticket_id="1002",
        mem0_results=mem0_items,
        hindsight_results=hindsight_items,
    )
    assert isinstance(eval_result, MemoryEvaluation)
    assert len(eval_result.hindsight_results) == 1
    assert eval_result.hindsight_results[0].category == MemoryCategory.SUCCESS


def test_support_experience_schema_validation():
    """Verify SupportExperience validates mandatory customer_id and problem fields."""
    exp = SupportExperience(
        customer_id="9999",
        problem="Large financial report export timeout",
        resolution="Set timeout parameter to 90 seconds",
    )
    assert exp.customer_id == "9999"
    assert exp.problem == "Large financial report export timeout"
    assert exp.resolution == "Set timeout parameter to 90 seconds"
    assert exp.experience_id is not None
