"""
Player Rating API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.services.player_rating import player_rating_service, PlayerStats
from app.models.player import Player
from app.models.fixture import Fixture


router = APIRouter(prefix="/players", tags=["Player Ratings"])


@router.post("/{player_id}/rating/calculate")
async def calculate_player_rating(
    player_id: int,
    stats: dict,
    db: Session = Depends(get_db)
):
    """
    Calculate player rating from match statistics
    
    Body should contain player stats:
    {
        "goals": 1,
        "assists": 2,
        "key_passes": 5,
        "successful_passes": 45,
        "shots_on_target": 3,
        ... etc
    }
    """
    # Verify player exists
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Create PlayerStats object
    player_stats = PlayerStats(**stats)
    
    # Calculate rating
    result = player_rating_service.calculate_rating(player_stats)
    
    return {
        "player_id": player_id,
        "player_name": player.name if hasattr(player, 'name') else None,
        **result.to_dict()
    }


@router.get("/{player_id}/fixtures/{fixture_id}/rating")
async def get_player_fixture_rating(
    player_id: int,
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get player rating for a specific fixture from API-Football
    """
    from app.services.api_football_service import api_football_service
    import asyncio
    
    try:
        # Get player stats from API-Football
        players_data = asyncio.run(api_football_service.get_fixture_players(fixture_id))
        
        if not players_data:
            raise HTTPException(status_code=404, detail="No player data found for this fixture")
        
        # Find specific player
        player_stats_data = None
        for team_data in players_data:
            for player_data in team_data.get('players', []):
                if player_data.get('player', {}).get('id') == player_id:
                    player_stats_data = player_data
                    break
            if player_stats_data:
                break
        
        if not player_stats_data:
            raise HTTPException(status_code=404, detail="Player not found in this fixture")
        
        # Extract stats
        player_info = player_stats_data.get('player', {})
        stats_array = player_stats_data.get('statistics', [])
        
        if not stats_array:
            raise HTTPException(status_code=404, detail="No statistics found for this player")
        
        stats = stats_array[0]  # Take first statistics entry
        
        # Get position
        position = stats.get('games', {}).get('position', 'CM')
        minutes_played = stats.get('games', {}).get('minutes', 0)
        
        # Build PlayerStats object
        from app.services.player_rating import PlayerStats
        
        player_stats_obj = PlayerStats(
            # Positive actions
            goals=stats.get('goals', {}).get('total', 0) or 0,
            assists=stats.get('goals', {}).get('assists', 0) or 0,
            key_passes=stats.get('passes', {}).get('key', 0) or 0,
            successful_passes=stats.get('passes', {}).get('total', 0) or 0,
            shots_on_target=stats.get('shots', {}).get('on', 0) or 0,
            tackles_won=stats.get('tackles', {}).get('total', 0) or 0,
            interceptions=stats.get('tackles', {}).get('interceptions', 0) or 0,
            clearances=stats.get('tackles', {}).get('blocks', 0) or 0,
            dribbles_successful=stats.get('dribbles', {}).get('success', 0) or 0,
            duels_won=stats.get('duels', {}).get('won', 0) or 0,
            
            # Negative actions
            errors_leading_to_goal=0,  # Not in API-Football basic data
            yellow_cards=stats.get('cards', {}).get('yellow', 0) or 0,
            red_cards=stats.get('cards', {}).get('red', 0) or 0,
            fouls=stats.get('fouls', {}).get('committed', 0) or 0,
            offsides=stats.get('offsides', 0) or 0,
            possession_lost=stats.get('dribbles', {}).get('attempts', 0) - stats.get('dribbles', {}).get('success', 0) if stats.get('dribbles', {}).get('attempts') and stats.get('dribbles', {}).get('success') else 0,
            
            # Goalkeeper specific
            saves=stats.get('goals', {}).get('saves', 0) or 0,
            goals_conceded=stats.get('goals', {}).get('conceded', 0) or 0,
            
            # Position and minutes
            position=position,
            minutes_played=minutes_played or 90
        )
        
        # Calculate rating
        result = player_rating_service.calculate_rating(player_stats_obj)
        
        return {
            "player_id": player_id,
            "player_name": player_info.get('name'),
            "fixture_id": fixture_id,
            **result.to_dict(),
            "stats": {
                "goals": player_stats_obj.goals,
                "assists": player_stats_obj.assists,
                "key_passes": player_stats_obj.key_passes,
                "successful_passes": player_stats_obj.successful_passes,
                "pass_accuracy": stats.get('passes', {}).get('accuracy', 0) or 0,
                "shots_on_target": player_stats_obj.shots_on_target,
                "tackles": player_stats_obj.tackles_won,
                "interceptions": player_stats_obj.interceptions,
                "dribbles": player_stats_obj.dribbles_successful,
                "duels_won": player_stats_obj.duels_won,
                "fouls": player_stats_obj.fouls,
                "yellow_cards": player_stats_obj.yellow_cards,
                "red_cards": player_stats_obj.red_cards
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating rating: {str(e)}")


@router.get("/fixtures/{fixture_id}/ratings")
async def get_fixture_player_ratings(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all player ratings for a fixture
    """
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # TODO: Get all player stats and calculate ratings
    # For now, return structure
    
    return {
        "fixture_id": fixture_id,
        "home_team": {
            "team_id": fixture.home_team_id,
            "players": []  # List of player ratings
        },
        "away_team": {
            "team_id": fixture.away_team_id,
            "players": []
        },
        "best_players": {
            "home": None,  # Highest rated home player
            "away": None   # Highest rated away player
        }
    }


@router.get("/{player_id}/season/{season_id}/average-rating")
async def get_player_season_rating(
    player_id: int,
    season_id: int,
    db: Session = Depends(get_db)
):
    """
    Get player's average rating for a season
    """
    # TODO: Calculate from all fixtures in season
    
    return {
        "player_id": player_id,
        "season_id": season_id,
        "average_rating": 7.2,
        "color": "#FFC107",
        "color_name": "good",
        "matches_played": 15,
        "rating_history": []  # List of ratings by match
    }


@router.get("/fixtures/{fixture_id}/best-players")
async def get_best_players(
    fixture_id: int,
    limit: int = 3,
    db: Session = Depends(get_db)
):
    """
    Get best players from a fixture (highest ratings)
    Used for "Best Players" section in match summary
    """
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # TODO: Get top rated players
    
    return {
        "fixture_id": fixture_id,
        "home_team": {
            "team_id": fixture.home_team_id,
            "best_players": [
                # {
                #     "player_id": 1,
                #     "name": "Player Name",
                #     "position": "ST",
                #     "rating": 9.2,
                #     "color": "#4CAF50",
                #     "goals": 2,
                #     "assists": 1
                # }
            ]
        },
        "away_team": {
            "team_id": fixture.away_team_id,
            "best_players": []
        }
    }

