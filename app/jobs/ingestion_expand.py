from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

# These are stubs — wire with real API-Football mapping in production.

def upsert_referee(db: Session, name: str) -> str:
    row = db.execute(text("""INSERT INTO referees(name) VALUES (:n)
    ON CONFLICT (name) DO NOTHING RETURNING id"""), {"n": name}).fetchone()
    if row: return str(row[0])
    row = db.execute(text("SELECT id FROM referees WHERE name=:n"), {"n": name}).fetchone()
    return str(row[0]) if row else None

def upsert_venue(db: Session, name: str, city: str|None, country: str|None, capacity: int|None):
    db.execute(text("""INSERT INTO venues(name,city,country,capacity) VALUES (:n,:c,:co,:cap)
    ON CONFLICT (name) DO UPDATE SET city=EXCLUDED.city, country=EXCLUDED.country, capacity=EXCLUDED.capacity"""),
    {"n": name, "c": city, "co": country, "cap": capacity})
    db.commit()

def update_team_form(db: Session, team_id: str, last5: str, gf: int, ga: int):
    db.execute(text("""INSERT INTO team_form(team_id,last5,gf,ga) VALUES (:t,:f,:gf,:ga)
    ON CONFLICT (team_id) DO UPDATE SET last5=EXCLUDED.last5, gf=EXCLUDED.gf, ga=EXCLUDED.ga, updated_at=NOW()"""),
    {"t": team_id, "f": last5, "gf": gf, "ga": ga})
    db.commit()

def put_player_status(db: Session, player_id: str, team_id: str, status: str, detail: str|None):
    db.execute(text("""INSERT INTO player_status(player_id,team_id,status,detail,updated_at)
    VALUES (:p,:t,:s,:d,NOW())
    ON CONFLICT (player_id,team_id,status) DO UPDATE SET detail=EXCLUDED.detail, updated_at=NOW()"""),
    {"p": player_id, "t": team_id, "s": status, "d": detail})
    db.commit()

def cache_h2h(db: Session, team_a: str, team_b: str, last_n: int, summary_json: dict):
    db.execute(text("""INSERT INTO h2h_cache(team_a,team_b,last_n,summary,updated_at)
    VALUES (:a,:b,:n,:s,NOW())
    ON CONFLICT (team_a,team_b,last_n) DO UPDATE SET summary=EXCLUDED.summary, updated_at=NOW()"""),
    {"a": team_a, "b": team_b, "n": last_n, "s": summary_json})
    db.commit()
