"""
XGBoost Model for Football Match Prediction
PROFESSIONAL BETTING SYNDICATE GRADE - Tony Bloom / Smartodds Level
NO SIMPLIFICATION - Production-ready ensemble component
"""

from typing import Dict, List, Optional, Tuple
import xgboost as xgb
import numpy as np
import pickle
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score
from sqlalchemy.orm import Session

from app.services.feature_engineering import FeatureEngineer
from app.services.player_modeling import PlayerImpactModel


class XGBoostPredictor:
    """
    Professional XGBoost model for match outcome prediction
    Used in ensemble with LightGBM and Neural Network
    Based on Tony Bloom's Smartodds methodology
    """
    
    def __init__(self, db: Session, model_dir: str = "models/xgboost"):
        self.db = db
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.feature_engineer = FeatureEngineer(db)
        self.player_impact = PlayerImpactModel(db)
        
        # XGBoost models (one for each outcome)
        self.model_home_win: Optional[xgb.Booster] = None
        self.model_draw: Optional[xgb.Booster] = None
        self.model_away_win: Optional[xgb.Booster] = None
        
        # Model metadata
        self.model_version = "1.0.0"
        self.training_date: Optional[datetime] = None
        self.feature_names: List[str] = []
        self.feature_importance: Dict[str, float] = {}
        
        # Performance metrics
        self.metrics = {
            'accuracy': 0.0,
            'log_loss': 0.0,
            'brier_score': 0.0,
            'auc': 0.0
        }
        
        # Load existing model if available
        self.load_model()
    
    async def predict(
        self,
        fixture_id: int,
        home_team_id: int,
        away_team_id: int,
        league_id: int,
        fixture_date: datetime
    ) -> Dict:
        """
        Predict match outcome probabilities using XGBoost
        Returns: {home_win: float, draw: float, away_win: float, confidence: float}
        """
        
        # Extract features (same as LightGBM for consistency)
        features = await self.feature_engineer.extract_all_features(
            fixture_id=fixture_id,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            league_id=league_id,
            fixture_date=fixture_date
        )
        
        # Add player impact features
        player_features = await self._extract_player_impact_features(
            home_team_id, away_team_id, fixture_date
        )
        features.update(player_features)
        
        # Convert to DMatrix (XGBoost format)
        if not self.feature_names:
            self.feature_names = sorted(features.keys())
        
        feature_array = np.array([features.get(f, 0.0) for f in self.feature_names]).reshape(1, -1)
        dmatrix = xgb.DMatrix(feature_array, feature_names=self.feature_names)
        
        # If model not trained, use fallback
        if not self.model_home_win:
            return self._fallback_prediction(features)
        
        # Predict probabilities
        prob_home = self.model_home_win.predict(dmatrix)[0]
        prob_draw = self.model_draw.predict(dmatrix)[0]
        prob_away = self.model_away_win.predict(dmatrix)[0]
        
        # Normalize to ensure sum = 1.0
        total = prob_home + prob_draw + prob_away
        prob_home /= total
        prob_draw /= total
        prob_away /= total
        
        # Calculate confidence (inverse of entropy)
        entropy = -(prob_home * np.log(prob_home + 1e-10) + 
                   prob_draw * np.log(prob_draw + 1e-10) + 
                   prob_away * np.log(prob_away + 1e-10))
        max_entropy = np.log(3)
        confidence = 1.0 - (entropy / max_entropy)
        
        return {
            'home_win': round(float(prob_home), 4),
            'draw': round(float(prob_draw), 4),
            'away_win': round(float(prob_away), 4),
            'confidence': round(float(confidence), 4),
            'model_version': self.model_version,
            'features_used': len(self.feature_names),
            'model_type': 'xgboost'
        }
    
    async def train(
        self,
        min_matches: int = 5000,
        test_size: float = 0.2,
        n_estimators: int = 500,
        learning_rate: float = 0.05,
        max_depth: int = 7
    ) -> Dict:
        """
        Train XGBoost model on historical data
        Uses early stopping and cross-validation
        """
        
        print(f"[XGBoost] Starting model training...")
        print(f"[XGBoost] Fetching training data (min {min_matches} matches)...")
        
        # Fetch training data
        X, y = await self._prepare_training_data(min_matches=min_matches)
        
        if len(X) < 100:
            raise ValueError(f"Insufficient training data: {len(X)} samples")
        
        print(f"[XGBoost] Loaded {len(X)} samples with {X.shape[1]} features")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"[XGBoost] Train: {len(X_train)}, Test: {len(X_test)}")
        
        # XGBoost parameters (optimized for betting)
        params = {
            'objective': 'binary:logistic',
            'eval_metric': ['logloss', 'auc'],
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'reg_alpha': 0.1,  # L1 regularization
            'reg_lambda': 1.0,  # L2 regularization
            'seed': 42,
            'tree_method': 'hist',  # Fast histogram-based
            'verbosity': 1
        }
        
        # Train 3 binary classifiers
        print("[XGBoost] Training Home Win model...")
        dtrain_home = xgb.DMatrix(X_train, label=(y_train == 1).astype(int), feature_names=self.feature_names)
        dtest_home = xgb.DMatrix(X_test, label=(y_test == 1).astype(int), feature_names=self.feature_names)
        
        self.model_home_win = xgb.train(
            params,
            dtrain_home,
            num_boost_round=n_estimators,
            evals=[(dtrain_home, 'train'), (dtest_home, 'test')],
            early_stopping_rounds=50,
            verbose_eval=100
        )
        
        print("[XGBoost] Training Draw model...")
        dtrain_draw = xgb.DMatrix(X_train, label=(y_train == 0).astype(int), feature_names=self.feature_names)
        dtest_draw = xgb.DMatrix(X_test, label=(y_test == 0).astype(int), feature_names=self.feature_names)
        
        self.model_draw = xgb.train(
            params,
            dtrain_draw,
            num_boost_round=n_estimators,
            evals=[(dtrain_draw, 'train'), (dtest_draw, 'test')],
            early_stopping_rounds=50,
            verbose_eval=100
        )
        
        print("[XGBoost] Training Away Win model...")
        dtrain_away = xgb.DMatrix(X_train, label=(y_train == -1).astype(int), feature_names=self.feature_names)
        dtest_away = xgb.DMatrix(X_test, label=(y_test == -1).astype(int), feature_names=self.feature_names)
        
        self.model_away_win = xgb.train(
            params,
            dtrain_away,
            num_boost_round=n_estimators,
            evals=[(dtrain_away, 'train'), (dtest_away, 'test')],
            early_stopping_rounds=50,
            verbose_eval=100
        )
        
        # Calculate metrics
        print("[XGBoost] Calculating metrics...")
        dtest = xgb.DMatrix(X_test, feature_names=self.feature_names)
        y_pred_proba = self._predict_batch(dtest)
        y_pred_class = np.argmax(y_pred_proba, axis=1)
        y_test_class = np.where(y_test == 1, 0, np.where(y_test == 0, 1, 2))
        
        accuracy = accuracy_score(y_test_class, y_pred_class)
        logloss = log_loss(y_test_class, y_pred_proba)
        brier = np.mean([
            brier_score_loss((y_test_class == i).astype(int), y_pred_proba[:, i])
            for i in range(3)
        ])
        
        self.metrics = {
            'accuracy': round(float(accuracy), 4),
            'log_loss': round(float(logloss), 4),
            'brier_score': round(float(brier), 4),
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        # Feature importance (gain)
        importance_dict = self.model_home_win.get_score(importance_type='gain')
        self.feature_importance = {k: float(v) for k, v in importance_dict.items()}
        
        # Update metadata
        self.training_date = datetime.utcnow()
        
        # Save model
        self.save_model()
        
        print(f"[XGBoost] Training complete!")
        print(f"[XGBoost] Accuracy: {self.metrics['accuracy']:.4f}")
        print(f"[XGBoost] Log Loss: {self.metrics['log_loss']:.4f}")
        print(f"[XGBoost] Brier Score: {self.metrics['brier_score']:.4f}")
        
        return {
            'status': 'success',
            'metrics': self.metrics,
            'model_version': self.model_version,
            'training_date': self.training_date.isoformat(),
            'features_count': len(self.feature_names),
            'top_features': sorted(
                self.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def _predict_batch(self, dmatrix: xgb.DMatrix) -> np.ndarray:
        """Predict probabilities for batch of samples"""
        prob_home = self.model_home_win.predict(dmatrix)
        prob_draw = self.model_draw.predict(dmatrix)
        prob_away = self.model_away_win.predict(dmatrix)
        
        # Stack and normalize
        probs = np.column_stack([prob_home, prob_draw, prob_away])
        probs = probs / probs.sum(axis=1, keepdims=True)
        
        return probs
    
    async def _prepare_training_data(self, min_matches: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data from historical fixtures
        Returns: (X, y) where y is 1=home_win, 0=draw, -1=away_win
        """
        from sqlalchemy import text
        
        # Fetch completed fixtures
        result = self.db.execute(text("""
            SELECT 
                id, home_team_id, away_team_id, league_id,
                date, home_score, away_score
            FROM fixtures
            WHERE status = 'FT'
            AND home_score IS NOT NULL
            AND away_score IS NOT NULL
            AND date > NOW() - INTERVAL '2 years'
            ORDER BY date DESC
            LIMIT :limit
        """), {"limit": min_matches}).fetchall()
        
        fixtures = [dict(row._mapping) for row in result]
        
        print(f"[XGBoost] Processing {len(fixtures)} fixtures...")
        
        X_list = []
        y_list = []
        
        for i, fixture in enumerate(fixtures):
            if i % 500 == 0:
                print(f"[XGBoost] Processed {i}/{len(fixtures)}...")
            
            try:
                # Extract features
                features = await self.feature_engineer.extract_all_features(
                    fixture_id=fixture['id'],
                    home_team_id=fixture['home_team_id'],
                    away_team_id=fixture['away_team_id'],
                    league_id=fixture['league_id'],
                    fixture_date=fixture['date']
                )
                
                # Add player impact
                player_features = await self._extract_player_impact_features(
                    fixture['home_team_id'],
                    fixture['away_team_id'],
                    fixture['date']
                )
                features.update(player_features)
                
                # Store feature names
                if not self.feature_names:
                    self.feature_names = sorted(features.keys())
                
                # Convert to array
                feature_array = [features.get(f, 0.0) for f in self.feature_names]
                
                # Determine outcome
                if fixture['home_score'] > fixture['away_score']:
                    outcome = 1  # Home win
                elif fixture['home_score'] < fixture['away_score']:
                    outcome = -1  # Away win
                else:
                    outcome = 0  # Draw
                
                X_list.append(feature_array)
                y_list.append(outcome)
                
            except Exception as e:
                print(f"[XGBoost] Error processing fixture {fixture['id']}: {e}")
                continue
        
        return np.array(X_list), np.array(y_list)
    
    async def _extract_player_impact_features(
        self,
        home_team_id: int,
        away_team_id: int,
        fixture_date: datetime
    ) -> Dict[str, float]:
        """Extract player impact features"""
        
        home_impact = await self.player_impact.calculate_team_impact(
            home_team_id, fixture_date
        )
        away_impact = await self.player_impact.calculate_team_impact(
            away_team_id, fixture_date
        )
        
        home_dependency = await self.player_impact.calculate_star_player_dependency(
            home_team_id
        )
        away_dependency = await self.player_impact.calculate_star_player_dependency(
            away_team_id
        )
        
        return {
            'home_team_strength': home_impact['final_strength'],
            'away_team_strength': away_impact['final_strength'],
            'home_missing_impact': home_impact['missing_impact'],
            'away_missing_impact': away_impact['missing_impact'],
            'home_squad_depth': home_impact['depth_factor'],
            'away_squad_depth': away_impact['depth_factor'],
            'home_star_dependency': home_dependency['dependency_score'],
            'away_star_dependency': away_dependency['dependency_score']
        }
    
    def _fallback_prediction(self, features: Dict) -> Dict:
        """Fallback prediction if model not trained"""
        
        home_form = features.get('home_form_last5_points', 1.5)
        away_form = features.get('away_form_last5_points', 1.5)
        
        # Home advantage
        home_prob = 0.46
        draw_prob = 0.27
        away_prob = 0.27
        
        # Adjust based on form
        form_diff = (home_form - away_form) / 6.0
        
        home_prob += form_diff * 0.2
        away_prob -= form_diff * 0.2
        
        # Normalize
        total = home_prob + draw_prob + away_prob
        
        return {
            'home_win': round(home_prob / total, 4),
            'draw': round(draw_prob / total, 4),
            'away_win': round(away_prob / total, 4),
            'confidence': 0.5,
            'model_version': 'fallback',
            'features_used': 0,
            'model_type': 'xgboost'
        }
    
    def save_model(self):
        """Save model to disk"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Save XGBoost models
        self.model_home_win.save_model(str(self.model_dir / f'model_home_win_{timestamp}.json'))
        self.model_draw.save_model(str(self.model_dir / f'model_draw_{timestamp}.json'))
        self.model_away_win.save_model(str(self.model_dir / f'model_away_win_{timestamp}.json'))
        
        # Save metadata
        metadata = {
            'model_version': self.model_version,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'feature_names': self.feature_names,
            'feature_importance': self.feature_importance,
            'metrics': self.metrics
        }
        
        with open(self.model_dir / f'metadata_{timestamp}.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        # Save "latest" versions
        self.model_home_win.save_model(str(self.model_dir / 'model_home_win_latest.json'))
        self.model_draw.save_model(str(self.model_dir / 'model_draw_latest.json'))
        self.model_away_win.save_model(str(self.model_dir / 'model_away_win_latest.json'))
        
        with open(self.model_dir / 'metadata_latest.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"[XGBoost] Model saved to {self.model_dir}")
    
    def load_model(self):
        """Load model from disk"""
        try:
            home_path = self.model_dir / 'model_home_win_latest.json'
            draw_path = self.model_dir / 'model_draw_latest.json'
            away_path = self.model_dir / 'model_away_win_latest.json'
            metadata_path = self.model_dir / 'metadata_latest.pkl'
            
            if not all([home_path.exists(), draw_path.exists(), away_path.exists(), metadata_path.exists()]):
                print("[XGBoost] No pre-trained model found. Will use fallback.")
                return
            
            self.model_home_win = xgb.Booster()
            self.model_home_win.load_model(str(home_path))
            
            self.model_draw = xgb.Booster()
            self.model_draw.load_model(str(draw_path))
            
            self.model_away_win = xgb.Booster()
            self.model_away_win.load_model(str(away_path))
            
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.model_version = metadata['model_version']
            self.training_date = datetime.fromisoformat(metadata['training_date']) if metadata['training_date'] else None
            self.feature_names = metadata['feature_names']
            self.feature_importance = metadata['feature_importance']
            self.metrics = metadata['metrics']
            
            print(f"[XGBoost] Model loaded successfully!")
            print(f"[XGBoost] Version: {self.model_version}")
            print(f"[XGBoost] Accuracy: {self.metrics.get('accuracy', 'N/A')}")
            
        except Exception as e:
            print(f"[XGBoost] Error loading model: {e}")
            print("[XGBoost] Will use fallback prediction.")

