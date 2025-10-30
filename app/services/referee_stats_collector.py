"""
Referee Stats Collector
=======================
Hakem istatistiklerini toplar, hesaplar ve tahminlere etkisini analiz eder.

Features:
- Her maç sonrası hakem verilerini topla
- İstatistikleri hesapla (kart, penaltı, gol ortalaması)
- Lig ortalaması ile karşılaştır
- Market etkisini hesapla (CARDS, PENALTIES)
- Value bet fırsatlarını tespit et
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics


@dataclass
class RefereeStats:
    """Hakem istatistikleri"""
    referee_id: str
    referee_name: str
    total_matches: int
    avg_cards_per_match: float
    avg_yellow_per_match: float
    avg_red_per_match: float
    red_card_percentage: float
    avg_penalties_per_match: float
    avg_goals_per_match: float
    home_bias: float  # Ev sahibi avantajı etkisi
    strict_rating: float  # 0-10 arası sertlik puanı


@dataclass
class LeagueAverages:
    """Lig ortalamaları"""
    avg_cards: float
    avg_yellow: float
    avg_red: float
    red_card_pct: float
    avg_penalties: float
    avg_goals: float


@dataclass
class RefereeImpact:
    """Hakemin tahminlere etkisi"""
    market_code: str
    original_probability: float
    adjusted_probability: float
    change_percentage: float
    is_significant: bool  # %10'dan fazla değişim


class RefereeStatsCollector:
    """Hakem istatistiklerini toplar ve analiz eder"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.league_averages_cache = {}
    
    async def collect_referee_data(self, referee_id: str, referee_name: str, match_data: dict):
        """
        Maç sonrası hakem verilerini topla
        
        Args:
            referee_id: Hakem ID
            referee_name: Hakem adı
            match_data: Maç verileri (kartlar, penaltılar, goller)
        """
        query = """
        INSERT INTO referee_match_data 
        (referee_id, referee_name, fixture_id, match_date, league_id,
         yellow_cards, red_cards, penalties, total_goals, home_won)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (referee_id, fixture_id) 
        DO UPDATE SET
            yellow_cards = EXCLUDED.yellow_cards,
            red_cards = EXCLUDED.red_cards,
            penalties = EXCLUDED.penalties,
            total_goals = EXCLUDED.total_goals,
            home_won = EXCLUDED.home_won,
            updated_at = NOW()
        """
        
        await self.db.execute(
            query,
            referee_id,
            referee_name,
            match_data['fixture_id'],
            match_data['match_date'],
            match_data['league_id'],
            match_data['yellow_cards'],
            match_data['red_cards'],
            match_data['penalties'],
            match_data['total_goals'],
            match_data['home_won']
        )
    
    async def get_referee_stats(
        self, 
        referee_id: str, 
        last_n_matches: int = 20,
        league_id: Optional[str] = None
    ) -> Optional[RefereeStats]:
        """
        Hakemin istatistiklerini getir
        
        Args:
            referee_id: Hakem ID
            last_n_matches: Son N maç
            league_id: Belirli bir lig (None = tüm ligler)
        
        Returns:
            RefereeStats veya None
        """
        # Son N maç verilerini çek
        query = """
        SELECT 
            referee_id,
            referee_name,
            yellow_cards,
            red_cards,
            penalties,
            total_goals,
            home_won
        FROM referee_match_data
        WHERE referee_id = $1
        """
        
        params = [referee_id]
        
        if league_id:
            query += " AND league_id = $2"
            params.append(league_id)
        
        query += """
        ORDER BY match_date DESC
        LIMIT ${}
        """.format(len(params) + 1)
        
        params.append(last_n_matches)
        
        rows = await self.db.fetch(query, *params)
        
        if not rows or len(rows) == 0:
            return None
        
        # İstatistikleri hesapla
        total_matches = len(rows)
        total_yellow = sum(r['yellow_cards'] for r in rows)
        total_red = sum(r['red_cards'] for r in rows)
        total_cards = total_yellow + total_red
        total_penalties = sum(r['penalties'] for r in rows)
        total_goals = sum(r['total_goals'] for r in rows)
        home_wins = sum(1 for r in rows if r['home_won'])
        
        avg_cards = total_cards / total_matches
        avg_yellow = total_yellow / total_matches
        avg_red = total_red / total_matches
        red_pct = (total_red / total_matches) * 100
        avg_penalties = total_penalties / total_matches
        avg_goals = total_goals / total_matches
        home_bias = (home_wins / total_matches) - 0.5  # 0.5 = nötr
        
        # Sertlik puanı (0-10): Kart ortalamasına göre
        # 3.0 kart = 5 puan (orta), her +0.5 kart = +1 puan
        strict_rating = min(10, max(0, 5 + (avg_cards - 3.0) * 2))
        
        return RefereeStats(
            referee_id=referee_id,
            referee_name=rows[0]['referee_name'],
            total_matches=total_matches,
            avg_cards_per_match=round(avg_cards, 2),
            avg_yellow_per_match=round(avg_yellow, 2),
            avg_red_per_match=round(avg_red, 2),
            red_card_percentage=round(red_pct, 1),
            avg_penalties_per_match=round(avg_penalties, 2),
            avg_goals_per_match=round(avg_goals, 2),
            home_bias=round(home_bias, 3),
            strict_rating=round(strict_rating, 1)
        )
    
    async def get_league_averages(self, league_id: str) -> LeagueAverages:
        """
        Lig ortalamalarını getir (cache'li)
        
        Args:
            league_id: Lig ID
        
        Returns:
            LeagueAverages
        """
        # Cache kontrolü
        if league_id in self.league_averages_cache:
            cached_data, cached_time = self.league_averages_cache[league_id]
            if datetime.now() - cached_time < timedelta(hours=24):
                return cached_data
        
        # Son 3 ay verileri
        query = """
        SELECT 
            AVG(yellow_cards + red_cards) as avg_cards,
            AVG(yellow_cards) as avg_yellow,
            AVG(red_cards) as avg_red,
            (SUM(red_cards)::float / COUNT(*)::float * 100) as red_pct,
            AVG(penalties) as avg_penalties,
            AVG(total_goals) as avg_goals
        FROM referee_match_data
        WHERE league_id = $1
        AND match_date >= NOW() - INTERVAL '3 months'
        """
        
        row = await self.db.fetchrow(query, league_id)
        
        if not row:
            # Varsayılan değerler
            averages = LeagueAverages(
                avg_cards=3.5,
                avg_yellow=3.0,
                avg_red=0.15,
                red_card_pct=8.0,
                avg_penalties=0.20,
                avg_goals=2.7
            )
        else:
            averages = LeagueAverages(
                avg_cards=round(float(row['avg_cards'] or 3.5), 2),
                avg_yellow=round(float(row['avg_yellow'] or 3.0), 2),
                avg_red=round(float(row['avg_red'] or 0.15), 2),
                red_card_pct=round(float(row['red_pct'] or 8.0), 1),
                avg_penalties=round(float(row['avg_penalties'] or 0.20), 2),
                avg_goals=round(float(row['avg_goals'] or 2.7), 2)
            )
        
        # Cache'e kaydet
        self.league_averages_cache[league_id] = (averages, datetime.now())
        
        return averages
    
    def calculate_referee_impact(
        self,
        referee_stats: RefereeStats,
        league_averages: LeagueAverages,
        base_probabilities: Dict[str, float]
    ) -> List[RefereeImpact]:
        """
        Hakemin tahminlere etkisini hesapla
        
        Args:
            referee_stats: Hakem istatistikleri
            league_averages: Lig ortalamaları
            base_probabilities: Temel olasılıklar (market_code: probability)
        
        Returns:
            List[RefereeImpact]
        """
        impacts = []
        
        # 1. KART PAZARLARINDAKİ ETKİ
        card_markets = [
            'CARDS_O3.5', 'CARDS_O4.5', 'CARDS_O5.5',
            'YELLOW_O2.5', 'YELLOW_O3.5', 'YELLOW_O4.5'
        ]
        
        # Hakem/Lig kart oranı
        card_ratio = referee_stats.avg_cards_per_match / league_averages.avg_cards
        
        for market in card_markets:
            if market not in base_probabilities:
                continue
            
            base_prob = base_probabilities[market]
            
            # Threshold'u al (O4.5 -> 4.5)
            threshold = float(market.split('O')[1])
            
            # Hakemin ortalaması threshold'a göre ayarla
            if 'YELLOW' in market:
                avg_value = referee_stats.avg_yellow_per_match
            else:
                avg_value = referee_stats.avg_cards_per_match
            
            # Olasılık ayarlaması: ±%20'ye kadar
            if avg_value > threshold:
                multiplier = min(1.20, 1.0 + (avg_value - threshold) * 0.10)
            else:
                multiplier = max(0.80, 1.0 - (threshold - avg_value) * 0.10)
            
            adjusted_prob = min(0.95, base_prob * multiplier)
            change_pct = ((adjusted_prob - base_prob) / base_prob) * 100
            
            impacts.append(RefereeImpact(
                market_code=market,
                original_probability=round(base_prob, 3),
                adjusted_probability=round(adjusted_prob, 3),
                change_percentage=round(change_pct, 1),
                is_significant=abs(change_pct) > 10
            ))
        
        # 2. KIRMIZI KART ETKİSİ
        if 'RED_CARD_YES' in base_probabilities:
            base_prob = base_probabilities['RED_CARD_YES']
            
            # Hakem/Lig kırmızı kart oranı
            red_ratio = referee_stats.red_card_percentage / league_averages.red_card_pct
            multiplier = min(2.0, max(0.5, red_ratio))
            
            adjusted_prob = min(0.50, base_prob * multiplier)
            change_pct = ((adjusted_prob - base_prob) / base_prob) * 100
            
            impacts.append(RefereeImpact(
                market_code='RED_CARD_YES',
                original_probability=round(base_prob, 3),
                adjusted_probability=round(adjusted_prob, 3),
                change_percentage=round(change_pct, 1),
                is_significant=abs(change_pct) > 10
            ))
        
        # 3. PENALTI ETKİSİ
        if 'PENALTY_YES' in base_probabilities:
            base_prob = base_probabilities['PENALTY_YES']
            
            # Hakem/Lig penaltı oranı
            penalty_ratio = referee_stats.avg_penalties_per_match / league_averages.avg_penalties
            multiplier = min(1.5, max(0.7, penalty_ratio))
            
            adjusted_prob = min(0.50, base_prob * multiplier)
            change_pct = ((adjusted_prob - base_prob) / base_prob) * 100
            
            impacts.append(RefereeImpact(
                market_code='PENALTY_YES',
                original_probability=round(base_prob, 3),
                adjusted_probability=round(adjusted_prob, 3),
                change_percentage=round(change_pct, 1),
                is_significant=abs(change_pct) > 10
            ))
        
        return impacts
    
    async def get_referee_for_match(self, fixture_id: str) -> Optional[Dict]:
        """
        Maç için hakem bilgisini getir (API-Football'dan veya DB'den)
        
        Args:
            fixture_id: Maç ID
        
        Returns:
            {"referee_id": str, "referee_name": str} veya None
        """
        # Önce DB'den kontrol et
        query = """
        SELECT referee_id, referee_name
        FROM referee_match_data
        WHERE fixture_id = $1
        LIMIT 1
        """
        
        row = await self.db.fetchrow(query, fixture_id)
        
        if row:
            return {
                "referee_id": row['referee_id'],
                "referee_name": row['referee_name']
            }
        
        # API-Football'dan çek (fixture detayları)
        # NOT: API-Football'da hakem bilgisi fixture.referee field'ında
        # Bu kısım API entegrasyonu ile doldurulacak
        
        return None
    
    async def store_referee_info(self, fixture_id: str, referee_name: str):
        """
        API'den gelen hakem bilgisini kaydet
        
        Args:
            fixture_id: Maç ID
            referee_name: Hakem adı
        """
        # Hakem ID'sini isimden türet (basit hash)
        referee_id = f"ref_{hash(referee_name) % 100000}"
        
        query = """
        INSERT INTO referee_match_data
        (referee_id, referee_name, fixture_id, match_date)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (referee_id, fixture_id) DO NOTHING
        """
        
        await self.db.execute(query, referee_id, referee_name, fixture_id)
        
        return referee_id


