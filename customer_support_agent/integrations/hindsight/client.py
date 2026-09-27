from __future__ import annotations

import logging
from typing import Optional

from hindsight_client import Hindsight

from customer_support_agent.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def create_hindsight_client(settings: Optional[Settings] = None) -> Hindsight:
    """
    Create a new Hindsight client configured from settings.
    Initialization is purely local and does not make network calls.
    """
    resolved_settings = settings or get_settings()
    base_url = resolved_settings.hindsight_api_url.rstrip("/")
    api_key = resolved_settings.hindsight_api_key or None
    timeout = resolved_settings.hindsight_timeout

    logger.debug("Configuring Hindsight client for URL: %s", base_url)

    return Hindsight(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        user_agent="meow-customer-support-agent/0.1.0",
        max_attempts=3,
    )
