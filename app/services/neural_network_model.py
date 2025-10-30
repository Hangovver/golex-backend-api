"""
Neural Network Model for Football Match Prediction
PROFESSIONAL BETTING SYNDICATE GRADE - Deep Learning
Uses TensorFlow/Keras for complex pattern recognition
NO SIMPLIFICATION - Production-ready ensemble component
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pickle
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss, brier_score_loss, accuracy_score
from sqlalchemy.orm import Session

# TensorFlow/Keras
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks

from app.services.feature_engineering import FeatureEngineer
from app.services.player_modeling import PlayerImpactModel


class NeuralNetworkPredictor:
    """
    Professional Deep Neural Network for match prediction
    Multi-layer perceptron with dropout and batch normalization
    Based on modern betting syndicate architectures
    """
    
    def __init__(self, db: Session, model_dir: str = "models/neural_network"):
        self.db = db
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.feature_engineer = FeatureEngineer(db)
        self.player_impact = PlayerImpactModel(db)
        
        # Neural Network model
        self.model: Optional[keras.Model] = None
        self.scaler: Optional[StandardScaler] = None
        
        # Model metadata
        self.model_version = "1.0.0"
        self.training_date: Optional[datetime] = None
        self.feature_names: List[str] = []
        
        # Performance metrics
        self.metrics = {
            'accuracy': 0.0,
            'log_loss': 0.0,
            'brier_score': 0.0,
            'val_accuracy': 0.0
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
        Predict match outcome probabilities using Neural Network
        Returns: {home_win: float, draw: float, away_win: float, confidence: float}
        """
        
        # Extract features
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
        
        # Convert to array
        if not self.feature_names:
            self.feature_names = sorted(features.keys())
        
        feature_array = np.array([features.get(f, 0.0) for f in self.feature_names]).reshape(1, -1)
        
        # If model not trained, use fallback
        if self.model is None or self.scaler is None:
            return self._fallback_prediction(features)
        
        # Scale features
        feature_scaled = self.scaler.transform(feature_array)
        
        # Predict probabilities (softmax output)
        predictions = self.model.predict(feature_scaled, verbose=0)[0]
        
        prob_home = float(predictions[0])
        prob_draw = float(predictions[1])
        prob_away = float(predictions[2])
        
        # Already normalized by softmax, but ensure sum=1.0
        total = prob_home + prob_draw + prob_away
        prob_home /= total
        prob_draw /= total
        prob_away /= total
        
        # Calculate confidence
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
            'model_type': 'neural_network'
        }
    
    async def train(
        self,
        min_matches: int = 5000,
        test_size: float = 0.2,
        epochs: int = 100,
        batch_size: int = 64,
        learning_rate: float = 0.001
    ) -> Dict:
        """
        Train Neural Network on historical data
        Uses early stopping and learning rate scheduling
        """
        
        print(f"[NeuralNet] Starting model training...")
        print(f"[NeuralNet] Fetching training data (min {min_matches} matches)...")
        
        # Fetch training data
        X, y = await self._prepare_training_data(min_matches=min_matches)
        
        if len(X) < 100:
            raise ValueError(f"Insufficient training data: {len(X)} samples")
        
        print(f"[NeuralNet] Loaded {len(X)} samples with {X.shape[1]} features")
        
        # Convert labels to one-hot encoding
        y_categorical = self._encode_labels(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_categorical, test_size=test_size, random_state=42, stratify=y
        )
        
        print(f"[NeuralNet] Train: {len(X_train)}, Test: {len(X_test)}")
        
        # Feature scaling (critical for neural networks)
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Build model architecture
        print("[NeuralNet] Building model architecture...")
        self.model = self._build_model(input_dim=X_train.shape[1], learning_rate=learning_rate)
        
        # Callbacks
        early_stop = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        )
        
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=5,
            min_lr=1e-6,
            verbose=1
        )
        
        # Train model
        print("[NeuralNet] Training...")
        history = self.model.fit(
            X_train_scaled, y_train,
            validation_data=(X_test_scaled, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
        
        # Calculate metrics
        print("[NeuralNet] Calculating metrics...")
        y_pred_proba = self.model.predict(X_test_scaled, verbose=0)
        y_pred_class = np.argmax(y_pred_proba, axis=1)
        y_test_class = np.argmax(y_test, axis=1)
        
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
            'val_accuracy': round(float(history.history['val_accuracy'][-1]), 4),
            'train_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        # Update metadata
        self.training_date = datetime.utcnow()
        
        # Save model
        self.save_model()
        
        print(f"[NeuralNet] Training complete!")
        print(f"[NeuralNet] Accuracy: {self.metrics['accuracy']:.4f}")
        print(f"[NeuralNet] Val Accuracy: {self.metrics['val_accuracy']:.4f}")
        print(f"[NeuralNet] Log Loss: {self.metrics['log_loss']:.4f}")
        print(f"[NeuralNet] Brier Score: {self.metrics['brier_score']:.4f}")
        
        return {
            'status': 'success',
            'metrics': self.metrics,
            'model_version': self.model_version,
            'training_date': self.training_date.isoformat(),
            'features_count': len(self.feature_names),
            'epochs_trained': len(history.history['loss'])
        }
    
    def _build_model(self, input_dim: int, learning_rate: float) -> keras.Model:
        """
        Build deep neural network architecture
        
        Architecture:
        - Input layer (input_dim features)
        - Dense 256 + BatchNorm + Dropout
        - Dense 128 + BatchNorm + Dropout
        - Dense 64 + BatchNorm + Dropout
        - Dense 32 + BatchNorm + Dropout
        - Output layer (3 classes - softmax)
        """
        
        model = models.Sequential([
            # Input layer
            layers.Input(shape=(input_dim,)),
            
            # Hidden layer 1
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Hidden layer 2
            layers.Dense(128, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            
            # Hidden layer 3
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Hidden layer 4
            layers.Dense(32, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.2),
            
            # Output layer (3 classes: Home Win, Draw, Away Win)
            layers.Dense(3, activation='softmax')
        ])
        
        # Compile model
        optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
        
        model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        print(model.summary())
        
        return model
    
    def _encode_labels(self, y: np.ndarray) -> np.ndarray:
        """
        Convert labels to one-hot encoding
        1 (home win) -> [1, 0, 0]
        0 (draw) -> [0, 1, 0]
        -1 (away win) -> [0, 0, 1]
        """
        y_encoded = np.zeros((len(y), 3))
        
        for i, label in enumerate(y):
            if label == 1:  # Home win
                y_encoded[i] = [1, 0, 0]
            elif label == 0:  # Draw
                y_encoded[i] = [0, 1, 0]
            else:  # Away win (-1)
                y_encoded[i] = [0, 0, 1]
        
        return y_encoded
    
    async def _prepare_training_data(self, min_matches: int) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from historical fixtures"""
        from sqlalchemy import text
        
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
        
        print(f"[NeuralNet] Processing {len(fixtures)} fixtures...")
        
        X_list = []
        y_list = []
        
        for i, fixture in enumerate(fixtures):
            if i % 500 == 0:
                print(f"[NeuralNet] Processed {i}/{len(fixtures)}...")
            
            try:
                features = await self.feature_engineer.extract_all_features(
                    fixture_id=fixture['id'],
                    home_team_id=fixture['home_team_id'],
                    away_team_id=fixture['away_team_id'],
                    league_id=fixture['league_id'],
                    fixture_date=fixture['date']
                )
                
                player_features = await self._extract_player_impact_features(
                    fixture['home_team_id'],
                    fixture['away_team_id'],
                    fixture['date']
                )
                features.update(player_features)
                
                if not self.feature_names:
                    self.feature_names = sorted(features.keys())
                
                feature_array = [features.get(f, 0.0) for f in self.feature_names]
                
                # Determine outcome
                if fixture['home_score'] > fixture['away_score']:
                    outcome = 1
                elif fixture['home_score'] < fixture['away_score']:
                    outcome = -1
                else:
                    outcome = 0
                
                X_list.append(feature_array)
                y_list.append(outcome)
                
            except Exception as e:
                print(f"[NeuralNet] Error processing fixture {fixture['id']}: {e}")
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
        
        home_prob = 0.46
        draw_prob = 0.27
        away_prob = 0.27
        
        form_diff = (home_form - away_form) / 6.0
        home_prob += form_diff * 0.2
        away_prob -= form_diff * 0.2
        
        total = home_prob + draw_prob + away_prob
        
        return {
            'home_win': round(home_prob / total, 4),
            'draw': round(draw_prob / total, 4),
            'away_win': round(away_prob / total, 4),
            'confidence': 0.5,
            'model_version': 'fallback',
            'features_used': 0,
            'model_type': 'neural_network'
        }
    
    def save_model(self):
        """Save model and scaler to disk"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        # Save Keras model
        model_path = self.model_dir / f'model_{timestamp}.h5'
        self.model.save(model_path)
        
        # Save scaler
        scaler_path = self.model_dir / f'scaler_{timestamp}.pkl'
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save metadata
        metadata = {
            'model_version': self.model_version,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'feature_names': self.feature_names,
            'metrics': self.metrics
        }
        
        metadata_path = self.model_dir / f'metadata_{timestamp}.pkl'
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        # Save "latest" versions
        self.model.save(self.model_dir / 'model_latest.h5')
        with open(self.model_dir / 'scaler_latest.pkl', 'wb') as f:
            pickle.dump(self.scaler, f)
        with open(self.model_dir / 'metadata_latest.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"[NeuralNet] Model saved to {self.model_dir}")
    
    def load_model(self):
        """Load model and scaler from disk"""
        try:
            model_path = self.model_dir / 'model_latest.h5'
            scaler_path = self.model_dir / 'scaler_latest.pkl'
            metadata_path = self.model_dir / 'metadata_latest.pkl'
            
            if not all([model_path.exists(), scaler_path.exists(), metadata_path.exists()]):
                print("[NeuralNet] No pre-trained model found. Will use fallback.")
                return
            
            self.model = keras.models.load_model(model_path)
            
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.model_version = metadata['model_version']
            self.training_date = datetime.fromisoformat(metadata['training_date']) if metadata['training_date'] else None
            self.feature_names = metadata['feature_names']
            self.metrics = metadata['metrics']
            
            print(f"[NeuralNet] Model loaded successfully!")
            print(f"[NeuralNet] Version: {self.model_version}")
            print(f"[NeuralNet] Accuracy: {self.metrics.get('accuracy', 'N/A')}")
            
        except Exception as e:
            print(f"[NeuralNet] Error loading model: {e}")
            print("[NeuralNet] Will use fallback prediction.")

