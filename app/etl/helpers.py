from typing import Any, Dict
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from ..models.fixture import Fixture
from ..models.team import Team
from ..models.league import League
from ..models.season import Season
from ..models.venue import Venue

def upsert_league(session: Session, data: Dict[str, Any]) -> str:
    stmt = insert(League).values(**data).on_conflict_do_update(
        index_elements=[League.api_football_id],
        set_=data
    )
    session.execute(stmt)
    return data.get("id")

def upsert_team(session: Session, data: Dict[str, Any]) -> str:
    stmt = insert(Team).values(**data).on_conflict_do_update(
        index_elements=[Team.api_football_id],
        set_=data
    )
    session.execute(stmt)
    return data.get("id")

def upsert_season(session: Session, data: Dict[str, Any]) -> str:
    stmt = insert(Season).values(**data).on_conflict_do_nothing()
    session.execute(stmt)
    return data.get("id")

def upsert_venue(session: Session, data: Dict[str, Any]) -> str:
    stmt = insert(Venue).values(**data).on_conflict_do_update(
        index_elements=[Venue.api_football_id],
        set_=data
    )
    session.execute(stmt)
    return data.get("id")

def upsert_fixture(session: Session, data: Dict[str, Any]) -> str:
    # Idempotent upsert by api_football_id if present, else by id
    if data.get("api_football_id") is not None:
        stmt = insert(Fixture).values(**data).on_conflict_do_update(
            index_elements=[Fixture.api_football_id],
            set_=data
        )
    else:
        stmt = insert(Fixture).values(**data).on_conflict_do_nothing()
    session.execute(stmt)
    return data.get("id")
