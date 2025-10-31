"""
Search Routes
API endpoints for searching teams, players, leagues
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.services.api_football_service import api_football_service

router = APIRouter(tags=["Search"])


@router.get("/search")
async def search(
    q: str = Query(..., min_length=2, description="Search query"),
    type: Optional[str] = Query(None, description="Filter by type: team, player, league"),
    limit: int = Query(10, ge=1, le=50, description="Results per type")
):
    """
    Universal search endpoint
    Searches across teams, players, and leagues
    """
    try:
        results = {
            "teams": [],
            "players": [],
            "leagues": []
        }
        
        if type is None or type == "team":
            teams = await api_football_service.search_teams(q)
            results["teams"] = teams[:limit]
        
        if type is None or type == "player":
            # Search players (simplified - use current season)
            players = await api_football_service.search_players(q, season=2024)
            results["players"] = players[:limit]
        
        if type is None or type == "league":
            # For leagues, we'd typically have them cached in database
            # For now, return empty list
            results["leagues"] = []
        
        return results
    
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/teams")
async def search_teams(
    q: str = Query(..., min_length=2, description="Team name"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Search for teams by name
    """
    try:
        teams = await api_football_service.search_teams(q)
        return {
            "query": q,
            "count": len(teams),
            "teams": teams[:limit]
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/players")
async def search_players(
    q: str = Query(..., min_length=2, description="Player name"),
    league_id: Optional[int] = None,
    season: int = Query(2024, description="Season year"),
    limit: int = Query(20, ge=1, le=50)
):
    """
    Search for players by name
    """
    try:
        players = await api_football_service.search_players(
            q,
            league_id=league_id,
            season=season
        )
        return {
            "query": q,
            "count": len(players),
            "players": players[:limit]
        }
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query"),
    limit: int = Query(5, ge=1, le=10)
):
    """
    Get search suggestions for autocomplete
    Returns quick suggestions based on partial input
    """
    try:
        # In a real implementation, this would use a faster search index
        # or cached popular searches
        
        # For now, return empty suggestions
        # In production, use Elasticsearch or similar
        suggestions = []
        
        return {
            "query": q,
            "suggestions": suggestions[:limit]
        }
    
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=20)
):
    """
    Get popular/trending searches
    """
    try:
        # In production, this would track search analytics
        # For now, return hardcoded popular searches
        popular = [
            {"query": "Manchester City", "type": "team", "count": 15234},
            {"query": "Cristiano Ronaldo", "type": "player", "count": 12456},
            {"query": "Premier League", "type": "league", "count": 10123},
            {"query": "Barcelona", "type": "team", "count": 9876},
            {"query": "Lionel Messi", "type": "player", "count": 8765},
            {"query": "Real Madrid", "type": "team", "count": 8543},
            {"query": "Liverpool", "type": "team", "count": 7654},
            {"query": "Kylian Mbappé", "type": "player", "count": 7123},
            {"query": "Bayern Munich", "type": "team", "count": 6543},
            {"query": "Erling Haaland", "type": "player", "count": 6234},
        ]
        
        return {
            "popular_searches": popular[:limit]
        }
    
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

