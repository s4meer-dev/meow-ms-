from __future__ import annotations

from datetime import datetime, timezone
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
