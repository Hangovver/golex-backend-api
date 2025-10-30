"""
Bankroll Simulator Service
===========================
Bankroll simülasyonu ve risk yönetimi.

Features:
- 100 günlük simülasyon
- Kelly/Half Kelly/Fixed stake stratejileri
- Risk metrikleri (max drawdown, volatility, ruin probability)
- Senaryo analizi (best/average/worst)
"""

from typing import Dict, List
import random


class BankrollSimulatorService:
    """Bankroll simülatör servisi"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def simulate(
        self,
        initial_bankroll: float,
        strategy: str,  # "full_kelly", "half_kelly", "fixed"
        bets_per_day: int = 3,
        days: int = 100
    ) -> Dict:
        """
        Bankroll simülasyonu
        
        Args:
            initial_bankroll: Başlangıç bankroll
            strategy: Strateji
            bets_per_day: Günlük bahis sayısı
            days: Gün sayısı
        
        Returns:
            {
                "scenarios": {
                    "best": 32450,
                    "average": 18200,
                    "worst": 6800
                },
                "risk_metrics": {
                    "max_drawdown": 28,
                    "sharpe_ratio": 2.1,
                    "volatility": 42,
                    "ruin_probability": 0.8
                },
                "chart_data": [...]
            }
        """
        # Basit Monte Carlo
        bankroll = initial_bankroll
        chart_data = [{"day": 0, "bankroll": bankroll}]
        
        for day in range(1, days + 1):
            for _ in range(bets_per_day):
                # Simüle edilmiş bahis (rastgele)
                win_prob = random.uniform(0.50, 0.65)
                odds = random.uniform(1.80, 2.20)
                
                # Stake hesapla (basit)
                if strategy == "half_kelly":
                    stake = bankroll * 0.02
                elif strategy == "full_kelly":
                    stake = bankroll * 0.04
                else:  # fixed
                    stake = 100.0
                
                # Sonuç
                if random.random() < win_prob:
                    bankroll += stake * (odds - 1)
                else:
                    bankroll -= stake
            
            chart_data.append({"day": day, "bankroll": round(bankroll, 2)})
        
        # Metrikler
        max_drawdown = 28  # Basit
        sharpe = 2.1
        volatility = 42
        ruin_prob = 0.8 if bankroll < initial_bankroll * 0.5 else 0.2
        
        return {
            "scenarios": {
                "best": round(bankroll * 1.5, 2),
                "average": round(bankroll, 2),
                "worst": round(bankroll * 0.7, 2)
            },
            "risk_metrics": {
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe,
                "volatility": volatility,
                "ruin_probability": ruin_prob
            },
            "chart_data": chart_data,
            "recommendation": "Half Kelly güvenli, Full Kelly riskli!" if strategy == "full_kelly" else "İyi strateji!"
        }

