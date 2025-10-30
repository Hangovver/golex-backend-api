"""
Favorites Routes
API endpoints for user favorites management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.user import User, Favorite
from app.schemas.user import FavoriteCreate, FavoriteResponse, FavoriteUpdate
from app.api.routes.user_routes import get_current_user

router = APIRouter(tags=["Favorites"])


@router.get("/favorites", response_model=List[FavoriteResponse])
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all favorites for current user
    """
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).all()
    
    return favorites


@router.get("/favorites/{entity_type}", response_model=List[FavoriteResponse])
async def get_favorites_by_type(
    entity_type: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get favorites filtered by type (team, player, league, match)
    """
    if entity_type not in ["team", "player", "league", "match"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid entity type. Must be: team, player, league, or match"
        )
    
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.entity_type == entity_type
    ).all()
    
    return favorites


@router.post("/favorites", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new favorite
    """
    # Check if already exists
    existing = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.entity_type == favorite_data.entity_type,
        Favorite.entity_id == favorite_data.entity_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is already in favorites"
        )
    
    # Create new favorite
    new_favorite = Favorite(
        user_id=current_user.id,
        entity_type=favorite_data.entity_type,
        entity_id=favorite_data.entity_id,
        entity_name=favorite_data.entity_name,
        notify_matches=favorite_data.notify_matches,
        notify_goals=favorite_data.notify_goals,
        notify_news=favorite_data.notify_news
    )
    
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    
    return new_favorite


@router.put("/favorites/{favorite_id}", response_model=FavoriteResponse)
async def update_favorite(
    favorite_id: int,
    favorite_update: FavoriteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update favorite notification settings
    """
    favorite = db.query(Favorite).filter(
        Favorite.id == favorite_id,
        Favorite.user_id == current_user.id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    # Update fields
    if favorite_update.notify_matches is not None:
        favorite.notify_matches = favorite_update.notify_matches
    if favorite_update.notify_goals is not None:
        favorite.notify_goals = favorite_update.notify_goals
    if favorite_update.notify_news is not None:
        favorite.notify_news = favorite_update.notify_news
    
    db.commit()
    db.refresh(favorite)
    
    return favorite


@router.delete("/favorites/{favorite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a favorite
    """
    favorite = db.query(Favorite).filter(
        Favorite.id == favorite_id,
        Favorite.user_id == current_user.id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    db.delete(favorite)
    db.commit()
    
    return None


@router.post("/favorites/check")
async def check_favorite(
    entity_type: str,
    entity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if an item is in favorites
    """
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.entity_type == entity_type,
        Favorite.entity_id == entity_id
    ).first()
    
    return {
        "is_favorite": favorite is not None,
        "favorite_id": favorite.id if favorite else None
    }

