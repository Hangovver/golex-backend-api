"""
Bet Tracker Service
===================
Kullanıcı bahislerini takip eder, istatistikler ve ROI hesaplar.

Features:
- Bahis kaydetme (market, stake, odds)
- Otomatik kazanç/kayıp hesaplama
- İstatistikler (toplam bahis, kazanan, kaybeden, ROI)
- Detaylı raporlar (Excel/PDF export)
- En iyi/kötü marketler
- Sharpe Ratio ve risk metrikleri
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics


class BetStatus(Enum):
    """Bahis durumu"""
    PENDING = "pending"  # Bekliyor
    WON = "won"  # Kazandı
    LOST = "lost"  # Kaybetti
    VOID = "void"  # İptal
    CASHOUT = "cashout"  # Erken çıkış


@dataclass
class Bet:
    """Bahis"""
    bet_id: str
    user_id: str
    fixture_id: str
    market: str  # "KG_YES", "O2.5", "1X2_HOME"
    stake: float
    odds: float
    potential_return: float  # stake * odds
    status: BetStatus
    result: Optional[str]  # "won", "lost", "void"
    pnl: Optional[float]  # Profit/Loss
    placed_at: datetime
    settled_at: Optional[datetime]


@dataclass
class BetStats:
    """Bahis istatistikleri"""
    user_id: str
    total_bets: int
    total_stake: float
    total_return: float
    total_pnl: float
    roi: float  # Return on Investment (%)
    win_rate: float  # Kazanma oranı (%)
    avg_odds: float
    avg_stake: float
    sharpe_ratio: float  # Risk-adjusted return
    longest_winning_streak: int
    longest_losing_streak: int
    best_market: Optional[str]
    worst_market: Optional[str]


@dataclass
class DailyStats:
    """Günlük istatistik"""
    date: str  # "2025-10-27"
    total_bets: int
    won: int
    lost: int
    pnl: float
    roi: float


class BetTrackerService:
    """Bahis takip servisi"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def create_bet(
        self,
        user_id: str,
        fixture_id: str,
        market: str,
        stake: float,
        odds: float
    ) -> Bet:
        """
        Yeni bahis oluştur
        
        Args:
            user_id: Kullanıcı ID
            fixture_id: Maç ID
            market: Market kodu
            stake: Yatırılan miktar
            odds: Oran
        
        Returns:
            Bet objesi
        """
        bet_id = f"bet_{user_id}_{int(datetime.now().timestamp())}"
        potential_return = stake * odds
        
        query = """
        INSERT INTO user_bets
        (bet_id, user_id, fixture_id, market, stake, odds, potential_return, status, placed_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
        RETURNING *
        """
        
        row = await self.db.fetchrow(
            query,
            bet_id,
            user_id,
            fixture_id,
            market,
            stake,
            odds,
            potential_return,
            BetStatus.PENDING.value
        )
        
        return Bet(
            bet_id=row['bet_id'],
            user_id=row['user_id'],
            fixture_id=row['fixture_id'],
            market=row['market'],
            stake=float(row['stake']),
            odds=float(row['odds']),
            potential_return=float(row['potential_return']),
            status=BetStatus(row['status']),
            result=row['result'],
            pnl=float(row['pnl']) if row['pnl'] else None,
            placed_at=row['placed_at'],
            settled_at=row['settled_at']
        )
    
    async def settle_bet(
        self,
        bet_id: str,
        result: str  # "won", "lost", "void"
    ) -> Bet:
        """
        Bahsi sonuçlandır
        
        Args:
            bet_id: Bahis ID
            result: Sonuç ("won", "lost", "void")
        
        Returns:
            Güncellenmiş Bet
        """
        # Önce bahsi getir
        query_get = "SELECT * FROM user_bets WHERE bet_id = $1"
        bet_row = await self.db.fetchrow(query_get, bet_id)
        
        if not bet_row:
            raise ValueError(f"Bet {bet_id} not found")
        
        # PnL hesapla
        stake = float(bet_row['stake'])
        potential_return = float(bet_row['potential_return'])
        
        if result == "won":
            pnl = potential_return - stake  # Kar
            status = BetStatus.WON
        elif result == "lost":
            pnl = -stake  # Zarar
            status = BetStatus.LOST
        elif result == "void":
            pnl = 0.0  # İptal (para iade)
            status = BetStatus.VOID
        else:
            raise ValueError(f"Invalid result: {result}")
        
        # Güncelle
        query_update = """
        UPDATE user_bets
        SET status = $2, result = $3, pnl = $4, settled_at = NOW()
        WHERE bet_id = $1
        RETURNING *
        """
        
        row = await self.db.fetchrow(query_update, bet_id, status.value, result, pnl)
        
        return Bet(
            bet_id=row['bet_id'],
            user_id=row['user_id'],
            fixture_id=row['fixture_id'],
            market=row['market'],
            stake=float(row['stake']),
            odds=float(row['odds']),
            potential_return=float(row['potential_return']),
            status=BetStatus(row['status']),
            result=row['result'],
            pnl=float(row['pnl']) if row['pnl'] else None,
            placed_at=row['placed_at'],
            settled_at=row['settled_at']
        )
    
    async def get_user_bets(
        self,
        user_id: str,
        status: Optional[BetStatus] = None,
        limit: int = 100
    ) -> List[Bet]:
        """
        Kullanıcı bahislerini getir
        
        Args:
            user_id: Kullanıcı ID
            status: Durum filtresi (opsiyonel)
            limit: Maksimum sonuç sayısı
        
        Returns:
            List[Bet]
        """
        query = "SELECT * FROM user_bets WHERE user_id = $1"
        params = [user_id]
        
        if status:
            query += " AND status = $2"
            params.append(status.value)
        
        query += " ORDER BY placed_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        rows = await self.db.fetch(query, *params)
        
        return [
            Bet(
                bet_id=row['bet_id'],
                user_id=row['user_id'],
                fixture_id=row['fixture_id'],
                market=row['market'],
                stake=float(row['stake']),
                odds=float(row['odds']),
                potential_return=float(row['potential_return']),
                status=BetStatus(row['status']),
                result=row['result'],
                pnl=float(row['pnl']) if row['pnl'] else None,
                placed_at=row['placed_at'],
                settled_at=row['settled_at']
            )
            for row in rows
        ]
    
    async def get_bet_stats(self, user_id: str) -> BetStats:
        """
        Kullanıcı bahis istatistiklerini hesapla
        
        Args:
            user_id: Kullanıcı ID
        
        Returns:
            BetStats
        """
        # Tüm bahisleri getir
        query = """
        SELECT 
            COUNT(*) as total_bets,
            SUM(stake) as total_stake,
            SUM(CASE WHEN status = 'won' THEN potential_return ELSE 0 END) as total_return,
            SUM(COALESCE(pnl, 0)) as total_pnl,
            AVG(odds) as avg_odds,
            AVG(stake) as avg_stake,
            COUNT(CASE WHEN status = 'won' THEN 1 END) as wins,
            COUNT(CASE WHEN status = 'lost' THEN 1 END) as losses
        FROM user_bets
        WHERE user_id = $1
        """
        
        row = await self.db.fetchrow(query, user_id)
        
        if not row or row['total_bets'] == 0:
            return BetStats(
                user_id=user_id,
                total_bets=0,
                total_stake=0.0,
                total_return=0.0,
                total_pnl=0.0,
                roi=0.0,
                win_rate=0.0,
                avg_odds=0.0,
                avg_stake=0.0,
                sharpe_ratio=0.0,
                longest_winning_streak=0,
                longest_losing_streak=0,
                best_market=None,
                worst_market=None
            )
        
        total_bets = int(row['total_bets'])
        total_stake = float(row['total_stake'] or 0)
        total_return = float(row['total_return'] or 0)
        total_pnl = float(row['total_pnl'] or 0)
        wins = int(row['wins'])
        losses = int(row['losses'])
        
        # ROI
        roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0.0
        
        # Win rate
        settled = wins + losses
        win_rate = (wins / settled * 100) if settled > 0 else 0.0
        
        # Avg odds & stake
        avg_odds = float(row['avg_odds'] or 0)
        avg_stake = float(row['avg_stake'] or 0)
        
        # Sharpe Ratio (basitleştirilmiş)
        # Gerçek hesaplama için günlük PnL'lerin std sapması gerekli
        sharpe_ratio = await self._calculate_sharpe_ratio(user_id)
        
        # Streaks
        winning_streak, losing_streak = await self._calculate_streaks(user_id)
        
        # Best/worst market
        best_market, worst_market = await self._calculate_best_worst_markets(user_id)
        
        return BetStats(
            user_id=user_id,
            total_bets=total_bets,
            total_stake=round(total_stake, 2),
            total_return=round(total_return, 2),
            total_pnl=round(total_pnl, 2),
            roi=round(roi, 2),
            win_rate=round(win_rate, 1),
            avg_odds=round(avg_odds, 2),
            avg_stake=round(avg_stake, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            longest_winning_streak=winning_streak,
            longest_losing_streak=losing_streak,
            best_market=best_market,
            worst_market=worst_market
        )
    
    async def _calculate_sharpe_ratio(self, user_id: str) -> float:
        """Sharpe Ratio hesapla (günlük PnL'ler)"""
        query = """
        SELECT 
            DATE(placed_at) as bet_date,
            SUM(COALESCE(pnl, 0)) as daily_pnl
        FROM user_bets
        WHERE user_id = $1
        AND status IN ('won', 'lost')
        GROUP BY DATE(placed_at)
        ORDER BY bet_date DESC
        """
        
        rows = await self.db.fetch(query, user_id)
        
        if len(rows) < 2:
            return 0.0
        
        pnl_list = [float(row['daily_pnl']) for row in rows]
        
        # Sharpe: (mean - risk_free_rate) / std_dev
        # Risk-free rate = 0 (basitleştirme)
        mean_pnl = statistics.mean(pnl_list)
        std_pnl = statistics.stdev(pnl_list) if len(pnl_list) > 1 else 1.0
        
        sharpe = mean_pnl / std_pnl if std_pnl > 0 else 0.0
        
        return sharpe
    
    async def _calculate_streaks(self, user_id: str) -> Tuple[int, int]:
        """En uzun kazanma/kaybetme serileri"""
        query = """
        SELECT status, result
        FROM user_bets
        WHERE user_id = $1
        AND status IN ('won', 'lost')
        ORDER BY placed_at ASC
        """
        
        rows = await self.db.fetch(query, user_id)
        
        if not rows:
            return 0, 0
        
        current_win_streak = 0
        current_lose_streak = 0
        max_win_streak = 0
        max_lose_streak = 0
        
        for row in rows:
            if row['status'] == 'won':
                current_win_streak += 1
                current_lose_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif row['status'] == 'lost':
                current_lose_streak += 1
                current_win_streak = 0
                max_lose_streak = max(max_lose_streak, current_lose_streak)
        
        return max_win_streak, max_lose_streak
    
    async def _calculate_best_worst_markets(self, user_id: str) -> Tuple[Optional[str], Optional[str]]:
        """En iyi ve en kötü marketler"""
        query = """
        SELECT 
            market,
            SUM(COALESCE(pnl, 0)) as total_pnl,
            COUNT(*) as bet_count
        FROM user_bets
        WHERE user_id = $1
        AND status IN ('won', 'lost')
        GROUP BY market
        HAVING COUNT(*) >= 5
        ORDER BY total_pnl DESC
        """
        
        rows = await self.db.fetch(query, user_id)
        
        if not rows:
            return None, None
        
        best_market = rows[0]['market'] if rows else None
        worst_market = rows[-1]['market'] if rows else None
        
        return best_market, worst_market
    
    async def get_daily_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> List[DailyStats]:
        """
        Günlük istatistikler
        
        Args:
            user_id: Kullanıcı ID
            days: Kaç gün geriye
        
        Returns:
            List[DailyStats]
        """
        query = """
        SELECT 
            DATE(placed_at) as bet_date,
            COUNT(*) as total_bets,
            COUNT(CASE WHEN status = 'won' THEN 1 END) as won,
            COUNT(CASE WHEN status = 'lost' THEN 1 END) as lost,
            SUM(COALESCE(pnl, 0)) as pnl,
            SUM(stake) as total_stake
        FROM user_bets
        WHERE user_id = $1
        AND placed_at >= NOW() - INTERVAL '1 day' * $2
        GROUP BY DATE(placed_at)
        ORDER BY bet_date DESC
        """
        
        rows = await self.db.fetch(query, user_id, days)
        
        return [
            DailyStats(
                date=row['bet_date'].isoformat(),
                total_bets=int(row['total_bets']),
                won=int(row['won']),
                lost=int(row['lost']),
                pnl=round(float(row['pnl']), 2),
                roi=round((float(row['pnl']) / float(row['total_stake']) * 100), 2) if float(row['total_stake']) > 0 else 0.0
            )
            for row in rows
        ]
    
    async def delete_bet(self, bet_id: str):
        """Bahsi sil"""
        query = "DELETE FROM user_bets WHERE bet_id = $1"
        await self.db.execute(query, bet_id)


# === UTILITY FUNCTIONS ===

def format_bet_report(stats: BetStats, daily: List[DailyStats]) -> Dict:
    """
    Bahis raporunu formatla (frontend için)
    
    Returns:
        {
            "summary": {...},
            "daily_chart": [...]
        }
    """
    return {
        "summary": {
            "total_bets": stats.total_bets,
            "total_stake": stats.total_stake,
            "total_return": stats.total_return,
            "total_pnl": stats.total_pnl,
            "roi": stats.roi,
            "win_rate": stats.win_rate,
            "avg_odds": stats.avg_odds,
            "avg_stake": stats.avg_stake,
            "sharpe_ratio": stats.sharpe_ratio,
            "longest_winning_streak": stats.longest_winning_streak,
            "longest_losing_streak": stats.longest_losing_streak,
            "best_market": stats.best_market,
            "worst_market": stats.worst_market
        },
        "daily_chart": [
            {
                "date": d.date,
                "bets": d.total_bets,
                "won": d.won,
                "lost": d.lost,
                "pnl": d.pnl,
                "roi": d.roi
            }
            for d in daily
        ]
    }

