from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional

from hindsight_client import Hindsight

from customer_support_agent.core.settings import Settings, get_settings
from customer_support_agent.integrations.hindsight.client import create_hindsight_client

logger = logging.getLogger(__name__)


class HindsightMemoryService:
    """
    High-level, async-first application service wrapping the official Hindsight SDK.
    Provides isolated customer memory retention, recall, and reflection.
    Designed with graceful degradation so Hindsight unavailability never crashes MEOW.
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        client: Optional[Hindsight] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client or create_hindsight_client(self._settings)

    @property
    def client(self) -> Hindsight:
        return self._client

    @property
    def is_enabled(self) -> bool:
        return bool(self._settings.hindsight_enabled)

    def _sanitize_error(self, message: str) -> str:
        """Sanitize error messages to ensure API keys are never leaked."""
        sanitized = message
        if self._settings.hindsight_api_key:
            sanitized = sanitized.replace(self._settings.hindsight_api_key, "[REDACTED_HINDSIGHT_KEY]")
        if self._settings.groq_api_key:
            sanitized = sanitized.replace(self._settings.groq_api_key, "[REDACTED_GROQ_KEY]")
        if self._settings.google_api_key:
            sanitized = sanitized.replace(self._settings.google_api_key, "[REDACTED_GOOGLE_KEY]")
        if self._settings.openai_api_key:
            sanitized = sanitized.replace(self._settings.openai_api_key, "[REDACTED_OPENAI_KEY]")
        return sanitized

    def close(self) -> None:
        """Clean up underlying aiohttp connection pools synchronously."""
        try:
            if hasattr(self._client, "close"):
                self._client.close()
            elif hasattr(self._client, "aclose"):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._client.aclose())
                except RuntimeError:
                    asyncio.run(self._client.aclose())
        except Exception as exc:
            logger.debug("Error while closing Hindsight client: %s", exc)

    async def aclose(self) -> None:
        """Clean up underlying aiohttp connection pools asynchronously."""
        try:
            if hasattr(self._client, "aclose"):
                await self._client.aclose()
            elif hasattr(self._client, "close"):
                self._client.close()
        except Exception as exc:
            logger.debug("Error while closing Hindsight client: %s", exc)

    def __enter__(self) -> HindsightMemoryService:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    async def __aenter__(self) -> HindsightMemoryService:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def health_check(self) -> dict[str, Any]:
        """
        Perform a non-destructive readiness and connectivity check against Hindsight.
        Returns a structured dictionary indicating availability.
        """
        base_url = self._settings.hindsight_api_url
        try:
            if hasattr(self._client, "aget_version"):
                version_resp = await self._client.aget_version()
                version_str = getattr(version_resp, "version", str(version_resp))
                return {
                    "status": "ok",
                    "available": True,
                    "url": base_url,
                    "version": version_str,
                }
            return {
                "status": "ok",
                "available": True,
                "url": base_url,
                "version": "unknown",
            }
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            logger.warning("Hindsight health check failed for %s: %s", base_url, clean_err)
            return {
                "status": "unavailable",
                "available": False,
                "url": base_url,
                "error": clean_err,
            }

    async def _execute_with_retry(self, coroutine_func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute an asynchronous Hindsight SDK call with automated backoff retry on provider rate limits."""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return await coroutine_func(*args, **kwargs)
            except Exception as exc:
                err_str = str(exc)
                is_rate_limit = (
                    "429" in err_str
                    or "rate_limit_exceeded" in err_str
                    or "rate limit reached" in err_str.lower()
                    or "provider quota exhausted" in err_str.lower()
                )
                is_daily_quota = (
                    "provider quota exhausted" in err_str.lower()
                    or "(tpd)" in err_str.lower()
                    or "tokens per day" in err_str.lower()
                    or bool(re.search(r"try again in \d+(?:\.\d+)?(?:h|m)", err_str, re.IGNORECASE))
                )
                if is_rate_limit and not is_daily_quota and attempt < max_retries - 1:
                    match = re.search(r"try again in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                    if match:
                        wait_sec = max(float(match.group(1)) + 3.0, 12.0)
                    else:
                        wait_sec = 10.0 * (attempt + 1)
                    wait_sec = min(wait_sec, 45.0)
                    logger.warning(
                        "Hindsight rate limit encountered. Backing off for %.1fs before retry (%d/%d)...",
                        wait_sec,
                        attempt + 1,
                        max_retries,
                    )
                    await asyncio.sleep(wait_sec)
                    continue
                raise

    async def aretain(
        self,
        bank_id: str,
        content: str | list[dict[str, Any]],
        context: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        tags: Optional[list[str]] = None,
        document_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Asynchronously retain experience or resolution knowledge into a specific bank.
        """
        if not bank_id or not bank_id.strip():
            raise ValueError("bank_id cannot be empty")
        if not content:
            raise ValueError("content cannot be empty")

        try:
            response = await self._execute_with_retry(
                self._client.aretain,
                bank_id=bank_id.strip(),
                content=content,
                context=context,
                metadata=metadata,
                tags=tags,
                document_id=document_id,
            )
            return {
                "status": "ok",
                "bank_id": bank_id,
                "response": response,
            }
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            logger.error("Hindsight aretain failed on bank '%s': %s", bank_id, clean_err)
            raise RuntimeError(f"Hindsight aretain failed: {clean_err}") from exc

    async def arecall(
        self,
        bank_id: str,
        query: str,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Asynchronously recall relevant experiential memories for a query from a specific bank.
        """
        if not bank_id or not bank_id.strip():
            raise ValueError("bank_id cannot be empty")
        if not query or not query.strip():
            raise ValueError("query cannot be empty")

        try:
            response = await self._execute_with_retry(
                self._client.arecall,
                bank_id=bank_id.strip(),
                query=query.strip(),
                max_tokens=max_tokens,
                budget=budget,
                tags=tags,
            )

            # Extract formatted prompt text or items if available
            text_representation = ""
            if hasattr(response, "to_prompt_string"):
                text_representation = response.to_prompt_string()
            elif hasattr(response, "text"):
                text_representation = getattr(response, "text", "")
            else:
                text_representation = str(response)

            results_list = []
            if hasattr(response, "results") and response.results:
                for item in response.results:
                    results_list.append(
                        {
                            "text": getattr(item, "text", str(item)),
                            "score": getattr(item, "score", None),
                            "metadata": getattr(item, "metadata", None),
                        }
                    )

            return {
                "status": "ok",
                "bank_id": bank_id,
                "query": query,
                "text": text_representation,
                "results": results_list,
                "raw": response,
            }
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            logger.error("Hindsight arecall failed on bank '%s': %s", bank_id, clean_err)
            raise RuntimeError(f"Hindsight arecall failed: {clean_err}") from exc

    async def areflect(
        self,
        bank_id: str,
        query: str,
        context: Optional[str] = None,
        budget: str = "low",
    ) -> dict[str, Any]:
        """
        Asynchronously synthesize reflective insights from memories in a specific bank.
        """
        if not bank_id or not bank_id.strip():
            raise ValueError("bank_id cannot be empty")
        if not query or not query.strip():
            raise ValueError("query cannot be empty")

        try:
            response = await self._execute_with_retry(
                self._client.areflect,
                bank_id=bank_id.strip(),
                query=query.strip(),
                context=context,
                budget=budget,
            )

            response_text = ""
            if hasattr(response, "response"):
                response_text = getattr(response, "response", "")
            elif hasattr(response, "text"):
                response_text = getattr(response, "text", "")
            else:
                response_text = str(response)

            return {
                "status": "ok",
                "bank_id": bank_id,
                "query": query,
                "response": response_text,
                "raw": response,
            }
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            logger.error("Hindsight areflect failed on bank '%s': %s", bank_id, clean_err)
            raise RuntimeError(f"Hindsight areflect failed: {clean_err}") from exc

    # Synchronous wrappers for scripts, CLI utilities, and synchronous tests
    def retain(
        self,
        bank_id: str,
        content: str | list[dict[str, Any]],
        context: Optional[str] = None,
        metadata: Optional[dict[str, str]] = None,
        tags: Optional[list[str]] = None,
        document_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Synchronous retain wrapper."""
        if not bank_id or not bank_id.strip():
            raise ValueError("bank_id cannot be empty")
        if not content:
            raise ValueError("content cannot be empty")
        try:
            resp = self._client.retain(
                bank_id=bank_id.strip(),
                content=content,
                context=context,
                metadata=metadata,
                tags=tags,
                document_id=document_id,
            )
            return {"status": "ok", "bank_id": bank_id, "response": resp}
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            raise RuntimeError(f"Hindsight retain failed: {clean_err}") from exc

    def recall(
        self,
        bank_id: str,
        query: str,
        max_tokens: int = 4096,
        budget: str = "mid",
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Synchronous recall wrapper."""
        if not bank_id or not bank_id.strip():
            raise ValueError("bank_id cannot be empty")
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        try:
            resp = self._client.recall(
                bank_id=bank_id.strip(),
                query=query.strip(),
                max_tokens=max_tokens,
                budget=budget,
                tags=tags,
            )
            return {"status": "ok", "bank_id": bank_id, "raw": resp}
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            raise RuntimeError(f"Hindsight recall failed: {clean_err}") from exc

    def reflect(
        self,
        bank_id: str,
        query: str,
        context: Optional[str] = None,
        budget: str = "low",
    ) -> dict[str, Any]:
        """Synchronous reflect wrapper."""
        if not bank_id or not bank_id.strip():
            raise ValueError("bank_id cannot be empty")
        if not query or not query.strip():
            raise ValueError("query cannot be empty")
        try:
            resp = self._client.reflect(
                bank_id=bank_id.strip(),
                query=query.strip(),
                context=context,
                budget=budget,
            )
            return {"status": "ok", "bank_id": bank_id, "raw": resp}
        except Exception as exc:
            clean_err = self._sanitize_error(str(exc))
            raise RuntimeError(f"Hindsight reflect failed: {clean_err}") from exc
