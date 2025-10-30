from sqlalchemy.orm import Session
from sqlalchemy import text
from ..utils.redis_pool import get_redis
import math, json, random, time

MODEL_VERSION = "v1.0-poisson-lite"

async def get_fixture_context(db: Session, fixture_id: str):
    row = db.execute(text("""            SELECT f.id::text AS id, f.league_id::text AS league_id,
               f.home_team_id::text AS home_id, th.name AS home_name,
               f.away_team_id::text AS away_id, ta.name AS away_name
        FROM fixtures f
        JOIN teams th ON th.id=f.home_team_id
        JOIN teams ta ON ta.id=f.away_team_id
        WHERE f.id=:id
    """), {"id": fixture_id}).fetchone()
    return dict(row._mapping) if row else None

def _softmax3(a,b,c):
    m = max(a,b,c)
    e1 = math.exp(a-m); e2 = math.exp(b-m); e3 = math.exp(c-m)
    s = e1+e2+e3
    return e1/s, e2/s, e3/s

async def predict_fixture(db: Session, fixture_id: str):
    # cache first
    r = await get_redis()
    key = f"golex:pred:{fixture_id}"
    cached = await r.get(key)
    if cached:
        return json.loads(cached)

    ctx = await get_fixture_context(db, fixture_id)
    if not ctx:
        return None

    # Basit bir "lite" model: takım isimlerine göre deterministik tohum
    seed = sum([ord(c) for c in (ctx["home_name"] + ctx["away_name"])])
    random.seed(seed)
    # pseudo xG difference proxy
    home_score = random.uniform(0.0, 1.0)
    away_score = random.uniform(0.0, 1.0)
    # logits -> probabilities
    ph, pd, pa = _softmax3(0.8*home_score, 0.2*(1-abs(home_score-away_score)), 0.8*away_score)
    # derived markets
    over25 = min(0.95, 0.4 + 0.8*(home_score+away_score)/2)
    btts = min(0.95, 0.3 + 0.9*min(home_score, away_score))

    # confidence: simple entropy-based
    import math
    ent = -sum([p*math.log(p+1e-9) for p in (ph,pd,pa)])/math.log(3)
    confidence = round(1.0 - ent, 3)

    result = {
        "fixtureId": fixture_id,
        "modelVersion": MODEL_VERSION,
        "probabilities": {
            "homeWin": round(ph, 3),
            "draw": round(pd, 3),
            "awayWin": round(pa, 3),
            "over25": round(over25, 3),
            "btts": round(btts, 3)
        },
        "confidence": confidence,
        "rationale": f"Lite features: team-name prior; entropy={confidence:.3f}"
    }
    await r.set(key, json.dumps(result), ex=60)
    return result
