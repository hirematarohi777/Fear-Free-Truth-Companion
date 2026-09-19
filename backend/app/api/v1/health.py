from fastapi import APIRouter, status, Response
from app.db.mongo import DatabaseManager
from app.services.llm.client import ollama_service


router = APIRouter(prefix="/health", tags=["Health & Readiness"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe():
    """Liveness probe: verifies process is alive."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe(response: Response):
    """
    Readiness probe: verifies critical dependencies without leaking credentials or network details.
    """
    mongo_ready = False
    ollama_ready = False

    # Check MongoDB
    if DatabaseManager.client:
        try:
            await DatabaseManager.client.admin.command('ping')
            mongo_ready = True
        except Exception:
            mongo_ready = False

    # Check Ollama
    ollama_ready = await ollama_service.is_available()

    all_ready = mongo_ready  # Ollama is optional for startup readiness (fallback to deterministic mode)

    if not all_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ready else "degraded",
        "database": "available" if mongo_ready else "unavailable",
        "local_llm": "available" if ollama_ready else "unavailable"
    }
