from sqlalchemy import text
from sqlalchemy.orm import Session
from ..ai.features.feature_pool import list_features

async def compute_basic_features(db: Session, fixture_id: str) -> dict:
    # Minimal placeholder computations to keep pipeline consistent
    # In real impl: query last N matches and compute aggregates
    row = db.execute(text("""
        SELECT f.id, f.home_team_id, f.away_team_id FROM fixtures f WHERE f.id=:id
    """), {"id": fixture_id}).fetchone()
    if not row:
        return {}
    return {
        "team_form_home_5": 0.6,
        "team_form_away_5": 0.5,
        "avg_goals_home": 1.4,
        "avg_goals_away": 1.1,
        "head2head_last5_diff": 0.2,
        "rest_days_diff": 1.0,
        "league_strength_home": 0.55,
        "league_strength_away": 0.50,
        "elo_home": 1510,
        "elo_away": 1490,
    }
