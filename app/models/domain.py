from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid as _uuid
from .base import Base

def UUID_PK():
    return Column(UUID(as_uuid=True), primary_key=True, default=_uuid.uuid4)

class League(Base):
    __tablename__ = "leagues"
    id = UUID_PK()
    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    type = Column(String, nullable=True)
    season_format = Column(String, nullable=True)
    __table_args__ = (UniqueConstraint("name", "country", name="uq_league_name_country"),)

class Team(Base):
    __tablename__ = "teams"
    id = UUID_PK()
    name = Column(String, nullable=False)
    country = Column(String, nullable=True)
    code = Column(String, nullable=True)
    founded = Column(Integer, nullable=True)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    venue = relationship("Venue", backref="teams")

class Player(Base):
    __tablename__ = "players"
    id = UUID_PK()
    name = Column(String, nullable=False)
    position = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    nationality = Column(String, nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    team = relationship("Team", backref="players")

class Venue(Base):
    __tablename__ = "venues"
    id = UUID_PK()
    name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True)

class Coach(Base):
    __tablename__ = "coaches"
    id = UUID_PK()
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    nationality = Column(String, nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)

class Season(Base):
    __tablename__ = "seasons"
    id = UUID_PK()
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)
    year_start = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    league = relationship("League", backref="seasons")
    __table_args__ = (UniqueConstraint("league_id", "year_start", name="uq_league_year"),)

class Fixture(Base):
    __tablename__ = "fixtures"
    id = UUID_PK()
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True)
    home_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    date_utc = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)  # SCHEDULED/LIVE/HT/FT/POSTPONED/CANCELLED
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=True)
    round = Column(String, nullable=True)
    league = relationship("League")
    season = relationship("Season")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])
    venue = relationship("Venue")

class Event(Base):
    __tablename__ = "events"
    id = UUID_PK()
    fixture_id = Column(UUID(as_uuid=True), ForeignKey("fixtures.id"), nullable=False)
    minute = Column(Integer, nullable=True)
    type = Column(String, nullable=True)
    detail = Column(String, nullable=True)
    player_name = Column(String, nullable=True)
    assist_name = Column(String, nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    extra = Column(JSONB, nullable=True)
    fixture = relationship("Fixture", backref="events")

class Lineup(Base):
    __tablename__ = "lineups"
    id = UUID_PK()
    fixture_id = Column(UUID(as_uuid=True), ForeignKey("fixtures.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    formation = Column(String, nullable=True)
    players = Column(JSONB, nullable=True)
    fixture = relationship("Fixture", backref="lineups")
    team = relationship("Team")

class Standing(Base):
    __tablename__ = "standings"
    id = UUID_PK()
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    played = Column(Integer, nullable=False, default=0)
    win = Column(Integer, nullable=False, default=0)
    draw = Column(Integer, nullable=False, default=0)
    loss = Column(Integer, nullable=False, default=0)
    goals_for = Column(Integer, nullable=False, default=0)
    goals_against = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=0)
    __table_args__ = (UniqueConstraint("league_id", "season_id", "team_id", name="uq_table_row"),)

# --- Auto Indexes (P013) ---
Index('ix_fixtures_date_status', getattr(Fixture, 'date_utc'), getattr(Fixture, 'status'))
Index('ix_fixtures_league', getattr(Fixture, 'league_id'))
Index('ix_fixtures_home_team', getattr(Fixture, 'home_team_id'))
Index('ix_fixtures_away_team', getattr(Fixture, 'away_team_id'))
Index('ix_events_fixture', getattr(Event, 'fixture_id'))
Index('ix_standings_team', getattr(Standing, 'team_id'))
