"""
Metrics Routes - EXACT COPY from SofaScore backend
Source: MetricsController.java
Features: Prometheus metrics export, Text/plain format v0.0.4, Metrics service integration
"""
from fastapi import APIRouter, Response
from ...services import metrics as M

router = APIRouter(tags=["metrics"])

@router.get("/metrics")
async def metrics():
    body = M.render_prom()
    return Response(content=body, media_type="text/plain; version=0.0.4")
