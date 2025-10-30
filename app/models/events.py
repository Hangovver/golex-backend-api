"""
Match Events/Incidents Models
For attack momentum, statistics, and timeline
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class MatchEvent(Base):
    """
    Match events for attack momentum and timeline
    """
    __tablename__ = "match_events"
    
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # goal, shot, corner, etc.
    event_class = Column(String(50))  # penalty, own_goal, red, yellow, etc.
    minute = Column(Integer, nullable=False)
    added_time = Column(Integer)
    
    # Team/Player
    is_home = Column(Boolean, nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"))
    player_in_id = Column(Integer, ForeignKey("players.id"))  # For substitutions
    player_out_id = Column(Integer, ForeignKey("players.id"))  # For substitutions
    
    # Scores (at time of event)
    home_score = Column(Integer)
    away_score = Column(Integer)
    
    # Additional data (JSON)
    details = Column(JSON)  # Extra event-specific data
    
    # For attack momentum calculation
    momentum_weight = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fixture = relationship("Fixture", back_populates="events")
    player = relationship("Player", foreign_keys=[player_id])


class PlayerMatchStats(Base):
    """
    Player statistics for a specific match
    For rating calculation
    """
    __tablename__ = "player_match_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Playing time
    minutes_played = Column(Integer, default=0)
    position = Column(String(10))  # GK, CB, CM, ST, etc.
    
    # Rating
    rating = Column(Float)  # 0.0 to 10.0
    rating_color = Column(String(20))  # excellent, very_good, good, average, poor
    
    # Positive actions
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    key_passes = Column(Integer, default=0)
    successful_passes = Column(Integer, default=0)
    total_passes = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    shots_total = Column(Integer, default=0)
    tackles_won = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    clearances = Column(Integer, default=0)
    dribbles_successful = Column(Integer, default=0)
    dribbles_attempted = Column(Integer, default=0)
    duels_won = Column(Integer, default=0)
    duels_total = Column(Integer, default=0)
    aerial_duels_won = Column(Integer, default=0)
    aerial_duels_total = Column(Integer, default=0)
    
    # Negative actions
    goals_conceded = Column(Integer, default=0)  # For goalkeepers
    errors_leading_to_goal = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    fouls_committed = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    possession_lost = Column(Integer, default=0)
    
    # Goalkeeper specific
    saves = Column(Integer, default=0)
    saves_inside_box = Column(Integer, default=0)
    punches = Column(Integer, default=0)
    high_claims = Column(Integer, default=0)
    
    # Physical
    distance_covered_km = Column(Float)
    touches = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fixture = relationship("Fixture")
    player = relationship("Player")
    team = relationship("Team")


class TeamMatchStats(Base):
    """
    Team statistics for a match
    """
    __tablename__ = "team_match_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    
    # Possession
    possession_percentage = Column(Integer)
    
    # Expected Goals
    expected_goals = Column(Float)  # xG
    
    # Shots
    shots_total = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    shots_off_target = Column(Integer, default=0)
    shots_blocked = Column(Integer, default=0)
    shots_inside_box = Column(Integer, default=0)
    shots_outside_box = Column(Integer, default=0)
    
    # Passes
    passes_total = Column(Integer, default=0)
    passes_accurate = Column(Integer, default=0)
    pass_accuracy_percentage = Column(Integer)
    key_passes = Column(Integer, default=0)
    crosses = Column(Integer, default=0)
    long_balls = Column(Integer, default=0)
    through_balls = Column(Integer, default=0)
    
    # Defense
    tackles = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    clearances = Column(Integer, default=0)
    blocked_shots = Column(Integer, default=0)
    
    # Discipline
    corners = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    fouls_committed = Column(Integer, default=0)
    fouls_won = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fixture = relationship("Fixture")
    team = relationship("Team")


class ShotData(Base):
    """
    Individual shot data for shot map and xG
    """
    __tablename__ = "shot_data"
    
    id = Column(Integer, primary_key=True, index=True)
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    
    # Timing
    minute = Column(Integer, nullable=False)
    added_time = Column(Integer)
    
    # Location (0-100 field percentage)
    x = Column(Float, nullable=False)  # 0=own goal, 100=opponent goal
    y = Column(Float, nullable=False)  # 0=left, 100=right
    
    # Shot details
    distance_to_goal = Column(Float)  # meters
    angle_to_goal = Column(Float)  # degrees
    body_part = Column(String(20))  # head, right_foot, left_foot, weak_foot
    situation = Column(String(50))  # open_play, corner, free_kick, penalty, one_on_one
    shot_type = Column(String(20))  # on_target, off_target, blocked, goal
    
    # xG
    xg_value = Column(Float)  # 0.0 to 1.0
    
    # Context
    goalkeeper_out = Column(Boolean, default=False)
    defender_pressure = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Result
    is_goal = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    fixture = relationship("Fixture")
    player = relationship("Player")
    team = relationship("Team")


# Event type weights for momentum calculation
EVENT_WEIGHTS = {
    'goal': 15.0,
    'shot_on_target': 3.0,
    'shot_off_target': 1.5,
    'corner': 2.0,
    'attack': 1.0,
    'dangerous_attack': 2.0,
    'possession': 0.5,
    'penalty': 10.0,
    'save': 2.0,
    'free_kick': 1.5,
    'big_chance': 4.0,
}