# === UTILITY FUNCTIONS ===

def format_referee_report(
    referee_stats: RefereeStats,
    league_averages: LeagueAverages,
    impacts: List[RefereeImpact]
) -> Dict:
    """
    Hakem raporunu formatla (frontend için)
    
    Returns:
        {
            "referee": {...},
            "league_comparison": {...},
            "market_impacts": [...]
        }
    """
    return {
        "referee": {
            "id": referee_stats.referee_id,
            "name": referee_stats.referee_name,
            "total_matches": referee_stats.total_matches,
            "stats": {
                "avg_cards": referee_stats.avg_cards_per_match,
                "avg_yellow": referee_stats.avg_yellow_per_match,
                "avg_red": referee_stats.avg_red_per_match,
                "red_card_pct": referee_stats.red_card_percentage,
                "avg_penalties": referee_stats.avg_penalties_per_match,
                "avg_goals": referee_stats.avg_goals_per_match,
                "home_bias": referee_stats.home_bias,
                "strict_rating": referee_stats.strict_rating
            }
        },
        "league_comparison": {
            "cards": {
                "referee": referee_stats.avg_cards_per_match,
                "league": league_averages.avg_cards,
                "diff_pct": round(
                    ((referee_stats.avg_cards_per_match - league_averages.avg_cards) / league_averages.avg_cards) * 100,
                    1
                )
            },
            "red_cards": {
                "referee": referee_stats.red_card_percentage,
                "league": league_averages.red_card_pct,
                "diff_pct": round(
                    ((referee_stats.red_card_percentage - league_averages.red_card_pct) / league_averages.red_card_pct) * 100,
                    1
                )
            },
            "penalties": {
                "referee": referee_stats.avg_penalties_per_match,
                "league": league_averages.avg_penalties,
                "diff_pct": round(
                    ((referee_stats.avg_penalties_per_match - league_averages.avg_penalties) / league_averages.avg_penalties) * 100,
                    1
                )
            }
        },
        "market_impacts": [
            {
                "market": impact.market_code,
                "original_prob": impact.original_probability,
                "adjusted_prob": impact.adjusted_probability,
                "change_pct": impact.change_percentage,
                "is_significant": impact.is_significant
            }
            for impact in impacts
            if impact.is_significant  # Sadece önemli değişimleri göster
        ]
    }

