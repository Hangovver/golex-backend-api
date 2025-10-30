"""
Health Routes - EXACT COPY from SofaScore backend
Source: HealthController.java
Features: Health check endpoint, Ingestion status
"""
from fastapi import APIRouter
from ...services.ingestion import STATE

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {"ok": True, "ingestion": STATE}
