"""
Celery Application
Background task processing for GOLEX
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "golex",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.data_sync_tasks",
        "app.tasks.notification_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (Beat schedule)
celery_app.conf.beat_schedule = {
    # Sync live matches every 30 seconds
    "sync-live-matches": {
        "task": "app.tasks.data_sync_tasks.sync_live_matches",
        "schedule": 30.0,
    },
    
    # Sync today's fixtures every 5 minutes
    "sync-today-fixtures": {
        "task": "app.tasks.data_sync_tasks.sync_today_fixtures",
        "schedule": 300.0,
    },
    
    # Calculate attack momentum for live matches every 1 minute
    "calculate-live-momentum": {
        "task": "app.tasks.data_sync_tasks.calculate_live_momentum",
        "schedule": 60.0,
    },
    
    # Update player ratings for finished matches every 10 minutes
    "update-player-ratings": {
        "task": "app.tasks.data_sync_tasks.update_player_ratings",
        "schedule": 600.0,
    },
    
    # Sync standings every hour
    "sync-standings": {
        "task": "app.tasks.data_sync_tasks.sync_standings",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Clean old data every day at 3 AM
    "cleanup-old-data": {
        "task": "app.tasks.data_sync_tasks.cleanup_old_data",
        "schedule": crontab(hour=3, minute=0),
    },
}

if __name__ == "__main__":
    celery_app.start()

