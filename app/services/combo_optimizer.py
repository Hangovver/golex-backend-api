"""
Combo Optimizer Service
========================
En iyi kombo bahisleri otomatik bulur.

Features:
- Seçilen pazarlardan en iyi kombo
- Expected Value (EV) hesaplama
- Kelly Criterion stake
- Manuel düzenleme seçeneği
"""

from typing import Dict, List
from app.ai_engine.models.kelly_criterion import KellyCriterion


class ComboOptimizerService:
    """Kombine optimize servisi"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.kelly = KellyCriterion()
    
    def find_best_combo(
        self,
        markets: List[Dict],  # [{"market": "KG_YES", "probability": 0.68, "odds": 1.85}, ...]
        bankroll: float = 10000.0
    ) -> Dict:
        """
        En iyi komboyu bul
        
        Args:
            markets: Market listesi
            bankroll: Bankroll
        
        Returns:
            {
                "selected_markets": [...],
                "combined_odds": 3.20,
                "combined_probability": 0.312,
                "ev": 48.8,
                "kelly_stake": 1100
            }
        """
        # En yüksek EV'li 3 marketi seç
        markets_with_ev = []
        for m in markets:
            ev = self.kelly.calculate_expected_value(
                probability=m['probability'],
                odds=m['odds']
            )
            markets_with_ev.append({**m, 'ev': ev})
        
        # EV'ye göre sırala
        markets_with_ev.sort(key=lambda x: x['ev'], reverse=True)
        
        # En iyi 3'ü al
        best_3 = markets_with_ev[:3]
        
        # Kombine oran ve olasılık
        combined_odds = 1.0
        combined_prob = 1.0
        for m in best_3:
            combined_odds *= m['odds']
            combined_prob *= m['probability']
        
        # Combined EV
        combined_ev = combined_odds * combined_prob * 100 - 100
        
        # Kelly stake
        kelly_stake = self.kelly.calculate_fractional_kelly(
            probability=combined_prob,
            odds=combined_odds,
            bankroll=bankroll,
            fraction=0.5
        )
        
        return {
            "selected_markets": [m['market'] for m in best_3],
            "combined_odds": round(combined_odds, 2),
            "combined_probability": round(combined_prob, 3),
            "ev": round(combined_ev, 1),
            "kelly_stake": round(kelly_stake, 2)
        }

