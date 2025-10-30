"""
Social Features Service
=======================
Leaderboard, takip sistemi ve kullanıcı etkileşimi.

Features:
- Leaderboard (ROI, win rate, total profit)
- Follow/Unfollow users
- User profiles
- Top tipsters
- Social proof
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LeaderboardEntry:
    """Leaderboard girdisi"""
    user_id: str
    username: str
    rank: int
    roi: float
    total_bets: int
    win_rate: float
    total_profit: float


class SocialFeaturesService:
    """Sosyal özellikler servisi"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_leaderboard(
        self,
        period: str = "all_time",  # "all_time", "month", "week"
        limit: int = 100
    ) -> List[LeaderboardEntry]:
        """
        Leaderboard getir
        
        Args:
            period: Dönem
            limit: Maksimum sonuç
        
        Returns:
            List[LeaderboardEntry]
        """
        date_filter = ""
        if period == "month":
            date_filter = "AND placed_at >= NOW() - INTERVAL '30 days'"
        elif period == "week":
            date_filter = "AND placed_at >= NOW() - INTERVAL '7 days'"
        
        query = f"""
        SELECT 
            user_id,
            SUM(stake) as total_stake,
            SUM(COALESCE(pnl, 0)) as total_pnl,
            COUNT(*) as total_bets,
            COUNT(CASE WHEN status = 'won' THEN 1 END) as wins
        FROM user_bets
        WHERE status IN ('won', 'lost')
        {date_filter}
        GROUP BY user_id
        HAVING SUM(stake) > 0
        ORDER BY (SUM(COALESCE(pnl, 0)) / SUM(stake)) DESC
        LIMIT $1
        """
        
        rows = await self.db.fetch(query, limit)
        
        leaderboard = []
        for rank, row in enumerate(rows, start=1):
            total_stake = float(row['total_stake'])
            total_pnl = float(row['total_pnl'])
            total_bets = int(row['total_bets'])
            wins = int(row['wins'])
            
            roi = (total_pnl / total_stake * 100) if total_stake > 0 else 0.0
            win_rate = (wins / total_bets * 100) if total_bets > 0 else 0.0
            
            leaderboard.append(LeaderboardEntry(
                user_id=row['user_id'],
                username=f"@{row['user_id'][:8]}",  # Basit username
                rank=rank,
                roi=round(roi, 2),
                total_bets=total_bets,
                win_rate=round(win_rate, 1),
                total_profit=round(total_pnl, 2)
            ))
        
        return leaderboard

