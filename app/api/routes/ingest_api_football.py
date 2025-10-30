from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import os, json

from ..security.deps import get_db

router = APIRouter(tags=['ingestion'], prefix='/ingestion')

def upsert_league(db: Session, api_id: int, name: str, country: str|None, season: int|None):
    db.execute(text("""INSERT INTO leagues(api_id,name,country,season)
                      VALUES(:api_id,:name,:country,:season)
                      ON CONFLICT (api_id) DO UPDATE SET name=:name, country=:country, season=:season"""),
               {'api_id': api_id, 'name': name, 'country': country, 'season': season})

def upsert_team(db: Session, api_id: int, name: str, country: str|None):
    db.execute(text("""INSERT INTO teams(api_id,name,country)
                      VALUES(:api_id,:name,:country)
                      ON CONFLICT (api_id) DO UPDATE SET name=:name, country=:country"""),
               {'api_id': api_id, 'name': name, 'country': country})

def upsert_fixture(db: Session, api_id: int, league_api_id: int|None, home_api: int|None, away_api: int|None, status: str|None, starts_at_utc: str|None):
    # map foreign keys by api_id
    league_id = db.execute(text("SELECT id FROM leagues WHERE api_id=:x"), {'x': league_api_id}).scalar() if league_api_id else None
    home_id = db.execute(text("SELECT id FROM teams WHERE api_id=:x"), {'x': home_api}).scalar() if home_api else None
    away_id = db.execute(text("SELECT id FROM teams WHERE api_id=:x"), {'x': away_api}).scalar() if away_api else None
    db.execute(text("""INSERT INTO fixtures(api_id,league_id,home_team_id,away_team_id,status,starts_at_utc)
                      VALUES(:api_id,:league_id,:home_id,:away_id,:status,:starts)
                      ON CONFLICT (api_id) DO UPDATE SET league_id=:league_id, home_team_id=:home_id, away_team_id=:away_id, status=:status, starts_at_utc=:starts"""),
               {'api_id': api_id, 'league_id': league_id, 'home_id': home_id, 'away_id': away_id, 'status': status, 'starts': starts_at_utc})

@router.post('/seed-demo')
def seed_demo(db: Session = Depends(get_db)):
    # Demo payload (gerçek API çağrısı yerine)
    leagues = [{'id': 39, 'name':'Premier League', 'country':'England', 'season':2024}]
    teams = [{'id': 33,'name':'Man Utd','country':'England'}, {'id':40,'name':'Liverpool','country':'England'}]
    fixtures = [{'id': 1001,'league':39,'home':33,'away':40,'status':'SCHEDULED','starts_at_utc':'2025-11-01T12:30:00Z'}]
    for l in leagues: upsert_league(db, l['id'], l['name'], l.get('country'), l.get('season'))
    for t in teams: upsert_team(db, t['id'], t['name'], t.get('country'))
    for f in fixtures: upsert_fixture(db, f['id'], f['league'], f['home'], f['away'], f['status'], f['starts_at_utc'])
    db.commit()
    return {'ok': True, 'leagues': len(leagues), 'teams': len(teams), 'fixtures': len(fixtures)}
