"""
Statistics Service
Fetches and processes match/player/team statistics
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.player_statistics import PlayerStatistics, TeamStatistics


class StatisticsService:
    """
    Service for managing statistics
    Fetches from database or external API
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_player_statistics(
        self,
        fixture_id: int,
        player_id: Optional[int] = None
    ) -> List[PlayerStatistics]:
        """
        Get player statistics for a fixture
        Optionally filter by player_id
        """
        query = self.db.query(PlayerStatistics).filter(
            PlayerStatistics.fixture_id == fixture_id
        )
        
        if player_id:
            query = query.filter(PlayerStatistics.player_id == player_id)
        
        return query.all()
    
    def get_team_statistics(
        self,
        fixture_id: int
    ) -> Dict[str, TeamStatistics]:
        """
        Get team statistics for a fixture
        Returns dict with 'home' and 'away' keys
        """
        stats = self.db.query(TeamStatistics).filter(
            TeamStatistics.fixture_id == fixture_id
        ).all()
        
        if len(stats) != 2:
            return {"home": None, "away": None}
        
        # Determine home/away based on fixture data
        # This is simplified - actual implementation would join with fixtures table
        return {
            "home": stats[0],
            "away": stats[1]
        }
    
    def get_player_season_stats(
        self,
        player_id: int,
        season_year: int
    ) -> Dict:
        """
        Get aggregated player statistics for a season
        """
        from sqlalchemy import func
        
        stats = self.db.query(
            func.count(PlayerStatistics.id).label("matches"),
            func.sum(PlayerStatistics.minutes_played).label("total_minutes"),
            func.avg(PlayerStatistics.rating).label("avg_rating"),
            func.sum(PlayerStatistics.goals).label("total_goals"),
            func.sum(PlayerStatistics.assists).label("total_assists"),
            func.sum(PlayerStatistics.shots_total).label("total_shots"),
            func.sum(PlayerStatistics.shots_on_target).label("total_shots_on_target"),
            func.sum(PlayerStatistics.passes_total).label("total_passes"),
            func.sum(PlayerStatistics.passes_accurate).label("total_passes_accurate"),
            func.sum(PlayerStatistics.yellow_cards).label("total_yellow_cards"),
            func.sum(PlayerStatistics.red_cards).label("total_red_cards"),
        ).filter(
            PlayerStatistics.player_id == player_id
            # TODO: Add season filter when fixtures table is joined
        ).first()
        
        if not stats:
            return {}
        
        return {
            "matches": stats.matches or 0,
            "minutes_played": stats.total_minutes or 0,
            "average_rating": round(stats.avg_rating, 1) if stats.avg_rating else None,
            "goals": stats.total_goals or 0,
            "assists": stats.total_assists or 0,
            "shots": stats.total_shots or 0,
            "shots_on_target": stats.total_shots_on_target or 0,
            "shot_accuracy": round(
                (stats.total_shots_on_target / stats.total_shots * 100), 1
            ) if stats.total_shots and stats.total_shots > 0 else 0,
            "passes": stats.total_passes or 0,
            "passes_accurate": stats.total_passes_accurate or 0,
            "pass_accuracy": round(
                (stats.total_passes_accurate / stats.total_passes * 100), 1
            ) if stats.total_passes and stats.total_passes > 0 else 0,
            "yellow_cards": stats.total_yellow_cards or 0,
            "red_cards": stats.total_red_cards or 0,
        }
    
    def get_team_season_stats(
        self,
        team_id: int,
        season_year: int
    ) -> Dict:
        """
        Get aggregated team statistics for a season
        """
        from sqlalchemy import func
        
        stats = self.db.query(
            func.count(TeamStatistics.id).label("matches"),
            func.avg(TeamStatistics.possession_percentage).label("avg_possession"),
            func.sum(TeamStatistics.expected_goals).label("total_xg"),
            func.sum(TeamStatistics.shots_total).label("total_shots"),
            func.sum(TeamStatistics.shots_on_target).label("total_shots_on_target"),
            func.sum(TeamStatistics.passes_total).label("total_passes"),
            func.sum(TeamStatistics.passes_accurate).label("total_passes_accurate"),
            func.sum(TeamStatistics.corners).label("total_corners"),
            func.sum(TeamStatistics.yellow_cards).label("total_yellow_cards"),
            func.sum(TeamStatistics.red_cards).label("total_red_cards"),
        ).filter(
            TeamStatistics.team_id == team_id
            # TODO: Add season filter
        ).first()
        
        if not stats:
            return {}
        
        return {
            "matches": stats.matches or 0,
            "average_possession": round(stats.avg_possession, 1) if stats.avg_possession else None,
            "expected_goals": round(stats.total_xg, 2) if stats.total_xg else 0,
            "shots": stats.total_shots or 0,
            "shots_on_target": stats.total_shots_on_target or 0,
            "passes": stats.total_passes or 0,
            "pass_accuracy": round(
                (stats.total_passes_accurate / stats.total_passes * 100), 1
            ) if stats.total_passes and stats.total_passes > 0 else 0,
            "corners": stats.total_corners or 0,
            "yellow_cards": stats.total_yellow_cards or 0,
            "red_cards": stats.total_red_cards or 0,
        }
    
    def get_top_rated_players(
        self,
        fixture_id: int,
        limit: int = 3
    ) -> Dict[str, List[PlayerStatistics]]:
        """
        Get top-rated players for each team in a match
        """
        stats = self.db.query(PlayerStatistics).filter(
            PlayerStatistics.fixture_id == fixture_id,
            PlayerStatistics.rating.isnot(None)
        ).order_by(
            PlayerStatistics.rating.desc()
        ).all()
        
        # Split by team (simplified - would need fixture data to determine home/away)
        home_players = [s for s in stats if s.team_id == stats[0].team_id][:limit]
        away_players = [s for s in stats if s.team_id != stats[0].team_id][:limit]
        
        return {
            "home": home_players,
            "away": away_players
        }
    
    def compare_players(
        self,
        player_id_1: int,
        player_id_2: int,
        season_year: int
    ) -> Dict:
        """
        Compare statistics between two players
        """
        player1_stats = self.get_player_season_stats(player_id_1, season_year)
        player2_stats = self.get_player_season_stats(player_id_2, season_year)
        
        return {
            "player_1": {
                "id": player_id_1,
                "stats": player1_stats
            },
            "player_2": {
                "id": player_id_2,
                "stats": player2_stats
            }
        }

