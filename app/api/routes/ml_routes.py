"""
Machine Learning API Routes
EXACT COPY from SofaScore backend ML infrastructure
Features:
- Model training endpoint (admin only)
- Prediction endpoint with LightGBM
- Model info and metrics
- Feature importance
- Training status check
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.lightgbm_model import LightGBMPredictor
from app.services.ml_training_service import MLTrainingService, train_model_task, celery_app
from app.core.security import require_admin

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


# ============================================================================
# PREDICTION ENDPOINTS
# ============================================================================

@router.get("/predict/{fixture_id}")
async def predict_fixture_ml(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Predict match outcome using LightGBM model
    Returns probabilities for Home/Draw/Away
    
    REAL ML PREDICTION - 50+ features, player impact, form analysis
    """
    from sqlalchemy import text
    
    # Fetch fixture details
    result = db.execute(text("""
        SELECT id, home_team_id, away_team_id, league_id, date
        FROM fixtures
        WHERE id = :fixture_id
    """), {"fixture_id": fixture_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    fixture = dict(result._mapping)
    
    # Create predictor
    predictor = LightGBMPredictor(db)
    
    # Get prediction
    prediction = await predictor.predict(
        fixture_id=fixture['id'],
        home_team_id=fixture['home_team_id'],
        away_team_id=fixture['away_team_id'],
        league_id=fixture['league_id'],
        fixture_date=fixture['date']
    )
    
    return {
        "fixture_id": fixture_id,
        "prediction": prediction,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/predict/batch")
async def predict_batch_ml(
    fixture_ids: list[int],
    db: Session = Depends(get_db)
):
    """
    Batch prediction for multiple fixtures
    Optimized for bulk processing
    """
    predictor = LightGBMPredictor(db)
    predictions = []
    
    from sqlalchemy import text
    
    for fixture_id in fixture_ids[:100]:  # Limit to 100 per request
        try:
            result = db.execute(text("""
                SELECT id, home_team_id, away_team_id, league_id, date
                FROM fixtures
                WHERE id = :fixture_id
            """), {"fixture_id": fixture_id}).fetchone()
            
            if not result:
                continue
            
            fixture = dict(result._mapping)
            
            prediction = await predictor.predict(
                fixture_id=fixture['id'],
                home_team_id=fixture['home_team_id'],
                away_team_id=fixture['away_team_id'],
                league_id=fixture['league_id'],
                fixture_date=fixture['date']
            )
            
            predictions.append({
                "fixture_id": fixture_id,
                "prediction": prediction
            })
            
        except Exception as e:
            predictions.append({
                "fixture_id": fixture_id,
                "error": str(e)
            })
    
    return {
        "predictions": predictions,
        "total": len(predictions),
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# MODEL MANAGEMENT ENDPOINTS (Admin Only)
# ============================================================================

@router.post("/train", dependencies=[Depends(require_admin)])
async def train_model(
    background_tasks: BackgroundTasks,
    min_matches: int = 5000,
    n_estimators: int = 500,
    learning_rate: float = 0.05,
    async_training: bool = True
):
    """
    Train LightGBM model on historical data
    
    Admin only - triggers model training
    
    Parameters:
    - min_matches: Minimum historical matches to use (default 5000)
    - n_estimators: Number of boosting rounds (default 500)
    - learning_rate: Learning rate (default 0.05)
    - async_training: Train in background (default True)
    """
    
    if async_training:
        # Start async training with Celery
        task = train_model_task.delay(
            min_matches=min_matches,
            n_estimators=n_estimators,
            learning_rate=learning_rate
        )
        
        return {
            "status": "training_started",
            "task_id": task.id,
            "message": "Model training started in background",
            "check_status_url": f"/api/ml/training/status/{task.id}",
            "parameters": {
                "min_matches": min_matches,
                "n_estimators": n_estimators,
                "learning_rate": learning_rate
            }
        }
    else:
        # Synchronous training (blocking - use only for testing)
        service = MLTrainingService()
        result = service.train_model_sync(
            min_matches=min_matches,
            n_estimators=n_estimators,
            learning_rate=learning_rate
        )
        
        return {
            "status": "training_complete",
            "result": result
        }


@router.get("/training/status/{task_id}", dependencies=[Depends(require_admin)])
async def get_training_status(task_id: str):
    """
    Check status of async training task
    
    Returns current progress and results when complete
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        return {
            "task_id": task_id,
            "status": "PENDING",
            "message": "Training task is queued"
        }
    elif task.state == 'PROGRESS':
        return {
            "task_id": task_id,
            "status": "PROGRESS",
            "progress": task.info.get('progress', 0),
            "message": task.info.get('status', 'Training in progress...')
        }
    elif task.state == 'SUCCESS':
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task.result
        }
    elif task.state == 'FAILURE':
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(task.info)
        }
    else:
        return {
            "task_id": task_id,
            "status": task.state
        }


@router.get("/model/info")
async def get_model_info(db: Session = Depends(get_db)):
    """
    Get current model information
    - Model version
    - Training date
    - Performance metrics
    - Feature count
    """
    service = MLTrainingService()
    info = service.get_model_info()
    
    return info


@router.get("/model/features")
async def get_feature_importance(
    top_n: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get feature importance from trained model
    
    Shows which features contribute most to predictions
    """
    predictor = LightGBMPredictor(db)
    
    if not predictor.feature_importance:
        raise HTTPException(status_code=404, detail="Model not trained yet")
    
    sorted_features = sorted(
        predictor.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:top_n]
    
    return {
        "top_features": [
            {"feature": name, "importance": round(float(importance), 4)}
            for name, importance in sorted_features
        ],
        "total_features": len(predictor.feature_names),
        "model_version": predictor.model_version
    }


@router.get("/model/metrics")
async def get_model_metrics(db: Session = Depends(get_db)):
    """
    Get model performance metrics
    - Accuracy
    - Log loss
    - Brier score
    - Cross-validation scores
    """
    predictor = LightGBMPredictor(db)
    
    if not predictor.metrics:
        raise HTTPException(status_code=404, detail="Model not trained yet")
    
    return {
        "metrics": predictor.metrics,
        "model_version": predictor.model_version,
        "training_date": predictor.training_date.isoformat() if predictor.training_date else None
    }


# ============================================================================
# FEATURE ENGINEERING ENDPOINTS (Debug/Analysis)
# ============================================================================

@router.get("/features/fixture/{fixture_id}")
async def get_fixture_features(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all extracted features for a fixture
    
    Debug endpoint - shows all 50+ features used by ML model
    """
    from sqlalchemy import text
    from app.services.feature_engineering import FeatureEngineer
    
    result = db.execute(text("""
        SELECT id, home_team_id, away_team_id, league_id, date
        FROM fixtures
        WHERE id = :fixture_id
    """), {"fixture_id": fixture_id}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    fixture = dict(result._mapping)
    
    engineer = FeatureEngineer(db)
    features = await engineer.extract_all_features(
        fixture_id=fixture['id'],
        home_team_id=fixture['home_team_id'],
        away_team_id=fixture['away_team_id'],
        league_id=fixture['league_id'],
        fixture_date=fixture['date']
    )
    
    return {
        "fixture_id": fixture_id,
        "features": features,
        "feature_count": len(features)
    }


@router.get("/player-impact/team/{team_id}")
async def get_team_player_impact(
    team_id: int,
    fixture_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get player impact analysis for a team
    - Team strength with/without key players
    - Missing players impact
    - Squad depth factor
    - Star player dependency
    """
    from app.services.player_modeling import PlayerImpactModel
    
    date = datetime.fromisoformat(fixture_date) if fixture_date else datetime.utcnow()
    
    player_impact = PlayerImpactModel(db)
    
    team_impact = await player_impact.calculate_team_impact(
        team_id=team_id,
        fixture_date=date
    )
    
    dependency = await player_impact.calculate_star_player_dependency(
        team_id=team_id
    )
    
    return {
        "team_id": team_id,
        "team_impact": team_impact,
        "star_dependency": dependency,
        "analysis_date": date.isoformat()
    }

