"""
Startup Validation & Auto-Fix
Validates system readiness and auto-fixes common issues
PRODUCTION GRADE - Ensures system is ready before accepting requests
NO SIMPLIFICATION - Comprehensive checks
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from pathlib import Path
import os
from datetime import datetime
from typing import Dict, List


class StartupValidator:
    """
    Validates professional betting system readiness
    Checks:
    - Database tables exist
    - Models are trained
    - Minimum data available
    - API keys configured
    - ELO ratings initialized
    
    Auto-fixes when possible
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.issues = []
        self.warnings = []
        self.auto_fixed = []
    
    async def validate_all(self) -> Dict:
        """Run all validation checks"""
        
        print("\n" + "="*60)
        print("🔍 PROFESSIONAL BETTING SYSTEM - STARTUP VALIDATION")
        print("="*60 + "\n")
        
        # 1. Database schema
        await self._validate_database_schema()
        
        # 2. Data availability
        await self._validate_data_availability()
        
        # 3. ML models
        await self._validate_ml_models()
        
        # 4. API keys
        await self._validate_api_keys()
        
        # 5. ELO ratings
        await self._validate_elo_ratings()
        
        # 6. Referee data
        await self._validate_referee_data()
        
        # Summary
        return self._generate_summary()
    
    async def _validate_database_schema(self):
        """Check if all required tables exist"""
        print("[1/6] Validating database schema...")
        
        required_tables = [
            'fixtures', 'teams', 'players', 'leagues',
            'team_elo_ratings', 'referees', 'referee_match_stats',
            'fixture_weather', 'betting_odds_history',
            'goalkeeper_stats', 'team_setpiece_stats',
            'managers', 'team_manager_history',
            'data_ingestion_log', 'ml_model_registry',
            'feature_cache'
        ]
        
        inspector = inspect(self.db.bind)
        existing_tables = inspector.get_table_names()
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            self.issues.append({
                'category': 'database',
                'severity': 'CRITICAL',
                'message': f'Missing tables: {", ".join(missing_tables)}',
                'fix': 'Run: psql -U golex -d golex_db -f app/db/migrations/002_professional_betting_system.sql'
            })
            print(f"   ❌ CRITICAL: Missing {len(missing_tables)} tables")
        else:
            print(f"   ✅ All {len(required_tables)} tables exist")
    
    async def _validate_data_availability(self):
        """Check if minimum data is available"""
        print("[2/6] Validating data availability...")
        
        # Check fixture count
        result = self.db.execute(text("SELECT COUNT(*) FROM fixtures WHERE status = 'FT'")).fetchone()
        fixture_count = result[0] if result else 0
        
        if fixture_count < 100:
            self.issues.append({
                'category': 'data',
                'severity': 'CRITICAL',
                'message': f'Only {fixture_count} fixtures available (need 5000+ for ML training)',
                'fix': 'Run: celery -A app.tasks.professional_tasks call initialize_professional_system'
            })
            print(f"   ❌ CRITICAL: Only {fixture_count} fixtures (need 5000+)")
        elif fixture_count < 5000:
            self.warnings.append({
                'category': 'data',
                'message': f'{fixture_count} fixtures available (recommended 5000+)',
                'impact': 'ML accuracy may be lower'
            })
            print(f"   ⚠️  WARNING: {fixture_count} fixtures (recommended 5000+)")
        else:
            print(f"   ✅ {fixture_count} fixtures available")
    
    async def _validate_ml_models(self):
        """Check if ML models are trained"""
        print("[3/6] Validating ML models...")
        
        models_to_check = {
            'lightgbm': 'models/lightgbm/model_home_win_latest.txt',
            'xgboost': 'models/xgboost/model_home_win_latest.json',
            'neural_network': 'models/neural_network/model_latest.h5'
        }
        
        missing_models = []
        
        for model_name, model_path in models_to_check.items():
            if not Path(model_path).exists():
                missing_models.append(model_name)
        
        if missing_models:
            self.issues.append({
                'category': 'models',
                'severity': 'HIGH',
                'message': f'Missing trained models: {", ".join(missing_models)}',
                'fix': 'Run: celery -A app.tasks.professional_tasks call train_all_models'
            })
            print(f"   ❌ HIGH: Missing {len(missing_models)} models")
        else:
            print(f"   ✅ All 3 models trained")
            
            # Check model freshness
            lgb_path = Path(models_to_check['lightgbm'])
            if lgb_path.exists():
                modified_time = datetime.fromtimestamp(lgb_path.stat().st_mtime)
                age_days = (datetime.now() - modified_time).days
                
                if age_days > 30:
                    self.warnings.append({
                        'category': 'models',
                        'message': f'Models are {age_days} days old',
                        'impact': 'Consider retraining'
                    })
                    print(f"   ⚠️  Models are {age_days} days old (retrain recommended)")
    
    async def _validate_api_keys(self):
        """Check if required API keys are configured"""
        print("[4/6] Validating API keys...")
        
        api_keys = {
            'API_FOOTBALL_KEY': os.getenv('API_FOOTBALL_KEY'),
            'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY')
        }
        
        missing_keys = [k for k, v in api_keys.items() if not v]
        
        if missing_keys:
            self.issues.append({
                'category': 'config',
                'severity': 'HIGH',
                'message': f'Missing API keys: {", ".join(missing_keys)}',
                'fix': 'Add to .env file or environment variables'
            })
            print(f"   ❌ HIGH: Missing {len(missing_keys)} API keys")
        else:
            print(f"   ✅ All API keys configured")
    
    async def _validate_elo_ratings(self):
        """Check if ELO ratings are initialized"""
        print("[5/6] Validating ELO ratings...")
        
        result = self.db.execute(text("SELECT COUNT(DISTINCT team_id) FROM team_elo_ratings")).fetchone()
        elo_count = result[0] if result else 0
        
        team_result = self.db.execute(text("SELECT COUNT(*) FROM teams")).fetchone()
        team_count = team_result[0] if team_result else 0
        
        if elo_count == 0:
            self.issues.append({
                'category': 'elo',
                'severity': 'HIGH',
                'message': 'No ELO ratings initialized',
                'fix': 'Run: celery -A app.tasks.professional_tasks call recalculate_all_elos'
            })
            print(f"   ❌ HIGH: No ELO ratings")
            
            # Auto-fix: Initialize default ELOs
            try:
                self.db.execute(text("""
                    INSERT INTO team_elo_ratings (team_id, date, elo_rating, matches_played)
                    SELECT id, CURRENT_TIMESTAMP, 1500.0, 0
                    FROM teams
                    ON CONFLICT (team_id, date) DO NOTHING
                """))
                self.db.commit()
                
                self.auto_fixed.append({
                    'category': 'elo',
                    'action': f'Initialized default ELO (1500) for {team_count} teams'
                })
                print(f"   🔧 AUTO-FIXED: Initialized {team_count} default ELOs")
            except Exception as e:
                print(f"   ⚠️  Auto-fix failed: {e}")
                
        elif elo_count < team_count:
            self.warnings.append({
                'category': 'elo',
                'message': f'Only {elo_count}/{team_count} teams have ELO ratings',
                'impact': 'Some teams may use default ELO'
            })
            print(f"   ⚠️  {elo_count}/{team_count} teams have ELO")
        else:
            print(f"   ✅ {elo_count} teams have ELO ratings")
    
    async def _validate_referee_data(self):
        """Check if referee data is available"""
        print("[6/6] Validating referee data...")
        
        result = self.db.execute(text("SELECT COUNT(*) FROM referee_match_stats")).fetchone()
        referee_stats_count = result[0] if result else 0
        
        if referee_stats_count == 0:
            self.warnings.append({
                'category': 'referee',
                'message': 'No referee statistics available',
                'impact': 'Referee features will use defaults'
            })
            print(f"   ⚠️  No referee stats (will use defaults)")
        else:
            print(f"   ✅ {referee_stats_count} referee match records")
    
    def _generate_summary(self) -> Dict:
        """Generate validation summary"""
        
        critical_count = len([i for i in self.issues if i.get('severity') == 'CRITICAL'])
        high_count = len([i for i in self.issues if i.get('severity') == 'HIGH'])
        
        print("\n" + "="*60)
        print("📋 VALIDATION SUMMARY")
        print("="*60)
        
        if not self.issues and not self.warnings:
            print("✅ ALL CHECKS PASSED - System ready for production!")
            status = 'READY'
        elif critical_count > 0:
            print(f"❌ {critical_count} CRITICAL ISSUE(S) - System NOT ready!")
            status = 'NOT_READY'
        elif high_count > 0:
            print(f"⚠️  {high_count} HIGH PRIORITY ISSUE(S) - Limited functionality")
            status = 'DEGRADED'
        else:
            print(f"⚠️  {len(self.warnings)} WARNING(S) - System functional with limitations")
            status = 'FUNCTIONAL'
        
        if self.auto_fixed:
            print(f"\n🔧 {len(self.auto_fixed)} ISSUE(S) AUTO-FIXED:")
            for fix in self.auto_fixed:
                print(f"   • {fix['action']}")
        
        if self.issues:
            print(f"\n❌ {len(self.issues)} ISSUE(S) FOUND:")
            for issue in self.issues:
                print(f"   • [{issue['severity']}] {issue['message']}")
                print(f"     Fix: {issue['fix']}")
        
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} WARNING(S):")
            for warning in self.warnings:
                print(f"   • {warning['message']}")
                if 'impact' in warning:
                    print(f"     Impact: {warning['impact']}")
        
        print("\n" + "="*60 + "\n")
        
        return {
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'issues': self.issues,
            'warnings': self.warnings,
            'auto_fixed': self.auto_fixed,
            'ready': status == 'READY'
        }


async def run_startup_validation(db: Session) -> Dict:
    """Convenience function to run validation"""
    validator = StartupValidator(db)
    return await validator.validate_all()

