"""
Admin Initialize Endpoint
Otomatik Migration + Initialize
Her şeyi tek seferde yapar - kullanıcı uğraşmaz
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from pathlib import Path
from typing import Dict
import os

from app.db.session import get_db
from app.security.rbac import require_role
from app.tasks.professional_tasks import initialize_professional_system_task
from app.services.data_ingestion_service import DataIngestionService
from app.services.elo_calculator import ELOCalculator
import asyncio

router = APIRouter(prefix="/admin", tags=["admin"])


def run_migration_func(db: Session) -> Dict:
    """Run database migration from SQL file"""
    migration_file = Path(__file__).parent.parent.parent / "db" / "migrations" / "002_professional_betting_system.sql"
    
    if not migration_file.exists():
        raise HTTPException(status_code=404, detail=f"Migration dosyası bulunamadı: {migration_file}")
    
    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        executed = 0
        errors = []
        
        for statement in statements:
            if statement and len(statement) > 10:
                try:
                    db.execute(text(statement))
                    executed += 1
                except Exception as e:
                    # Ignore "already exists" errors
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        errors.append(f"Statement {executed+1}: {str(e)[:100]}")
        
        db.commit()
        
        # Verify tables
        inspector = inspect(db.bind)
        existing_tables = inspector.get_table_names()
        required_tables = [
            'team_elo_ratings', 'referees', 'referee_match_stats',
            'fixture_weather', 'betting_odds_history', 'goalkeeper_stats',
            'team_setpiece_stats', 'managers', 'team_manager_history',
            'data_ingestion_log', 'ml_model_registry', 'feature_cache'
        ]
        created_tables = [t for t in required_tables if t in existing_tables]
        
        return {
            "status": "success",
            "statements_executed": executed,
            "tables_created": len(created_tables),
            "total_tables": len(required_tables),
            "errors": errors[:5] if errors else []
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration hatası: {str(e)}")


@router.post("/initialize", dependencies=[Depends(require_role('admin'))])
async def initialize_system(
    background_tasks: BackgroundTasks,
    run_migration: bool = True,
    run_initialize: bool = True,
    db: Session = Depends(get_db)
):
    """
    Otomatik Migration + Initialize
    Her şeyi tek seferde yapar - kullanıcı uğraşmaz
    
    Steps:
    1. Database migration (002_professional_betting_system.sql)
    2. System initialize (celery task - 2-4 saat sürebilir)
    """
    results = {
        "migration": None,
        "initialize": None,
        "status": "pending"
    }
    
    try:
        # Step 1: Migration
        if run_migration:
            print("[Initialize] Step 1/2: Running database migration...")
            migration_result = run_migration_func(db)
            results["migration"] = migration_result
            print(f"[Initialize] Migration: {migration_result['status']} - {migration_result['tables_created']}/{migration_result['total_tables']} tables")
        
        # Step 2: Initialize (background task or direct)
        if run_initialize:
            print("[Initialize] Step 2/2: Starting system initialize...")
            print("[Initialize] ⚠️  Bu işlem 2-4 saat sürebilir!")
            
            try:
                # Try Celery first (if Redis available)
                task = initialize_professional_system_task.delay()
                results["initialize"] = {
                    "status": "started",
                    "task_id": task.id,
                    "method": "celery",
                    "message": "Initialize task Celery ile başlatıldı. İlerlemeyi görmek için Celery worker loglarını kontrol et.",
                    "estimated_time": "2-4 hours"
                }
                print(f"[Initialize] Task ID: {task.id}")
            except Exception as celery_error:
                # Fallback: Run directly without Celery (if Redis not available)
                print(f"[Initialize] Celery hatası (Redis yok?): {celery_error}")
                print("[Initialize] Redis olmadan direkt çalıştırılıyor...")
                
                # Start background task (direct Python, no Celery)
                def run_initialize_direct():
                    try:
                        from app.tasks.professional_tasks import (
                            ingest_historical_data_task,
                            recalculate_all_elos_task,
                            collect_referee_stats_task,
                            train_all_models_task
                        )
                        from sqlalchemy.orm import Session
                        from app.db.session import SessionLocal
                        
                        db = SessionLocal()
                        
                        try:
                            # Step 1: Ingest data
                            print("[Init] Step 1/4: Ingesting historical data...")
                            ingest_result = ingest_historical_data_task.apply(
                                args=([39, 140, 135, 78, 61], ['2022', '2023', '2024'], 5000)
                            ).get()
                            
                            # Step 2: Calculate ELO
                            print("[Init] Step 2/4: Calculating ELO ratings...")
                            elo_result = recalculate_all_elos_task.apply().get()
                            
                            # Step 3: Collect referee stats
                            print("[Init] Step 3/4: Collecting referee stats...")
                            referee_result = collect_referee_stats_task.apply(args=(730,)).get()
                            
                            # Step 4: Train models
                            print("[Init] Step 4/4: Training ML models...")
                            train_result = train_all_models_task.apply(args=(5000, 500)).get()
                            
                            print("[Init] ✅ Professional Betting System fully initialized!")
                            
                        finally:
                            db.close()
                            
                    except Exception as e:
                        print(f"[Init] ❌ Initialize hatası: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Run in background thread (don't wait)
                import threading
                thread = threading.Thread(target=run_initialize_direct, daemon=True)
                thread.start()
                
                results["initialize"] = {
                    "status": "started",
                    "method": "direct",
                    "message": "Initialize direkt başlatıldı (Redis yok, Celery kullanılmadı). İlerleme loglarda görünecek.",
                    "estimated_time": "2-4 hours",
                    "note": "Redis olmadan çalışıyor - arka planda thread olarak çalışıyor"
                }
                print("[Initialize] Background thread başlatıldı")
        
        results["status"] = "success"
        
        return {
            "message": "✅ Initialize başlatıldı!",
            "results": results,
            "next_steps": [
                "Migration tamamlandı" if run_migration else "Migration atlandı",
                "Initialize task arka planda çalışıyor (2-4 saat)",
                "İlerlemeyi görmek için: Railway → Backend API → Logs"
            ]
        }
        
    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)
        raise HTTPException(status_code=500, detail=f"Initialize hatası: {str(e)}")


@router.get("/initialize/status")
async def get_initialize_status(db: Session = Depends(get_db)):
    """Check initialization status"""
    
    # Check migration
    inspector = inspect(db.bind)
    existing_tables = inspector.get_table_names()
    required_tables = [
        'team_elo_ratings', 'referees', 'referee_match_stats',
        'fixture_weather', 'betting_odds_history', 'goalkeeper_stats',
        'team_setpiece_stats', 'managers', 'team_manager_history',
        'data_ingestion_log', 'ml_model_registry', 'feature_cache'
    ]
    migration_complete = all(t in existing_tables for t in required_tables)
    
    # Check data
    fixture_count = db.execute(text("SELECT COUNT(*) FROM fixtures WHERE status = 'FT'")).scalar() or 0
    elo_count = db.execute(text("SELECT COUNT(*) FROM team_elo_ratings")).scalar() or 0
    
    # Check models
    model_count = db.execute(text("SELECT COUNT(*) FROM ml_model_registry WHERE is_active = true")).scalar() or 0
    
    return {
        "migration": {
            "complete": migration_complete,
            "tables_created": len([t for t in required_tables if t in existing_tables]),
            "total_tables": len(required_tables)
        },
        "data": {
            "fixtures": fixture_count,
            "elo_ratings": elo_count,
            "models": model_count
        },
        "ready": migration_complete and fixture_count >= 5000 and model_count >= 1
    }

