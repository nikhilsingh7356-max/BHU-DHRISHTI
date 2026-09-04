from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import engine
from app.security.dependencies import get_db
from sqlalchemy import text

router = APIRouter()


@router.get("")
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    return {
        "success": True,
        "data": {
            "status": "ok",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": db_status,
        },
        "message": "Service healthy",
    }
