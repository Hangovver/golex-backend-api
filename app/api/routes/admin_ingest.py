from fastapi import APIRouter, Query
from ..jobs.ingestion import ingest_fixtures_by_date, ingest_events_for_fixture, ingest_lineups_for_fixture, ingest_standings
router = APIRouter(prefix="/admin/ingest", tags=["admin.ingest"])

@router.post("/fixtures")
async def fixtures(date: str = Query(..., description="YYYY-MM-DD")):
    count = await ingest_fixtures_by_date(date)
    return {"ok": True, "count": count}

@router.post("/events")
async def events(fixture_id: str):
    count = await ingest_events_for_fixture(fixture_id)
    return {"ok": True, "count": count}

@router.post("/lineups")
async def lineups(fixture_id: str):
    count = await ingest_lineups_for_fixture(fixture_id)
    return {"ok": True, "count": count}

@router.post("/standings")
async def standings(league_id: str, season_year: int):
    count = await ingest_standings(league_id, season_year)
    return {"ok": True, "count": count}
