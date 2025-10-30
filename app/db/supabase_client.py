"""
GOLEX Backend - Supabase Database Client
PostgreSQL connection via Supabase
"""

import asyncpg
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase database client wrapper"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY  # Use service role for backend
        )
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self):
        """Create async connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("✅ Supabase connection pool created")
        except Exception as e:
            logger.error(f"❌ Supabase connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("🔌 Supabase connection pool closed")
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one row"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
    
    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and fetch all rows"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
    
    async def execute(self, query: str, *args) -> str:
        """Execute query without returning results"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def execute_many(self, query: str, args_list: List[tuple]) -> None:
        """Execute query multiple times with different parameters"""
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args_list)
    
    # ==========================================
    # FIXTURES (Maçlar)
    # ==========================================
    
    async def get_fixtures(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        league_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get fixtures with filters"""
        query = """
            SELECT * FROM fixtures
            WHERE 1=1
        """
        params = []
        param_count = 1
        
        if date_from:
            query += f" AND match_date >= ${param_count}"
            params.append(date_from)
            param_count += 1
        
        if date_to:
            query += f" AND match_date <= ${param_count}"
            params.append(date_to)
            param_count += 1
        
        if league_id:
            query += f" AND league_id = ${param_count}"
            params.append(league_id)
            param_count += 1
        
        if status:
            query += f" AND status = ${param_count}"
            params.append(status)
            param_count += 1
        
        query += f" ORDER BY match_date ASC LIMIT ${param_count}"
        params.append(limit)
        
        return await self.fetch_all(query, *params)
    
    async def upsert_fixture(self, fixture_data: Dict[str, Any]) -> None:
        """Insert or update fixture"""
        query = """
            INSERT INTO fixtures (
                id, league_id, home_team_id, away_team_id,
                match_date, status, home_score, away_score,
                venue, referee_id, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                updated_at = NOW()
        """
        await self.execute(
            query,
            fixture_data.get('id'),
            fixture_data.get('league_id'),
            fixture_data.get('home_team_id'),
            fixture_data.get('away_team_id'),
            fixture_data.get('match_date'),
            fixture_data.get('status'),
            fixture_data.get('home_score'),
            fixture_data.get('away_score'),
            fixture_data.get('venue'),
            fixture_data.get('referee_id')
        )
    
    # ==========================================
    # TEAMS (Takımlar)
    # ==========================================
    
    async def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team by ID"""
        query = "SELECT * FROM teams WHERE id = $1"
        return await self.fetch_one(query, team_id)
    
    async def upsert_team(self, team_data: Dict[str, Any]) -> None:
        """Insert or update team"""
        query = """
            INSERT INTO teams (
                id, name, logo_url, country, league_id,
                founded, venue, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                logo_url = EXCLUDED.logo_url,
                venue = EXCLUDED.venue
        """
        await self.execute(
            query,
            team_data.get('id'),
            team_data.get('name'),
            team_data.get('logo_url'),
            team_data.get('country'),
            team_data.get('league_id'),
            team_data.get('founded'),
            team_data.get('venue')
        )
    
    # ==========================================
    # STATS (İstatistikler)
    # ==========================================
    
    async def upsert_fixture_stats(self, fixture_id: str, stats: Dict[str, Any]) -> None:
        """Insert or update fixture statistics"""
        query = """
            INSERT INTO fixture_stats (
                fixture_id, home_xg, away_xg, home_possession, away_possession,
                home_shots, away_shots, home_shots_on_target, away_shots_on_target,
                home_corners, away_corners, home_fouls, away_fouls,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW())
            ON CONFLICT (fixture_id) DO UPDATE SET
                home_xg = EXCLUDED.home_xg,
                away_xg = EXCLUDED.away_xg,
                home_possession = EXCLUDED.home_possession,
                away_possession = EXCLUDED.away_possession,
                home_shots = EXCLUDED.home_shots,
                away_shots = EXCLUDED.away_shots,
                updated_at = NOW()
        """
        await self.execute(
            query,
            fixture_id,
            stats.get('home_xg'),
            stats.get('away_xg'),
            stats.get('home_possession'),
            stats.get('away_possession'),
            stats.get('home_shots'),
            stats.get('away_shots'),
            stats.get('home_shots_on_target'),
            stats.get('away_shots_on_target'),
            stats.get('home_corners'),
            stats.get('away_corners'),
            stats.get('home_fouls'),
            stats.get('away_fouls')
        )


# Global Supabase client instance
supabase_client = SupabaseClient()


# Convenience functions
async def get_db():
    """Dependency for FastAPI routes"""
    return supabase_client

