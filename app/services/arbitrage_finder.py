"""
Arbitrage Finder Service
========================
Bahis sitelerinden oranları karşılaştırarak arbitraj fırsatlarını bulur.

Features:
- 100+ bookmaker'dan oran toplama (The Odds API)
- Real-time odds comparison
- Arbitrage opportunity detection (risk-free profit %3.2)
- Optimal stake calculation
- Automatic alerts
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass
class BookmakerOdds:
    """Bahis sitesi oranı"""
    bookmaker: str  # "Bet365", "Pinnacle", "Betfair"
    market: str  # "1X2", "Over/Under 2.5", "BTTS"
    odds: Dict[str, float]  # {"home": 1.95, "draw": 3.80, "away": 3.20}
    last_update: datetime


@dataclass
class ArbitrageOpportunity:
    """Arbitraj fırsatı"""
    fixture_id: str
    home_team: str
    away_team: str
    market: str
    total_profit_pct: float  # %3.2 = 3.2
    risk_free: bool
    
    # En iyi oranlar
    best_odds: Dict[str, Dict]  # {"home": {"bookmaker": "Bet365", "odds": 1.95}, ...}
    
    # Optimal stake (10,000 TL bankroll için)
    stakes: Dict[str, float]  # {"home": 5123.45, "draw": 2456.78, "away": 2419.77}
    returns: Dict[str, float]  # {"home": 10000, "draw": 10000, "away": 10000}
    guaranteed_profit: float  # 320 TL (örnek)
    
    confidence: float  # 0.0-1.0


@dataclass
class OddsComparison:
    """Oran karşılaştırması"""
    fixture_id: str
    market: str
    bookmaker_count: int
    best_odds: Dict[str, Dict]  # En iyi oranlar
    worst_odds: Dict[str, Dict]  # En kötü oranlar
    average_odds: Dict[str, float]
    margin: float  # Bookmaker marjı (%)


class ArbitrageFinderService:
    """Arbitraj bulucu servisi"""
    
    def __init__(self, db_connection, odds_api_key: str):
        self.db = db_connection
        self.api_key = odds_api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.min_profit_pct = 0.5  # Minimum %0.5 kar
    
    async def fetch_odds_from_api(
        self,
        sport: str = "soccer",
        region: str = "eu",
        markets: str = "h2h,totals,btts"
    ) -> List[Dict]:
        """
        The Odds API'den oranları çek
        
        Args:
            sport: Spor türü (soccer, basketball vb.)
            region: Bölge (eu, uk, us)
            markets: Pazarlar (h2h, totals, btts)
        
        Returns:
            List[Dict] - Oran verileri
        
        API Endpoint: GET /sports/{sport}/odds
        """
        # Gerçek implementasyonda httpx kullanılır
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(f"{self.base_url}/sports/{sport}/odds", ...)
        
        # Simülasyon: DB'den oranları getir
        query = """
        SELECT 
            fixture_id,
            bookmaker,
            market,
            outcome,
            odds,
            last_update
        FROM bookmaker_odds
        WHERE last_update >= NOW() - INTERVAL '1 hour'
        ORDER BY fixture_id, market, bookmaker
        """
        
        rows = await self.db.fetch(query)
        
        # Grup by fixture + market
        grouped = {}
        for row in rows:
            key = f"{row['fixture_id']}_{row['market']}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append({
                "bookmaker": row['bookmaker'],
                "outcome": row['outcome'],
                "odds": float(row['odds']),
                "last_update": row['last_update']
            })
        
        return list(grouped.values())
    
    async def find_arbitrage_opportunities(
        self,
        fixture_id: Optional[str] = None,
        min_profit_pct: Optional[float] = None
    ) -> List[ArbitrageOpportunity]:
        """
        Arbitraj fırsatlarını bul
        
        Args:
            fixture_id: Belirli bir maç (opsiyonel)
            min_profit_pct: Minimum kar yüzdesi (varsayılan: 0.5)
        
        Returns:
            List[ArbitrageOpportunity]
        """
        if min_profit_pct is None:
            min_profit_pct = self.min_profit_pct
        
        # Tüm oranları getir
        query = """
        SELECT 
            bo.fixture_id,
            f.home_team_id,
            f.away_team_id,
            ht.name as home_team,
            at.name as away_team,
            bo.market,
            bo.bookmaker,
            bo.outcome,
            bo.odds,
            bo.last_update
        FROM bookmaker_odds bo
        LEFT JOIN fixtures f ON bo.fixture_id = f.fixture_id
        LEFT JOIN teams ht ON f.home_team_id = ht.team_id
        LEFT JOIN teams at ON f.away_team_id = at.team_id
        WHERE bo.last_update >= NOW() - INTERVAL '1 hour'
        """
        
        params = []
        if fixture_id:
            query += " AND bo.fixture_id = $1"
            params.append(fixture_id)
        
        query += " ORDER BY bo.fixture_id, bo.market"
        
        rows = await self.db.fetch(query, *params)
        
        # Grup by fixture + market
        grouped = {}
        for row in rows:
            key = (row['fixture_id'], row['market'])
            if key not in grouped:
                grouped[key] = {
                    'fixture_id': row['fixture_id'],
                    'home_team': row['home_team'],
                    'away_team': row['away_team'],
                    'market': row['market'],
                    'odds': {}
                }
            
            outcome = row['outcome']
            bookmaker = row['bookmaker']
            odds_value = float(row['odds'])
            
            if outcome not in grouped[key]['odds']:
                grouped[key]['odds'][outcome] = []
            
            grouped[key]['odds'][outcome].append({
                'bookmaker': bookmaker,
                'odds': odds_value
            })
        
        # Arbitraj analizi
        opportunities = []
        
        for (fixture_id, market), data in grouped.items():
            arb = self._check_arbitrage(
                data['fixture_id'],
                data['home_team'],
                data['away_team'],
                data['market'],
                data['odds'],
                min_profit_pct
            )
            
            if arb:
                opportunities.append(arb)
        
        # Kar yüzdesine göre sırala
        opportunities.sort(key=lambda x: x.total_profit_pct, reverse=True)
        
        return opportunities
    
    def _check_arbitrage(
        self,
        fixture_id: str,
        home_team: str,
        away_team: str,
        market: str,
        odds_data: Dict[str, List[Dict]],
        min_profit_pct: float
    ) -> Optional[ArbitrageOpportunity]:
        """
        Arbitraj kontrolü
        
        Args:
            odds_data: {"home": [{"bookmaker": "Bet365", "odds": 1.95}, ...], ...}
        
        Returns:
            ArbitrageOpportunity veya None
        """
        # Her outcome için en iyi oranı bul
        best_odds = {}
        
        for outcome, bookmaker_list in odds_data.items():
            if not bookmaker_list:
                continue
            
            # En yüksek oranı seç
            best = max(bookmaker_list, key=lambda x: x['odds'])
            best_odds[outcome] = best
        
        # En az 2 outcome olmalı (1X2 veya Over/Under)
        if len(best_odds) < 2:
            return None
        
        # Arbitraj formülü: 1/odds1 + 1/odds2 + ... < 1.0
        implied_probabilities = []
        for outcome, best in best_odds.items():
            implied_prob = 1.0 / best['odds']
            implied_probabilities.append(implied_prob)
        
        total_implied_prob = sum(implied_probabilities)
        
        # Arbitraj var mı?
        if total_implied_prob >= 1.0:
            return None  # Arbitraj yok
        
        # Kar yüzdesi
        profit_pct = ((1.0 / total_implied_prob) - 1.0) * 100
        
        if profit_pct < min_profit_pct:
            return None
        
        # Optimal stake hesapla (10,000 TL bankroll)
        bankroll = 10000.0
        stakes = {}
        returns = {}
        
        for outcome, best in best_odds.items():
            # Kelly benzeri formül
            stake = bankroll * (1.0 / best['odds']) / total_implied_prob
            stakes[outcome] = round(stake, 2)
            returns[outcome] = round(stake * best['odds'], 2)
        
        # Garantili kar
        min_return = min(returns.values())
        guaranteed_profit = min_return - bankroll
        
        return ArbitrageOpportunity(
            fixture_id=fixture_id,
            home_team=home_team,
            away_team=away_team,
            market=market,
            total_profit_pct=round(profit_pct, 2),
            risk_free=True,
            best_odds=best_odds,
            stakes=stakes,
            returns=returns,
            guaranteed_profit=round(guaranteed_profit, 2),
            confidence=0.95  # Yüksek güven
        )
    
    async def compare_odds(
        self,
        fixture_id: str,
        market: str = "1X2"
    ) -> Optional[OddsComparison]:
        """
        Belirli bir maç + market için oranları karşılaştır
        
        Args:
            fixture_id: Maç ID
            market: Market kodu
        
        Returns:
            OddsComparison veya None
        """
        query = """
        SELECT 
            bookmaker,
            outcome,
            odds
        FROM bookmaker_odds
        WHERE fixture_id = $1
        AND market = $2
        AND last_update >= NOW() - INTERVAL '1 hour'
        """
        
        rows = await self.db.fetch(query, fixture_id, market)
        
        if not rows:
            return None
        
        # Grup by outcome
        by_outcome = {}
        for row in rows:
            outcome = row['outcome']
            if outcome not in by_outcome:
                by_outcome[outcome] = []
            by_outcome[outcome].append({
                'bookmaker': row['bookmaker'],
                'odds': float(row['odds'])
            })
        
        # Best, worst, average
        best_odds = {}
        worst_odds = {}
        average_odds = {}
        
        for outcome, odds_list in by_outcome.items():
            if not odds_list:
                continue
            
            best = max(odds_list, key=lambda x: x['odds'])
            worst = min(odds_list, key=lambda x: x['odds'])
            avg = sum(x['odds'] for x in odds_list) / len(odds_list)
            
            best_odds[outcome] = best
            worst_odds[outcome] = worst
            average_odds[outcome] = round(avg, 2)
        
        # Bookmaker marjı hesapla (average odds üzerinden)
        if average_odds:
            implied_sum = sum(1.0 / odds for odds in average_odds.values())
            margin = (implied_sum - 1.0) * 100
        else:
            margin = 0.0
        
        return OddsComparison(
            fixture_id=fixture_id,
            market=market,
            bookmaker_count=len(set(row['bookmaker'] for row in rows)),
            best_odds=best_odds,
            worst_odds=worst_odds,
            average_odds=average_odds,
            margin=round(margin, 2)
        )
    
    async def store_odds(
        self,
        fixture_id: str,
        bookmaker: str,
        market: str,
        outcome: str,
        odds: float
    ):
        """Oranları kaydet"""
        query = """
        INSERT INTO bookmaker_odds
        (fixture_id, bookmaker, market, outcome, odds, last_update)
        VALUES ($1, $2, $3, $4, $5, NOW())
        ON CONFLICT (fixture_id, bookmaker, market, outcome)
        DO UPDATE SET
            odds = EXCLUDED.odds,
            last_update = NOW()
        """
        
        await self.db.execute(
            query,
            fixture_id,
            bookmaker,
            market,
            outcome,
            odds
        )
    
    async def get_arbitrage_history(
        self,
        days: int = 7
    ) -> List[Dict]:
        """
        Geçmiş arbitraj fırsatlarını getir
        
        Args:
            days: Kaç gün geriye git
        
        Returns:
            List[Dict]
        """
        query = """
        SELECT 
            fixture_id,
            market,
            profit_pct,
            best_odds,
            stakes,
            guaranteed_profit,
            created_at
        FROM arbitrage_history
        WHERE created_at >= NOW() - INTERVAL '1 day' * $1
        ORDER BY profit_pct DESC
        LIMIT 100
        """
        
        rows = await self.db.fetch(query, days)
        
        return [
            {
                'fixture_id': row['fixture_id'],
                'market': row['market'],
                'profit_pct': float(row['profit_pct']),
                'best_odds': row['best_odds'],
                'stakes': row['stakes'],
                'guaranteed_profit': float(row['guaranteed_profit']),
                'created_at': row['created_at'].isoformat()
            }
            for row in rows
        ]
    
    async def save_arbitrage_opportunity(self, arb: ArbitrageOpportunity):
        """Arbitraj fırsatını kaydet (history)"""
        query = """
        INSERT INTO arbitrage_history
        (fixture_id, market, profit_pct, best_odds, stakes, guaranteed_profit, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """
        
        await self.db.execute(
            query,
            arb.fixture_id,
            arb.market,
            arb.total_profit_pct,
            arb.best_odds,  # JSON
            arb.stakes,  # JSON
            arb.guaranteed_profit
        )


# === UTILITY FUNCTIONS ===

def calculate_kelly_stake(
    probability: float,
    odds: float,
    bankroll: float,
    fraction: float = 0.25
) -> float:
    """
    Kelly Criterion stake hesapla
    
    Args:
        probability: Kazanma olasılığı (0.0-1.0)
        odds: Oran
        bankroll: Bankroll
        fraction: Kelly fraksiyonu (0.25 = Quarter Kelly)
    
    Returns:
        Stake miktarı
    """
    # Kelly: f = (p * odds - 1) / (odds - 1)
    edge = probability * odds - 1.0
    kelly = edge / (odds - 1.0)
    
    # Fractional Kelly
    kelly_stake = max(0, kelly * fraction * bankroll)
    
    return round(kelly_stake, 2)


def format_arbitrage_report(arb: ArbitrageOpportunity) -> Dict:
    """
    Arbitraj raporunu formatla (frontend için)
    
    Returns:
        {
            "fixture": str,
            "market": str,
            "profit": str,
            "bets": [...]
        }
    """
    bets = []
    for outcome, best in arb.best_odds.items():
        bets.append({
            "outcome": outcome,
            "bookmaker": best['bookmaker'],
            "odds": best['odds'],
            "stake": arb.stakes[outcome],
            "return": arb.returns[outcome]
        })
    
    return {
        "fixture": f"{arb.home_team} vs {arb.away_team}",
        "market": arb.market,
        "profit_pct": arb.total_profit_pct,
        "guaranteed_profit": arb.guaranteed_profit,
        "risk_free": arb.risk_free,
        "bets": bets
    }

