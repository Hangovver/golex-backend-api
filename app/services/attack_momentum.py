"""
Attack Momentum Calculation Service
Based on SofaScore analysis
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MomentumEvent:
    """Single event contributing to momentum"""
    minute: float
    event_type: str
    is_home: bool
    weight: float


@dataclass
class MomentumPoint:
    """Momentum value at a specific minute"""
    minute: float
    value: float  # -1.0 (away dominance) to 1.0 (home dominance)
    
    def to_dict(self) -> Dict:
        return {
            "minute": self.minute,
            "value": round(self.value, 3)
        }


class AttackMomentumService:
    """
    Calculate attack momentum based on match events
    Algorithm from SofaScore APK analysis
    """
    
    # Event weights (from AttackMomentumGraph.java)
    WEIGHTS = {
        'goal': 15.0,
        'shot_on_target': 3.0,
        'shot_off_target': 1.5,
        'corner': 2.0,
        'attack': 1.0,
        'dangerous_attack': 2.0,
        'possession': 0.5,  # per minute
        'penalty': 10.0,
        'save': 2.0,
        'free_kick': 1.5,
        'big_chance': 4.0,
    }
    
    # Time decay window (minutes)
    TIME_WINDOW = 5
    TIME_DECAY_FACTOR = 0.3  # 30% decay
    
    # Smoothing window
    SMOOTHING_WINDOW = 3
    
    def calculate_momentum(
        self,
        events: List[Dict],
        total_minutes: int = 90
    ) -> List[MomentumPoint]:
        """
        Calculate momentum for entire match
        
        Args:
            events: List of match events with:
                - minute: float
                - type: str (goal, shot_on_target, etc.)
                - is_home: bool
            total_minutes: Total match minutes (90, 120, etc.)
        
        Returns:
            List of MomentumPoint objects
        """
        # Convert events
        momentum_events = [
            MomentumEvent(
                minute=e.get('minute', 0),
                event_type=e.get('type', 'unknown'),
                is_home=e.get('is_home', True),
                weight=self.WEIGHTS.get(e.get('type', ''), 0)
            )
            for e in events
            if e.get('minute', 0) > 0
        ]
        
        # Calculate momentum for each minute
        momentum_points = []
        for minute in range(1, total_minutes + 1):
            value = self._calculate_minute_momentum(
                minute,
                momentum_events
            )
            momentum_points.append(
                MomentumPoint(minute=float(minute), value=value)
            )
        
        # Apply smoothing
        smoothed = self._apply_smoothing(momentum_points)
        
        return smoothed
    
    def _calculate_minute_momentum(
        self,
        minute: int,
        events: List[MomentumEvent]
    ) -> float:
        """
        Calculate momentum at specific minute
        Uses time decay for recent events (last 5 minutes)
        """
        home_score = 0.0
        away_score = 0.0
        
        # Get events in time window
        start_minute = max(0, minute - self.TIME_WINDOW)
        
        for event in events:
            if start_minute <= event.minute <= minute:
                # Calculate time decay
                age = minute - event.minute
                decay = 1.0 - (age / self.TIME_WINDOW) * self.TIME_DECAY_FACTOR
                decay = max(0.0, min(1.0, decay))
                
                # Add to appropriate team
                weighted_value = event.weight * decay
                if event.is_home:
                    home_score += weighted_value
                else:
                    away_score += weighted_value
        
        # Normalize to -1.0 to 1.0
        total = home_score + away_score
        if total > 0:
            normalized = (home_score - away_score) / total
        else:
            normalized = 0.0
        
        # Clamp
        return max(-1.0, min(1.0, normalized))
    
    def _apply_smoothing(
        self,
        points: List[MomentumPoint]
    ) -> List[MomentumPoint]:
        """
        Apply moving average smoothing
        """
        if len(points) < self.SMOOTHING_WINDOW:
            return points
        
        smoothed = []
        half_window = self.SMOOTHING_WINDOW // 2
        
        for i, point in enumerate(points):
            # Get window bounds
            start = max(0, i - half_window)
            end = min(len(points), i + half_window + 1)
            
            # Calculate average
            window_points = points[start:end]
            avg_value = sum(p.value for p in window_points) / len(window_points)
            
            smoothed.append(
                MomentumPoint(minute=point.minute, value=avg_value)
            )
        
        return smoothed
    
    def get_phases(self, total_minutes: int) -> List[Dict]:
        """
        Get match phases (0-45, 46-90, 91-105, 106-120)
        From AttackMomentumGraph.java getDividers()
        """
        if total_minutes >= 106:
            # Extra time 2nd half
            return [
                {"start": 0, "end": 45, "label": "1st Half"},
                {"start": 46, "end": 90, "label": "2nd Half"},
                {"start": 91, "end": 105, "label": "ET 1st"},
                {"start": 106, "end": 120, "label": "ET 2nd"}
            ]
        elif total_minutes >= 91:
            # Extra time 1st half
            return [
                {"start": 0, "end": 45, "label": "1st Half"},
                {"start": 46, "end": 90, "label": "2nd Half"},
                {"start": 91, "end": 105, "label": "ET 1st"}
            ]
        else:
            # Regular time
            return [
                {"start": 0, "end": 45, "label": "1st Half"},
                {"start": 46, "end": 90, "label": "2nd Half"}
            ]


# Singleton instance
attack_momentum_service = AttackMomentumService()

