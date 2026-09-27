from typing import Any
from fastapi import APIRouter, Depends

from customer_support_agent.api.dependencies import get_hindsight_service
from customer_support_agent.integrations.hindsight import HindsightMemoryService

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/hindsight")
async def health_hindsight(
    hindsight_service: HindsightMemoryService = Depends(get_hindsight_service),
) -> dict[str, Any]:
    return await hindsight_service.health_check()

