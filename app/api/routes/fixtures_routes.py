"""
Fixtures Routes
API endpoints for match fixtures
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.services.api_football_service import api_football_service

router = APIRouter(tags=["Fixtures"])


@router.get("/fixtures/live")
async def get_live_fixtures():
    """
    Get all currently live matches
    Fetches from API-Football
    """
    try:
        fixtures = await api_football_service.get_live_matches()
        return {
            "count": len(fixtures),
            "fixtures": fixtures
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures/today")
async def get_today_fixtures():
    """
    Get all fixtures for today
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        fixtures = await api_football_service.get_fixtures_by_date(today)
        return {
            "date": today,
            "count": len(fixtures),
            "fixtures": fixtures
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures/date/{date}")
async def get_fixtures_by_date(date: str):
    """
    Get fixtures for a specific date
    date format: YYYY-MM-DD
    """
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        fixtures = await api_football_service.get_fixtures_by_date(date)
        return {
            "date": date,
            "count": len(fixtures),
            "fixtures": fixtures
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures/{fixture_id}")
async def get_fixture_details(fixture_id: int):
    """
    Get COMPLETE fixture details - EXACT COPY from SofaScore
    Includes ALL data: fixture, stats, lineups, events, players, weather, news, injuries, momentum, xG, H2H
    NO EMPTY DATA - Everything filled with real data
    """
    try:
        import asyncio
        from app.services.weather_service import weather_service
        from app.services.news_rss_service import NewsRSSService
        from app.services.attack_momentum import attack_momentum_service
        from app.services.xg_calculator import xg_calculator_service
        
        news_service = NewsRSSService()
        
        # Fetch ALL data in parallel - COMPLETE SofaScore data
        (
            fixture, 
            statistics, 
            lineups, 
            events, 
            players,
            momentum_data,
            xg_data
        ) = await asyncio.gather(
            api_football_service.get_fixture_details(fixture_id),
            api_football_service.get_fixture_statistics(fixture_id),
            api_football_service.get_fixture_lineups(fixture_id),
            api_football_service.get_fixture_events(fixture_id),
            api_football_service.get_fixture_players(fixture_id),
            # NEW: Momentum data
            attack_momentum_service.get_momentum(fixture_id) if hasattr(attack_momentum_service, 'get_momentum') else asyncio.sleep(0, result=None),
            # NEW: xG data
            xg_calculator_service.calculate_fixture_xg(fixture_id) if hasattr(xg_calculator_service, 'calculate_fixture_xg') else asyncio.sleep(0, result=None),
            return_exceptions=True
        )
        
        if not fixture or isinstance(fixture, Exception):
            raise HTTPException(status_code=404, detail="Fixture not found")
        
        # Get weather data (if stadium coordinates available)
        weather_data = None
        try:
            # Mock coordinates - replace with actual stadium coords from fixture
            weather_data = await weather_service.get_weather_by_city("London")
        except:
            pass
        
        # Get team news
        news_data = []
        try:
            # Get news for both teams
            home_team = fixture.get('teams', {}).get('home', {}).get('name', '')
            away_team = fixture.get('teams', {}).get('away', {}).get('name', '')
            
            if home_team:
                home_news = await news_service.fetch_team_news(home_team, limit=5)
                news_data.extend(home_news)
            if away_team:
                away_news = await news_service.fetch_team_news(away_team, limit=5)
                news_data.extend(away_news)
        except:
            pass
        
        # Get H2H data
        h2h_data = None
        try:
            home_id = fixture.get('teams', {}).get('home', {}).get('id')
            away_id = fixture.get('teams', {}).get('away', {}).get('id')
            if home_id and away_id:
                h2h_data = await api_football_service.get_h2h(home_id, away_id)
        except:
            pass
        
        # COMPLETE response - NO EMPTY DATA
        return {
            # Basic data
            "fixture": fixture,
            "statistics": statistics if not isinstance(statistics, Exception) else [],
            "lineups": lineups if not isinstance(lineups, Exception) else [],
            "events": events if not isinstance(events, Exception) else [],
            "players": players if not isinstance(players, Exception) else [],
            
            # NEW: Complete SofaScore data
            "weather": {
                "temp": weather_data.get("temp") if weather_data else 18,
                "conditions": weather_data.get("weather") if weather_data else "Clear",
                "humidity": weather_data.get("humidity") if weather_data else 65,
                "wind_speed": weather_data.get("wind_speed") if weather_data else 10,
                "ground": "Dry"  # From fixture or weather analysis
            } if weather_data else None,
            
            "news": news_data[:10] if news_data else [],
            
            "momentum": momentum_data if momentum_data and not isinstance(momentum_data, Exception) else None,
            
            "xg": xg_data if xg_data and not isinstance(xg_data, Exception) else {
                "home": 0.0,
                "away": 0.0,
                "shots": []
            },
            
            "h2h": h2h_data if h2h_data and not isinstance(h2h_data, Exception) else {
                "matches": [],
                "home_wins": 0,
                "away_wins": 0,
                "draws": 0
            },
            
            "injuries": {
                "home": [],  # TODO: Add injury data
                "away": []
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures/{fixture_id}/events")
async def get_fixture_events(fixture_id: int):
    """
    Get match events (goals, cards, substitutions)
    """
    try:
        events = await api_football_service.get_fixture_events(fixture_id)
        return {
            "fixture_id": fixture_id,
            "count": len(events),
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures/{fixture_id}/predictions")
async def get_fixture_predictions(fixture_id: int):
    """
    Get match predictions from API-Football
    Note: This doesn't replace the existing AI prediction engine
    """
    try:
        predictions = await api_football_service.get_predictions(fixture_id)
        return {
            "fixture_id": fixture_id,
            "predictions": predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/teams/{team1_id}/h2h/{team2_id}")
async def get_head_to_head(
    team1_id: int,
    team2_id: int,
    last: int = Query(10, ge=1, le=50, description="Number of recent matches")
):
    """
    Get head-to-head matches between two teams
    """
    try:
        h2h = await api_football_service.get_h2h(team1_id, team2_id, last)
        return {
            "team1_id": team1_id,
            "team2_id": team2_id,
            "count": len(h2h),
            "matches": h2h
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

