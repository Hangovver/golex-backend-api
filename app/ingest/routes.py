from fastapi import APIRouter, Query
from .pipeline import ingest_fixtures_by_date, ingest_live_fixtures

router = APIRouter()

@router.post("/fixtures/by-date")
def fixtures_by_date(date: str = Query(..., example="2025-10-26")):
    return ingest_fixtures_by_date(date)

@router.post("/fixtures/live")
def fixtures_live():
    return ingest_live_fixtures()
