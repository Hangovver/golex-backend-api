from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class FixtureEventDTO(BaseModel):
    id: str
    minute: Optional[int] = None
    type: Optional[str] = None
    detail: Optional[str] = None
    playerName: Optional[str] = Field(default=None, alias="player_name")
    assistName: Optional[str] = Field(default=None, alias="assist_name")
    teamId: Optional[str] = Field(default=None, alias="team_id")

    class Config:
        allow_population_by_field_name = True

class LineupDTO(BaseModel):
    teamId: Optional[str] = Field(default=None, alias="team_id")
    formation: Optional[str] = None
    players: Any = None  # JSON array

    class Config:
        allow_population_by_field_name = True

class FixtureDetailDTO(BaseModel):
    id: str
    dateUtc: datetime = Field(alias="date_utc")
    status: str
    leagueId: str = Field(alias="league_id")
    leagueName: str = Field(alias="league_name")
    homeTeamId: str = Field(alias="home_team_id")
    homeTeamName: str = Field(alias="home_team_name")
    awayTeamId: str = Field(alias="away_team_id")
    awayTeamName: str = Field(alias="away_team_name")
    round: Optional[str] = None
    events: Optional[List[FixtureEventDTO]] = None
    lineups: Optional[List[LineupDTO]] = None
    stats: Optional[dict] = None

    class Config:
        allow_population_by_field_name = True

class TeamDTO(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    code: Optional[str] = None
    founded: Optional[int] = None
    venueId: Optional[str] = Field(default=None, alias="venue_id")
    venueName: Optional[str] = Field(default=None, alias="venue_name")
    venueCity: Optional[str] = Field(default=None, alias="venue_city")
    venueCapacity: Optional[int] = Field(default=None, alias="venue_capacity")

    class Config:
        allow_population_by_field_name = True

class PlayerDTO(BaseModel):
    id: str
    name: str
    position: Optional[str] = None
    age: Optional[int] = None
    nationality: Optional[str] = None
    teamId: Optional[str] = Field(default=None, alias="team_id")
    teamName: Optional[str] = Field(default=None, alias="team_name")

    class Config:
        allow_population_by_field_name = True

class SearchResultDTO(BaseModel):
    type: str  # team|player|league
    id: str
    name: str
    extra: Optional[dict] = None
