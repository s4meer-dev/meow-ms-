from typing import Any
from fastapi import APIRouter, Depends

from customer_support_agent.api.dependencies import get_hindsight_service, get_settings_dep
from customer_support_agent.core.settings import Settings
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


@router.get("/debug/memory-flow")
async def debug_memory_flow(
    settings: Settings = Depends(get_settings_dep),
    hindsight_service: HindsightMemoryService = Depends(get_hindsight_service),
) -> dict[str, Any]:
    """Safe development diagnostic endpoint showing component health and pipeline routing."""
    db_available = False
    try:
        from customer_support_agent.repositories.sqlite.base import connect
        with connect() as conn:
            conn.execute("SELECT 1")
            db_available = True
    except Exception:
        db_available = False

    mem0_available = False
    try:
        from mem0 import Memory
        mem0_available = Memory is not None
    except Exception:
        mem0_available = False

    chromadb_available = False
    try:
        import chromadb  # noqa: F401
        chromadb_available = True
    except Exception:
        chromadb_available = False

    hindsight_health = await hindsight_service.health_check()
    hindsight_available = bool(hindsight_health.get("available", False))

    return {
        "status": "ok",
        "database_available": db_available,
        "mem0_available": mem0_available,
        "chromadb_available": chromadb_available,
        "hindsight_available": hindsight_available,
        "active_production_flow": {
            "draft_generation": "SupportCopilot (LangChain + ChatGroq)",
            "customer_memory": "Mem0 (ChromaDB Vector Store)",
            "knowledge_rag": "ChromaDB RAG (Markdown Documents)",
            "connected": True,
        },
        "shadow_experience_flow": {
            "experience_memory": "ExperienceMemoryService (Hindsight Isolated Banks)",
            "connected_to_production": False,
            "connected_to_ui": False,
            "status": "isolated_shadow",
        },
    }


