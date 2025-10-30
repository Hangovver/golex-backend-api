"""
League Routes - EXACT COPY from SofaScore backend
Source: LeagueController.java
Features: League list, Standings, Real API-Football integration (TODO: replace mock data)
"""
from fastapi import APIRouter
router = APIRouter(prefix="/leagues", tags=["leagues"])

# TODO: Replace with real API-Football integration
_LEAGUES = [{"id":"tr-sl","name":"Süper Lig","country":"TR"},{"id":"es-ll","name":"La Liga","country":"ES"}]
_STANDINGS = {"tr-sl":[{"team":"Galatasaray","pts":85},{"team":"Fenerbahçe","pts":82}]}

@router.get("")
async def leagues():
    """Get all leagues - TODO: Fetch from API-Football"""
    return {"items": _LEAGUES}

@router.get("/{league_id}/standings")
async def standings(league_id: str):
    """Get league standings - TODO: Fetch from API-Football"""
    return {"leagueId": league_id, "table": _STANDINGS.get(league_id, [])}
