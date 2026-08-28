from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "integrations": {
            "openai": settings.has_openai,
            "pinecone": settings.has_pinecone,
            "sqlitecloud": settings.has_sqlitecloud,
        },
    }
