"""
Lineup Models
For storing match lineups and formations
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.models.base import Base


class Lineup(Base):
    """
    Team lineup for a match
    Stores formation and shirt colors
    """
    __tablename__ = "lineups"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    fixture_id = Column(Integer, ForeignKey("fixtures.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    
    # Match context
    is_home = Column(Boolean, nullable=False)
    
    # Formation
    formation = Column(String(10))  # e.g., "4-3-3", "4-4-2"
    
    # Shirt colors (hex)
    player_shirt_color = Column(String(7))  # e.g., "#FF0000"
    goalkeeper_shirt_color = Column(String(7))  # e.g., "#00FF00"
    
    # Relationships
    fixture = relationship("Fixture", back_populates="lineups")
    team = relationship("Team")
    players = relationship("LineupPlayer", back_populates="lineup", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "fixture_id": self.fixture_id,
            "team_id": self.team_id,
            "is_home": self.is_home,
            "formation": self.formation,
            "player_shirt_color": self.player_shirt_color,
            "goalkeeper_shirt_color": self.goalkeeper_shirt_color,
            "players": [p.to_dict() for p in self.players]
        }


class LineupPlayer(Base):
    """
    Individual player in a lineup
    Stores position on field and role
    """
    __tablename__ = "lineup_players"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    lineup_id = Column(Integer, ForeignKey("lineups.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    
    # Position info
    position = Column(String(10))  # GK, CB, CM, ST, etc.
    shirt_number = Column(Integer, nullable=False)
    
    # Field position (0-100 percentage)
    position_x = Column(Float)  # Horizontal position
    position_y = Column(Float)  # Vertical position
    
    # Role
    is_starter = Column(Boolean, default=True)
    is_captain = Column(Boolean, default=False)
    
    # Substitution
    was_substituted = Column(Boolean, default=False)
    substituted_minute = Column(Integer)
    
    # Rating (if match finished)
    rating = Column(Float)
    
    # Relationships
    lineup = relationship("Lineup", back_populates="players")
    player = relationship("Player")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "position": self.position,
            "shirt_number": self.shirt_number,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "is_starter": self.is_starter,
            "is_captain": self.is_captain,
            "was_substituted": self.was_substituted,
            "substituted_minute": self.substituted_minute,
            "rating": round(self.rating, 1) if self.rating else None
        }
