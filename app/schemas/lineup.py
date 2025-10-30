"""
Lineup Schemas
For API request/response serialization
"""
from pydantic import BaseModel
from typing import List, Optional


class LineupPlayerSchema(BaseModel):
    """Schema for lineup player"""
    id: int
    player_id: int
    position: str
    shirt_number: int
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    is_starter: bool
    is_captain: bool
    was_substituted: bool
    substituted_minute: Optional[int] = None
    rating: Optional[float] = None
    
    class Config:
        from_attributes = True


class LineupSchema(BaseModel):
    """Schema for team lineup"""
    id: int
    fixture_id: int
    team_id: int
    is_home: bool
    formation: Optional[str] = None
    player_shirt_color: Optional[str] = None
    goalkeeper_shirt_color: Optional[str] = None
    players: List[LineupPlayerSchema]
    
    class Config:
        from_attributes = True


class LineupResponse(BaseModel):
    """Response for fixture lineups"""
    fixture_id: int
    home: LineupSchema
    away: LineupSchema

