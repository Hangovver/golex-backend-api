from fastapi import APIRouter
router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/live-predictions/{fixture_id}")
async def live_predictions(fixture_id: str):
    return {
        "fixtureId": fixture_id,
        "sampling": "per_minute",
        "series": [
            {"m": 1, "homeWin": 0.41, "draw": 0.30, "awayWin": 0.29},
            {"m": 15, "homeWin": 0.45, "draw": 0.29, "awayWin": 0.26},
            {"m": 45, "homeWin": 0.43, "draw": 0.33, "awayWin": 0.24},
            {"m": 75, "homeWin": 0.51, "draw": 0.27, "awayWin": 0.22}
        ]
    }

@router.get("/xthreat/{fixture_id}")
async def xthreat_series(fixture_id: str):
    return {
        "fixtureId": fixture_id,
        "bucket": "5min",
        "home": [0.02, 0.05, 0.03, 0.08, 0.10, 0.04, 0.02, 0.01, 0.00, 0.03, 0.06, 0.02, 0.01, 0.00, 0.00, 0.01, 0.00, 0.02],
        "away": [0.01, 0.02, 0.03, 0.03, 0.02, 0.01, 0.05, 0.07, 0.06, 0.04, 0.01, 0.00, 0.00, 0.02, 0.03, 0.01, 0.01, 0.00]
    }

@router.get("/pass-network/{fixture_id}")
async def pass_network(fixture_id: str):
    return {
        "fixtureId": fixture_id,
        "home": [{"playerId": 11, "x": 0.2, "y": 0.7, "links":[{"to":7,"w":0.35},{"to":9,"w":0.22}]}],
        "away": [{"playerId": 10, "x": 0.8, "y": 0.7, "links":[{"to":9,"w":0.41}]}]
    }
