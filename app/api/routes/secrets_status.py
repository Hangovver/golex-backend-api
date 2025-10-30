from fastapi import APIRouter
from ..config import settings

router = APIRouter(prefix="/admin/secrets", tags=["admin.secrets"])

@router.get("/status")
def status():
    return {
        "api_football_base_url": str(settings.API_FOOTBALL_BASE_URL),
        "api_football_key_configured": bool(settings.API_FOOTBALL_KEY),
        "db_url_configured": bool(settings.DB_URL),
        "redis_url_configured": bool(settings.REDIS_URL),
    }
