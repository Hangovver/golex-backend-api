from fastapi import APIRouter, Query, Depends, HTTPException, Header
from typing import Optional
from fastapi import Request, Response
from ...utils.etag import with_http_caching
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from ...db.session import get_db
from sqlalchemy import text
from ...services.markets_466 import predict_466_markets
from ...services.lightgbm_model import LightGBMPredictor
import hashlib

router = APIRouter(prefix="/predictions", tags=["predictions"])

async def get_fixture_xg_data(db: Session, fixture_id: str):
    """Get fixture xG data from database"""
    try:
        # Try to get from fixtures table with stats
        row = db.execute(text("""
            SELECT 
                f.id,
                COALESCE(fs.home_xg_for, 1.5) as home_xg_for,
                COALESCE(fs.home_xg_against, 1.5) as home_xg_against,
                COALESCE(fs.away_xg_for, 1.5) as away_xg_for,
                COALESCE(fs.away_xg_against, 1.5) as away_xg_against
            FROM fixtures f
            LEFT JOIN fixture_stats fs ON fs.fixture_id = f.id
            WHERE f.id = :id
        """), {"id": fixture_id}).fetchone()
        
        if row:
            return {
                "home_xg_for": float(row.home_xg_for),
                "home_xg_against": float(row.home_xg_against),
                "away_xg_for": float(row.away_xg_for),
                "away_xg_against": float(row.away_xg_against)
            }
    except Exception:
        pass
    
    # Fallback: use defaults
    return {
        "home_xg_for": 1.5,
        "home_xg_against": 1.5,
        "away_xg_for": 1.5,
        "away_xg_against": 1.5
    }

async def get_odds_data(db: Session, fixture_id: str, requested_markets: str = "all"):
    """Get bookmaker odds from database (if available)"""
    try:
        rows = db.execute(text("""
            SELECT market_code, odds
            FROM fixture_odds
            WHERE fixture_id = :id
        """), {"id": fixture_id}).fetchall()
        
        if rows:
            return {row.market_code: float(row.odds) for row in rows}
    except Exception:
        pass
    
    return None

def _should_use_lightgbm(user_id: Optional[str], device_id: Optional[str]) -> bool:
    """
    A/B Testing: Determine if user should receive LightGBM predictions
    
    50% split based on user_id/device_id hash
    """
    identifier = user_id or device_id or "anonymous"
    hash_value = int(hashlib.sha256(identifier.encode()).hexdigest(), 16)
    return (hash_value % 100) < 50  # 50% to LightGBM


