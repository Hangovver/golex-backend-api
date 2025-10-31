import asyncio, json, time, datetime as dt
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db.session import SessionLocal
from ..services.apifootball import ApiFootball
from ..etl.raw import save_raw
from ..etl.staging import stage_fixtures, stage_events, stage_lineups, stage_standings
from ..etl.clean import upsert_fixtures as _up_fx, upsert_events as _up_ev, upsert_lineups as _up_ln
from ..mappers import apifootball as M
from ..repositories import upserts as U
from ..utils.time_norm import parse_to_utc, season_year_for_date
from ..utils.redis_pool import get_redis

async def ingest_fixtures_by_date(date_str: str):
    api = ApiFootball()
    data = await api.get("fixtures", params={"date": date_str}); save_raw(SessionLocal(), "api-football", "fixtures", {"date": date_str}, data); staged = stage_fixtures(data)
    resp = data.get("response", [])
    db: Session = SessionLocal()
    try:
        for item in resp:
            U.upsert_league(db, M.league(item.get("league", {})))
            for side in ("home", "away"):
                tm = (item.get("teams") or {}).get(side)
                if tm: U.upsert_team(db, M.team({"team": tm, "venue": item.get("fixture", {}).get("venue")}))
            U.upsert_fixture(db, M.fixture(item))
        return len(resp)
    finally:
        db.close()

async def ingest_events_for_fixture(fixture_id: str):
    api = ApiFootball()
    data = await api.get("fixtures/events", params={"fixture": fixture_id}); save_raw(SessionLocal(), "api-football", "fixtures/events", {"fixture": fixture_id}, data); staged = stage_events(data, fixture_id)
    resp = data.get("response", [])
    db: Session = SessionLocal()
    try:
        count = 0
        for e in resp:
            U.upsert_event(db, M.event(e))
            count += 1
        return count
    finally:
        db.close()

async def ingest_lineups_for_fixture(fixture_id: str):
    api = ApiFootball()
    data = await api.get("fixtures/lineups", params={"fixture": fixture_id}); save_raw(SessionLocal(), "api-football", "fixtures/lineups", {"fixture": fixture_id}, data); staged = stage_lineups(data, fixture_id)
    resp = data.get("response", [])
    db: Session = SessionLocal()
    try:
        for row in resp:
            U.upsert_lineup(db, M.lineup(row))
        return len(resp)
    finally:
        db.close()

async def ingest_standings(league_id: str, season_year: int):
    api = ApiFootball()
    data = await api.get("standings", params={"league": league_id, "season": season_year}); save_raw(SessionLocal(), "api-football", "standings", {"league": league_id, "season": season_year}, data)
    resp = data.get("response", [])
    if not resp: return 0
    table = resp[0].get("league", {}).get("standings", [[]])[0]
    db: Session = SessionLocal()
    try:
        league_uuid = U.upsert_league(db, M.league(resp[0].get("league", {})))
        season_row = U.upsert_season(db, league_uuid, season_year)
        for row in table:
            U.upsert_team(db, M.team({"team": row.get("team")}))
            U.upsert_standing(db, league_uuid, season_row, M.standing_row(row))
        return len(table)
    finally:
        db.close()

async def poll_live_and_push():
    from ..config import settings
    r = await get_redis()
    api = ApiFootball()
    while True:
        try:
            data = await api.get("fixtures", params={"live": "all"})
            resp = data.get("response", [])
            db: Session = SessionLocal()
            try:
                for item in resp:
                    U.upsert_fixture(db, M.fixture(item))
                    fix_id_ext = str((item.get("fixture") or {}).get("id"))
                    await ingest_events_for_fixture(fix_id_ext)
                    goals = item.get("goals") or {}
                    status = (item.get("fixture", {}).get("status") or {}).get("short")
                    stamp = {"fixture_ext": fix_id_ext, "goals": goals, "status": status}
                    key = f"golex:last:fx:{stamp['fixture_ext']}"
                    prev = await r.get(key)
                    await r.set(key, json.dumps(stamp), ex=300)
                    if prev:
                        prev = json.loads(prev)
                        if prev.get("goals") != goals or prev.get("status") != status:
                            ev = {"type":"fixture_update","fixture_ext": stamp["fixture_ext"],
                                  "status": status, "goals": goals, "ts": int(time.time())}
                            await r.lpush("golex:push:events", json.dumps(ev))
                await asyncio.sleep(getattr(settings, "INGESTION_POLL_SECONDS", 15))
            finally:
                db.close()
        except Exception:
            await asyncio.sleep(5)
