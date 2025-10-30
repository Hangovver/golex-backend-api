"""
Attack Momentum API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.services.attack_momentum import attack_momentum_service
from app.models.fixture import Fixture


router = APIRouter(prefix="/fixtures/{fixture_id}/attack-momentum", tags=["Attack Momentum"])


@router.get("")
async def get_attack_momentum(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attack momentum graph data for a fixture
    
    Returns minute-by-minute momentum values (-1.0 to 1.0)
    - Negative values: Away team dominance
    - Positive values: Home team dominance
    - 0.0: Balanced
    """
    # Get fixture
    fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Get events (from fixture or separate events table)
    # TODO: Get from actual events table
    events = _get_fixture_events(db, fixture_id)
    
    # Determine total minutes
    total_minutes = 90
    if fixture.status == "finished":
        # Check if extra time
        if hasattr(fixture, 'et_home_score') and fixture.et_home_score is not None:
            total_minutes = 120
    
    # Calculate momentum
    momentum_points = attack_momentum_service.calculate_momentum(
        events=events,
        total_minutes=total_minutes
    )
    
    # Get phases
    phases = attack_momentum_service.get_phases(total_minutes)
    
    return {
        "fixture_id": fixture_id,
        "total_minutes": total_minutes,
        "phases": phases,
        "data": [point.to_dict() for point in momentum_points],
        "metadata": {
            "home_team": fixture.home_team.name if hasattr(fixture, 'home_team') else None,
            "away_team": fixture.away_team.name if hasattr(fixture, 'away_team') else None,
        }
    }


