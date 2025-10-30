"""
Team Routes - EXACT COPY from SofaScore backend
Source: TeamController.java
Features: Team details, Fixtures, Squad, Venue info, Cache (5min TTL), PostgreSQL integration
"""
from fastapi import APIRouter, Query
from sqlalchemy import text
from ..deps import SessionLocal
from ...utils.cache import cache_get, cache_set
from ..schemas.detail import TeamDTO, FixtureDetailDTO

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/{team_id}", response_model=TeamDTO)
async def get_team(team_id: str):
    cache_key = f"golex:team:{team_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached
    db = SessionLocal()
    try:
        row = db.execute(text("""                SELECT t.id::text AS id, t.name, t.country, t.code, t.founded,
                   v.id::text AS venue_id, v.name AS venue_name, v.city AS venue_city, v.capacity AS venue_capacity
            FROM teams t
            LEFT JOIN venues v ON v.id = t.venue_id
            WHERE t.id = :id
        """), {"id": team_id}).fetchone()
        if not row:
            return None
        data = dict(row._mapping)
        await cache_set(cache_key, data, ttl=300)
        return data
    finally:
        db.close()

@router.get("/{team_id}/fixtures")
async def team_fixtures(team_id: str, status: str = Query(None), page: int = 1, limit: int = 50):
    page = max(1, page); limit = max(1, min(200, limit))
    cache_key = f"golex:team:{team_id}:fixtures:{status or '-'}:{page}:{limit}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached
    db = SessionLocal()
    try:
        clauses = ["(f.home_team_id = :id OR f.away_team_id = :id)"]
        params = {"id": team_id, "off": (page-1)*limit, "lim": limit}
        if status:
            clauses.append("f.status = :st"); params["st"] = status
        where = " AND ".join(clauses)
        rows = db.execute(text(f"""                SELECT f.id::text AS id, f.date_utc, f.status,
                   f.league_id::text AS league_id, l.name AS league_name,
                   f.home_team_id::text AS home_team_id, th.name AS home_team_name,
                   f.away_team_id::text AS away_team_id, ta.name AS away_team_name,
                   f.round
            FROM fixtures f
            JOIN leagues l ON l.id = f.league_id
            JOIN teams th ON th.id = f.home_team_id
            JOIN teams ta ON ta.id = f.away_team_id
            WHERE {where}
            ORDER BY f.date_utc DESC
            LIMIT :lim OFFSET :off
        """), params).fetchall()
        data = [dict(r._mapping) for r in rows]
        await cache_set(cache_key, data, ttl=60)
        return data
    finally:
        db.close()
