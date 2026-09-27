from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from customer_support_agent.core.settings import Settings, get_settings
from customer_support_agent.integrations.hindsight.banks import (
    get_customer_bank_id,
    sanitize_identifier,
)
from customer_support_agent.integrations.hindsight.service import HindsightMemoryService
from customer_support_agent.schemas.experience import (
    ExperienceRecallItem,
    ExperienceRecallResponse,
    ExperienceReflectionResponse,
    HindsightEvidence,
    MemoryCategory,
    MemoryEvaluation,
    SupportExperience,
    build_hindsight_recall_query,
    evaluate_memory_overlap,
)

logger = logging.getLogger(__name__)


def format_experience_narrative(experience: SupportExperience) -> str:
    """
    Format a SupportExperience into a high-density, causal narrative document
    optimized for Hindsight's temporal and entity graph extraction.
    Explicitly preserves problems, environments, symptoms, failed attempts,
    successful attempts, resolutions, outcomes, and customer preferences.
    """
    lines: list[str] = [
        "=== SUPPORT EXPERIENCE REPORT ===",
        f"Ticket ID: {experience.ticket_id or 'Unassigned'}",
        f"Customer ID: {experience.customer_id}",
        f"Company ID: {experience.company_id or 'None'}",
        f"Timestamp: {experience.timestamp.isoformat()}",
    ]

    # Environment Context
    lines.append("\n[ENVIRONMENT & INFRASTRUCTURE]")
    if isinstance(experience.environment, dict):
        for k, v in sorted(experience.environment.items()):
            lines.append(f"- {k}: {v}")
    elif experience.environment:
        lines.append(str(experience.environment).strip())
    else:
        lines.append("Not specified")

    # Problem Statement
    lines.append("\n[PROBLEM REPORTED]")
    lines.append(experience.problem.strip())

    # Observed Symptoms
    lines.append("\n[OBSERVED SYMPTOMS]")
    if experience.symptoms:
        for s in experience.symptoms:
            lines.append(f"- {s.strip()}")
    else:
        lines.append("None explicitly recorded")

    # Chronological Troubleshooting Progression with Causal Links
    lines.append("\n[TROUBLESHOOTING & CAUSAL ATTEMPTS]")
    if experience.attempts:
        for idx, attempt in enumerate(experience.attempts, start=1):
            tag = "[ATTEMPT]"
            if attempt.is_failure:
                tag = "[FAILED - DO NOT REPEAT]"
            elif attempt.is_success:
                tag = "[SUCCESS - PROVEN FIX]"

            lines.append(f"{idx}. {tag} Action: {attempt.action.strip()}")
            lines.append(f"   Outcome: {attempt.result.strip()}")
            if attempt.reason:
                prefix = "Why it failed" if attempt.is_failure else ("Why it succeeded" if attempt.is_success else "Reason")
                lines.append(f"   {prefix}: {attempt.reason.strip()}")
    else:
        lines.append("No intermediate troubleshooting steps logged.")

    # Final Resolution & Outcome
    lines.append("\n[FINAL RESOLUTION]")
    lines.append(experience.resolution.strip() if experience.resolution else "Issue remains unresolved")

    lines.append("\n[FINAL OUTCOME & IMPACT]")
    lines.append(experience.outcome.strip() if experience.outcome else "Outcome not measured")

    # Customer Sentiment & Reaction
    lines.append("\n[CUSTOMER REACTION & SENTIMENT]")
    lines.append(f"Reaction: {experience.customer_reaction.strip() if experience.customer_reaction else 'None noted'}")
    lines.append(f"Sentiment: {experience.customer_sentiment.strip() if experience.customer_sentiment else 'Neutral'}")

    # Preferences & Operational Constraints
    lines.append("\n[CUSTOMER PREFERENCES & OPERATIONAL CONSTRAINTS]")
    if experience.preferences:
        for pref in experience.preferences:
            lines.append(f"- {pref.strip()}")
    else:
        lines.append("No explicit preferences logged.")

    return "\n".join(lines)


def get_experience_document_id(experience: SupportExperience) -> str:
    """
    Generate an idempotent, deterministic document ID for an experience.
    Ensures updates to a ticket update the existing document rather than creating duplicates.
    """
    if experience.ticket_id:
        clean_ticket = sanitize_identifier(str(experience.ticket_id))
        return f"meow-experience-ticket-{clean_ticket}"
    clean_exp = sanitize_identifier(str(experience.experience_id))
    return f"meow-experience-{clean_exp}"


