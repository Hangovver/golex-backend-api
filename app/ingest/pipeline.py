import json, logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.session import SessionLocal
from ..providers.client import ApiFootballClient
from ..ingest.mappers import map_fixture
from ..etl.helpers import upsert_fixture
from ..metrics.quality import Quality

log = logging.getLogger("ingest")

client = ApiFootballClient()

def save_raw(session: Session, provider: str, endpoint: str, payload: Dict[str, Any], key: str|None=None):
    session.execute(
        text("INSERT INTO raw_ingest(provider, endpoint, key, payload) VALUES (:p,:e,:k,CAST(:j AS JSONB))"),
        {"p": provider, "e": endpoint, "k": key, "j": json.dumps(payload)},
    )

def ingest_fixtures_by_date(date_str: str) -> Dict[str, Any]:
    """P018: fixtures ingestion for a given date."""
    endpoint = "/fixtures"
    params = {"date": date_str}
    data = client.get(endpoint, params=params)

    inserted = 0
    with SessionLocal() as session:
        save_raw(session, "api-football", endpoint, data, key=date_str)
        for item in data.get("response", []):
            mapped = map_fixture(item)
            upsert_fixture(session, mapped)
            inserted += 1
        session.commit()
    Quality.record("fixtures_by_date", count=len(data.get("response", [])), inserted=inserted)
    return {"fetched": len(data.get("response", [])), "upserted": inserted}

def ingest_live_fixtures() -> Dict[str, Any]:
    endpoint = "/fixtures"
    params = {"live": "all"}
    data = client.get(endpoint, params=params)
    inserted = 0
    with SessionLocal() as session:
        save_raw(session, "api-football", endpoint, data, key="live")
        for item in data.get("response", []):
            mapped = map_fixture(item)
            upsert_fixture(session, mapped)
            inserted += 1
        session.commit()
    Quality.record("fixtures_live", count=len(data.get("response", [])), upserted=inserted)
    return {"fetched": len(data.get("response", [])), "upserted": inserted}
