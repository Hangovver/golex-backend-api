"""
Player Rating Calculation Service
Based on SofaScore analysis (0-10 scale with 5 colors)
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class PlayerStats:
    """Player match statistics"""
    # Positive actions
    goals: int = 0
    assists: int = 0
    key_passes: int = 0
    successful_passes: int = 0
    shots_on_target: int = 0
    tackles_won: int = 0
    interceptions: int = 0
    clearances: int = 0
    dribbles_successful: int = 0
    duels_won: int = 0
    
    # Negative actions
    goals_conceded: int = 0  # For goalkeepers
    errors_leading_to_goal: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    fouls: int = 0
    offsides: int = 0
    possession_lost: int = 0
    
    # Goalkeeper specific
    saves: int = 0
    
    # Position
    position: str = "CM"  # GK, CB, LB, RB, CM, CDM, CAM, LW, RW, ST
    
    # Minutes played
    minutes_played: int = 90


@dataclass
class RatingResult:
    """Rating calculation result"""
    rating: float  # 0.0 to 10.0
    color: str  # Color code
    color_name: str  # excellent, very_good, good, average, poor
    
    def to_dict(self) -> Dict:
        return {
            "rating": round(self.rating, 1),
            "color": self.color,
            "color_name": self.color_name
        }


class PlayerRatingService:
    """
    Calculate player rating based on match statistics
    Algorithm from SofaScore (SofascoreRatingView.java analysis)
    """
    
    # Rating color thresholds and colors
    # From SofascoreRatingView.java
    RATING_COLORS = {
        "excellent": {"min": 9.0, "color": "#4CAF50"},  # Green
        "very_good": {"min": 8.0, "color": "#8BC34A"},  # Light Green
        "good": {"min": 7.0, "color": "#FFC107"},       # Yellow
        "average": {"min": 6.0, "color": "#FF9800"},    # Orange
        "poor": {"min": 0.0, "color": "#F44336"}        # Red
    }
    
    # Position multipliers for specific actions
    POSITION_MULTIPLIERS = {
        "GK": {
            "saves": 0.15,
            "goals_conceded_penalty": -0.5
        },
        "CB": {
            "tackles_won": 0.15,
            "clearances": 0.10,
            "aerial_duels": 0.15
        },
        "LB": {
            "tackles_won": 0.12,
            "key_passes": 0.10
        },
        "RB": {
            "tackles_won": 0.12,
            "key_passes": 0.10
        },
        "CDM": {
            "tackles_won": 0.12,
            "interceptions": 0.12
        },
        "CM": {
            "key_passes": 0.15,
            "successful_passes": 0.008
        },
        "CAM": {
            "key_passes": 0.20,
            "assists": 0.10
        },
        "LW": {
            "shots_on_target": 0.25,
            "dribbles": 0.15
        },
        "RW": {
            "shots_on_target": 0.25,
            "dribbles": 0.15
        },
        "ST": {
            "goals": 0.15,
            "shots_on_target": 0.25
        }
    }
    
    def calculate_rating(self, stats: PlayerStats) -> RatingResult:
        """
        Calculate player rating
        
        Base rating: 6.0
        Maximum: 10.0
        Minimum: 0.0
        
        Formula:
        rating = 6.0 + positive_actions - negative_actions + position_bonus
        """
        # Start with base rating
        rating = 6.0
        
        # Positive actions (base)
        rating += stats.goals * 1.0
        rating += stats.assists * 0.7
        rating += stats.key_passes * 0.1
        rating += stats.successful_passes * 0.005
        rating += stats.tackles_won * 0.1
        rating += stats.interceptions * 0.1
        rating += stats.clearances * 0.05
        rating += stats.shots_on_target * 0.2
        rating += stats.dribbles_successful * 0.15
        rating += stats.duels_won * 0.05
        
        # Negative actions
        rating -= stats.errors_leading_to_goal * 2.0
        rating -= stats.yellow_cards * 0.2
        rating -= stats.red_cards * 3.0
        rating -= stats.fouls * 0.05
        rating -= stats.offsides * 0.1
        rating -= stats.possession_lost * 0.02
        
        # Position-specific bonuses
        position_bonus = self._calculate_position_bonus(stats)
        rating += position_bonus
        
        # Goalkeeper specific
        if stats.position == "GK":
            rating += stats.saves * 0.15
            rating -= stats.goals_conceded * 0.5
        
        # Clamp between 0.0 and 10.0
        rating = max(0.0, min(10.0, rating))
        
        # Get color
        color_info = self._get_rating_color(rating)
        
        return RatingResult(
            rating=rating,
            color=color_info["color"],
            color_name=color_info["name"]
        )
    
    def _calculate_position_bonus(self, stats: PlayerStats) -> float:
        """Calculate position-specific bonus"""
        bonus = 0.0
        
        multipliers = self.POSITION_MULTIPLIERS.get(stats.position, {})
        
        if "saves" in multipliers:
            bonus += stats.saves * multipliers["saves"]
        if "tackles_won" in multipliers:
            bonus += stats.tackles_won * multipliers["tackles_won"]
        if "key_passes" in multipliers:
            bonus += stats.key_passes * multipliers["key_passes"]
        if "shots_on_target" in multipliers:
            bonus += stats.shots_on_target * multipliers["shots_on_target"]
        if "clearances" in multipliers:
            bonus += stats.clearances * multipliers["clearances"]
        if "dribbles" in multipliers:
            bonus += stats.dribbles_successful * multipliers["dribbles"]
        if "interceptions" in multipliers:
            bonus += stats.interceptions * multipliers["interceptions"]
        if "successful_passes" in multipliers:
            bonus += stats.successful_passes * multipliers["successful_passes"]
        
        return bonus
    
    def _get_rating_color(self, rating: float) -> Dict:
        """
        Get color based on rating
        From SofascoreRatingView.java color mapping
        """
        if rating >= 9.0:
            return {"name": "excellent", "color": self.RATING_COLORS["excellent"]["color"]}
        elif rating >= 8.0:
            return {"name": "very_good", "color": self.RATING_COLORS["very_good"]["color"]}
        elif rating >= 7.0:
            return {"name": "good", "color": self.RATING_COLORS["good"]["color"]}
        elif rating >= 6.0:
            return {"name": "average", "color": self.RATING_COLORS["average"]["color"]}
        else:
            return {"name": "poor", "color": self.RATING_COLORS["poor"]["color"]}


# Singleton instance
player_rating_service = PlayerRatingService()

