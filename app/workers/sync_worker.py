"""
GOLEX Backend - Sync Worker
API-Football → Supabase Database + R2 Storage
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.config import settings
from app.db.supabase_client import supabase_client
from app.storage.r2_client import r2_client
from app.services.auto_market_analyzer import auto_analyzer
from app.services.weather_service import weather_service
from app.services.news_rss_service import news_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncWorker:
    """Sync data from API-Football to Supabase + R2"""
    
    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.api_base = settings.API_FOOTBALL_BASE_URL
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
    
    async def sync_fixtures(
        self,
        date_from: str,
        date_to: str,
        leagues: List[str] = None
    ) -> int:
        """
        Sync fixtures from API-Football
        
        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            leagues: List of league IDs (e.g., ["39", "140"])
        
        Returns:
            Number of fixtures synced
        """
        logger.info(f"📥 Syncing fixtures: {date_from} to {date_to}")
        
        if not leagues:
            # Default: Premier League, La Liga, Bundesliga, Serie A, Ligue 1
            leagues = ["39", "140", "78", "135", "61"]
        
        total_synced = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for league_id in leagues:
                try:
                    # Fetch fixtures from API-Football
                    response = await client.get(
                        f"{self.api_base}/fixtures",
                        headers=self.headers,
                        params={
                            "league": league_id,
                            "from": date_from,
                            "to": date_to,
                            "season": "2024"
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    fixtures = data.get("response", [])
                    logger.info(f"  📋 League {league_id}: {len(fixtures)} fixtures")
                    
                    # Save to Supabase
                    for fixture in fixtures:
                        await self._save_fixture(fixture)
                        total_synced += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error syncing league {league_id}: {e}")
                    continue
        
        logger.info(f"✅ Synced {total_synced} fixtures")
        return total_synced
    
    async def _save_fixture(self, fixture_data: Dict[str, Any]):
        """Save fixture to database"""
        fixture = fixture_data.get("fixture", {})
        league = fixture_data.get("league", {})
        teams = fixture_data.get("teams", {})
        goals = fixture_data.get("goals", {})
        
        fixture_obj = {
            "id": str(fixture.get("id")),
            "league_id": str(league.get("id")),
            "home_team_id": str(teams.get("home", {}).get("id")),
            "away_team_id": str(teams.get("away", {}).get("id")),
            "match_date": fixture.get("date"),
            "status": fixture.get("status", {}).get("short", "NS"),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "venue": fixture.get("venue", {}).get("name"),
            "referee_id": fixture.get("referee")
        }
        
        await supabase_client.upsert_fixture(fixture_obj)
        
        # Also save teams if not exists
        await self._save_team(teams.get("home"))
        await self._save_team(teams.get("away"))
    
    async def _save_team(self, team_data: Dict[str, Any]):
        """Save team to database"""
        if not team_data:
            return
        
        team_obj = {
            "id": str(team_data.get("id")),
            "name": team_data.get("name"),
            "logo_url": team_data.get("logo"),  # Original API URL (will upload to R2 later)
            "country": team_data.get("country"),
            "league_id": None,  # Will be set later
            "founded": None,
            "venue": None
        }
        
        await supabase_client.upsert_team(team_obj)
    
    async def sync_team_logos(self, limit: int = 50) -> int:
        """
        Upload team logos to R2
        
        Args:
            limit: Maximum number of logos to process per run
        
        Returns:
            Number of logos uploaded
        """
        logger.info(f"🖼️ Syncing team logos (limit: {limit})")
        
        # Get teams without R2 logo
        query = """
            SELECT id, name, logo_url 
            FROM teams 
            WHERE logo_url LIKE 'https://media.api-sports.io%'
            LIMIT $1
        """
        teams = await supabase_client.fetch_all(query, limit)
        
        uploaded = 0
        for team in teams:
            try:
                team_id = team['id']
                api_logo_url = team['logo_url']
                
                # Upload to R2
                r2_url = await r2_client.upload_team_logo(team_id, api_logo_url)
                
                # Update database with R2 URL
                update_query = "UPDATE teams SET logo_url = $1 WHERE id = $2"
                await supabase_client.execute(update_query, r2_url, team_id)
                
                uploaded += 1
                logger.info(f"  ✅ {team['name']}: {r2_url}")
                
            except Exception as e:
                logger.error(f"  ❌ {team['name']}: {e}")
                continue
        
        logger.info(f"✅ Uploaded {uploaded} team logos to R2")
        return uploaded
    
    async def sync_fixture_stats(self, fixture_ids: List[str]) -> int:
        """Sync fixture statistics"""
        logger.info(f"📊 Syncing stats for {len(fixture_ids)} fixtures")
        
        synced = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for fixture_id in fixture_ids:
                try:
                    response = await client.get(
                        f"{self.api_base}/fixtures/statistics",
                        headers=self.headers,
                        params={"fixture": fixture_id}
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Parse statistics
                    stats = self._parse_fixture_stats(data.get("response", []))
                    
                    # Save to database
                    await supabase_client.upsert_fixture_stats(fixture_id, stats)
                    synced += 1
                    
                except Exception as e:
                    logger.error(f"❌ Error syncing stats for {fixture_id}: {e}")
                    continue
        
        logger.info(f"✅ Synced {synced} fixture stats")
        return synced
    
    def _parse_fixture_stats(self, stats_data: List[Dict]) -> Dict[str, Any]:
        """Parse fixture statistics from API response"""
        home_stats = stats_data[0].get("statistics", []) if len(stats_data) > 0 else []
        away_stats = stats_data[1].get("statistics", []) if len(stats_data) > 1 else []
        
        def get_stat(stats_list, stat_type):
            for stat in stats_list:
                if stat.get("type") == stat_type:
                    value = stat.get("value")
                    # Convert percentage strings to int
                    if isinstance(value, str) and '%' in value:
                        return int(value.replace('%', ''))
                    return value
            return None
        
        return {
            "home_xg": None,  # Not available in free API
            "away_xg": None,
            "home_possession": get_stat(home_stats, "Ball Possession"),
            "away_possession": get_stat(away_stats, "Ball Possession"),
            "home_shots": get_stat(home_stats, "Total Shots"),
            "away_shots": get_stat(away_stats, "Total Shots"),
            "home_shots_on_target": get_stat(home_stats, "Shots on Goal"),
            "away_shots_on_target": get_stat(away_stats, "Shots on Goal"),
            "home_corners": get_stat(home_stats, "Corner Kicks"),
            "away_corners": get_stat(away_stats, "Corner Kicks"),
            "home_fouls": get_stat(home_stats, "Fouls"),
            "away_fouls": get_stat(away_stats, "Fouls")
        }


# ==========================================
# SCHEDULED TASKS
# ==========================================

async def daily_fixture_sync():
    """Run daily fixture sync (cron job)"""
    worker = SyncWorker()
    
    # Connect to database
    await supabase_client.connect()
    
    try:
        # Sync next 7 days
        today = datetime.now().date()
        date_from = today.strftime("%Y-%m-%d")
        date_to = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        await worker.sync_fixtures(date_from, date_to)
        
        # Upload team logos (50 per day)
        await worker.sync_team_logos(limit=50)
        
    finally:
        await supabase_client.disconnect()


async def live_score_sync():
    """Run live score sync (every 30 seconds during matches)"""
    worker = SyncWorker()
    
    await supabase_client.connect()
    
    try:
        # Get today's live fixtures
        today = datetime.now().date().strftime("%Y-%m-%d")
        await worker.sync_fixtures(today, today)
        
    finally:
        await supabase_client.disconnect()


async def auto_market_analysis():
    """
    Automatic market analysis for all upcoming fixtures (background worker)
    - Analyzes all 466 markets
    - Filters predictions with confidence >= 60%
    - Runs every 1 hour
    """
    await supabase_client.connect()
    
    try:
        logger.info("🤖 Starting automatic market analysis...")
        
        # Get upcoming fixtures (next 24 hours)
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Query fixtures from database
        result = await supabase_client.client.table("fixtures").select(
            "id, home_team_id, away_team_id, match_date, league_id, stadium_coords"
        ).gte("match_date", today.strftime("%Y-%m-%d")).lte(
            "match_date", tomorrow.strftime("%Y-%m-%d")
        ).eq("status", "NS").execute()  # Not Started
        
        fixtures = result.data if result else []
        logger.info(f"  📊 Found {len(fixtures)} upcoming fixtures")
        
        if not fixtures:
            logger.info("  ✅ No fixtures to analyze")
            return
        
        # Get team stats for each fixture
        analyzed_count = 0
        for fixture in fixtures:
            try:
                fixture_id = fixture["id"]
                home_team_id = fixture["home_team_id"]
                away_team_id = fixture["away_team_id"]
                
                # Get team names
                home_team_result = await supabase_client.client.table("teams").select(
                    "name"
                ).eq("id", home_team_id).single().execute()
                away_team_result = await supabase_client.client.table("teams").select(
                    "name"
                ).eq("id", away_team_id).single().execute()
                
                if not home_team_result.data or not away_team_result.data:
                    continue
                
                home_team_name = home_team_result.data["name"]
                away_team_name = away_team_result.data["name"]
                
                # Get team stats (last 10 games)
                home_stats = await _get_team_recent_stats(home_team_id)
                away_stats = await _get_team_recent_stats(away_team_id)
                
                # Parse stadium coordinates (if available)
                stadium_coords = None
                if fixture.get("stadium_coords"):
                    try:
                        coords_str = fixture["stadium_coords"]
                        if isinstance(coords_str, str) and "," in coords_str:
                            lat, lon = coords_str.split(",")
                            stadium_coords = (float(lat.strip()), float(lon.strip()))
                    except:
                        pass
                
                # Run automatic analysis
                analysis = await auto_analyzer.analyze_match(
                    fixture_id=fixture_id,
                    home_team=home_team_name,
                    away_team=away_team_name,
                    home_stats=home_stats,
                    away_stats=away_stats,
                    stadium_coords=stadium_coords,
                    match_date=fixture["match_date"]
                )
                
                # Save high-confidence predictions to database
                high_conf_count = analysis["high_confidence_markets"]
                if high_conf_count > 0:
                    await _save_predictions(fixture_id, analysis)
                    logger.info(f"  ✅ {fixture_id}: {high_conf_count} high-confidence predictions saved")
                    analyzed_count += 1
                else:
                    logger.info(f"  ⚠️ {fixture_id}: No high-confidence predictions (threshold: 60%)")
                
            except Exception as e:
                logger.error(f"  ❌ Error analyzing fixture {fixture.get('id')}: {e}")
                continue
        
        logger.info(f"🎯 Analysis complete: {analyzed_count}/{len(fixtures)} fixtures with predictions")
        
    except Exception as e:
        logger.error(f"❌ Auto market analysis failed: {e}")
    finally:
        await supabase_client.disconnect()


async def _get_team_recent_stats(team_id: str) -> Dict[str, Any]:
    """Get team's recent stats (last 10 games average)"""
    try:
        # Query recent fixtures stats
        result = await supabase_client.client.table("fixture_stats").select(
            "*"
        ).or_(
            f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}"
        ).order("created_at", desc=True).limit(10).execute()
        
        stats = result.data if result else []
        
        if not stats:
            # Return default stats if no data
            return {
                "goals_scored_avg": 1.5,
                "goals_conceded_avg": 1.2,
                "shots_avg": 12.0,
                "shots_on_target_avg": 4.5,
                "possession_avg": 50.0,
                "corners_avg": 5.0,
                "xg_avg": 1.3
            }
        
        # Calculate averages
        total_goals_scored = 0
        total_goals_conceded = 0
        total_shots = 0
        total_shots_on_target = 0
        total_possession = 0
        total_corners = 0
        
        for stat in stats:
            is_home = stat.get("home_team_id") == team_id
            
            if is_home:
                total_goals_scored += stat.get("home_score", 0) or 0
                total_goals_conceded += stat.get("away_score", 0) or 0
                total_shots += stat.get("home_shots", 0) or 0
                total_shots_on_target += stat.get("home_shots_on_target", 0) or 0
                total_possession += stat.get("home_possession", 0) or 0
                total_corners += stat.get("home_corners", 0) or 0
            else:
                total_goals_scored += stat.get("away_score", 0) or 0
                total_goals_conceded += stat.get("home_score", 0) or 0
                total_shots += stat.get("away_shots", 0) or 0
                total_shots_on_target += stat.get("away_shots_on_target", 0) or 0
                total_possession += stat.get("away_possession", 0) or 0
                total_corners += stat.get("away_corners", 0) or 0
        
        count = len(stats)
        return {
            "goals_scored_avg": total_goals_scored / count,
            "goals_conceded_avg": total_goals_conceded / count,
            "shots_avg": total_shots / count,
            "shots_on_target_avg": total_shots_on_target / count,
            "possession_avg": total_possession / count,
            "corners_avg": total_corners / count,
            "xg_avg": total_goals_scored / count * 0.9  # Rough xG estimate
        }
    except Exception as e:
        logger.error(f"Error getting team stats: {e}")
        return {
            "goals_scored_avg": 1.5,
            "goals_conceded_avg": 1.2,
            "shots_avg": 12.0,
            "shots_on_target_avg": 4.5,
            "possession_avg": 50.0,
            "corners_avg": 5.0,
            "xg_avg": 1.3
        }