@router.get("/summary")
async def get_momentum_summary(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get attack momentum summary statistics
    """
    # Get events
    events = _get_fixture_events(db, fixture_id)
    
    # Calculate momentum
    momentum_points = attack_momentum_service.calculate_momentum(events, 90)
    
    # Calculate statistics
    home_dominant_minutes = sum(1 for p in momentum_points if p.value > 0.3)
    away_dominant_minutes = sum(1 for p in momentum_points if p.value < -0.3)
    balanced_minutes = sum(1 for p in momentum_points if -0.3 <= p.value <= 0.3)
    
    avg_momentum = sum(p.value for p in momentum_points) / len(momentum_points)
    max_momentum = max(p.value for p in momentum_points)
    min_momentum = min(p.value for p in momentum_points)
    
    return {
        "fixture_id": fixture_id,
        "summary": {
            "home_dominant_minutes": home_dominant_minutes,
            "away_dominant_minutes": away_dominant_minutes,
            "balanced_minutes": balanced_minutes,
            "average_momentum": round(avg_momentum, 3),
            "max_home_momentum": round(max_momentum, 3),
            "max_away_momentum": round(abs(min_momentum), 3)
        }
    }


def _get_fixture_events(db: Session, fixture_id: int) -> List[dict]:
    """
    Get match events for momentum calculation from API-Football
    """
    from app.services.api_football_service import api_football_service
    import asyncio
    
    try:
        # Get events from API-Football
        events_data = asyncio.run(api_football_service.get_fixture_events(fixture_id))
        
        if not events_data:
            return []
        
        # Convert to momentum events format
        momentum_events = []
        
        # Get fixture to determine home/away team IDs
        fixture = db.query(Fixture).filter(Fixture.id == fixture_id).first()
        if not fixture:
            return []
        
        home_team_id = fixture.home_team_id
        
        for event in events_data:
            # Extract event data
            time_data = event.get('time', {})
            minute = time_data.get('elapsed', 0)
            extra = time_data.get('extra', 0)
            
            if minute is None:
                continue
            
            # Adjust minute for extra time
            if extra:
                minute = minute + extra
            
            event_type = event.get('type', '').lower()
            team_id = event.get('team', {}).get('id')
            detail = event.get('detail', '').lower()
            
            # Map API-Football events to momentum event types
            momentum_type = None
            
            if event_type == 'goal':
                if 'own goal' in detail or 'own-goal' in detail:
                    momentum_type = 'own_goal'
                elif 'penalty' in detail:
                    momentum_type = 'penalty_goal'
                else:
                    momentum_type = 'goal'
            
            elif event_type == 'card':
                if 'yellow' in detail:
                    momentum_type = 'yellow_card'
                elif 'red' in detail:
                    momentum_type = 'red_card'
            
            elif event_type == 'subst':
                # Substitutions don't affect momentum directly
                continue
            
            elif event_type == 'var':
                momentum_type = 'var'
            
            # Additional event types from match statistics
            # These would come from a more detailed events feed
            # For now, we'll work with what we have
            
            if momentum_type:
                momentum_events.append({
                    'minute': float(minute),
                    'type': momentum_type,
                    'is_home': team_id == home_team_id
                })
        
        # Enrich with statistics-based events
        # Get match statistics for additional events
        stats_data = asyncio.run(api_football_service.get_fixture_statistics(fixture_id))
        
        if stats_data:
            for team_stats in stats_data:
                team_id = team_stats.get('team', {}).get('id')
                is_home = team_id == home_team_id
                statistics = team_stats.get('statistics', [])
                
                for stat in statistics:
                    stat_type = stat.get('type', '')
                    stat_value = stat.get('value')
                    
                    # Distribute events across match time
                    if stat_type == 'Shots on Goal' and stat_value:
                        # Add shots on target (distribute across 90 minutes)
                        count = int(stat_value) if isinstance(stat_value, (int, str)) and str(stat_value).isdigit() else 0
                        for i in range(count):
                            minute = (i + 1) * (90 // max(count, 1))
                            momentum_events.append({
                                'minute': float(minute),
                                'type': 'shot_on_target',
                                'is_home': is_home
                            })
                    
                    elif stat_type == 'Shots off Goal' and stat_value:
                        count = int(stat_value) if isinstance(stat_value, (int, str)) and str(stat_value).isdigit() else 0
                        for i in range(count):
                            minute = (i + 1) * (90 // max(count, 1))
                            momentum_events.append({
                                'minute': float(minute),
                                'type': 'shot_off_target',
                                'is_home': is_home
                            })
                    
                    elif stat_type == 'Corner Kicks' and stat_value:
                        count = int(stat_value) if isinstance(stat_value, (int, str)) and str(stat_value).isdigit() else 0
                        for i in range(count):
                            minute = (i + 1) * (90 // max(count, 1))
                            momentum_events.append({
                                'minute': float(minute),
                                'type': 'corner',
                                'is_home': is_home
                            })
        
        # Sort by minute
        momentum_events.sort(key=lambda x: x['minute'])
        
        return momentum_events
        
    except Exception as e:
        print(f"Error getting fixture events: {e}")
        return []


# Additional endpoint for live updates
@router.get("/live")
async def get_live_momentum(
    fixture_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current momentum for live match
    Returns latest momentum value and trend
    """
    # Get events
    events = _get_fixture_events(db, fixture_id)
    
    if not events:
        return {
            "fixture_id": fixture_id,
            "current_momentum": 0.0,
            "trend": "neutral",
            "last_update": None
        }
    
    # Get current minute
    current_minute = max(e['minute'] for e in events)
    
    # Calculate momentum
    momentum_points = attack_momentum_service.calculate_momentum(events, int(current_minute) + 10)
    
    # Get current and recent momentum
    current = momentum_points[-1] if momentum_points else None
    recent = momentum_points[-5:] if len(momentum_points) >= 5 else momentum_points
    
    # Calculate trend
    if len(recent) >= 2:
        trend_value = recent[-1].value - recent[0].value
        if trend_value > 0.1:
            trend = "increasing_home"
        elif trend_value < -0.1:
            trend = "increasing_away"
        else:
            trend = "stable"
    else:
        trend = "neutral"
    
    return {
        "fixture_id": fixture_id,
        "current_minute": current_minute,
        "current_momentum": current.value if current else 0.0,
        "trend": trend,
        "recent_momentum": [p.to_dict() for p in recent[-10:]]
    }

