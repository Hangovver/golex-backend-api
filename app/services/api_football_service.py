"""
API-Football Service
Integration with API-Football (https://www.api-football.com/)
Handles all external API calls for real football data
"""
import httpx
from typing import List, Dict, Optional
from app.core.config import settings


class APIFootballService:
    """Service for API-Football integration"""
    
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.api_key = settings.API_FOOTBALL_KEY
        self.headers = {
            "x-apisports-key": self.api_key
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make HTTP request to API-Football"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                headers=self.headers,
                params=params,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    
    # ============================================
    # FIXTURES
    # ============================================
    
    async def get_live_fixtures(self) -> List[Dict]:
        """Get all live fixtures"""
        try:
            data = await self._make_request("fixtures", {"live": "all"})
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching live fixtures: {e}")
            return []
    
    async def get_fixtures_by_date(self, date: str) -> List[Dict]:
        """Get fixtures for a specific date (YYYY-MM-DD)"""
        try:
            data = await self._make_request("fixtures", {"date": date})
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching fixtures for {date}: {e}")
            return []
    
    async def get_fixture_details(self, fixture_id: int) -> Optional[Dict]:
        """Get detailed fixture information"""
        try:
            data = await self._make_request("fixtures", {"id": fixture_id})
            results = data.get("response", [])
            return results[0] if results else None
        except Exception as e:
            print(f"Error fetching fixture {fixture_id}: {e}")
            return None
    
    async def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        """Get match events (goals, cards, subs)"""
        try:
            data = await self._make_request("fixtures/events", {"fixture": fixture_id})
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching events for fixture {fixture_id}: {e}")
            return []
    
    async def get_fixture_statistics(self, fixture_id: int) -> List[Dict]:
        """Get match statistics"""
        try:
            data = await self._make_request("fixtures/statistics", {"fixture": fixture_id})
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching statistics for fixture {fixture_id}: {e}")
            return []
    
    async def get_fixture_lineups(self, fixture_id: int) -> List[Dict]:
        """Get match lineups"""
        try:
            data = await self._make_request("fixtures/lineups", {"fixture": fixture_id})
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching lineups for fixture {fixture_id}: {e}")
            return []
    
    async def get_fixture_players(self, fixture_id: int) -> List[Dict]:
        """Get player statistics for a match"""
        try:
            data = await self._make_request("fixtures/players", {"fixture": fixture_id})
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching player stats for fixture {fixture_id}: {e}")
            return []
    
    # ============================================
    # LEAGUES & STANDINGS
    # ============================================
    
    async def get_leagues(self) -> List[Dict]:
        """Get all leagues"""
        try:
            data = await self._make_request("leagues")
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching leagues: {e}")
            return []
    
    async def get_standings(self, league_id: int, season: int) -> List[Dict]:
        """Get league standings"""
        try:
            data = await self._make_request("standings", {
                "league": league_id,
                "season": season
            })
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return []
    
    # ============================================
    # TEAMS
    # ============================================
    
    async def get_team(self, team_id: int) -> Optional[Dict]:
        """Get team information"""
        try:
            data = await self._make_request("teams", {"id": team_id})
            results = data.get("response", [])
            return results[0] if results else None
        except Exception as e:
            print(f"Error fetching team {team_id}: {e}")
            return None
    
    async def search_teams(self, query: str) -> List[Dict]:
        """Search for teams"""
        try:
            data = await self._make_request("teams", {"search": query})
            return data.get("response", [])
        except Exception as e:
            print(f"Error searching teams: {e}")
            return []
    
    async def get_team_statistics(self, team_id: int, season: int, league_id: int) -> Optional[Dict]:
        """Get team season statistics"""
        try:
            data = await self._make_request("teams/statistics", {
                "team": team_id,
                "season": season,
                "league": league_id
            })
            results = data.get("response", {})
            return results
        except Exception as e:
            print(f"Error fetching team statistics: {e}")
            return None
    
    # ============================================
    # PLAYERS
    # ============================================
    
    async def get_player(self, player_id: int, season: int) -> Optional[Dict]:
        """Get player information"""
        try:
            data = await self._make_request("players", {
                "id": player_id,
                "season": season
            })
            results = data.get("response", [])
            return results[0] if results else None
        except Exception as e:
            print(f"Error fetching player {player_id}: {e}")
            return None
    
    async def search_players(self, query: str, season: int = 2024, league_id: Optional[int] = None) -> List[Dict]:
        """Search for players"""
        try:
            params = {"search": query, "season": season}
            if league_id:
                params["league"] = league_id
            
            data = await self._make_request("players", params)
            return data.get("response", [])
        except Exception as e:
            print(f"Error searching players: {e}")
            return []
    
    async def get_player_statistics(self, player_id: int, season: int) -> List[Dict]:
        """Get player season statistics"""
        try:
            data = await self._make_request("players", {
                "id": player_id,
                "season": season
            })
            results = data.get("response", [])
            if results:
                return results[0].get("statistics", [])
            return []
        except Exception as e:
            print(f"Error fetching player statistics: {e}")
            return []
    
    # ============================================
    # HEAD TO HEAD
    # ============================================
    
    async def get_h2h(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict]:
        """Get head-to-head matches between two teams"""
        try:
            data = await self._make_request("fixtures/headtohead", {
                "h2h": f"{team1_id}-{team2_id}",
                "last": last
            })
            return data.get("response", [])
        except Exception as e:
            print(f"Error fetching H2H: {e}")
            return []


# Singleton instance
api_football_service = APIFootballService()
