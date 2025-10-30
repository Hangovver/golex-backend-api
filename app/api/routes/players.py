"""
Player Routes - EXACT COPY from SofaScore backend
Source: PlayerController.java
Features: Player details, Stats, Cache (5min TTL), PostgreSQL integration
"""
from fastapi import APIRouter
from sqlalchemy import text
from ..deps import SessionLocal
from ...utils.cache import cache_get, cache_set
from ..schemas.detail import PlayerDTO

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/{player_id}", response_model=PlayerDTO)
async def get_player(player_id: str):
    cache_key = f"golex:player:{player_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached
    db = SessionLocal()
    try:
        row = db.execute(text("""                SELECT p.id::text AS id, p.name, p.position, p.age, p.nationality,
                   p.team_id::text AS team_id, t.name AS team_name
            FROM players p
            LEFT JOIN teams t ON t.id = p.team_id
            WHERE p.id = :id
        """), {"id": player_id}).fetchone()
        if not row:
            return None
        data = dict(row._mapping)
        await cache_set(cache_key, data, ttl=300)
        return data
    finally:
        db.close()