class ExperienceMemoryService:
    """
    Domain-level service that manages support experiences and customer preferences
    in Hindsight memory banks.
    Acts as an intelligent experience layer above raw Hindsight operations.
    """

    def __init__(
        self,
        hindsight_service: Optional[HindsightMemoryService] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._hindsight = hindsight_service or HindsightMemoryService(self._settings)

    @property
    def hindsight(self) -> HindsightMemoryService:
        return self._hindsight

    @property
    def is_enabled(self) -> bool:
        return self._hindsight.is_enabled

    def close(self) -> None:
        """Close underlying Hindsight client connections synchronously."""
        if hasattr(self._hindsight, "close"):
            self._hindsight.close()

    async def aclose(self) -> None:
        """Clean up underlying Hindsight client connections asynchronously."""
        if hasattr(self._hindsight, "aclose"):
            await self._hindsight.aclose()

    def __enter__(self) -> ExperienceMemoryService:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    async def __aenter__(self) -> ExperienceMemoryService:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def aretain_experience(
        self,
        experience: SupportExperience,
        target_bank: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Retain a complete, structured SupportExperience into the customer's Hindsight memory bank.
        """
        bank_id = target_bank or get_customer_bank_id(experience.customer_id)
        narrative = format_experience_narrative(experience)
        doc_id = get_experience_document_id(experience)

        context = f"Support experience report for customer {experience.customer_id}"
        if experience.ticket_id:
            context += f", ticket {experience.ticket_id}"

        metadata = {
            "customer_id": str(experience.customer_id),
            "experience_id": str(experience.experience_id),
            "ticket_id": str(experience.ticket_id or ""),
            "company_id": str(experience.company_id or ""),
            "memory_type": "support_experience",
            "has_failed_attempts": "true" if experience.has_failed_attempts else "false",
            "has_successful_attempts": "true" if experience.has_successful_attempts else "false",
            "is_resolved": "true" if experience.is_resolved else "false",
        }

        tags = ["experience", "support"]
        if experience.is_resolved:
            tags.append("resolved")
        else:
            tags.append("unresolved")
        if experience.has_failed_attempts:
            tags.append("has_failures")

        logger.info(
            "Retaining support experience %s for customer %s in bank %s (doc: %s)",
            experience.experience_id,
            experience.customer_id,
            bank_id,
            doc_id,
        )

        res = await self._hindsight.aretain(
            bank_id=bank_id,
            content=narrative,
            context=context,
            metadata=metadata,
            tags=tags,
            document_id=doc_id,
        )

        return {
            "status": "ok",
            "bank_id": bank_id,
            "document_id": doc_id,
            "experience_id": experience.experience_id,
            "raw_response": res.get("response"),
        }

    def retain_experience(
        self,
        experience: SupportExperience,
        target_bank: Optional[str] = None,
    ) -> dict[str, Any]:
        """Synchronous wrapper for aretain_experience."""
        bank_id = target_bank or get_customer_bank_id(experience.customer_id)
        narrative = format_experience_narrative(experience)
        doc_id = get_experience_document_id(experience)

        context = f"Support experience report for customer {experience.customer_id}"
        if experience.ticket_id:
            context += f", ticket {experience.ticket_id}"

        metadata = {
            "customer_id": str(experience.customer_id),
            "experience_id": str(experience.experience_id),
            "ticket_id": str(experience.ticket_id or ""),
            "company_id": str(experience.company_id or ""),
            "memory_type": "support_experience",
            "has_failed_attempts": "true" if experience.has_failed_attempts else "false",
            "has_successful_attempts": "true" if experience.has_successful_attempts else "false",
            "is_resolved": "true" if experience.is_resolved else "false",
        }

        tags = ["experience", "support"]
        if experience.is_resolved:
            tags.append("resolved")
        else:
            tags.append("unresolved")
        if experience.has_failed_attempts:
            tags.append("has_failures")

        res = self._hindsight.retain(
            bank_id=bank_id,
            content=narrative,
            context=context,
            metadata=metadata,
            tags=tags,
            document_id=doc_id,
        )

        return {
            "status": "ok",
            "bank_id": bank_id,
            "document_id": doc_id,
            "experience_id": experience.experience_id,
            "raw_response": res.get("response"),
        }

    async def arecall_relevant_experiences(
        self,
        customer_id: str | int,
        query: str,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[list[str]] = None,
    ) -> ExperienceRecallResponse:
        """
        Recall relevant past support experiences and troubleshooting attempts for a customer.
        """
        bank_id = get_customer_bank_id(customer_id)
        raw_recall = await self._hindsight.arecall(
            bank_id=bank_id,
            query=query,
            max_tokens=max_tokens,
            budget=budget,
            tags=tags,
        )

        raw_items = raw_recall.get("results") or []
        items = [
            ExperienceRecallItem(
                text=item.get("text", ""),
                score=item.get("score"),
                metadata=item.get("metadata"),
            )
            for item in raw_items
        ]

        return ExperienceRecallResponse(
            customer_id=str(customer_id),
            bank_id=bank_id,
            query=query,
            summary_text=raw_recall.get("text", ""),
            experiences=items,
            raw_response=raw_recall.get("raw"),
        )

    def recall_relevant_experiences(
        self,
        customer_id: str | int,
        query: str,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[list[str]] = None,
    ) -> ExperienceRecallResponse:
        """Synchronous wrapper for arecall_relevant_experiences."""
        bank_id = get_customer_bank_id(customer_id)
        raw_recall = self._hindsight.recall(
            bank_id=bank_id,
            query=query,
            max_tokens=max_tokens,
            budget=budget,
            tags=tags,
        )

        raw_items = []
        raw_obj = raw_recall.get("raw")
        if hasattr(raw_obj, "results") and raw_obj.results:
            for item in raw_obj.results:
                raw_items.append(
                    ExperienceRecallItem(
                        text=getattr(item, "text", str(item)),
                        score=getattr(item, "score", None),
                        metadata=getattr(item, "metadata", None),
                    )
                )

        summary_text = ""
        if hasattr(raw_obj, "to_prompt_string") and callable(raw_obj.to_prompt_string):
            summary_text = str(raw_obj.to_prompt_string())
        elif hasattr(raw_obj, "text"):
            summary_text = str(getattr(raw_obj, "text", ""))

        return ExperienceRecallResponse(
            customer_id=str(customer_id),
            bank_id=bank_id,
            query=query,
            summary_text=summary_text,
            experiences=raw_items,
            raw_response=raw_obj,
        )

    def recall_customer_evidence(
        self,
        customer_id: str | int,
        query: str,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[list[str]] = None,
    ) -> list[HindsightEvidence]:
        """
        Recalls and classifies structured HindsightEvidence items for a customer.
        Safe for use inside synchronous execution paths.
        """
        resp = self.recall_relevant_experiences(
            customer_id=customer_id,
            query=query,
            max_tokens=max_tokens,
            budget=budget,
            tags=tags,
        )
        evidence_list: list[HindsightEvidence] = []
        for item in resp.experiences:
            ev = HindsightEvidence.from_raw_item(
                text=item.text,
                score=item.score,
                metadata=item.metadata,
            )
            evidence_list.append(ev)

        if resp.summary_text and not evidence_list:
            evidence_list.append(
                HindsightEvidence.from_raw_item(
                    text=resp.summary_text,
                    metadata={"source": "hindsight_summary"},
                )
            )
        return evidence_list

    async def arecall_customer_evidence(
        self,
        customer_id: str | int,
        query: str,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[list[str]] = None,
    ) -> list[HindsightEvidence]:
        """
        Asynchronously recalls and classifies structured HindsightEvidence items for a customer.
        """
        resp = await self.arecall_relevant_experiences(
            customer_id=customer_id,
            query=query,
            max_tokens=max_tokens,
            budget=budget,
            tags=tags,
        )
        evidence_list: list[HindsightEvidence] = []
        for item in resp.experiences:
            ev = HindsightEvidence.from_raw_item(
                text=item.text,
                score=item.score,
                metadata=item.metadata,
            )
            evidence_list.append(ev)

        if resp.summary_text and not evidence_list:
            evidence_list.append(
                HindsightEvidence.from_raw_item(
                    text=resp.summary_text,
                    metadata={"source": "hindsight_summary"},
                )
            )
        return evidence_list

    async def areflect_on_customer_experience(
        self,
        customer_id: str | int,
        question: str,
        context: Optional[str] = None,
        budget: str = "low",
    ) -> ExperienceReflectionResponse:
        """
        Synthesize cross-experience reflective insights for a customer.
        Useful for answering questions like:
        - "What troubleshooting steps previously failed for this customer?"
        - "What recurring infrastructure issues does this customer face?"
        - "What are this customer's operational constraints and preferences?"
        """
        bank_id = get_customer_bank_id(customer_id)
        raw_reflect = await self._hindsight.areflect(
            bank_id=bank_id,
            query=question,
            context=context,
            budget=budget,
        )

        return ExperienceReflectionResponse(
            customer_id=str(customer_id),
            bank_id=bank_id,
            question=question,
            insights=str(raw_reflect.get("response", "")),
            raw_response=raw_reflect.get("raw"),
        )

    def reflect_on_customer_experience(
        self,
        customer_id: str | int,
        question: str,
        context: Optional[str] = None,
        budget: str = "low",
    ) -> ExperienceReflectionResponse:
        """Synchronous wrapper for areflect_on_customer_experience."""
        bank_id = get_customer_bank_id(customer_id)
        raw_reflect = self._hindsight.reflect(
            bank_id=bank_id,
            query=question,
            context=context,
            budget=budget,
        )
        raw_obj = raw_reflect.get("raw")
        insights = ""
        if hasattr(raw_obj, "response"):
            insights = str(getattr(raw_obj, "response", ""))
        elif hasattr(raw_obj, "text"):
            insights = str(getattr(raw_obj, "text", ""))

        return ExperienceReflectionResponse(
            customer_id=str(customer_id),
            bank_id=bank_id,
            question=question,
            insights=insights,
            raw_response=raw_obj,
        )

    async def aretain_preference(
        self,
        customer_id: str | int,
        preference: str,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Retain a specific operational or communication preference for a customer.
        """
        if not preference or not preference.strip():
            raise ValueError("Preference cannot be empty")

        clean_customer = sanitize_identifier(customer_id)
        bank_id = get_customer_bank_id(clean_customer)
        pref_slug = sanitize_identifier(preference[:30])
        doc_id = f"meow-pref-{clean_customer}-{pref_slug}"

        narrative = (
            f"=== CUSTOMER PREFERENCE & OPERATIONAL CONSTRAINT ===\n"
            f"Customer ID: {clean_customer}\n"
            f"Preference / Constraint:\n"
            f"{preference.strip()}\n"
        )

        metadata = {
            "customer_id": str(clean_customer),
            "memory_type": "customer_preference",
        }

        res = await self._hindsight.aretain(
            bank_id=bank_id,
            content=narrative,
            context=context or f"Customer preference update for {clean_customer}",
            metadata=metadata,
            tags=["preference", "customer_profile"],
            document_id=doc_id,
        )

        return {
            "status": "ok",
            "bank_id": bank_id,
            "document_id": doc_id,
            "raw_response": res.get("response"),
        }

    def retain_preference(
        self,
        customer_id: str | int,
        preference: str,
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Synchronous wrapper for aretain_preference."""
        if not preference or not preference.strip():
            raise ValueError("Preference cannot be empty")

        clean_customer = sanitize_identifier(customer_id)
        bank_id = get_customer_bank_id(clean_customer)
        pref_slug = sanitize_identifier(preference[:30])
        doc_id = f"meow-pref-{clean_customer}-{pref_slug}"

        narrative = (
            f"=== CUSTOMER PREFERENCE & OPERATIONAL CONSTRAINT ===\n"
            f"Customer ID: {clean_customer}\n"
            f"Preference / Constraint:\n"
            f"{preference.strip()}\n"
        )

        metadata = {
            "customer_id": str(clean_customer),
            "memory_type": "customer_preference",
        }

        res = self._hindsight.retain(
            bank_id=bank_id,
            content=narrative,
            context=context or f"Customer preference update for {clean_customer}",
            metadata=metadata,
            tags=["preference", "customer_profile"],
            document_id=doc_id,
        )

        return {
            "status": "ok",
            "bank_id": bank_id,
            "document_id": doc_id,
            "raw_response": res.get("response"),
        }