@router.get("/{fixture_id}")
async def get_prediction(
    request: Request,
    response: Response,
    fixture_id: str,
    markets: str = Query("all", description="Markets to return: 'all', 'core', or comma-separated codes"),
    include_kelly: bool = Query(False, description="Include Kelly Criterion stake recommendations"),
    bankroll: float = Query(10000, description="User bankroll for Kelly calculations"),
    explain: bool = Query(False, description="Include explanation/rationale"),
    force_model: Optional[str] = Query(None, description="Force model: 'lightgbm' or 'dixon_coles'"),
    user_id: Optional[str] = Header(None, alias="X-User-ID"),
    device_id: Optional[str] = Header(None, alias="X-Device-ID"),
    db: Session = Depends(get_db)
):
    """
    Get 466 market predictions for a fixture
    
    Uses HYBRID approach:
    - LightGBM for 50% of users (A/B testing)
    - Dixon-Coles for remaining 50%
    - Fallback: If LightGBM fails, use Dixon-Coles
    
    Args:
        fixture_id: Match ID
        markets: "all", "core", or specific markets (e.g., "KG_YES,O2.5")
        include_kelly: Include optimal stake recommendations
        bankroll: User's bankroll (for Kelly calculations)
        explain: Include model explanation
        force_model: Override A/B testing (admin only)
        user_id: User identifier (from header)
        device_id: Device identifier (from header)
        db: Database session
    
    Returns:
        {
            "fixtureId": "...",
            "markets": [...],
            "model": "lightgbm" or "dixon_coles",
            "confidence": 0.85,
            "expected_goals": {"home": 2.1, "away": 1.6}
        }
    """
    # Determine which model to use (A/B testing)
    use_lightgbm = False
    if force_model == "lightgbm":
        use_lightgbm = True
    elif force_model == "dixon_coles":
        use_lightgbm = False
    else:
        use_lightgbm = _should_use_lightgbm(user_id, device_id)
    
    # Get fixture details for LightGBM
    fixture_data = None
    if use_lightgbm:
        try:
            result = db.execute(text("""
                SELECT id, home_team_id, away_team_id, league_id, date
                FROM fixtures
                WHERE id = :fixture_id
            """), {"fixture_id": fixture_id}).fetchone()
            
            if result:
                fixture_data = dict(result._mapping)
        except Exception:
            pass
    
    # TRY LIGHTGBM FIRST (if assigned)
    if use_lightgbm and fixture_data:
        try:
            predictor = LightGBMPredictor(db)
            
            # Get 1X2 probabilities from LightGBM
            ml_prediction = await predictor.predict(
                fixture_id=fixture_data['id'],
                home_team_id=fixture_data['home_team_id'],
                away_team_id=fixture_data['away_team_id'],
                league_id=fixture_data['league_id'],
                fixture_date=fixture_data['date']
            )
            
            # Get fixture xG data
            xg_data = await get_fixture_xg_data(db, fixture_id)
            
            # Get bookmaker odds (if Kelly requested)
            odds_data = None
            if include_kelly:
                odds_data = await get_odds_data(db, fixture_id, markets)
            
            # Use LightGBM probabilities for Dixon-Coles input
            # This combines ML prediction with market coverage
            prediction = predict_466_markets(
                fixture_id=fixture_id,
                home_xg_for=xg_data["home_xg_for"],
                home_xg_against=xg_data["home_xg_against"],
                away_xg_for=xg_data["away_xg_for"],
                away_xg_against=xg_data["away_xg_against"],
                requested_markets=markets,
                include_kelly=include_kelly,
                bankroll=bankroll,
                odds_data=odds_data
            )
            
            # Override 1X2 probabilities with LightGBM
            for market in prediction.get("markets", []):
                if market.get("market") == "1X2":
                    market["probability"] = ml_prediction["home_win"]
                    market["lightgbm_enhanced"] = True
                elif market.get("market") == "DRAW":
                    market["probability"] = ml_prediction["draw"]
                    market["lightgbm_enhanced"] = True
                elif market.get("market") == "AWAY_WIN":
                    market["probability"] = ml_prediction["away_win"]
                    market["lightgbm_enhanced"] = True
            
            # Update model metadata
            prediction["model"] = "lightgbm"
            prediction["model_version"] = ml_prediction.get("model_version", "1.0.0")
            prediction["confidence"] = ml_prediction.get("confidence", 0.75)
            prediction["features_used"] = ml_prediction.get("features_used", 50)
            prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            # Filter out explanation if not requested
            if not explain:
                for market in prediction.get("markets", []):
                    market.pop("rationale", None)
                    market.pop("explanation", None)
            
            # Cache response
            res = with_http_caching(request, response, prediction)
            return res if res is not None else Response(status_code=304)
            
        except Exception as e:
            # LightGBM failed, fallback to Dixon-Coles
            print(f"[Prediction] LightGBM failed: {e}, falling back to Dixon-Coles")
            use_lightgbm = False
    
    # FALLBACK TO DIXON-COLES (default for 50% or if LightGBM fails)
    try:
        # Get fixture xG data
        xg_data = await get_fixture_xg_data(db, fixture_id)
        
        # Get bookmaker odds (if Kelly requested)
        odds_data = None
        if include_kelly:
            odds_data = await get_odds_data(db, fixture_id, markets)
        
        # Calculate 466 markets using Dixon-Coles model
        prediction = predict_466_markets(
            fixture_id=fixture_id,
            home_xg_for=xg_data["home_xg_for"],
            home_xg_against=xg_data["home_xg_against"],
            away_xg_for=xg_data["away_xg_for"],
            away_xg_against=xg_data["away_xg_against"],
            requested_markets=markets,
            include_kelly=include_kelly,
            bankroll=bankroll,
            odds_data=odds_data
        )
        
        # Add timestamp
        prediction["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Filter out explanation if not requested
        if not explain:
            for market in prediction.get("markets", []):
                market.pop("rationale", None)
                market.pop("explanation", None)
        
        # Cache response
        res = with_http_caching(request, response, prediction)
        return res if res is not None else Response(status_code=304)
        
    except Exception as e:
        # Ultimate fallback to basic prediction if all fails
        import traceback
        print(f"Error in predictions: {e}")
        print(traceback.format_exc())
        
        # Return basic prediction
        basic_payload = {
            "fixtureId": fixture_id,
            "markets": [
                {"market": "1X2", "probability": 0.45, "confidence": 0.75},
                {"market": "KG_YES", "probability": 0.65, "confidence": 0.75},
                {"market": "O2.5", "probability": 0.60, "confidence": 0.75}
            ],
            "model": "fallback",
            "confidence": 0.75,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "Full calculation unavailable, using fallback"
        }
        
        return basic_payload
