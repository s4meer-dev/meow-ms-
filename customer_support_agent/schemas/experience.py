from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TroubleshootingAttempt(BaseModel):
    """
    Represents a discrete troubleshooting action, its immediate result,
    and the causal reason why it failed or succeeded.
    """

    model_config = ConfigDict(extra="ignore")

    action: str = Field(..., min_length=1, description="Specific action, test, or command attempted")
    result: str = Field(..., min_length=1, description="Direct result of the attempt (e.g., 'failed', 'succeeded')")
    reason: Optional[str] = Field(None, description="Causal explanation of why this step succeeded or failed")
    timestamp: Optional[datetime] = Field(None, description="When this action took place")

    @property
    def is_failure(self) -> bool:
        """Heuristic check whether this attempt was unsuccessful."""
        val = self.result.strip().lower()
        return any(term in val for term in ("fail", "error", "abort", "crash", "timeout", "revert", "unsuccessful"))

    @property
    def is_success(self) -> bool:
        """Heuristic check whether this attempt was successful."""
        val = self.result.strip().lower()
        return any(term in val for term in ("success", "succeed", "work", "pass", "resolv", "fix", "ok"))


class SupportExperience(BaseModel):
    """
    Structured causal model of a complete support interaction experience.
    Captures context, symptoms, attempts (failed and successful), resolution,
    outcome, customer reaction, and learned preferences.
    """

    model_config = ConfigDict(extra="ignore")

    experience_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this experience record",
    )
    customer_id: str = Field(..., description="Unique identifier for the customer (string or converted from int)")
    company_id: Optional[str] = Field(None, description="Optional corporate / organization identifier")
    ticket_id: Optional[str] = Field(None, description="Associated ticket ID (string or converted from int)")
    problem: str = Field(..., min_length=3, description="Core issue or question reported by customer")
    environment: Optional[str | dict[str, Any]] = Field(
        None,
        description="Operating system, versions, browser, infrastructure, or hardware context",
    )
    symptoms: list[str] = Field(
        default_factory=list,
        description="Specific error codes, stack traces, logs, or observable symptoms",
    )
    attempts: list[TroubleshootingAttempt] = Field(
        default_factory=list,
        description="Chronological record of all troubleshooting actions attempted",
    )
    failed_attempts: list[TroubleshootingAttempt] = Field(
        default_factory=list,
        description="Troubleshooting actions that failed and should NOT be repeated",
    )
    successful_attempts: list[TroubleshootingAttempt] = Field(
        default_factory=list,
        description="Troubleshooting actions that proved effective",
    )
    resolution: Optional[str] = Field(None, description="Ultimate resolution or workaround applied")
    outcome: Optional[str] = Field(None, description="Final measured state or operational impact")
    customer_reaction: Optional[str] = Field(None, description="Customer feedback or response to resolution")
    customer_sentiment: Optional[Literal["positive", "neutral", "negative", "frustrated", "satisfied"] | str] = Field(
        None,
        description="Customer sentiment assessment",
    )
    preferences: list[str] = Field(
        default_factory=list,
        description="Customer operational constraints, tool preferences, or communication habits",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this experience was recorded",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary additional metadata tags",
    )

    @field_validator("customer_id", "company_id", "ticket_id", mode="before")
    @classmethod
    def _coerce_id_to_str(cls, value: Any) -> Optional[str]:
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None
        return s

    @field_validator("customer_id")
    @classmethod
    def _validate_customer_id(cls, value: Optional[str]) -> str:
        if not value:
            raise ValueError("customer_id cannot be empty")
        return value

    @model_validator(mode="after")
    def _synchronize_attempts(self) -> SupportExperience:
        """
        Ensure attempts, failed_attempts, and successful_attempts stay synchronized.
        If attempts are provided without partitioning, partition them automatically.
        If partitioned attempts are provided without attempts, merge them chronologically.
        """
        if self.attempts and not self.failed_attempts and not self.successful_attempts:
            failed = []
            successful = []
            for attempt in self.attempts:
                if attempt.is_failure:
                    failed.append(attempt)
                elif attempt.is_success:
                    successful.append(attempt)
            self.failed_attempts = failed
            self.successful_attempts = successful
        elif not self.attempts and (self.failed_attempts or self.successful_attempts):
            self.attempts = [*self.failed_attempts, *self.successful_attempts]
        return self

    @property
    def has_failed_attempts(self) -> bool:
        return bool(self.failed_attempts)

    @property
    def has_successful_attempts(self) -> bool:
        return bool(self.successful_attempts)

    @property
    def is_resolved(self) -> bool:
        return bool(self.resolution and self.resolution.strip())

    def add_attempt(
        self,
        action: str,
        result: str,
        reason: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> TroubleshootingAttempt:
        """Convenience method to append an attempt and update partitions."""
        attempt = TroubleshootingAttempt(
            action=action,
            result=result,
            reason=reason,
            timestamp=timestamp,
        )
        self.attempts.append(attempt)
        if attempt.is_failure:
            self.failed_attempts.append(attempt)
        elif attempt.is_success:
            self.successful_attempts.append(attempt)
        return attempt


class ExperienceRecallItem(BaseModel):
    """Single item retrieved from experiential memory recall."""

    model_config = ConfigDict(extra="ignore")

    text: str
    score: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class ExperienceRecallResponse(BaseModel):
    """Structured response container for experience recall."""

    model_config = ConfigDict(extra="ignore")

    customer_id: str
    bank_id: str
    query: str
    summary_text: str = ""
    experiences: list[ExperienceRecallItem] = Field(default_factory=list)
    raw_response: Optional[Any] = None


class ExperienceReflectionResponse(BaseModel):
    """Structured response container for experience reflection."""

    model_config = ConfigDict(extra="ignore")

    customer_id: str
    bank_id: str
    question: str
    insights: str = ""
    raw_response: Optional[Any] = None


# ---------------------------------------------------------------------------
# Phase 3: Structured Hindsight Evidence & Memory Evaluation Schemas
# ---------------------------------------------------------------------------

class MemoryCategory(str, Enum):
    """Classification of recalled experience facts."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PREFERENCE = "PREFERENCE"
    PATTERN = "PATTERN"
    OTHER = "OTHER"


class HindsightEvidence(BaseModel):
    """
    Structured representation of an individual experiential memory item
    retrieved from Hindsight during shadow evaluation.
    """

    model_config = ConfigDict(extra="ignore")

    memory_id: Optional[str] = None
    text: str = ""
    type: MemoryCategory = MemoryCategory.OTHER
    category: Optional[MemoryCategory] = None
    score: Optional[float] = None
    context: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    source_document_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _sync_category_and_type(self) -> HindsightEvidence:
        if self.category is None:
            self.category = self.type
        elif self.type == MemoryCategory.OTHER and self.category != MemoryCategory.OTHER:
            self.type = self.category
        return self

    @classmethod
    def from_raw_item(
        cls,
        text: Any,
        score: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
        memory_id: Optional[str] = None,
    ) -> HindsightEvidence:
        """Constructs and classifies a HindsightEvidence instance from raw recall data."""
        if text is None:
            text_str = ""
        elif isinstance(text, str):
            text_str = text
        elif isinstance(text, dict):
            text_str = str(text.get("text") or text.get("content") or text.get("summary") or text)
        else:
            text_str = str(text)

        meta = metadata or {}
        tags = [str(t).lower() for t in meta.get("tags") or []]
        text_lower = text_str.lower()

        # Determine category based on tags, metadata, and causal markers
        category = MemoryCategory.OTHER
        if (
            "[success" in text_lower
            or meta.get("is_resolved") in (True, "true", "True")
            or "resolved" in tags
            or "success" in tags
        ):
            category = MemoryCategory.SUCCESS
        elif (
            "[failed" in text_lower
            or "[failure" in text_lower
            or meta.get("has_failed_attempts") in (True, "true", "True")
            or "has_failures" in tags
            or "failure" in tags
        ):
            category = MemoryCategory.FAILURE
        elif (
            "[preference" in text_lower
            or "preference" in tags
            or meta.get("type") == "preference"
            or "prefers" in text_lower
        ):
            category = MemoryCategory.PREFERENCE
        elif (
            "[pattern" in text_lower
            or "pattern" in tags
            or "recurring" in text_lower
        ):
            category = MemoryCategory.PATTERN

        doc_id = meta.get("document_id") or meta.get("source_document_id")

        return cls(
            memory_id=memory_id or meta.get("memory_id") or meta.get("id"),
            text=text_str,
            type=category,
            category=category,
            score=score or 0.0,
            context=meta.get("context"),
            metadata=meta,
            source_document_id=str(doc_id) if doc_id else None,
            tags=tags,
        )


class MemoryEvaluation(BaseModel):
    """
    Deterministic evaluation object comparing Mem0 context against
    Hindsight experience context during shadow mode.
    """

    model_config = ConfigDict(extra="ignore")

    customer_id: str
    ticket_id: Optional[str] = None
    mem0_results: list[dict[str, Any]] = Field(default_factory=list)
    hindsight_results: list[HindsightEvidence] = Field(default_factory=list)
    mem0_count: int = 0
    hindsight_count: int = 0
    overlap_count: int = 0
    overlap_ratio: float = 0.0
    unique_hindsight_count: int = 0
    unique_mem0_count: int = 0
    common_memories: list[str] = Field(default_factory=list)
    mem0_only_memories: list[str] = Field(default_factory=list)
    hindsight_only_memories: list[str] = Field(default_factory=list)
    hindsight_available: bool = True
    hindsight_status: str = "LIVE_SUCCESS"
    mem0_status: str = "LIVE_SUCCESS"
    latency_ms: float = 0.0
    errors: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def common_facts(self) -> list[str]:
        return self.common_memories

    @property
    def mem0_only_facts(self) -> list[str]:
        return self.mem0_only_memories

    @property
    def hindsight_only_facts(self) -> list[str]:
        return self.hindsight_only_memories


def build_hindsight_recall_query(ticket: dict[str, Any], customer: dict[str, Any]) -> str:
    """
    Constructs a high-quality, focused Hindsight recall query from ticket and customer data.
    Focuses on previous incidents, failed attempts, proven fixes, and preferences.
    """
    subject = str(ticket.get("subject") or "").strip()
    description = str(ticket.get("description") or "").strip()
    company = str(customer.get("company") or "").strip()
    environment = str(ticket.get("environment") or "").strip()
    customer_email = str(customer.get("email") or "").strip()

    parts = []
    if subject:
        parts.append(subject)
    if description:
        # Avoid prompt bloat by focusing on the first 300 characters of problem description
        parts.append(description[:300].strip())
    if customer_email:
        parts.append(f"Customer: {customer_email}")
    if environment:
        parts.append(f"Environment: {environment}")
    if company:
        parts.append(f"Company: {company}")

    base_query = " | ".join(parts) if parts else "troubleshooting experience and resolutions"
    return f"{base_query} (troubleshooting attempts, failed solutions, proven fixes, customer preferences)"


def evaluate_memory_overlap(
    mem0_results: list[dict[str, Any]],
    hindsight_results: list[HindsightEvidence],
    ticket_id: Optional[str | int] = None,
    customer_id: str = "",
    hindsight_available: bool = True,
    hindsight_status: Optional[str] = None,
    mem0_status: Optional[str] = None,
    latency_ms: float = 0.0,
    errors: Optional[list[str]] = None,
    error: Optional[str] = None,
    **kwargs: Any,
) -> MemoryEvaluation:
    """
    Performs a deterministic, fact-based comparison between Mem0 memories and Hindsight memories.
    Identifies COMMON, MEM0_ONLY, and HINDSIGHT_ONLY memories without subjective quality claims.
    """
    common: list[str] = []
    mem0_only: list[str] = []
    hindsight_only: list[str] = []

    err_list = list(errors or [])
    if error:
        err_list.append(error)

    if any("failed" in e.lower() or "not enabled" in e.lower() or "unavailable" in e.lower() for e in err_list):
        hindsight_available = False

    # Infer hindsight_status if not explicitly provided
    resolved_hindsight_status = hindsight_status
    if not resolved_hindsight_status:
        err_text = " ".join(err_list).lower()
        if "quota" in err_text or "rate limit" in err_text or "429" in err_text:
            resolved_hindsight_status = "PROVIDER_QUOTA_ERROR"
        elif "disabled" in err_text or "not enabled" in err_text:
            resolved_hindsight_status = "DISABLED"
        elif not hindsight_available or "unavailable" in err_text or "connection" in err_text:
            resolved_hindsight_status = "UNAVAILABLE"
        elif err_list:
            if any("hindsight" in e.lower() for e in err_list):
                resolved_hindsight_status = "LIVE_PARTIAL"
            else:
                resolved_hindsight_status = "LIVE_SUCCESS"
        else:
            resolved_hindsight_status = "LIVE_SUCCESS"

    # Infer mem0_status if not explicitly provided
    resolved_mem0_status = mem0_status
    if not resolved_mem0_status:
        err_text = " ".join(err_list).lower()
        if "no embedding provider" in err_text or "not installed" in err_text:
            resolved_mem0_status = "CONFIGURATION_ERROR"
        elif "mem0" in err_text and ("error" in err_text or "failed" in err_text):
            resolved_mem0_status = "UNAVAILABLE"
        else:
            resolved_mem0_status = "LIVE_SUCCESS"

    # Helper to extract clean keywords from a string
    stop_words = {
        "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by",
        "is", "was", "it", "and", "or", "but", "be", "this", "that", "from",
        "has", "had", "have", "not", "did", "action", "result", "why", "outcome",
    }

    def tokenize(text: str) -> set[str]:
        words = "".join(ch if ch.isalnum() else " " for ch in text.lower()).split()
        return {w for w in words if len(w) > 2 and w not in stop_words}

    # Extract Mem0 text items
    mem0_items: list[tuple[str, set[str]]] = []
    for m in mem0_results:
        raw_text = str(m.get("memory") or m.get("text") or m.get("content") or "").strip()
        if raw_text:
            mem0_items.append((raw_text, tokenize(raw_text)))

    # Extract Hindsight text items
    hindsight_items: list[tuple[HindsightEvidence, set[str]]] = []
    for h in hindsight_results:
        raw_text = h.text.strip()
        if raw_text:
            hindsight_items.append((h, tokenize(raw_text)))

    matched_hindsight_indices: set[int] = set()

    for m_text, m_tokens in mem0_items:
        found_overlap = False
        for idx, (h_ev, h_tokens) in enumerate(hindsight_items):
            if not m_tokens or not h_tokens:
                continue
            intersection = m_tokens.intersection(h_tokens)
            union = m_tokens.union(h_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0
            if len(intersection) >= 2 or jaccard >= 0.15 or m_text.lower() == h_ev.text.lower():
                common.append(m_text)
                matched_hindsight_indices.add(idx)
                found_overlap = True
                break

        if not found_overlap:
            mem0_only.append(m_text)

    for idx, (h_ev, _) in enumerate(hindsight_items):
        if idx not in matched_hindsight_indices:
            cat_name = h_ev.category.value if h_ev.category else "OTHER"
            hindsight_only.append(f"[{cat_name}] {h_ev.text}")

    total_distinct = len(mem0_items) + len(hindsight_items) - len(common)
    overlap_ratio = round(len(common) / max(1, total_distinct), 2) if total_distinct > 0 else 0.0

    return MemoryEvaluation(
        customer_id=str(customer_id),
        ticket_id=str(ticket_id) if ticket_id else None,
        mem0_results=mem0_results,
        hindsight_results=hindsight_results,
        mem0_count=len(mem0_results),
        hindsight_count=len(hindsight_results),
        overlap_count=len(common),
        overlap_ratio=overlap_ratio,
        unique_mem0_count=len(mem0_only),
        unique_hindsight_count=len(hindsight_only),
        common_memories=common,
        mem0_only_memories=mem0_only,
        hindsight_only_memories=hindsight_only,
        hindsight_available=hindsight_available,
        hindsight_status=resolved_hindsight_status,
        mem0_status=resolved_mem0_status,
        latency_ms=round(latency_ms, 2),
        errors=err_list,
    )

