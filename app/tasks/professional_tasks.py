"""
Celery Tasks for Professional Betting System
Automates data collection, ELO updates, and model training
PRODUCTION GRADE - Scheduled and manual tasks
NO SIMPLIFICATION - Full automation pipeline
"""

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os

from app.core.config import settings
from app.services.data_ingestion_service import DataIngestionService
from app.services.elo_calculator import ELOCalculator
from app.services.lightgbm_model import LightGBMPredictor
from app.services.xgboost_model import XGBoostPredictor
from app.services.neural_network_model import NeuralNetworkPredictor


# Celery app
# IMPORTANT: Use settings first (pydantic-settings loads env vars automatically)
# Fallback to os.getenv() only if settings doesn't have the value
# This ensures Railway environment variables are loaded correctly via settings
CELERY_BROKER_URL = (
    settings.celery_broker_url if settings.celery_broker_url != "redis://localhost:6379/0" else
    os.getenv('CELERY_BROKER_URL') or 
    os.getenv('REDIS_URL') or 
    'redis://localhost:6379/0'
)
CELERY_RESULT_BACKEND = (
    settings.celery_result_backend if settings.celery_result_backend != "redis://localhost:6379/0" else
    os.getenv('CELERY_RESULT_BACKEND') or 
    os.getenv('REDIS_URL') or 
    'redis://localhost:6379/0'
)

# Debug: Print Redis URL (will be removed in production)
import logging
logger = logging.getLogger(__name__)
logger.info(f"[Celery] BROKER_URL: {CELERY_BROKER_URL[:50]}...")
logger.info(f"[Celery] RESULT_BACKEND: {CELERY_RESULT_BACKEND[:50]}...")

celery_app = Celery(
    'professional_tasks',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)


def get_db_session():
    """Create database session"""
    engine = create_engine(os.getenv('DATABASE_URL') or settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# ============================================================================
# DATA INGESTION TASKS
# ============================================================================

@celery_app.task(bind=True, name='ingest_historical_data')
def ingest_historical_data_task(
    self,
    league_ids: list = [39, 140, 135, 78, 61],  # Premier League, La Liga, Serie A, Bundesliga, Ligue 1
    seasons: list = ['2022', '2023', '2024'],
    min_fixtures: int = 5000
):
    """
    Ingest historical fixture data from API-Football
    
    Args:
        league_ids: List of league IDs
        seasons: List of seasons (e.g., ['2022', '2023'])
        min_fixtures: Minimum fixtures to collect
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting data ingestion...', 'progress': 0}
        )
        
        db = get_db_session()
        service = DataIngestionService(db)
        
        # Run ingestion
        import asyncio
        stats = asyncio.run(service.ingest_historical_fixtures(
            league_ids=league_ids,
            seasons=seasons,
            min_fixtures=min_fixtures
        ))
        
        db.close()
        
        return {
            'status': 'SUCCESS',
            'stats': stats,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e),
            'failed_at': datetime.utcnow().isoformat()
        }


@celery_app.task(name='collect_referee_stats')
def collect_referee_stats_task(days_back: int = 365):
    """
    Collect referee statistics for recent matches
    
    Args:
        days_back: How many days back to collect
    """
    try:
        db = get_db_session()
        service = DataIngestionService(db)
        
        # Get fixtures without referee stats
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT f.api_football_id
            FROM fixtures f
            LEFT JOIN referee_match_stats rms ON rms.match_id = f.id
            WHERE f.date > NOW() - INTERVAL ':days days'
            AND f.status = 'FT'
            AND rms.id IS NULL
            LIMIT 1000
        """), {"days": days_back}).fetchall()
        
        fixture_ids = [row[0] for row in result]
        
        print(f"[Celery] Collecting referee stats for {len(fixture_ids)} fixtures...")
        
        stats_collected = 0
        import asyncio
        for fixture_id in fixture_ids:
            success = asyncio.run(service.collect_referee_stats(fixture_id))
            if success:
                stats_collected += 1
        
        db.close()
        
        return {
            'status': 'SUCCESS',
            'fixtures_processed': len(fixture_ids),
            'stats_collected': stats_collected
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }


# ============================================================================
# ELO RATING TASKS
# ============================================================================

