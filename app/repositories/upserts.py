import json
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..models.idmap import upsert_map, get_uuid

SRC = "api-football"

def upsert_league(db: Session, m):
    ext = m["external_id"]; d = m["data"]
    uuid = get_uuid(db, SRC, "league", ext)
    if not uuid:
        row = db.execute(text("INSERT INTO leagues(id,name,country,type,season_format) VALUES (gen_random_uuid(),:n,:c,:t,:sf) RETURNING id"),
                         {"n": d["name"], "c": d["country"], "t": d["type"], "sf": d["season_format"]}).fetchone()
        uuid = row[0]; upsert_map(db, SRC, "league", ext, uuid)
    else:
        db.execute(text("UPDATE leagues SET name=:n,country=:c,type=:t,season_format=:sf WHERE id=:id"),
                   {"n": d["name"], "c": d["country"], "t": d["type"], "sf": d["season_format"], "id": uuid})
    return uuid

def upsert_venue(db: Session, m):
    if m is None or m.get("external_id") is None: return None
    ext = m["external_id"]; d = m["data"]
    uuid = get_uuid(db, SRC, "venue", ext)
    if not uuid:
        row = db.execute(text("INSERT INTO venues(id,name,city,capacity) VALUES (gen_random_uuid(),:n,:c,:cap) RETURNING id"),
                         {"n": d["name"], "c": d["city"], "cap": d["capacity"]}).fetchone()
        uuid = row[0]; upsert_map(db, SRC, "venue", ext, uuid)
    else:
        db.execute(text("UPDATE venues SET name=:n,city=:c,capacity=:cap WHERE id=:id"),
                   {"n": d["name"], "c": d["city"], "cap": d["capacity"], "id": uuid})
    return uuid

def upsert_team(db: Session, m):
    ext = m["external_id"]; d = m["data"]
    v_uuid = upsert_venue(db, d.get("venue")) if d.get("venue") else None
    uuid = get_uuid(db, SRC, "team", ext)
    if not uuid:
        row = db.execute(text("INSERT INTO teams(id,name,country,code,founded,venue_id) VALUES (gen_random_uuid(),:n,:c,:code,:f,:v) RETURNING id"),
                         {"n": d["name"], "c": d["country"], "code": d["code"], "f": d["founded"], "v": v_uuid}).fetchone()
        uuid = row[0]; upsert_map(db, SRC, "team", ext, uuid)
    else:
        db.execute(text("UPDATE teams SET name=:n,country=:c,code=:code,founded=:f,venue_id=:v WHERE id=:id"),
                   {"n": d["name"], "c": d["country"], "code": d["code"], "f": d["founded"], "v": v_uuid, "id": uuid})
    return uuid

def upsert_season(db: Session, league_uuid, year_start: int):
    row = db.execute(text("SELECT id FROM seasons WHERE league_id=:l AND year_start=:y"), {"l": league_uuid, "y": year_start}).fetchone()
    if row: return row[0]
    row = db.execute(text("INSERT INTO seasons(id,league_id,year_start,name,active) VALUES (gen_random_uuid(),:l,:y,:name,true) RETURNING id"),
                     {"l": league_uuid, "y": year_start, "name": f"{year_start}/{str((year_start+1)%100).zfill(2)}"}).fetchone()
    return row[0]

def upsert_fixture(db: Session, m):
    ext = m["external_id"]; d = m["data"]
    league_uuid = get_uuid(db, SRC, "league", d.get("league_external_id")) if d.get("league_external_id") else None
    home_uuid = get_uuid(db, SRC, "team", d.get("home_team_external_id")) if d.get("home_team_external_id") else None
    away_uuid = get_uuid(db, SRC, "team", d.get("away_team_external_id")) if d.get("away_team_external_id") else None
    venue_uuid = get_uuid(db, SRC, "venue", d.get("venue_external_id")) if d.get("venue_external_id") else None
    season_uuid = None
    if league_uuid and d.get("season_year_start") is not None:
        season_uuid = upsert_season(db, league_uuid, d["season_year_start"])

    uuid = get_uuid(db, SRC, "fixture", ext)
    if not uuid:
        row = db.execute(text("""
        INSERT INTO fixtures(id,league_id,season_id,home_team_id,away_team_id,date_utc,status,venue_id,round)
        VALUES (gen_random_uuid(),:l,:s,:h,:a,:date,:status,:v,:r)
        RETURNING id
        """), {"l": league_uuid, "s": season_uuid, "h": home_uuid, "a": away_uuid,
                 "date": d["date_utc"], "status": d["status"], "v": venue_uuid, "r": d.get("round")}).fetchone()
        uuid = row[0]; upsert_map(db, SRC, "fixture", ext, uuid)
    else:
        db.execute(text("""
        UPDATE fixtures SET league_id=:l,season_id=:s,home_team_id=:h,away_team_id=:a,date_utc=:date,status=:status,venue_id=:v,round=:r
        WHERE id=:id
        """), {"l": league_uuid, "s": season_uuid, "h": home_uuid, "a": away_uuid,
                 "date": d["date_utc"], "status": d["status"], "v": venue_uuid, "r": d.get("round"), "id": uuid})
    return uuid

