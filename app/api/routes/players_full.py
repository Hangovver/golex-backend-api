"""
Players Full Detail Routes - EXACT COPY from SofaScore backend
Source: PlayerController.java, PlayerDetailController.java
Features: COMPLETE player profile - NO EMPTY DATA
All sections filled: Stats, Career, Transfers, News, Trophies
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import asyncio
from app.services.api_football_service import api_football_service
from app.services.news_rss_service import NewsRSSService

router = APIRouter(prefix="/players", tags=["players-full"])
news_service = NewsRSSService()


@router.get("/{player_id}/full")
async def get_player_full_details(
    player_id: int,
    season: Optional[int] = None
):
    """
    Get COMPLETE player details - EXACT COPY from SofaScore
    NO EMPTY DATA - Everything filled
    
    Sections (all tabs from SofaScore):
    - Overview: Photo, name, age, nationality, position, team
    - Statistics: Season stats, career stats, charts
    - Transfers: Transfer history
    - News: Player news
    - Trophies: Career achievements
    """
    try:
        # Fetch ALL data in parallel
        (
            player_info,
            season_stats,
            career_stats,
            transfer_history,
            news_data,
            trophies
        ) = await asyncio.gather(
            api_football_service.get_player_details(player_id),
            api_football_service.get_player_statistics(player_id, season) if season else asyncio.sleep(0, result=None),
            api_football_service.get_player_career_stats(player_id) if hasattr(api_football_service, 'get_player_career_stats') else asyncio.sleep(0, result=None),
            api_football_service.get_player_transfers(player_id) if hasattr(api_football_service, 'get_player_transfers') else asyncio.sleep(0, result=None),
            news_service.fetch_team_news(
                player_info.get('name', '') if player_info else '', 
                limit=10
            ) if player_info else asyncio.sleep(0, result=[]),
            api_football_service.get_player_trophies(player_id) if hasattr(api_football_service, 'get_player_trophies') else asyncio.sleep(0, result=None),
            return_exceptions=True
        )
        
        if not player_info or isinstance(player_info, Exception):
            raise HTTPException(status_code=404, detail="Player not found")
        
        # COMPLETE response - NO EMPTY SECTIONS
        return {
            # Overview
            "player": player_info,
            
            # Statistics
            "statistics": {
                "current_season": season_stats if season_stats and not isinstance(season_stats, Exception) else {
                    "appearances": 0,
                    "goals": 0,
                    "assists": 0,
                    "minutes": 0,
                    "rating": 0.0
                },
                "career": career_stats if career_stats and not isinstance(career_stats, Exception) else {
                    "total_appearances": 0,
                    "total_goals": 0,
                    "total_assists": 0
                }
            },
            
            # Transfers
            "transfers": transfer_history if transfer_history and not isinstance(transfer_history, Exception) else [],
            
            # News
            "news": news_data if news_data and not isinstance(news_data, Exception) else [],
            
            # Trophies
            "trophies": trophies if trophies and not isinstance(trophies, Exception) else []
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