@celery_app.task(bind=True, name='recalculate_all_elos')
def recalculate_all_elos_task(self, league_ids: list = None):
    """
    Recalculate all ELO ratings from scratch
    Run this once during initial setup
    
    Args:
        league_ids: List of league IDs (None = all leagues)
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Recalculating ELO ratings...', 'progress': 0}
        )
        
        db = get_db_session()
        calculator = ELOCalculator(db)
        
        # Recalculate
        import asyncio
        stats = asyncio.run(calculator.recalculate_all_elos(league_ids=league_ids))
        
        db.close()
        
        return {
            'status': 'SUCCESS',
            'stats': stats,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }


@celery_app.task(name='update_elo_for_recent_matches')
def update_elo_for_recent_matches_task(hours_back: int = 24):
    """
    Update ELO ratings for recently completed matches
    Run this daily or after each match day
    
    Args:
        hours_back: How many hours back to check for completed matches
    """
    try:
        db = get_db_session()
        calculator = ELOCalculator(db)
        
        # Get recently completed matches without ELO updates
        from sqlalchemy import text
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        result = db.execute(text("""
            SELECT 
                f.id, f.home_team_id, f.away_team_id,
                f.home_score, f.away_score, f.date
            FROM fixtures f
            WHERE f.status = 'FT'
            AND f.date > :cutoff
            AND f.home_score IS NOT NULL
            AND f.away_score IS NOT NULL
            ORDER BY f.date ASC
        """), {"cutoff": cutoff_time}).fetchall()
        
        matches = [dict(row._mapping) for row in result]
        
        print(f"[Celery] Updating ELO for {len(matches)} matches...")
        
        import asyncio
        for match in matches:
            asyncio.run(calculator.update_elo_after_match(
                home_team_id=match['home_team_id'],
                away_team_id=match['away_team_id'],
                home_score=match['home_score'],
                away_score=match['away_score'],
                match_date=match['date']
            ))
        
        db.close()
        
        return {
            'status': 'SUCCESS',
            'matches_updated': len(matches)
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }


# ============================================================================
# MODEL TRAINING TASKS
# ============================================================================

@celery_app.task(bind=True, name='train_all_models')
def train_all_models_task(
    self,
    min_matches: int = 5000,
    n_estimators: int = 500
):
    """
    Train all ML models (LightGBM + XGBoost + Neural Network)
    
    Args:
        min_matches: Minimum training samples
        n_estimators: Boosting rounds
    """
    try:
        db = get_db_session()
        
        results = {}
        
        # Train LightGBM
        self.update_state(state='PROGRESS', meta={'status': 'Training LightGBM...', 'progress': 10})
        lgb = LightGBMPredictor(db)
        import asyncio
        lgb_result = asyncio.run(lgb.train(min_matches=min_matches, n_estimators=n_estimators))
        results['lightgbm'] = lgb_result
        
        # Train XGBoost
        self.update_state(state='PROGRESS', meta={'status': 'Training XGBoost...', 'progress': 40})
        xgb = XGBoostPredictor(db)
        xgb_result = asyncio.run(xgb.train(min_matches=min_matches, n_estimators=n_estimators))
        results['xgboost'] = xgb_result
        
        # Train Neural Network
        self.update_state(state='PROGRESS', meta={'status': 'Training Neural Network...', 'progress': 70})
        nn = NeuralNetworkPredictor(db)
        nn_result = asyncio.run(nn.train(min_matches=min_matches, epochs=100))
        results['neural_network'] = nn_result
        
        db.close()
        
        return {
            'status': 'SUCCESS',
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e)
        }


# ============================================================================
# SCHEDULED TASKS (Celery Beat)
# ============================================================================

celery_app.conf.beat_schedule = {
    # Daily data ingestion (new fixtures)
    'daily-data-ingestion': {
        'task': 'collect_referee_stats',
        'schedule': 86400.0,  # 24 hours
        'kwargs': {'days_back': 7}
    },
    
    # Daily ELO updates
    'daily-elo-update': {
        'task': 'update_elo_for_recent_matches',
        'schedule': 86400.0,  # 24 hours
        'kwargs': {'hours_back': 48}
    },
    
    # Weekly model retraining
    'weekly-model-retrain': {
        'task': 'train_all_models',
        'schedule': 604800.0,  # 7 days
        'kwargs': {'min_matches': 5000, 'n_estimators': 500}
    }
}


# ============================================================================
# INITIALIZATION TASK (Run once)
# ============================================================================

@celery_app.task(name='initialize_professional_system')
def initialize_professional_system_task():
    """
    ONE-TIME initialization task
    Runs all setup steps in sequence:
    1. Ingest historical data (5000+ fixtures)
    2. Calculate ELO ratings
    3. Collect referee stats
    4. Train all ML models
    
    This should be run once after database migration
    """
    try:
        print("[Init] Starting Professional Betting System initialization...")
        
        # Step 1: Ingest historical data
        print("[Init] Step 1/4: Ingesting historical data...")
        ingest_result = ingest_historical_data_task.delay(
            league_ids=[39, 140, 135, 78, 61],
            seasons=['2022', '2023', '2024'],
            min_fixtures=5000
        )
        ingest_result.wait(timeout=7200)  # Wait up to 2 hours
        print(f"[Init] Data ingestion: {ingest_result.result['status']}")
        
        # Step 2: Calculate ELO ratings
        print("[Init] Step 2/4: Calculating ELO ratings...")
        elo_result = recalculate_all_elos_task.delay()
        elo_result.wait(timeout=3600)  # Wait up to 1 hour
        print(f"[Init] ELO calculation: {elo_result.result['status']}")
        
        # Step 3: Collect referee stats
        print("[Init] Step 3/4: Collecting referee stats...")
        referee_result = collect_referee_stats_task.delay(days_back=730)
        referee_result.wait(timeout=3600)  # Wait up to 1 hour
        print(f"[Init] Referee stats: {referee_result.result['status']}")
        
        # Step 4: Train all models
        print("[Init] Step 4/4: Training ML models...")
        train_result = train_all_models_task.delay(min_matches=5000, n_estimators=500)
        train_result.wait(timeout=7200)  # Wait up to 2 hours
        print(f"[Init] Model training: {train_result.result['status']}")
        
        print("[Init] ✅ Professional Betting System fully initialized!")
        
        return {
            'status': 'SUCCESS',
            'steps': {
                'data_ingestion': ingest_result.result,
                'elo_calculation': elo_result.result,
                'referee_stats': referee_result.result,
                'model_training': train_result.result
            },
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e),
            'failed_at': datetime.utcnow().isoformat()
        }