def upsert_event(db: Session, m):
    ext = m["external_id"]; d = m["data"]
    fx_uuid = get_uuid(db, SRC, "fixture", d.get("fixture_external_id")) if d.get("fixture_external_id") else None
    team_uuid = get_uuid(db, SRC, "team", d.get("team_external_id")) if d.get("team_external_id") else None
    row = db.execute(text("SELECT internal_uuid FROM ext_id_map WHERE source=:s AND entity='event' AND external_id=:x"),
                     {"s": SRC, "x": ext}).fetchone()
    if row: return row[0]
    row = db.execute(text("""
    INSERT INTO events(id, fixture_id, minute, type, detail, player_name, assist_name, team_id, extra)
    VALUES (gen_random_uuid(), :f, :m, :t, :d, :p, :a, :team, :e) RETURNING id
    """), {"f": fx_uuid, "m": d.get("minute"), "t": d.get("type"), "d": d.get("detail"), "p": d.get("player_name"),
             "a": d.get("assist_name"), "team": team_uuid, "e": json.dumps(d.get("extra") or {})}).fetchone()
    uuid = row[0]
    upsert_map(db, SRC, "event", ext, uuid)
    return uuid

def upsert_lineup(db: Session, m):
    ext = m["external_id"]; d = m["data"]
    fx_uuid = get_uuid(db, SRC, "fixture", d.get("fixture_external_id")) if d.get("fixture_external_id") else None
    team_uuid = get_uuid(db, SRC, "team", d.get("team_external_id")) if d.get("team_external_id") else None
    row = db.execute(text("SELECT internal_uuid FROM ext_id_map WHERE source=:s AND entity='lineup' AND external_id=:x"),
                     {"s": SRC, "x": ext}).fetchone()
    if not row:
        row = db.execute(text("""
        INSERT INTO lineups(id, fixture_id, team_id, formation, players) VALUES (gen_random_uuid(), :f, :t, :form, :pl) RETURNING id
        """), {"f": fx_uuid, "t": team_uuid, "form": d.get("formation"), "pl": json.dumps(d.get("players") or [])}).fetchone()
        uuid = row[0]; upsert_map(db, SRC, "lineup", ext, uuid)
    else:
        uuid = row[0]
        db.execute(text("""
        UPDATE lineups SET fixture_id=:f, team_id=:t, formation=:form, players=:pl WHERE id=:id
        """), {"f": fx_uuid, "t": team_uuid, "form": d.get("formation"), "pl": json.dumps(d.get("players") or []), "id": uuid})
    return uuid

def upsert_standing(db: Session, league_uuid, season_uuid, m):
    d = m["data"]
    team_uuid = get_uuid(db, SRC, "team", d.get("team_external_id")) if d.get("team_external_id") else None
    db.execute(text("""
    INSERT INTO standings(id, league_id, season_id, team_id, rank, played, win, draw, loss, goals_for, goals_against, points)
    VALUES (gen_random_uuid(), :l, :s, :t, :r, :p, :w, :d, :lo, :gf, :ga, :pts)
    ON CONFLICT (league_id, season_id, team_id)
    DO UPDATE SET rank=:r, played=:p, win=:w, draw=:d, loss=:lo, goals_for=:gf, goals_against=:ga, points=:pts
    """), {"l": league_uuid, "s": season_uuid, "t": team_uuid, "r": d.get("rank"), "p": d.get("played"),
             "w": d.get("win"), "d": d.get("draw"), "lo": d.get("loss"), "gf": d.get("goals_for"), "ga": d.get("goals_against"), "pts": d.get("points")})
    return True
