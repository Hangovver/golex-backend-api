"""
Player Statistics Models
For storing match-level player statistics
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship
from app.models.base import Base


class PlayerStatistics(Base):
    """
    Player statistics for a single match
    Stores all stats needed for rating calculation
    """
    __tablename__ = "player_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    
    # Basic info
    minutes_played = Column(Integer, default=0)
    position = Column(String(10))  # GK, CB, CM, ST, etc.
    
    # Rating
    rating = Column(Float)  # 0.0 to 10.0
    
    # Attacking stats
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots_total = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    big_chances_created = Column(Integer, default=0)
    big_chances_missed = Column(Integer, default=0)
    
    # Passing stats
    passes_total = Column(Integer, default=0)
    passes_accurate = Column(Integer, default=0)
    key_passes = Column(Integer, default=0)
    crosses = Column(Integer, default=0)
    long_balls = Column(Integer, default=0)
    through_balls = Column(Integer, default=0)
    
    # Dribbling stats
    dribbles_attempted = Column(Integer, default=0)
    dribbles_successful = Column(Integer, default=0)
    
    # Defensive stats
    tackles = Column(Integer, default=0)
    tackles_won = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    clearances = Column(Integer, default=0)
    blocked_shots = Column(Integer, default=0)
    
    # Duels
    duels_total = Column(Integer, default=0)
    duels_won = Column(Integer, default=0)
    aerial_duels_total = Column(Integer, default=0)
    aerial_duels_won = Column(Integer, default=0)
    
    # Discipline
    fouls_committed = Column(Integer, default=0)
    fouls_won = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    
    # Other
    touches = Column(Integer, default=0)
    possession_lost = Column(Integer, default=0)
    distance_covered_km = Column(Float)
    
    # Goalkeeper specific
    saves = Column(Integer, default=0)
    saves_inside_box = Column(Integer, default=0)
    goals_conceded = Column(Integer, default=0)
    punches = Column(Integer, default=0)
    high_claims = Column(Integer, default=0)
    successful_keeper_sweeper = Column(Integer, default=0)
    
    # Errors
    errors_leading_to_goal = Column(Integer, default=0)
    errors_leading_to_shot = Column(Integer, default=0)
    
    # Substitution info
    was_substituted = Column(Boolean, default=False)
    substituted_in_minute = Column(Integer)
    substituted_out_minute = Column(Integer)
    
    # Relationships
    fixture = relationship("Fixture", back_populates="player_statistics")
    player = relationship("Player")
    team = relationship("Team")
    
    @property
    def pass_accuracy(self) -> float:
        """Calculate pass accuracy percentage"""
        if self.passes_total > 0:
            return (self.passes_accurate / self.passes_total) * 100
        return 0.0
    
    @property
    def dribble_success_rate(self) -> float:
        """Calculate dribble success rate"""
        if self.dribbles_attempted > 0:
            return (self.dribbles_successful / self.dribbles_attempted) * 100
        return 0.0
    
    @property
    def aerial_duel_success_rate(self) -> float:
        """Calculate aerial duel success rate"""
        if self.aerial_duels_total > 0:
            return (self.aerial_duels_won / self.aerial_duels_total) * 100
        return 0.0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "fixture_id": self.fixture_id,
            "player_id": self.player_id,
            "team_id": self.team_id,
            "minutes_played": self.minutes_played,
            "position": self.position,
            "rating": round(self.rating, 1) if self.rating else None,
            "goals": self.goals,
            "assists": self.assists,
            "shots_total": self.shots_total,
            "shots_on_target": self.shots_on_target,
            "passes_total": self.passes_total,
            "passes_accurate": self.passes_accurate,
            "pass_accuracy": round(self.pass_accuracy, 1),
            "key_passes": self.key_passes,
            "dribbles_successful": self.dribbles_successful,
            "dribbles_attempted": self.dribbles_attempted,
            "tackles": self.tackles,
            "interceptions": self.interceptions,
            "duels_won": self.duels_won,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "saves": self.saves if self.position == "GK" else None,
        }


class TeamStatistics(Base):
    """
    Team statistics for a single match
    Aggregate team-level stats
    """
    __tablename__ = "team_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    
    # Possession
    possession_percentage = Column(Integer)  # 0-100
    
    # xG
    expected_goals = Column(Float)
    
    # Shots
    shots_total = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)
    shots_off_target = Column(Integer, default=0)
    shots_blocked = Column(Integer, default=0)
    shots_inside_box = Column(Integer, default=0)
    shots_outside_box = Column(Integer, default=0)
    
    # Passing
    passes_total = Column(Integer, default=0)
    passes_accurate = Column(Integer, default=0)
    key_passes = Column(Integer, default=0)
    crosses = Column(Integer, default=0)
    long_balls = Column(Integer, default=0)
    
    # Defensive
    tackles = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    clearances = Column(Integer, default=0)
    
    # Set pieces
    corners = Column(Integer, default=0)
    free_kicks = Column(Integer, default=0)
    
    # Discipline
    fouls_committed = Column(Integer, default=0)
    fouls_won = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    offsides = Column(Integer, default=0)
    
    # Relationships
    fixture = relationship("Fixture")
    team = relationship("Team")
    
    @property
    def pass_accuracy(self) -> float:
        """Calculate pass accuracy percentage"""
        if self.passes_total > 0:
            return (self.passes_accurate / self.passes_total) * 100
        return 0.0
    
    @property
    def shot_accuracy(self) -> float:
        """Calculate shot accuracy percentage"""
        if self.shots_total > 0:
            return (self.shots_on_target / self.shots_total) * 100
        return 0.0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "fixture_id": self.fixture_id,
            "team_id": self.team_id,
            "possession_percentage": self.possession_percentage,
            "expected_goals": round(self.expected_goals, 2) if self.expected_goals else None,
            "shots_total": self.shots_total,
            "shots_on_target": self.shots_on_target,
            "pass_accuracy": round(self.pass_accuracy, 1),
            "passes_total": self.passes_total,
            "key_passes": self.key_passes,
            "tackles": self.tackles,
            "interceptions": self.interceptions,
            "corners": self.corners,
            "fouls_committed": self.fouls_committed,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
        }

