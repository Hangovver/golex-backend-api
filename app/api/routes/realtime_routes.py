"""
Real-time Data Routes
Server-Sent Events (SSE) for live match updates
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json
from typing import AsyncGenerator

from app.db.session import get_db
from app.services.api_football_service import api_football_service

router = APIRouter(tags=["Real-time"])


async def generate_live_updates(fixture_id: int) -> AsyncGenerator[str, None]:
    """
    Generator for SSE live match updates
    Sends updates every 10 seconds
    """
    while True:
        try:
            # Fetch latest match data
            fixture = await api_football_service.get_fixture_details(fixture_id)
            events = await api_football_service.get_fixture_events(fixture_id)
            
            # Prepare update data
            update = {
                "type": "match_update",
                "fixture_id": fixture_id,
                "status": fixture.get("fixture", {}).get("status", {}),
                "score": fixture.get("score", {}),
                "events": events[-5:] if events else [],  # Last 5 events
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Send as SSE
            yield f"data: {json.dumps(update)}\n\n"
            
            # Check if match is finished
            status = fixture.get("fixture", {}).get("status", {}).get("short", "")
            if status in ["FT", "AET", "PEN"]:
                # Send final update
                yield f"data: {json.dumps({'type': 'match_finished', 'fixture_id': fixture_id})}\n\n"
                break
            
            # Wait before next update
            await asyncio.sleep(10)
            
        except Exception as e:
            error_data = {
                "type": "error",
                "message": str(e),
                "fixture_id": fixture_id
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            await asyncio.sleep(10)


async def generate_all_live_matches() -> AsyncGenerator[str, None]:
    """
    Generator for all live matches SSE
    Updates every 30 seconds
    """
    while True:
        try:
            # Fetch all live matches
            fixtures = await api_football_service.get_live_matches()
            
            # Prepare update data
            update = {
                "type": "live_matches_update",
                "count": len(fixtures),
                "fixtures": [
                    {
                        "id": f["fixture"]["id"],
                        "status": f["fixture"]["status"],
                        "home": f["teams"]["home"]["name"],
                        "away": f["teams"]["away"]["name"],
                        "score": f["score"]
                    }
                    for f in fixtures
                ],
                "timestamp": asyncio.get_event_loop().time()
            }
            
            yield f"data: {json.dumps(update)}\n\n"
            
            await asyncio.sleep(30)
            
        except Exception as e:
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            await asyncio.sleep(30)


@router.get("/realtime/fixtures/{fixture_id}/live")
async def stream_fixture_updates(fixture_id: int):
    """
    SSE endpoint for live match updates
    Subscribe to this endpoint to receive real-time updates for a specific match
    
    Example client code (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/v1/realtime/fixtures/12345/live');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Update:', data);
    };
    ```
    """
    return StreamingResponse(
        generate_live_updates(fixture_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/realtime/matches/live")
async def stream_all_live_matches():
    """
    SSE endpoint for all live matches
    Subscribe to this endpoint to receive updates for all ongoing matches
    """
    return StreamingResponse(
        generate_all_live_matches(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/realtime/fixtures/{fixture_id}/attack-momentum")
async def stream_attack_momentum(fixture_id: int):
    """
    SSE endpoint for live attack momentum updates
    """
    async def generate_momentum():
        while True:
            try:
                # Calculate current momentum (simplified)
                events = await api_football_service.get_fixture_events(fixture_id)
                
                # Send momentum data
                update = {
                    "type": "momentum_update",
                    "fixture_id": fixture_id,
                    "momentum": 0.5,  # Simplified - would use actual calculation
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                yield f"data: {json.dumps(update)}\n\n"
                
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        generate_momentum(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

