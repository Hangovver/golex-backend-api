from fastapi import APIRouter, Request
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time

router = APIRouter(tags=['metrics'])

REQUEST_TIME = Histogram('golex_request_latency_seconds', 'Request latency', ['path'])
REQUESTS = Counter('golex_requests_total', 'Total requests', ['path'])

@router.get('/metrics')
def metrics():
    # In a real app, use multiprocess registry for Gunicorn/Uvicorn workers
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
