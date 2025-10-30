from sqlalchemy import text
from sqlalchemy.orm import Session
import random

# Toy dataset builder: derives labels from final score in events (Goal events) if available
# Returns list of samples: { "fixture_id": ..., "features": {...}, "labels": {"homeWin":0/1,"over25":0/1,"btts":0/1} }
def build_dataset(db: Session, limit: int = 500):
    rows = db.execute(text("""            SELECT f.id::text AS id, f.home_team_id::text AS home_id, f.away_team_id::text AS away_id
        FROM fixtures f
        ORDER BY f.date_utc DESC
        LIMIT :lim
    """), {"lim": limit}).fetchall()
    samples = []
    for r in rows:
        fid = r[0]
        # features: placeholder numeric signals
        feats = {
            "elo_home": 1500 + random.randint(-50, 60),
            "elo_away": 1500 + random.randint(-60, 50),
            "avg_goals_home": 1.0 + random.random()*1.2,
            "avg_goals_away": 0.8 + random.random()*1.2,
        }
        # labels from events (fallback random if no events)
        erows = db.execute(text("SELECT type, team_id FROM events WHERE fixture_id=:id"), {"id": fid}).fetchall()
        hg=0; ag=0
        for e in erows:
            if e[0] == "Goal":
                if str(e[1]) == r[1]: hg += 1
                elif str(e[1]) == r[2]: ag += 1
        if hg==0 and ag==0:
            # fallback coin toss to keep pipeline running in MVP
            hg = random.randint(0,3); ag = random.randint(0,3)
        homeWin = 1 if hg>ag else 0
        over25 = 1 if (hg+ag)>=3 else 0
        btts = 1 if (hg>=1 and ag>=1) else 0
        samples.append({"fixture_id": fid, "features": feats, "labels": {"homeWin": homeWin, "over25": over25, "btts": btts}})
    return samples
