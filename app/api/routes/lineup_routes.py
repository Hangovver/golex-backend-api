"""
Lineup Routes
API endpoints for match lineups and formations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.lineup import Lineup, LineupPlayer
from app.schemas.lineup import LineupResponse, LineupPlayerSchema

router = APIRouter(tags=["Lineups"])


@router.get("/fixtures/{fixture_id}/lineups", response_model=LineupResponse)
async def get_fixture_lineups(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get lineups for a specific fixture
    
    Returns home and away team lineups with:
    - Formation (e.g., "4-3-3")
    - Starting XI
    - Substitutes
    - Player positions on field
    - Player ratings (if match finished)
    - Shirt colors
    """
    # Query lineups
    home_lineup = db.query(Lineup).filter(
        Lineup.fixture_id == fixture_id,
        Lineup.is_home == True
    ).first()
    
    away_lineup = db.query(Lineup).filter(
        Lineup.fixture_id == fixture_id,
        Lineup.is_home == False
    ).first()
    
    if not home_lineup or not away_lineup:
        raise HTTPException(
            status_code=404,
            detail="Lineups not found for this fixture"
        )
    
    return {
        "fixture_id": fixture_id,
        "home": home_lineup.to_dict(),
        "away": away_lineup.to_dict()
    }


@router.get("/fixtures/{fixture_id}/lineups/home", response_model=dict)
async def get_home_lineup(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """Get home team lineup only"""
    lineup = db.query(Lineup).filter(
        Lineup.fixture_id == fixture_id,
        Lineup.is_home == True
    ).first()
    
    if not lineup:
        raise HTTPException(status_code=404, detail="Home lineup not found")
    
    return lineup.to_dict()


@router.get("/fixtures/{fixture_id}/lineups/away", response_model=dict)
async def get_away_lineup(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """Get away team lineup only"""
    lineup = db.query(Lineup).filter(
        Lineup.fixture_id == fixture_id,
        Lineup.is_home == False
    ).first()
    
    if not lineup:
        raise HTTPException(status_code=404, detail="Away lineup not found")
    
    return lineup.to_dict()


@router.get("/players/{player_id}/lineup-history")
async def get_player_lineup_history(
    player_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get player's recent lineup appearances
    Shows positions played, ratings, and formations
    """
    lineup_players = db.query(LineupPlayer).filter(
        LineupPlayer.player_id == player_id
    ).order_by(
        LineupPlayer.created_at.desc()
    ).limit(limit).all()
    
    return {
        "player_id": player_id,
        "total_appearances": len(lineup_players),
        "lineups": [lp.to_dict() for lp in lineup_players]
    }


@router.get("/formations/popular")
async def get_popular_formations(
    league_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Get most popular formations
    Optionally filtered by league
    """
    from sqlalchemy import func
    
    query = db.query(
        Lineup.formation,
        func.count(Lineup.id).label("count")
    ).group_by(Lineup.formation)
    
    if league_id:
        query = query.join(Lineup.fixture).filter(
            Lineup.fixture.league_id == league_id
        )
    
    formations = query.order_by(
        func.count(Lineup.id).desc()
    ).limit(limit).all()
    
    return {
        "formations": [
            {
                "formation": f[0],
                "usage_count": f[1]
            }
            for f in formations
        ]
    }

