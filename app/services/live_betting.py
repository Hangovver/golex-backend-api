"""
Live Betting Service
====================
Canlı maç verileri, real-time tahminler ve momentum analizi.

Features:
- Real-time match events (goller, kartlar, kornerler)
- Live statistics (şutlar, pozisyon, pas başarısı)
- Momentum calculation (son 10 dakika trendi)
- Live predictions (sonraki gol, maç sonu skoru)
- Value bet opportunities (canlı oranlar vs. tahmin)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics


class EventType(Enum):
    """Maç olayı tipi"""
    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    PENALTY = "penalty"
    VAR = "var"


class Momentum(Enum):
    """Momentum durumu"""
    STRONG_HOME = "strong_home"  # Ev sahibi baskılı
    MODERATE_HOME = "moderate_home"
    BALANCED = "balanced"  # Dengeli
    MODERATE_AWAY = "moderate_away"
    STRONG_AWAY = "strong_away"  # Deplasman baskılı


@dataclass
class LiveEvent:
    """Canlı maç olayı"""
    event_id: str
    fixture_id: str
    event_type: EventType
    minute: int
    team_id: str
    player_id: Optional[str]
    player_name: Optional[str]
    detail: Optional[str]  # "Normal Goal", "Penalty", "Own Goal"
    timestamp: datetime


@dataclass
class LiveStats:
    """Canlı maç istatistikleri"""
    fixture_id: str
    minute: int
    home_stats: Dict[str, float]  # {"shots": 12, "shots_on_target": 5, ...}
    away_stats: Dict[str, float]
    home_score: int
    away_score: int
    possession: Tuple[int, int]  # (home%, away%)
    momentum: Momentum
    updated_at: datetime


@dataclass
class LivePrediction:
    """Canlı tahmin"""
    fixture_id: str
    minute: int
    next_goal_prob: Dict[str, float]  # {"home": 0.48, "away": 0.32, "none": 0.20}
    next_goal_minute: int  # Sonraki gol tahmini dakika
    final_score_prob: Dict[str, float]  # {"2-1": 0.28, "2-2": 0.22, ...}
    recommended_bets: List[Dict]  # Value bet önerileri
    confidence: float


@dataclass
class MomentumAnalysis:
    """Momentum analizi"""
    current_momentum: Momentum
    momentum_score: float  # -1.0 (strong away) to +1.0 (strong home)
    last_10_minutes: Dict[str, any]
    dangerous_attacks: Dict[str, int]  # {"home": 3, "away": 1}
    key_events: List[LiveEvent]


class LiveBettingService:
    """Canlı bahis servisi"""
    
    def __init__(self, db_connection, api_football_key: str):
        self.db = db_connection
        self.api_key = api_football_key
        self.base_url = "https://v3.football.api-sports.io"
    
    async def get_live_fixtures(self, league_id: Optional[str] = None) -> List[Dict]:
        """
        Canlı maçları getir
        
        Args:
            league_id: Belirli bir lig (opsiyonel)
        
        Returns:
            List[Dict] - Canlı maç listesi
        
        API Endpoint: GET /fixtures?live=all
        """
        # API-Football'dan canlı maçları çek
        # Gerçek implementasyonda httpx kullanılır
        
        query = """
        SELECT 
            f.fixture_id,
            f.home_team_id,
            f.away_team_id,
            f.league_id,
            f.match_date,
            ht.name as home_team_name,
            at.name as away_team_name,
            ls.minute,
            ls.home_score,
            ls.away_score,
            ls.home_shots,
            ls.away_shots,
            ls.home_possession,
            ls.away_possession
        FROM fixtures f
        LEFT JOIN teams ht ON f.home_team_id = ht.team_id
        LEFT JOIN teams at ON f.away_team_id = at.team_id
        LEFT JOIN live_stats ls ON f.fixture_id = ls.fixture_id
        WHERE f.status = 'live'
        """
        
        params = []
        if league_id:
            query += " AND f.league_id = $1"
            params.append(league_id)
        
        query += " ORDER BY f.match_date DESC"
        
        rows = await self.db.fetch(query, *params)
        
        return [
            {
                "fixture_id": row['fixture_id'],
                "home_team": row['home_team_name'],
                "away_team": row['away_team_name'],
                "league_id": row['league_id'],
                "minute": row['minute'],
                "score": f"{row['home_score']}-{row['away_score']}",
                "stats": {
                    "shots": f"{row['home_shots']}-{row['away_shots']}",
                    "possession": f"{row['home_possession']}%-{row['away_possession']}%"
                }
            }
            for row in rows
        ]
    
    async def get_live_events(
        self,
        fixture_id: str,
        since_minute: Optional[int] = None
    ) -> List[LiveEvent]:
        """
        Maç olaylarını getir
        
        Args:
            fixture_id: Maç ID
            since_minute: Belirli bir dakikadan sonraki olaylar
        
        Returns:
            List[LiveEvent]
        
        API Endpoint: GET /fixtures/events?fixture={fixture_id}
        """
        query = """
        SELECT 
            event_id,
            fixture_id,
            event_type,
            minute,
            team_id,
            player_id,
            player_name,
            detail,
            timestamp
        FROM live_events
        WHERE fixture_id = $1
        """
        
        params = [fixture_id]
        
        if since_minute is not None:
            query += " AND minute >= $2"
            params.append(since_minute)
        
        query += " ORDER BY minute ASC, timestamp ASC"
        
        rows = await self.db.fetch(query, *params)
        
        return [
            LiveEvent(
                event_id=row['event_id'],
                fixture_id=row['fixture_id'],
                event_type=EventType(row['event_type']),
                minute=row['minute'],
                team_id=row['team_id'],
                player_id=row['player_id'],
                player_name=row['player_name'],
                detail=row['detail'],
                timestamp=row['timestamp']
            )
            for row in rows
        ]
    
    async def get_live_stats(self, fixture_id: str) -> Optional[LiveStats]:
        """
        Canlı maç istatistiklerini getir
        
        Args:
            fixture_id: Maç ID
        
        Returns:
            LiveStats veya None
        
        API Endpoint: GET /fixtures/statistics?fixture={fixture_id}
        """
        query = """
        SELECT 
            fixture_id,
            minute,
            home_score,
            away_score,
            home_shots,
            away_shots,
            home_shots_on_target,
            away_shots_on_target,
            home_possession,
            away_possession,
            home_passes,
            away_passes,
            home_pass_accuracy,
            away_pass_accuracy,
            home_fouls,
            away_fouls,
            home_corners,
            away_corners,
            home_offsides,
            away_offsides,
            home_yellow_cards,
            away_yellow_cards,
            home_red_cards,
            away_red_cards,
            updated_at
        FROM live_stats
        WHERE fixture_id = $1
        """
        
        row = await self.db.fetchrow(query, fixture_id)
        
        if not row:
            return None
        
        # Momentum hesapla
        momentum = await self._calculate_momentum(fixture_id, row)
        
        return LiveStats(
            fixture_id=row['fixture_id'],
            minute=row['minute'],
            home_stats={
                "shots": row['home_shots'],
                "shots_on_target": row['home_shots_on_target'],
                "passes": row['home_passes'],
                "pass_accuracy": row['home_pass_accuracy'],
                "fouls": row['home_fouls'],
                "corners": row['home_corners'],
                "offsides": row['home_offsides'],
                "yellow_cards": row['home_yellow_cards'],
                "red_cards": row['home_red_cards']
            },
            away_stats={
                "shots": row['away_shots'],
                "shots_on_target": row['away_shots_on_target'],
                "passes": row['away_passes'],
                "pass_accuracy": row['away_pass_accuracy'],
                "fouls": row['away_fouls'],
                "corners": row['away_corners'],
                "offsides": row['away_offsides'],
                "yellow_cards": row['away_yellow_cards'],
                "red_cards": row['away_red_cards']
            },
            home_score=row['home_score'],
            away_score=row['away_score'],
            possession=(row['home_possession'], row['away_possession']),
            momentum=momentum,
            updated_at=row['updated_at']
        )
    
    async def _calculate_momentum(self, fixture_id: str, stats_row) -> Momentum:
        """
        Momentum hesapla (son 10 dakika verileri)
        
        Returns:
            Momentum enum
        """
        # Son 10 dakika olaylarını getir
        current_minute = stats_row['minute']
        since_minute = max(0, current_minute - 10)
        
        events = await self.get_live_events(fixture_id, since_minute)
        
        # Puanlama sistemi
        home_momentum_score = 0.0
        away_momentum_score = 0.0
        
        # Maç için takım ID'lerini bul
        query = "SELECT home_team_id, away_team_id FROM fixtures WHERE fixture_id = $1"
        fixture = await self.db.fetchrow(query, fixture_id)
        
        if not fixture:
            return Momentum.BALANCED
        
        home_team_id = fixture['home_team_id']
        away_team_id = fixture['away_team_id']
        
        # Olaylara puan ver
        for event in events:
            if event.event_type == EventType.GOAL:
                if event.team_id == home_team_id:
                    home_momentum_score += 3.0
                else:
                    away_momentum_score += 3.0
            # Diğer olaylar daha az etki...
        
        # İstatistiklere göre
        home_shots = float(stats_row['home_shots'])
        away_shots = float(stats_row['away_shots'])
        home_possession = float(stats_row['home_possession'])
        away_possession = float(stats_row['away_possession'])
        
        # Basitleştirilmiş momentum
        total_shots = home_shots + away_shots
        if total_shots > 0:
            home_momentum_score += (home_shots / total_shots) * 2.0
            away_momentum_score += (away_shots / total_shots) * 2.0
        
        home_momentum_score += (home_possession / 100.0) * 1.0
        away_momentum_score += (away_possession / 100.0) * 1.0
        
        # Momentum belirle
        diff = home_momentum_score - away_momentum_score
        
        if diff > 2.0:
            return Momentum.STRONG_HOME
        elif diff > 0.5:
            return Momentum.MODERATE_HOME
        elif diff < -2.0:
            return Momentum.STRONG_AWAY
        elif diff < -0.5:
            return Momentum.MODERATE_AWAY
        else:
            return Momentum.BALANCED
    
    async def get_live_prediction(
        self,
        fixture_id: str,
        include_value_bets: bool = True
    ) -> Optional[LivePrediction]:
        """
        Canlı tahmin getir
        
        Args:
            fixture_id: Maç ID
            include_value_bets: Value bet önerilerini dahil et
        
        Returns:
            LivePrediction veya None
        """
        # Canlı istatistikleri getir
        stats = await self.get_live_stats(fixture_id)
        
        if not stats:
            return None
        
        # Maç bilgilerini getir
        query = """
        SELECT home_team_id, away_team_id FROM fixtures WHERE fixture_id = $1
        """
        fixture = await self.db.fetchrow(query, fixture_id)
        
        if not fixture:
            return None
        
        # xG verilerini getir (pre-match)
        query_xg = """
        SELECT home_xg_for, away_xg_for FROM fixture_stats WHERE fixture_id = $1
        """
        xg = await self.db.fetchrow(query_xg, fixture_id)
        
        # Basitleştirilmiş tahmin (gerçek implementasyonda ML model)
        home_xg = float(xg['home_xg_for']) if xg else 1.5
        away_xg = float(xg['away_xg_for']) if xg else 1.2
        
        # Momentum'a göre ayarla
        if stats.momentum == Momentum.STRONG_HOME:
            home_xg *= 1.2
            away_xg *= 0.8
        elif stats.momentum == Momentum.STRONG_AWAY:
            home_xg *= 0.8
            away_xg *= 1.2
        
        # Kalan süre (basit: 90 - current_minute)
        remaining_minutes = max(0, 90 - stats.minute)
        remaining_factor = remaining_minutes / 90.0
        
        home_xg_remaining = home_xg * remaining_factor
        away_xg_remaining = away_xg * remaining_factor
        
        # Sonraki gol olasılığı (Poisson)
        total_xg = home_xg_remaining + away_xg_remaining
        
        if total_xg > 0:
            next_goal_home = home_xg_remaining / total_xg
            next_goal_away = away_xg_remaining / total_xg
            next_goal_none = max(0, 1.0 - (total_xg / 2.0))
        else:
            next_goal_home = 0.33
            next_goal_away = 0.33
            next_goal_none = 0.34
        
        # Normalize
        total = next_goal_home + next_goal_away + next_goal_none
        next_goal_prob = {
            "home": round(next_goal_home / total, 3),
            "away": round(next_goal_away / total, 3),
            "none": round(next_goal_none / total, 3)
        }
        
        # Sonraki gol dakika tahmini
        if total_xg > 0:
            expected_goal_time = int(stats.minute + (remaining_minutes / (total_xg + 1)))
        else:
            expected_goal_time = 90
        
        # Maç sonu skoru (basit)
        final_score_prob = {
            f"{stats.home_score + 1}-{stats.away_score}": 0.25,
            f"{stats.home_score}-{stats.away_score + 1}": 0.22,
            f"{stats.home_score}-{stats.away_score}": 0.20,
            f"{stats.home_score + 1}-{stats.away_score + 1}": 0.15,
            f"{stats.home_score + 2}-{stats.away_score}": 0.10,
            f"{stats.home_score}-{stats.away_score + 2}": 0.08
        }
        
        # Value bet önerileri (TODO: Gerçek oranlarla karşılaştır)
        recommended_bets = []
        if include_value_bets:
            if next_goal_prob["home"] > 0.5:
                recommended_bets.append({
                    "market": "NEXT_GOAL_HOME",
                    "probability": next_goal_prob["home"],
                    "recommended": True,
                    "reason": "Strong home momentum"
                })
        
        return LivePrediction(
            fixture_id=fixture_id,
            minute=stats.minute,
            next_goal_prob=next_goal_prob,
            next_goal_minute=expected_goal_time,
            final_score_prob=final_score_prob,
            recommended_bets=recommended_bets,
            confidence=0.75  # Basit
        )
    
    async def store_live_event(self, event: LiveEvent):
        """Canlı olay kaydet"""
        query = """
        INSERT INTO live_events
        (event_id, fixture_id, event_type, minute, team_id, player_id, player_name, detail, timestamp)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (event_id) DO NOTHING
        """
        
        await self.db.execute(
            query,
            event.event_id,
            event.fixture_id,
            event.event_type.value,
            event.minute,
            event.team_id,
            event.player_id,
            event.player_name,
            event.detail,
            event.timestamp
        )
    
    async def update_live_stats(self, fixture_id: str, stats_data: Dict):
        """Canlı istatistikleri güncelle"""
        query = """
        INSERT INTO live_stats
        (fixture_id, minute, home_score, away_score, home_shots, away_shots,
         home_shots_on_target, away_shots_on_target, home_possession, away_possession,
         home_passes, away_passes, home_pass_accuracy, away_pass_accuracy,
         home_fouls, away_fouls, home_corners, away_corners,
         home_offsides, away_offsides, home_yellow_cards, away_yellow_cards,
         home_red_cards, away_red_cards, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, NOW())
        ON CONFLICT (fixture_id)
        DO UPDATE SET
            minute = EXCLUDED.minute,
            home_score = EXCLUDED.home_score,
            away_score = EXCLUDED.away_score,
            home_shots = EXCLUDED.home_shots,
            away_shots = EXCLUDED.away_shots,
            home_shots_on_target = EXCLUDED.home_shots_on_target,
            away_shots_on_target = EXCLUDED.away_shots_on_target,
            home_possession = EXCLUDED.home_possession,
            away_possession = EXCLUDED.away_possession,
            home_passes = EXCLUDED.home_passes,
            away_passes = EXCLUDED.away_passes,
            home_pass_accuracy = EXCLUDED.home_pass_accuracy,
            away_pass_accuracy = EXCLUDED.away_pass_accuracy,
            home_fouls = EXCLUDED.home_fouls,
            away_fouls = EXCLUDED.away_fouls,
            home_corners = EXCLUDED.home_corners,
            away_corners = EXCLUDED.away_corners,
            home_offsides = EXCLUDED.home_offsides,
            away_offsides = EXCLUDED.away_offsides,
            home_yellow_cards = EXCLUDED.home_yellow_cards,
            away_yellow_cards = EXCLUDED.away_yellow_cards,
            home_red_cards = EXCLUDED.home_red_cards,
            away_red_cards = EXCLUDED.away_red_cards,
            updated_at = NOW()
        """
        
        await self.db.execute(
            query,
            fixture_id,
            stats_data.get('minute', 0),
            stats_data.get('home_score', 0),
            stats_data.get('away_score', 0),
            stats_data.get('home_shots', 0),
            stats_data.get('away_shots', 0),
            stats_data.get('home_shots_on_target', 0),
            stats_data.get('away_shots_on_target', 0),
            stats_data.get('home_possession', 50),
            stats_data.get('away_possession', 50),
            stats_data.get('home_passes', 0),
            stats_data.get('away_passes', 0),
            stats_data.get('home_pass_accuracy', 0.0),
            stats_data.get('away_pass_accuracy', 0.0),
            stats_data.get('home_fouls', 0),
            stats_data.get('away_fouls', 0),
            stats_data.get('home_corners', 0),
            stats_data.get('away_corners', 0),
            stats_data.get('home_offsides', 0),
            stats_data.get('away_offsides', 0),
            stats_data.get('home_yellow_cards', 0),
            stats_data.get('away_yellow_cards', 0),
            stats_data.get('home_red_cards', 0),
            stats_data.get('away_red_cards', 0)
        )

