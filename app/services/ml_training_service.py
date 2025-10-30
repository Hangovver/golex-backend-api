"""
ML Model Training Service
Handles automated model training, retraining, and version management
REAL PRODUCTION SERVICE - Celery tasks for async training
"""

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from app.services.lightgbm_model import LightGBMPredictor
from app.core.config import settings


# Celery app for async training
celery_app = Celery(
    'ml_training',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)


class MLTrainingService:
    """
    Service for managing ML model training lifecycle
    - Manual training trigger
    - Scheduled retraining (weekly)
    - Performance monitoring
    - Model versioning
    """
    
    def __init__(self):
        # Database engine for training
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        self.db = SessionLocal()
        
        self.model = LightGBMPredictor(self.db)
    
    def train_model_sync(
        self,
        min_matches: int = 5000,
        n_estimators: int = 500,
        learning_rate: float = 0.05
    ) -> dict:
        """
        Train model synchronously (blocking)
        Use for manual training or testing
        """
        print(f"[MLTraining] Starting synchronous training...")
        
        result = asyncio.run(self.model.train(
            min_matches=min_matches,
            n_estimators=n_estimators,
            learning_rate=learning_rate
        ))
        
        print(f"[MLTraining] Training complete!")
        return result
    
    async def train_model_async(
        self,
        min_matches: int = 5000,
        n_estimators: int = 500,
        learning_rate: float = 0.05
    ) -> dict:
        """
        Train model asynchronously
        Returns task ID for status checking
        """
        task = train_model_task.delay(
            min_matches=min_matches,
            n_estimators=n_estimators,
            learning_rate=learning_rate
        )
        
        return {
            'task_id': task.id,
            'status': 'PENDING',
            'message': 'Model training started. Check /api/ml/training/status/{task_id}'
        }
    
    def get_model_info(self) -> dict:
        """Get current model information"""
        return {
            'model_version': self.model.model_version,
            'training_date': self.model.training_date.isoformat() if self.model.training_date else None,
            'metrics': self.model.metrics,
            'features_count': len(self.model.feature_names),
            'is_trained': self.model.model_home_win is not None,
            'top_features': sorted(
                self.model.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:15] if self.model.feature_importance else []
        }


# ============================================================================
# CELERY TASKS - Async training jobs
# ============================================================================

@celery_app.task(bind=True, name='train_model_task')
def train_model_task(
    self,
    min_matches: int = 5000,
    n_estimators: int = 500,
    learning_rate: float = 0.05
):
    """
    Celery task for async model training
    Can be triggered manually or scheduled
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Initializing training...', 'progress': 0}
        )
        
        # Create DB session
        engine = create_engine(os.getenv('DATABASE_URL'))
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Create model instance
        model = LightGBMPredictor(db)
        
        # Update state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Preparing training data...', 'progress': 20}
        )
        
        # Train model
        import asyncio
        result = asyncio.run(model.train(
            min_matches=min_matches,
            n_estimators=n_estimators,
            learning_rate=learning_rate
        ))
        
        # Close DB session
        db.close()
        
        return {
            'status': 'SUCCESS',
            'result': result,
            'completed_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'FAILURE',
            'error': str(e),
            'failed_at': datetime.utcnow().isoformat()
        }


@celery_app.task(name='scheduled_retrain')
def scheduled_retrain_task():
    """
    Scheduled weekly retraining task
    Configured in Celery Beat schedule
    """
    print("[Celery] Starting scheduled model retraining...")
    
    result = train_model_task.delay(min_matches=10000, n_estimators=1000)
    
    print(f"[Celery] Retraining task started: {result.id}")
    return result.id


# ============================================================================
# CELERY BEAT SCHEDULE - Automated retraining
# ============================================================================

celery_app.conf.beat_schedule = {
    'retrain-model-weekly': {
        'task': 'scheduled_retrain',
        'schedule': 604800.0,  # 7 days in seconds
        'options': {'expires': 86400}  # Expire after 24 hours if not run
    }
}


import asyncio

