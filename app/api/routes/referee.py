"""
Referee Stats API Routes
=========================
Hakem istatistikleri ve tahminlere etkisi için API endpoints.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.services.referee_stats_collector import (
    RefereeStatsCollector,
    format_referee_report
)
from app.db import get_db_connection


router = APIRouter(prefix="/referee", tags=["referee"])


@router.get("/{referee_id}")
async def get_referee_stats(
    referee_id: str,
    last_n_matches: int = Query(20, ge=1, le=100, description="Son N maç"),
    league_id: Optional[str] = Query(None, description="Belirli bir lig")
):
    """
    Hakem istatistiklerini getir
    
    Args:
        referee_id: Hakem ID
        last_n_matches: Son N maç (varsayılan: 20)
        league_id: Belirli bir lig (opsiyonel)
    
    Returns:
        {
            "referee": {
                "id": str,
                "name": str,
                "total_matches": int,
                "stats": {
                    "avg_cards": float,
                    "avg_yellow": float,
                    "avg_red": float,
                    "red_card_pct": float,
                    "avg_penalties": float,
                    "avg_goals": float,
                    "home_bias": float,
                    "strict_rating": float
                }
            },
            "league_comparison": {
                "cards": {"referee": float, "league": float, "diff_pct": float},
                "red_cards": {...},
                "penalties": {...}
            }
        }
    """
    try:
        db = await get_db_connection()
        collector = RefereeStatsCollector(db)
        
        # Hakem istatistiklerini getir
        referee_stats = await collector.get_referee_stats(
            referee_id,
            last_n_matches,
            league_id
        )
        
        if not referee_stats:
            raise HTTPException(
                status_code=404,
                detail=f"Referee {referee_id} not found"
            )
        
        # Lig ortalamalarını getir
        league_id_for_avg = league_id or "default_league"
        league_averages = await collector.get_league_averages(league_id_for_avg)
        
        # Rapor formatla
        report = format_referee_report(
            referee_stats,
            league_averages,
            []  # Impacts boş (sadece stats)
        )
        
        return report
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting referee stats: {str(e)}"
        )


@router.get("/{referee_id}/impact")
async def get_referee_impact_on_match(
    referee_id: str,
    fixture_id: str,
    include_base_predictions: bool = Query(True, description="Temel tahminleri dahil et")
):
    """
    Hakemin maça etkisini hesapla
    
    Args:
        referee_id: Hakem ID
        fixture_id: Maç ID
        include_base_predictions: Temel tahminleri de döndür
    
    Returns:
        {
            "referee": {...},
            "league_comparison": {...},
            "market_impacts": [
                {
                    "market": "CARDS_O4.5",
                    "original_prob": 0.48,
                    "adjusted_prob": 0.72,
                    "change_pct": 50.0,
                    "is_significant": true
                }
            ],
            "base_predictions": {...}  # Eğer include_base_predictions=true
        }
    """
    try:
        db = await get_db_connection()
        collector = RefereeStatsCollector(db)
        
        # Hakem istatistiklerini getir
        referee_stats = await collector.get_referee_stats(referee_id)
        
        if not referee_stats:
            raise HTTPException(
                status_code=404,
                detail=f"Referee {referee_id} not found"
            )
        
        # Maç için temel tahminleri getir
        from app.services.markets_466 import predict_466_markets
        
        # xG verilerini çek
        query_xg = """
        SELECT home_xg_for, home_xg_against, away_xg_for, away_xg_against
        FROM fixture_stats
        WHERE fixture_id = $1
        """
        xg_data = await db.fetchrow(query_xg, fixture_id)
        
        if not xg_data:
            raise HTTPException(
                status_code=404,
                detail=f"Fixture {fixture_id} xG data not found"
            )
        
        # Maç bilgilerini getir
        query_fixture = """
        SELECT league_id FROM fixtures WHERE fixture_id = $1
        """
        fixture = await db.fetchrow(query_fixture, fixture_id)
        league_id = fixture['league_id'] if fixture else "default"
        
        # Temel tahminleri hesapla
        base_prediction = predict_466_markets(
            home_xg_for=float(xg_data['home_xg_for']),
            away_xg_for=float(xg_data['away_xg_for']),
            home_xg_against=float(xg_data['home_xg_against']),
            away_xg_against=float(xg_data['away_xg_against']),
            markets=['CARDS_O4.5', 'YELLOW_O3.5', 'RED_CARD_YES', 'PENALTY_YES'],
            include_kelly=False
        )
        
        # Temel olasılıkları çıkar
        base_probabilities = {
            market['market']: market['probability']
            for market in base_prediction['markets']
        }
        
        # Lig ortalamalarını getir
        league_averages = await collector.get_league_averages(league_id)
        
        # Hakem etkisini hesapla
        impacts = collector.calculate_referee_impact(
            referee_stats,
            league_averages,
            base_probabilities
        )
        
        # Rapor formatla
        report = format_referee_report(
            referee_stats,
            league_averages,
            impacts
        )
        
        # Temel tahminleri ekle (istenirse)
        if include_base_predictions:
            report['base_predictions'] = base_prediction
        
        return report
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating referee impact: {str(e)}"
        )


@router.get("/match/{fixture_id}")
async def get_referee_for_match(fixture_id: str):
    """
    Maç için hakem bilgisini getir
    
    Args:
        fixture_id: Maç ID
    
    Returns:
        {
            "fixture_id": str,
            "referee": {
                "referee_id": str,
                "referee_name": str,
                "stats": {...}
            } | null
        }
    """
    try:
        db = await get_db_connection()
        collector = RefereeStatsCollector(db)
        
        # Hakem bilgisini getir
        referee_info = await collector.get_referee_for_match(fixture_id)
        
        if not referee_info:
            return {
                "fixture_id": fixture_id,
                "referee": None
            }
        
        # Hakem istatistiklerini getir
        referee_stats = await collector.get_referee_stats(referee_info['referee_id'])
        
        return {
            "fixture_id": fixture_id,
            "referee": {
                "referee_id": referee_info['referee_id'],
                "referee_name": referee_info['referee_name'],
                "stats": referee_stats.__dict__ if referee_stats else None
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting referee for match: {str(e)}"
        )


@router.post("/{referee_id}/collect")
async def collect_referee_data(
    referee_id: str,
    referee_name: str,
    match_data: dict
):
    """
    Maç sonrası hakem verilerini kaydet
    
    Args:
        referee_id: Hakem ID
        referee_name: Hakem adı
        match_data: {
            "fixture_id": str,
            "match_date": str (ISO format),
            "league_id": str,
            "yellow_cards": int,
            "red_cards": int,
            "penalties": int,
            "total_goals": int,
            "home_won": bool
        }
    
    Returns:
        {"success": true, "message": "Referee data collected"}
    """
    try:
        db = await get_db_connection()
        collector = RefereeStatsCollector(db)
        
        # Veri doğrulama
        required_fields = [
            'fixture_id', 'match_date', 'league_id',
            'yellow_cards', 'red_cards', 'penalties',
            'total_goals', 'home_won'
        ]
        
        for field in required_fields:
            if field not in match_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Tarihi parse et
        match_data['match_date'] = datetime.fromisoformat(
            match_data['match_date'].replace('Z', '+00:00')
        )
        
        # Veriyi kaydet
        await collector.collect_referee_data(
            referee_id,
            referee_name,
            match_data
        )
        
        return {
            "success": True,
            "message": f"Referee data collected for {referee_name}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error collecting referee data: {str(e)}"
        )

