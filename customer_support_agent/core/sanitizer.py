"""
Privacy and secret sanitization utilities.
Ensures sensitive tokens, API keys, and authorization credentials never leak to UI or logs.
"""

from __future__ import annotations

import re
from typing import Any


def sanitize_obj_for_display(obj: Any) -> Any:
    """Ensure no API keys, tokens, or authorization headers leak to UI display."""
    if isinstance(obj, dict):
        sanitized: dict[str, Any] = {}
        for k, v in obj.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ("key", "token", "auth", "secret", "password", "credential")):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_obj_for_display(v)
        return sanitized
    elif isinstance(obj, list):
        return [sanitize_obj_for_display(item) for item in obj]
    elif isinstance(obj, str):
        if any(p in obj for p in ("gsk_", "Bearer ", "sk-", "AIza")):
            return re.sub(
                r"(gsk_[a-zA-Z0-9_-]+|Bearer\s+[a-zA-Z0-9_.-]+|sk-[a-zA-Z0-9_-]+|AIza[a-zA-Z0-9_-]+)",
                "[REDACTED_SECRET]",
                obj,
            )
        return obj
    return obj
