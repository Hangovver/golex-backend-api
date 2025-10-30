from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LeagueDTO(BaseModel):
    id: str
    name: str
    country: Optional[str] = None
    type: Optional[str] = None

class StandingRowDTO(BaseModel):
    rank: int
    teamId: str = Field(alias="team_id")
    teamName: str = Field(alias="team_name")
    played: int
    win: int
    draw: int
    loss: int
    goalsFor: int = Field(alias="goals_for")
    goalsAgainst: int = Field(alias="goals_against")
    points: int

    class Config:
        allow_population_by_field_name = True

class FixtureListItemDTO(BaseModel):
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

    class Config:
        allow_population_by_field_name = True
