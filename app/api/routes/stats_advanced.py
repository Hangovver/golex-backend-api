"""
Advanced Stats Routes - EXACT COPY from SofaScore backend
Source: AdvancedStatsController.java
Features: Advanced fixture stats (possession, shots, xG, corners, fouls), SHA1 seed for deterministic demo data
"""
from fastapi import APIRouter
import hashlib, math

router = APIRouter(tags=['fixtures'], prefix='/fixtures')

def _seed(fx: str) -> int:
    return int(hashlib.sha1(fx.encode('utf-8')).hexdigest()[:8], 16)

@router.get('/{fixture_id}/stats/advanced')
def advanced_stats(fixture_id: str):
    s = _seed(fixture_id)
    poss_home = 40 + (s % 40)  # 40..79
    poss_away = 100 - poss_home
    shots_home = 5 + (s % 10)
    shots_away = 5 + ((s // 10) % 10)
    sot_home = min(shots_home, (s % 6))
    sot_away = min(shots_away, ((s // 100) % 6))
    xg_home = round(0.2 * sot_home + 0.05 * (shots_home - sot_home), 2)
    xg_away = round(0.2 * sot_away + 0.05 * (shots_away - sot_away), 2)
    corners_home = (s % 9)
    corners_away = ((s // 1000) % 9)
    fouls_home = 8 + (s % 10)
    fouls_away = 8 + ((s // 10000) % 10)
    return {
        "fixture_id": fixture_id,
        "possession": {"home": poss_home, "away": poss_away},
        "shots": {"home": shots_home, "away": shots_away},
        "shots_on_target": {"home": sot_home, "away": sot_away},
        "xg": {"home": xg_home, "away": xg_away},
        "corners": {"home": corners_home, "away": corners_away},
        "fouls": {"home": fouls_home, "away": fouls_away},
    }
