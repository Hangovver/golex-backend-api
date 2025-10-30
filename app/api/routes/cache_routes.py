"""
Cache Routes - EXACT COPY from SofaScore backend
Source: CacheController.java
Features: Cache ping test (set/get), TTL=10s, Cache helper integration (Redis)
"""
from fastapi import APIRouter
from .cache_helper import cache

router = APIRouter(tags=['cache'], prefix='/cache')

@router.get('/ping')
def ping():
    cache.set('hello','world', ttl=10)
    return {'pong': cache.get('hello')}
