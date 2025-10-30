"""
News & Injury API Routes
=========================
Sakatlık ve haber bilgileri için API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime

from app.services.news_injury_scraper import (
    NewsInjuryScraper,
    format_injury_report,
    InjuryStatus
)
from app.db import get_db_connection


router = APIRouter(prefix="/news", tags=["news"])


@router.get("/injuries/{league_id}")
async def get_league_injuries(
    league_id: str,
    status: Optional[str] = Query(None, description="Duruma göre filtrele (injured, doubtful, suspended)"),
    team_id: Optional[str] = Query(None, description="Takıma göre filtrele")
):
    """
    Lig sakatlıklarını getir
    
    Args:
        league_id: Lig ID
        status: Durum filtresi (opsiyonel)
        team_id: Takım filtresi (opsiyonel)
    
    Returns:
        {
            "league_id": str,
            "total_injuries": int,
            "injuries": [
                {
                    "player_id": str,
                    "player_name": str,
                    "team_name": str,
                    "status": str,
                    "injury_type": str,
                    "expected_return": str | null,
                    "confidence": float
                }
            ]
        }
    """
    try:
        db = await get_db_connection()
        scraper = NewsInjuryScraper(db)
        
        # Sakatlıkları çek
        injuries = await scraper.scrape_transfermarkt_injuries(league_id)
        
        # Filtrele
        if status:
            try:
                status_enum = InjuryStatus(status)
                injuries = [inj for inj in injuries if inj.status == status_enum]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status: {status}. Valid: injured, doubtful, suspended, healthy"
                )
        
        if team_id:
            injuries = [inj for inj in injuries if inj.team_id == team_id]
        
        # Format
        return {
            "league_id": league_id,
            "total_injuries": len(injuries),
            "injuries": [
                {
                    "player_id": inj.player_id,
                    "player_name": inj.player_name,
                    "team_name": inj.team_name,
                    "status": inj.status.value,
                    "injury_type": inj.injury_type,
                    "severity": inj.severity.value if inj.severity else None,
                    "expected_return": inj.expected_return.isoformat() if inj.expected_return else None,
                    "confidence": inj.confidence
                }
                for inj in injuries
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting injuries: {str(e)}"
        )


@router.get("/injuries/player/{player_id}")
async def get_player_injury(player_id: str):
    """
    Oyuncu sakatlık bilgisini getir
    
    Args:
        player_id: Oyuncu ID
    
    Returns:
        {
            "player_id": str,
            "player_name": str,
            "current_injury": {...} | null
        }
    """
    try:
        db = await get_db_connection()
        
        query = """
        SELECT * FROM player_injuries
        WHERE player_id = $1
        """
        
        row = await db.fetchrow(query, player_id)
        
        if not row:
            return {
                "player_id": player_id,
                "player_name": None,
                "current_injury": None
            }
        
        return {
            "player_id": row['player_id'],
            "player_name": row['player_name'],
            "current_injury": {
                "status": row['status'],
                "injury_type": row['injury_type'],
                "severity": row['severity'],
                "expected_return": row['expected_return'].isoformat() if row['expected_return'] else None,
                "source": row['source'],
                "confidence": float(row['confidence']),
                "updated_at": row['updated_at'].isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting player injury: {str(e)}"
        )


@router.get("/match/{fixture_id}/lineup-changes")
async def get_match_lineup_changes(fixture_id: str):
    """
    Maç için kadro değişikliklerini ve xG etkisini getir
    
    Args:
        fixture_id: Maç ID
    
    Returns:
        {
            "fixture_id": str,
            "lineup_changes": [
                {
                    "team_id": str,
                    "player_out": str,
                    "player_in": str | null,
                    "xg_impact": float,
                    "market_impacts": {...}
                }
            ],
            "total_xg_impact": {
                "home": float,
                "away": float
            }
        }
    """
    try:
        db = await get_db_connection()
        scraper = NewsInjuryScraper(db)
        
        # Kadro değişikliklerini getir
        changes = await scraper.get_lineup_changes_for_match(fixture_id)
        
        if not changes:
            return {
                "fixture_id": fixture_id,
                "lineup_changes": [],
                "total_xg_impact": {"home": 0.0, "away": 0.0}
            }
        
        # Maç bilgilerini getir (home/away ayırmak için)
        query = """
        SELECT home_team_id, away_team_id FROM fixtures WHERE fixture_id = $1
        """
        fixture = await db.fetchrow(query, fixture_id)
        
        if not fixture:
            raise HTTPException(status_code=404, detail="Fixture not found")
        
        # xG etkilerini hesapla
        home_xg_impact = sum(
            change.xg_impact
            for change in changes
            if change.team_id == fixture['home_team_id']
        )
        
        away_xg_impact = sum(
            change.xg_impact
            for change in changes
            if change.team_id == fixture['away_team_id']
        )
        
        return {
            "fixture_id": fixture_id,
            "lineup_changes": [
                {
                    "team_id": change.team_id,
                    "player_out": change.player_out_name,
                    "player_in": change.player_in_name,
                    "xg_impact": change.xg_impact,
                    "market_impacts": change.market_impacts
                }
                for change in changes
            ],
            "total_xg_impact": {
                "home": round(home_xg_impact, 2),
                "away": round(away_xg_impact, 2)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting lineup changes: {str(e)}"
        )


@router.get("/match/{fixture_id}")
async def get_match_news(
    fixture_id: str,
    hours_back: int = Query(24, ge=1, le=168, description="Kaç saat geriye git")
):
    """
    Maç için haberleri getir
    
    Args:
        fixture_id: Maç ID
        hours_back: Kaç saat geriye git (varsayılan: 24)
    
    Returns:
        {
            "fixture_id": str,
            "total_news": int,
            "news": [
                {
                    "news_id": str,
                    "title": str,
                    "content": str,
                    "source": str,
                    "published_at": str,
                    "importance": float
                }
            ]
        }
    """
    try:
        db = await get_db_connection()
        
        query = """
        SELECT * FROM news_items
        WHERE fixture_id = $1
        AND published_at >= NOW() - INTERVAL '1 hour' * $2
        ORDER BY importance DESC, published_at DESC
        """
        
        rows = await db.fetch(query, fixture_id, hours_back)
        
        return {
            "fixture_id": fixture_id,
            "total_news": len(rows),
            "news": [
                {
                    "news_id": row['news_id'],
                    "title": row['title'],
                    "content": row['content'],
                    "source": row['source'],
                    "published_at": row['published_at'].isoformat(),
                    "keywords": row['keywords'],
                    "importance": float(row['importance'])
                }
                for row in rows
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting match news: {str(e)}"
        )


@router.get("/team/{team_id}")
async def get_team_news(
    team_id: str,
    hours_back: int = Query(24, ge=1, le=168, description="Kaç saat geriye git")
):
    """
    Takım haberlerini getir
    
    Args:
        team_id: Takım ID
        hours_back: Kaç saat geriye git (varsayılan: 24)
    
    Returns:
        {
            "team_id": str,
            "total_news": int,
            "news": [...]
        }
    """
    try:
        db = await get_db_connection()
        scraper = NewsInjuryScraper(db)
        
        # Takım adını getir
        query_team = "SELECT name FROM teams WHERE team_id = $1"
        team = await db.fetchrow(query_team, team_id)
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Twitter haberlerini çek
        news_items = await scraper.scrape_twitter_news(team['name'], hours_back)
        
        return {
            "team_id": team_id,
            "total_news": len(news_items),
            "news": [
                {
                    "news_id": news.news_id,
                    "title": news.title,
                    "content": news.content,
                    "source": news.source,
                    "published_at": news.published_at.isoformat(),
                    "importance": news.importance
                }
                for news in news_items
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting team news: {str(e)}"
        )


@router.post("/injuries/store")
async def store_injury(injury_data: dict):
    """
    Sakatlık bilgisini kaydet
    
    Args:
        injury_data: {
            "player_id": str,
            "player_name": str,
            "team_id": str,
            "team_name": str,
            "league_id": str,
            "status": str,  # healthy, doubtful, injured, suspended
            "injury_type": str | null,
            "severity": str | null,  # minor, moderate, major, season_ending
            "expected_return": str | null,  # ISO format
            "source": str,
            "confidence": float
        }
    
    Returns:
        {"success": true, "message": "Injury stored"}
    """
    try:
        db = await get_db_connection()
        
        # Veri doğrulama
        required_fields = [
            'player_id', 'player_name', 'team_id', 'team_name',
            'league_id', 'status', 'source', 'confidence'
        ]
        
        for field in required_fields:
            if field not in injury_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Status doğrulama
        valid_statuses = ['healthy', 'doubtful', 'injured', 'suspended']
        if injury_data['status'] not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Valid: {', '.join(valid_statuses)}"
            )
        
        # Tarihi parse et (varsa)
        expected_return = None
        if injury_data.get('expected_return'):
            expected_return = datetime.fromisoformat(
                injury_data['expected_return'].replace('Z', '+00:00')
            )
        
        # Kaydet
        query = """
        INSERT INTO player_injuries
        (player_id, player_name, team_id, team_name, league_id,
         status, injury_type, severity, expected_return, source, confidence, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
        ON CONFLICT (player_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            injury_type = EXCLUDED.injury_type,
            severity = EXCLUDED.severity,
            expected_return = EXCLUDED.expected_return,
            source = EXCLUDED.source,
            confidence = EXCLUDED.confidence,
            updated_at = NOW()
        """
        
        await db.execute(
            query,
            injury_data['player_id'],
            injury_data['player_name'],
            injury_data['team_id'],
            injury_data['team_name'],
            injury_data['league_id'],
            injury_data['status'],
            injury_data.get('injury_type'),
            injury_data.get('severity'),
            expected_return,
            injury_data['source'],
            injury_data['confidence']
        )
        
        return {
            "success": True,
            "message": f"Injury stored for {injury_data['player_name']}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error storing injury: {str(e)}"
        )


@router.get("/notifications/{fixture_id}")
async def get_fixture_notifications(fixture_id: str):
    """
    Maç için bildirimleri getir
    
    Args:
        fixture_id: Maç ID
    
    Returns:
        {
            "fixture_id": str,
            "total_notifications": int,
            "notifications": [
                {
                    "type": str,
                    "title": str,
                    "message": str,
                    "created_at": str
                }
            ]
        }
    """
    try:
        db = await get_db_connection()
        
        query = """
        SELECT * FROM notifications
        WHERE fixture_id = $1
        ORDER BY created_at DESC
        """
        
        rows = await db.fetch(query, fixture_id)
        
        return {
            "fixture_id": fixture_id,
            "total_notifications": len(rows),
            "notifications": [
                {
                    "type": row['type'],
                    "title": row['title'],
                    "message": row['message'],
                    "created_at": row['created_at'].isoformat()
                }
                for row in rows
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting notifications: {str(e)}"
        )

