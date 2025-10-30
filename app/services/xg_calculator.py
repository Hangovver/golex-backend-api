"""
Expected Goals (xG) Calculation Service
Based on SofaScore analysis
"""
from typing import Dict, Optional
from dataclasses import dataclass
import math


@dataclass
class ShotData:
    """Shot data for xG calculation"""
    distance_to_goal: float  # meters
    angle_to_goal: float  # degrees (0-90)
    body_part: str  # 'head', 'right_foot', 'left_foot', 'weak_foot'
    situation: str  # 'open_play', 'corner', 'free_kick', 'penalty', 'one_on_one'
    goalkeeper_out: bool = False
    defender_pressure: float = 0.0  # 0.0 (no pressure) to 1.0 (heavy pressure)
    shot_type: str = 'on_target'  # 'on_target', 'off_target', 'blocked', 'goal'
    
    # Location data (optional)
    x: Optional[float] = None  # 0-100 (field percentage)
    y: Optional[float] = None  # 0-100


@dataclass
class XGResult:
    """xG calculation result"""
    xg: float  # 0.0 to 1.0
    factors: Dict[str, float]  # breakdown of contributing factors
    
    def to_dict(self) -> Dict:
        return {
            "xg": round(self.xg, 3),
            "factors": {k: round(v, 3) for k, v in self.factors.items()}
        }


class XGCalculatorService:
    """
    Calculate Expected Goals (xG) for shots
    Algorithm based on SofaScore analysis
    """
    
    # Historical averages
    PENALTY_XG = 0.76  # 76% conversion rate
    OPEN_PLAY_BASE = 0.5
    
    # Distance zones (meters from goal)
    DISTANCE_ZONES = {
        "very_close": (0, 6),      # Inside 6-yard box
        "close": (6, 11),          # Penalty box close
        "medium": (11, 16.5),      # Penalty box edge
        "far": (16.5, 30),         # Outside box
        "very_far": (30, 100)      # Long range
    }
    
    # Distance multipliers
    DISTANCE_MULTIPLIERS = {
        "very_close": 1.5,
        "close": 1.2,
        "medium": 1.0,
        "far": 0.5,
        "very_far": 0.2
    }
    
    # Body part multipliers
    BODY_PART_MULTIPLIERS = {
        "head": 0.7,
        "weak_foot": 0.8,
        "right_foot": 1.0,
        "left_foot": 1.0
    }
    
    # Situation multipliers
    SITUATION_MULTIPLIERS = {
        "penalty": 0.76,  # Fixed
        "one_on_one": 2.0,
        "open_play": 1.0,
        "corner": 0.6,
        "free_kick": 0.05,
        "counter_attack": 1.3
    }
    
    def calculate_xg(self, shot: ShotData) -> XGResult:
        """
        Calculate xG for a shot
        
        Returns:
            XGResult with xG value (0.0-1.0) and factor breakdown
        """
        # Special case: penalties
        if shot.situation == 'penalty':
            return XGResult(
                xg=self.PENALTY_XG,
                factors={
                    "base": self.PENALTY_XG,
                    "situation": "penalty"
                }
            )
        
        # Start with base xG
        xg = self.OPEN_PLAY_BASE
        factors = {"base": self.OPEN_PLAY_BASE}
        
        # Distance factor
        distance_factor = self._calculate_distance_factor(shot.distance_to_goal)
        xg *= distance_factor
        factors["distance"] = distance_factor
        
        # Angle factor
        angle_factor = self._calculate_angle_factor(shot.angle_to_goal)
        xg *= angle_factor
        factors["angle"] = angle_factor
        
        # Body part factor
        body_factor = self.BODY_PART_MULTIPLIERS.get(shot.body_part, 1.0)
        xg *= body_factor
        factors["body_part"] = body_factor
        
        # Situation factor
        situation_factor = self.SITUATION_MULTIPLIERS.get(shot.situation, 1.0)
        xg *= situation_factor
        factors["situation"] = situation_factor
        
        # Goalkeeper position
        if shot.goalkeeper_out:
            gk_factor = 1.3
            xg *= gk_factor
            factors["goalkeeper_out"] = gk_factor
        
        # Defender pressure
        if shot.defender_pressure > 0:
            pressure_factor = 1.0 - (shot.defender_pressure * 0.5)
            xg *= pressure_factor
            factors["defender_pressure"] = pressure_factor
        
        # Clamp to [0.0, 1.0]
        xg = max(0.0, min(1.0, xg))
        
        return XGResult(xg=xg, factors=factors)
    
    def _calculate_distance_factor(self, distance: float) -> float:
        """
        Calculate distance multiplier
        Closer shots have higher xG
        """
        # Find distance zone
        for zone, (min_dist, max_dist) in self.DISTANCE_ZONES.items():
            if min_dist <= distance < max_dist:
                multiplier = self.DISTANCE_MULTIPLIERS[zone]
                
                # If far or very_far, apply exponential decay
                if zone in ["far", "very_far"]:
                    multiplier = 0.5 ** (distance / 20)
                
                return multiplier
        
        # Default for very long range
        return 0.1
    
    def _calculate_angle_factor(self, angle: float) -> float:
        """
        Calculate angle multiplier
        Better angle = higher xG
        
        angle: 0-90 degrees
        """
        # Normalize to 0-1
        normalized = angle / 90.0
        
        return max(0.1, normalized)
    
    def calculate_team_xg(self, shots: list) -> float:
        """
        Calculate total xG for a team
        
        Args:
            shots: List of ShotData objects
        
        Returns:
            Total xG (sum of individual shot xGs)
        """
        total_xg = 0.0
        
        for shot_data in shots:
            if isinstance(shot_data, dict):
                shot = ShotData(**shot_data)
            else:
                shot = shot_data
            
            result = self.calculate_xg(shot)
            total_xg += result.xg
        
        return round(total_xg, 2)
    
    def get_xg_from_location(self, x: float, y: float) -> float:
        """
        Calculate xG from field coordinates
        
        Args:
            x: 0-100 (0 = own goal, 100 = opponent goal)
            y: 0-100 (0 = left sideline, 100 = right sideline)
        
        Returns:
            xG value
        """
        # Goal is at x=100, y=50 (center)
        goal_x, goal_y = 100, 50
        
        # Calculate distance to goal (meters)
        # Field is ~105m x 68m
        distance = math.sqrt(
            ((goal_x - x) * 1.05) ** 2 + 
            ((goal_y - y) * 0.68) ** 2
        )
        
        # Calculate angle to goal
        # Angle from sideline to center
        dy = abs(y - goal_y)
        dx = goal_x - x
        angle = math.degrees(math.atan2(dx, dy)) if dx > 0 else 0
        
        # Create shot data
        shot = ShotData(
            distance_to_goal=distance,
            angle_to_goal=angle,
            body_part='right_foot',
            situation='open_play',
            x=x,
            y=y
        )
        
        result = self.calculate_xg(shot)
        return result.xg


# Singleton instance
xg_calculator_service = XGCalculatorService()

