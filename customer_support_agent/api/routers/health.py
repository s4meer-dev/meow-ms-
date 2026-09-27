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
            "connected_to_production": bool(getattr(settings, "meow_hindsight_enabled", False)),
            "shadow_mode": bool(getattr(settings, "meow_hindsight_shadow_mode", True)),
            "context_injection": bool(getattr(settings, "meow_hindsight_context_injection", False)),
            "connected_to_ui": True,
            "status": "active_shadow" if getattr(settings, "meow_hindsight_shadow_mode", True) else "authoritative_candidate",
        },
    }


@router.get("/debug/memory-evaluation")
async def debug_memory_evaluation(
    customer_email: str = "demo@example.com",
    query: str = "timeout error",
    company: str | None = None,
    settings: Settings = Depends(get_settings_dep),
) -> dict[str, Any]:
    """Safe diagnostic endpoint to test and observe dual-memory evaluation without exposing secrets."""
    from customer_support_agent.schemas.experience import evaluate_memory_overlap, HindsightEvidence

    clean_email = customer_email.strip().lower()
    mem0_hits: list[dict[str, Any]] = []
    mem0_error: str | None = None
    try:
        from customer_support_agent.integrations.memory.mem0_store import CustomerMemoryStore
        mem0_store = CustomerMemoryStore(settings=settings)
        mem0_hits = mem0_store.search(query=query, user_id=clean_email, limit=5)
    except Exception as exc:
        mem0_error = f"Mem0 search skipped or unavailable: {exc}"

    hindsight_hits: list[HindsightEvidence] = []
    hindsight_error: str | None = None
    if getattr(settings, "hindsight_enabled", False) and getattr(settings, "meow_hindsight_enabled", False):
        try:
            from customer_support_agent.integrations.hindsight.experience import ExperienceMemoryService
            exp_service = ExperienceMemoryService(settings=settings)
            hindsight_hits = await exp_service.arecall_customer_evidence(
                customer_id=clean_email,
                query=query,
                budget="mid",
            )
        except Exception as exc:
            hindsight_error = f"Hindsight shadow recall unavailable: {exc}"
    else:
        hindsight_error = "Hindsight is disabled in settings"

    error_msg = "; ".join(filter(None, [mem0_error, hindsight_error])) or None
    evaluation = evaluate_memory_overlap(
        mem0_results=mem0_hits,
        hindsight_results=hindsight_hits,
        ticket_id="debug-probe",
        customer_id=clean_email,
        error=error_msg,
    )

    return {
        "status": "ok",
        "customer_email": clean_email,
        "query": query,
        "company": company,
        "mem0_count": len(mem0_hits),
        "hindsight_count": len(hindsight_hits),
        "evaluation": evaluation.model_dump(),
        "shadow_mode": getattr(settings, "meow_hindsight_shadow_mode", True),
        "context_injection": getattr(settings, "meow_hindsight_context_injection", False),
    }



