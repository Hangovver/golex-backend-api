"""
GOLEX Backend - Configuration
Environment variables and app settings
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # ==========================================
    # APPLICATION CONFIG
    # ==========================================
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # ==========================================
    # API-FOOTBALL (Existing)
    # ==========================================
    API_FOOTBALL_KEY: Optional[str] = os.getenv("API_FOOTBALL_KEY")
    API_FOOTBALL_BASE_URL: str = os.getenv(
        "API_FOOTBALL_BASE_URL",
        "https://v3.football.api-sports.io"
    )
    
    # ==========================================
    # THE ODDS API (Existing)
    # ==========================================
    ODDS_API_KEY: Optional[str] = os.getenv("ODDS_API_KEY")
    ODDS_API_BASE_URL: str = os.getenv(
        "ODDS_API_BASE_URL",
        "https://api.the-odds-api.com/v4"
    )
    
    # ==========================================
    # OPENWEATHER API (Existing)
    # ==========================================
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    
    # ==========================================
    # SUPABASE DATABASE (NEW!)
    # ==========================================
    SUPABASE_URL: str = os.getenv(
        "SUPABASE_URL",
        "https://jsgilbidgllwzcbdxjbd.supabase.co"
    )
    SUPABASE_ANON_KEY: str = os.getenv(
        "SUPABASE_ANON_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzZ2lsYmlkZ2xsd3pjYmR4amJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2MjkyMDMsImV4cCI6MjA3NzIwNTIwM30.jmSHF60U96dVdOymZ-8XU0m4yls4VbY7gh6g7ixbV74"
    )
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpzZ2lsYmlkZ2xsd3pjYmR4amJkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTYyOTIwMywiZXhwIjoyMDc3MjA1MjAzfQ.iLs6qSkMVSyPCopdHjW2mcZpdGCSAiLr_0j5rCxXS10"
    )
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:3438864El@db.jsgilbidgllwzcbdxjbd.supabase.co:5432/postgres"
    )
    
    # ==========================================
    # CLOUDFLARE R2 STORAGE (NEW!)
    # ==========================================
    R2_ACCOUNT_ID: str = os.getenv("R2_ACCOUNT_ID", "e0a61e40f2ca2a0d86d95788c423dc9c")
    R2_ACCESS_KEY_ID: str = os.getenv("R2_ACCESS_KEY_ID", "f79dd21eaf8c0e0c9befdf90421da901")
    R2_SECRET_ACCESS_KEY: str = os.getenv("R2_SECRET_ACCESS_KEY", "2181f2747112e2752ec75d72cbf75432944f42045eed44cacb7b5fb6cdfbfc80")
    R2_BUCKET_NAME: str = os.getenv("R2_BUCKET_NAME", "golex-images")
    R2_ENDPOINT: str = os.getenv(
        "R2_ENDPOINT",
        "https://e0a61e40f2ca2a0d86d95788c423dc9c.r2.cloudflarestorage.com"
    )
    R2_PUBLIC_URL: str = os.getenv(
        "R2_PUBLIC_URL",
        f"https://golex-images.{R2_ACCOUNT_ID}.r2.dev"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
