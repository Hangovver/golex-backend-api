"""
Statistics Routes
API endpoints for match, player, and team statistics
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.services.statistics_service import StatisticsService

router = APIRouter(tags=["Statistics"])


@router.get("/fixtures/{fixture_id}/statistics")
async def get_fixture_statistics(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for a fixture
    Includes team stats and all player stats
    """
    service = StatisticsService(db)
    
    team_stats = service.get_team_statistics(fixture_id)
    player_stats = service.get_player_statistics(fixture_id)
    
    return {
        "fixture_id": fixture_id,
        "teams": {
            "home": team_stats["home"].to_dict() if team_stats["home"] else None,
            "away": team_stats["away"].to_dict() if team_stats["away"] else None
        },
        "players": [ps.to_dict() for ps in player_stats]
    }


@router.get("/fixtures/{fixture_id}/statistics/players/{player_id}")
async def get_player_match_statistics(
    fixture_id: int,
    player_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific player's statistics for a match
    """
    service = StatisticsService(db)
    
    stats = service.get_player_statistics(fixture_id, player_id)
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail="Player statistics not found for this match"
        )
    
    return stats[0].to_dict()


@router.get("/players/{player_id}/statistics/season")
async def get_player_season_statistics(
    player_id: int,
    season_year: int = Query(..., description="Season year (e.g., 2024)"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated player statistics for a season
    """
    service = StatisticsService(db)
    
    stats = service.get_player_season_stats(player_id, season_year)
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail="No statistics found for this player in the specified season"
        )
    
    return {
        "player_id": player_id,
        "season_year": season_year,
        "statistics": stats
    }


@router.get("/teams/{team_id}/statistics/season")
async def get_team_season_statistics(
    team_id: int,
    season_year: int = Query(..., description="Season year (e.g., 2024)"),
    db: Session = Depends(get_db)
):
    """
    Get aggregated team statistics for a season
    """
    service = StatisticsService(db)
    
    stats = service.get_team_season_stats(team_id, season_year)
    
    if not stats:
        raise HTTPException(
            status_code=404,
            detail="No statistics found for this team in the specified season"
        )
    
    return {
        "team_id": team_id,
        "season_year": season_year,
        "statistics": stats
    }


@router.get("/fixtures/{fixture_id}/statistics/top-players")
async def get_top_rated_players(
    fixture_id: int,
    limit: int = Query(3, ge=1, le=10, description="Number of top players per team"),
    db: Session = Depends(get_db)
):
    """
    Get top-rated players for each team in a match
    """
    service = StatisticsService(db)
    
    top_players = service.get_top_rated_players(fixture_id, limit)
    
    return {
        "fixture_id": fixture_id,
        "home_top_players": [p.to_dict() for p in top_players["home"]],
        "away_top_players": [p.to_dict() for p in top_players["away"]]
    }


@router.get("/players/compare")
async def compare_players(
    player_id_1: int = Query(..., description="First player ID"),
    player_id_2: int = Query(..., description="Second player ID"),
    season_year: int = Query(..., description="Season year (e.g., 2024)"),
    db: Session = Depends(get_db)
):
    """
    Compare statistics between two players for a season
    """
    service = StatisticsService(db)
    
    comparison = service.compare_players(player_id_1, player_id_2, season_year)
    
    return {
        "season_year": season_year,
        "comparison": comparison
    }

