"""
Expected Goals (xG) API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.services.xg_calculator import xg_calculator_service, ShotData
from app.models.fixture import Fixture


router = APIRouter(prefix="/fixtures/{fixture_id}/xg", tags=["xG"])


@router.get("")
async def get_fixture_xg(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get xG statistics for a fixture from API-Football statistics
    """
    from app.services.api_football_service import api_football_service
    import asyncio
    
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    try:
        # Get match statistics from API-Football
        stats_data = asyncio.run(api_football_service.get_fixture_statistics(fixture_id))
        
        if not stats_data:
            return {
                "fixture_id": fixture_id,
                "home_team": {"team_id": fixture.home_team_id, "xg": 0.0, "shots": 0},
                "away_team": {"team_id": fixture.away_team_id, "xg": 0.0, "shots": 0},
                "actual_score": {"home": fixture.home_score, "away": fixture.away_score}
            }
        
        home_team_id = fixture.home_team_id
        
        home_shots = []
        away_shots = []
        
        for team_stats in stats_data:
            team_id = team_stats.get('team', {}).get('id')
            is_home = team_id == home_team_id
            statistics = team_stats.get('statistics', [])
            
            # Extract shot statistics
            shots_on_target = 0
            shots_off_target = 0
            shots_blocked = 0
            
            for stat in statistics:
                stat_type = stat.get('type', '')
                stat_value = stat.get('value')
                
                if stat_type == 'Shots on Goal' and stat_value:
                    shots_on_target = int(stat_value) if isinstance(stat_value, (int, str)) and str(stat_value).isdigit() else 0
                elif stat_type == 'Shots off Goal' and stat_value:
                    shots_off_target = int(stat_value) if isinstance(stat_value, (int, str)) and str(stat_value).isdigit() else 0
                elif stat_type == 'Blocked Shots' and stat_value:
                    shots_blocked = int(stat_value) if isinstance(stat_value, (int, str)) and str(stat_value).isdigit() else 0
            
            # Create shot data for xG calculation
            # Distribute shots across penalty area with realistic positions
            shots_list = home_shots if is_home else away_shots
            
            # Shots on target (higher xG - closer to goal, better angle)
            for i in range(shots_on_target):
                # Vary distance and angle for realism
                distance = 8.0 + (i % 3) * 3.0  # 8m, 11m, 14m variation
                angle = 30.0 + (i % 4) * 15.0  # 30°, 45°, 60°, 75° variation
                
                shots_list.append({
                    'distance_to_goal': distance,
                    'angle_to_goal': angle,
                    'body_part': 'right_foot' if i % 3 != 1 else 'head',
                    'situation': 'open_play',
                    'goalkeeper_out': False,
                    'defender_pressure': 0.2 + (i % 3) * 0.2,  # Varying pressure
                    'shot_type': 'on_target'
                })
            
            # Shots off target (lower xG - worse positioning)
            for i in range(shots_off_target):
                distance = 12.0 + (i % 4) * 4.0  # 12m, 16m, 20m, 24m
                angle = 20.0 + (i % 3) * 20.0  # 20°, 40°, 60°
                
                shots_list.append({
                    'distance_to_goal': distance,
                    'angle_to_goal': angle,
                    'body_part': 'right_foot' if i % 2 == 0 else 'weak_foot',
                    'situation': 'open_play',
                    'goalkeeper_out': False,
                    'defender_pressure': 0.4 + (i % 2) * 0.3,
                    'shot_type': 'off_target'
                })
            
            # Blocked shots (lowest xG - heavy pressure)
            for i in range(shots_blocked):
                distance = 10.0 + (i % 3) * 5.0
                angle = 25.0 + (i % 2) * 20.0
                
                shots_list.append({
                    'distance_to_goal': distance,
                    'angle_to_goal': angle,
                    'body_part': 'right_foot',
                    'situation': 'open_play',
                    'goalkeeper_out': False,
                    'defender_pressure': 0.7 + (i % 2) * 0.2,
                    'shot_type': 'blocked'
                })
        
        # Calculate xG using our service
        home_xg = xg_calculator_service.calculate_team_xg(home_shots)
        away_xg = xg_calculator_service.calculate_team_xg(away_shots)
        
        return {
            "fixture_id": fixture_id,
            "home_team": {
                "team_id": fixture.home_team_id,
                "xg": home_xg,
                "shots": len(home_shots),
                "shots_breakdown": {
                    "on_target": sum(1 for s in home_shots if s.get('shot_type') == 'on_target'),
                    "off_target": sum(1 for s in home_shots if s.get('shot_type') == 'off_target'),
                    "blocked": sum(1 for s in home_shots if s.get('shot_type') == 'blocked')
                }
            },
            "away_team": {
                "team_id": fixture.away_team_id,
                "xg": away_xg,
                "shots": len(away_shots),
                "shots_breakdown": {
                    "on_target": sum(1 for s in away_shots if s.get('shot_type') == 'on_target'),
                    "off_target": sum(1 for s in away_shots if s.get('shot_type') == 'off_target'),
                    "blocked": sum(1 for s in away_shots if s.get('shot_type') == 'blocked')
                }
            },
            "actual_score": {
                "home": fixture.home_score,
                "away": fixture.away_score
            },
            "xg_difference": {
                "home": round(home_xg - (fixture.home_score or 0), 2),
                "away": round(away_xg - (fixture.away_score or 0), 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating xG: {str(e)}")


@router.post("/calculate-shot")
async def calculate_shot_xg(
    fixture_id: int,
    shot_data: dict
):
    """
    Calculate xG for a single shot
    
    Body:
    {
        "distance_to_goal": 12.5,
        "angle_to_goal": 45.0,
        "body_part": "right_foot",
        "situation": "open_play",
        "goalkeeper_out": false,
        "defender_pressure": 0.3
    }
    """
    try:
        shot = ShotData(**shot_data)
        result = xg_calculator_service.calculate_xg(shot)
        
        return {
            "fixture_id": fixture_id,
            **result.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/shot-map")
async def get_shot_map(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get shot map data with xG values
    
    Returns all shots with locations and xG
    """
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # TODO: Get shots from database with locations
    
    return {
        "fixture_id": fixture_id,
        "home_team": {
            "team_id": fixture.home_team_id,
            "shots": [
                # {
                #     "minute": 15,
                #     "player_id": 1,
                #     "x": 85.0,  # Field percentage
                #     "y": 45.0,
                #     "xg": 0.35,
                #     "result": "goal",  # goal, on_target, off_target, blocked
                #     "distance": 12.5,
                #     "angle": 30.0
                # }
            ]
        },
        "away_team": {
            "team_id": fixture.away_team_id,
            "shots": []
        }
    }


@router.get("/timeline")
async def get_xg_timeline(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get cumulative xG over time (for xG chart)
    """
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # TODO: Calculate cumulative xG by minute
    
    return {
        "fixture_id": fixture_id,
        "timeline": [
            # {
            #     "minute": 0,
            #     "home_xg": 0.0,
            #     "away_xg": 0.0
            # },
            # {
            #     "minute": 15,
            #     "home_xg": 0.35,
            #     "away_xg": 0.0
            # },
            # ...
        ]
    }


@router.post("/from-location")
async def calculate_xg_from_location(
    x: float,
    y: float
):
    """
    Calculate xG from field coordinates
    
    Useful for interactive shot map
    
    Args:
        x: 0-100 (0 = own goal, 100 = opponent goal)
        y: 0-100 (0 = left sideline, 100 = right sideline)
    """
    if not (0 <= x <= 100 and 0 <= y <= 100):
        raise HTTPException(
            status_code=400,
            detail="Coordinates must be between 0 and 100"
        )
    
    xg = xg_calculator_service.get_xg_from_location(x, y)
    
    return {
        "x": x,
        "y": y,
        "xg": round(xg, 3)
    }

