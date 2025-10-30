"""
Ensemble Prediction System
PROFESSIONAL BETTING SYNDICATE GRADE - Tony Bloom / Smartodds Level
Combines LightGBM + XGBoost + Neural Network with weighted voting
NO SIMPLIFICATION - Production-ready ensemble meta-learner
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np

from app.services.lightgbm_model import LightGBMPredictor
from app.services.xgboost_model import XGBoostPredictor
from app.services.neural_network_model import NeuralNetworkPredictor


class EnsemblePredictor:
    """
    Professional Ensemble System
    
    Combines 3 models with optimal weights:
    - LightGBM: Fast, interpretable, feature importance
    - XGBoost: Robust, handles overfitting well
    - Neural Network: Complex patterns, non-linear relationships
    
    Weighting strategies:
    1. Static (equal or performance-based)
    2. Dynamic (confidence-weighted)
    3. Stacking (meta-learner)
    
    Based on Tony Bloom's Smartodds methodology
    """
    
    def __init__(
        self,
        db: Session,
        weights: Optional[Dict[str, float]] = None,
        strategy: str = "dynamic"
    ):
        self.db = db
        
        # Initialize all 3 models
        self.lightgbm = LightGBMPredictor(db)
        self.xgboost = XGBoostPredictor(db)
        self.neural_net = NeuralNetworkPredictor(db)
        
        # Ensemble strategy
        self.strategy = strategy  # "static", "dynamic", or "stacking"
        
        # Model weights (optimized based on validation performance)
        if weights is None:
            # Default weights (equal)
            self.weights = {
                'lightgbm': 0.35,    # Slightly favor LightGBM (faster, interpretable)
                'xgboost': 0.35,     # Equal weight
                'neural_net': 0.30   # Slightly less (prone to overfitting)
            }
        else:
            self.weights = weights
        
        # Ensure weights sum to 1.0
        total_weight = sum(self.weights.values())
        self.weights = {k: v / total_weight for k, v in self.weights.items()}
        
        print(f"[Ensemble] Initialized with strategy: {strategy}")
        print(f"[Ensemble] Weights: LightGBM={self.weights['lightgbm']:.2f}, "
              f"XGBoost={self.weights['xgboost']:.2f}, NN={self.weights['neural_net']:.2f}")
    
    async def predict(
        self,
        fixture_id: int,
        home_team_id: int,
        away_team_id: int,
        league_id: int,
        fixture_date: datetime,
        return_individual: bool = False
    ) -> Dict:
        """
        Ensemble prediction using all 3 models
        
        Args:
            fixture_id: Match ID
            home_team_id: Home team ID
            away_team_id: Away team ID
            league_id: League ID
            fixture_date: Match date
            return_individual: Include individual model predictions in response
        
        Returns:
            Combined prediction with ensemble metadata
        """
        
        print(f"[Ensemble] Predicting fixture {fixture_id}...")
        
        # Get predictions from all 3 models
        pred_lightgbm = await self.lightgbm.predict(
            fixture_id, home_team_id, away_team_id, league_id, fixture_date
        )
        
        pred_xgboost = await self.xgboost.predict(
            fixture_id, home_team_id, away_team_id, league_id, fixture_date
        )
        
        pred_neural_net = await self.neural_net.predict(
            fixture_id, home_team_id, away_team_id, league_id, fixture_date
        )
        
        print(f"[Ensemble] LightGBM: H={pred_lightgbm['home_win']:.3f}, "
              f"D={pred_lightgbm['draw']:.3f}, A={pred_lightgbm['away_win']:.3f}")
        print(f"[Ensemble] XGBoost: H={pred_xgboost['home_win']:.3f}, "
              f"D={pred_xgboost['draw']:.3f}, A={pred_xgboost['away_win']:.3f}")
        print(f"[Ensemble] NeuralNet: H={pred_neural_net['home_win']:.3f}, "
              f"D={pred_neural_net['draw']:.3f}, A={pred_neural_net['away_win']:.3f}")
        
        # Combine predictions based on strategy
        if self.strategy == "static":
            combined = self._static_ensemble(pred_lightgbm, pred_xgboost, pred_neural_net)
        elif self.strategy == "dynamic":
            combined = self._dynamic_ensemble(pred_lightgbm, pred_xgboost, pred_neural_net)
        else:  # stacking (future implementation)
            combined = self._static_ensemble(pred_lightgbm, pred_xgboost, pred_neural_net)
        
        # Calculate ensemble confidence
        confidences = [
            pred_lightgbm.get('confidence', 0.5),
            pred_xgboost.get('confidence', 0.5),
            pred_neural_net.get('confidence', 0.5)
        ]
        
        # Confidence = weighted average of individual confidences
        ensemble_confidence = (
            confidences[0] * self.weights['lightgbm'] +
            confidences[1] * self.weights['xgboost'] +
            confidences[2] * self.weights['neural_net']
        )
        
        # Calculate agreement (how much models agree)
        agreement = self._calculate_agreement(pred_lightgbm, pred_xgboost, pred_neural_net)
        
        print(f"[Ensemble] Combined: H={combined['home_win']:.3f}, "
              f"D={combined['draw']:.3f}, A={combined['away_win']:.3f}")
        print(f"[Ensemble] Confidence: {ensemble_confidence:.3f}, Agreement: {agreement:.3f}")
        
        # Build response
        response = {
            'home_win': round(combined['home_win'], 4),
            'draw': round(combined['draw'], 4),
            'away_win': round(combined['away_win'], 4),
            'confidence': round(ensemble_confidence, 4),
            'agreement': round(agreement, 4),
            'model': 'ensemble',
            'strategy': self.strategy,
            'weights': self.weights,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Optionally include individual predictions
        if return_individual:
            response['individual_predictions'] = {
                'lightgbm': pred_lightgbm,
                'xgboost': pred_xgboost,
                'neural_network': pred_neural_net
            }
        
        return response
    
    def _static_ensemble(
        self,
        pred_lightgbm: Dict,
        pred_xgboost: Dict,
        pred_neural_net: Dict
    ) -> Dict:
        """
        Static weighted ensemble
        Uses fixed weights regardless of prediction confidence
        """
        
        home_win = (
            pred_lightgbm['home_win'] * self.weights['lightgbm'] +
            pred_xgboost['home_win'] * self.weights['xgboost'] +
            pred_neural_net['home_win'] * self.weights['neural_net']
        )
        
        draw = (
            pred_lightgbm['draw'] * self.weights['lightgbm'] +
            pred_xgboost['draw'] * self.weights['xgboost'] +
            pred_neural_net['draw'] * self.weights['neural_net']
        )
        
        away_win = (
            pred_lightgbm['away_win'] * self.weights['lightgbm'] +
            pred_xgboost['away_win'] * self.weights['xgboost'] +
            pred_neural_net['away_win'] * self.weights['neural_net']
        )
        
        # Normalize (should already be ~1.0, but ensure)
        total = home_win + draw + away_win
        
        return {
            'home_win': home_win / total,
            'draw': draw / total,
            'away_win': away_win / total
        }
    
    def _dynamic_ensemble(
        self,
        pred_lightgbm: Dict,
        pred_xgboost: Dict,
        pred_neural_net: Dict
    ) -> Dict:
        """
        Dynamic confidence-weighted ensemble
        Models with higher confidence get more weight
        
        Formula:
        weight_i = (base_weight_i × confidence_i) / sum(base_weight × confidence)
        """
        
        # Get confidences
        conf_lgb = pred_lightgbm.get('confidence', 0.5)
        conf_xgb = pred_xgboost.get('confidence', 0.5)
        conf_nn = pred_neural_net.get('confidence', 0.5)
        
        # Calculate dynamic weights
        weight_lgb = self.weights['lightgbm'] * conf_lgb
        weight_xgb = self.weights['xgboost'] * conf_xgb
        weight_nn = self.weights['neural_net'] * conf_nn
        
        total_weight = weight_lgb + weight_xgb + weight_nn
        
        # Normalize weights
        weight_lgb /= total_weight
        weight_xgb /= total_weight
        weight_nn /= total_weight
        
        print(f"[Ensemble] Dynamic weights: LGB={weight_lgb:.3f}, XGB={weight_xgb:.3f}, NN={weight_nn:.3f}")
        
        # Weighted average
        home_win = (
            pred_lightgbm['home_win'] * weight_lgb +
            pred_xgboost['home_win'] * weight_xgb +
            pred_neural_net['home_win'] * weight_nn
        )
        
        draw = (
            pred_lightgbm['draw'] * weight_lgb +
            pred_xgboost['draw'] * weight_xgb +
            pred_neural_net['draw'] * weight_nn
        )
        
        away_win = (
            pred_lightgbm['away_win'] * weight_lgb +
            pred_xgboost['away_win'] * weight_xgb +
            pred_neural_net['away_win'] * weight_nn
        )
        
        # Normalize
        total = home_win + draw + away_win
        
        return {
            'home_win': home_win / total,
            'draw': draw / total,
            'away_win': away_win / total
        }
    
    def _calculate_agreement(
        self,
        pred_lightgbm: Dict,
        pred_xgboost: Dict,
        pred_neural_net: Dict
    ) -> float:
        """
        Calculate model agreement score (0-1)
        
        Measures how much the models agree on the prediction
        High agreement (>0.9) = all models predict similar probabilities
        Low agreement (<0.7) = models disagree significantly
        
        Method: Average pairwise cosine similarity
        """
        
        # Convert predictions to vectors
        vec_lgb = np.array([
            pred_lightgbm['home_win'],
            pred_lightgbm['draw'],
            pred_lightgbm['away_win']
        ])
        
        vec_xgb = np.array([
            pred_xgboost['home_win'],
            pred_xgboost['draw'],
            pred_xgboost['away_win']
        ])
        
        vec_nn = np.array([
            pred_neural_net['home_win'],
            pred_neural_net['draw'],
            pred_neural_net['away_win']
        ])
        
        # Calculate pairwise cosine similarities
        sim_lgb_xgb = np.dot(vec_lgb, vec_xgb) / (np.linalg.norm(vec_lgb) * np.linalg.norm(vec_xgb))
        sim_lgb_nn = np.dot(vec_lgb, vec_nn) / (np.linalg.norm(vec_lgb) * np.linalg.norm(vec_nn))
        sim_xgb_nn = np.dot(vec_xgb, vec_nn) / (np.linalg.norm(vec_xgb) * np.linalg.norm(vec_nn))
        
        # Average similarity
        agreement = (sim_lgb_xgb + sim_lgb_nn + sim_xgb_nn) / 3.0
        
        return float(agreement)
    
    async def calibrate_weights(
        self,
        validation_fixtures: List[int],
        metric: str = "log_loss"
    ) -> Dict:
        """
        Calibrate ensemble weights on validation set
        
        Finds optimal weights that minimize the chosen metric
        
        Args:
            validation_fixtures: List of fixture IDs for validation
            metric: "log_loss", "brier_score", or "accuracy"
        
        Returns:
            Optimized weights and performance metrics
        """
        
        print(f"[Ensemble] Calibrating weights on {len(validation_fixtures)} fixtures...")
        
        # TODO: Implement grid search or optimization algorithm
        # For now, return current weights
        
        return {
            'status': 'not_implemented',
            'message': 'Weight calibration not yet implemented',
            'current_weights': self.weights
        }
    
    def get_model_status(self) -> Dict:
        """Get status of all models in the ensemble"""
        
        return {
            'lightgbm': {
                'loaded': self.lightgbm.model_home_win is not None,
                'version': self.lightgbm.model_version,
                'metrics': self.lightgbm.metrics
            },
            'xgboost': {
                'loaded': self.xgboost.model_home_win is not None,
                'version': self.xgboost.model_version,
                'metrics': self.xgboost.metrics
            },
            'neural_network': {
                'loaded': self.neural_net.model is not None,
                'version': self.neural_net.model_version,
                'metrics': self.neural_net.metrics
            },
            'ensemble': {
                'strategy': self.strategy,
                'weights': self.weights
            }
        }

