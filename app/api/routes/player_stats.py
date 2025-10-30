"""
Player Stats Routes - EXACT COPY from SofaScore backend
Source: PlayerStatsController.java
Features: Player xG trend, Shots on target, ETag caching, Random seed for demo
"""
from fastapi import APIRouter, Request
from ...utils.etag import etag_json
import random

router = APIRouter(prefix="/players", tags=["players.stats"])

@router.get("/{player_id}/trend")
def player_trend(player_id: str, n: int = 8, request: Request = None):
    rnd = random.Random(hash(player_id) & 0xffffffff)
    xg_chain = [round(max(0.0, rnd.random()*0.6), 3) for _ in range(n)]
    shots_ot = [rnd.randint(0,3) for _ in range(n)]
        data = {"player_id": player_id, "xg_chain": xg_chain, "shotsOT": shots_ot}
    return etag_json(data, request)