async def _save_predictions(fixture_id: str, analysis: Dict[str, Any]):
    """Save high-confidence predictions to database"""
    try:
        predictions = analysis.get("predictions", [])
        
        # Prepare bulk insert data
        records = []
        for pred in predictions:
            records.append({
                "fixture_id": fixture_id,
                "market": pred["market"],
                "prediction": pred["prediction"],
                "confidence": pred["confidence"],
                "base_confidence": pred.get("base_confidence"),
                "odds": pred.get("odds"),
                "kelly_stake": pred.get("kelly_stake"),
                "expected_value": pred.get("ev"),
                "weather_impact": pred.get("weather_impact"),
                "news_impact": pred.get("news_impact"),
                "formula": pred.get("formula"),
                "created_at": datetime.now().isoformat()
            })
        
        # Bulk insert (upsert to avoid duplicates)
        if records:
            await supabase_client.client.table("predictions").upsert(
                records,
                on_conflict="fixture_id,market"
            ).execute()
            
    except Exception as e:
        logger.error(f"Error saving predictions: {e}")


# ==========================================
# MANUAL RUN
# ==========================================

async def main():
    """Manual sync (for testing)"""
    worker = SyncWorker()
    
    # Connect
    await supabase_client.connect()
    
    try:
        # Sync today + next 7 days
        today = datetime.now().date()
        date_from = today.strftime("%Y-%m-%d")
        date_to = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        logger.info("=" * 50)
        logger.info("🚀 GOLEX SYNC WORKER - MANUAL RUN")
        logger.info("=" * 50)
        
        # Step 1: Sync fixtures
        await worker.sync_fixtures(date_from, date_to)
        
        # Step 2: Upload logos
        await worker.sync_team_logos(limit=100)
        
        logger.info("=" * 50)
        logger.info("✅ SYNC COMPLETE!")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        raise
    finally:
        await supabase_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

