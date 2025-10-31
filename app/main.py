"""
GOLEX Backend API - Main Application
Extended with football features (attack momentum, player ratings, xG)
Deploy trigger: 2025-10-31
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

# Import existing routers
from app.api.routes import (
    fixtures,
    leagues,
    teams,
    players,
    search,
    predictions,
    auth,
    favorites,
    notifications,
)

# Import NEW football feature routers
from app.api.routes import (
    attack_momentum_routes,
    player_rating_routes,
    xg_routes,
    lineup_routes,
    statistics_routes,
    fixtures_routes,
    fixtures_analytics,
    news,
    players_full,
    teams_full,
    leagues_full,
    realtime_routes,
    search_routes,
    user_routes,
    favorites_routes,
    ml_routes,
)

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting GOLEX Backend with Football Features...")
    yield
    # Shutdown
    print("👋 Shutting down GOLEX Backend...")


# Create FastAPI app
app = FastAPI(
    title="GOLEX API",
    description="Football Live Scores, Statistics & AI Predictions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGIN", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include EXISTING routers (don't touch prediction engine!)
app.include_router(fixtures.router, prefix="/api/v1")
app.include_router(leagues.router, prefix="/api/v1")
app.include_router(teams.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")  # ← EXISTING AI PREDICTION ENGINE
app.include_router(auth.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")

# Include NEW football feature routers
app.include_router(attack_momentum_routes.router, prefix="/api/v1")
app.include_router(player_rating_routes.router, prefix="/api/v1")
app.include_router(xg_routes.router, prefix="/api/v1")
app.include_router(lineup_routes.router, prefix="/api/v1")
app.include_router(statistics_routes.router, prefix="/api/v1")
app.include_router(fixtures_routes.router, prefix="/api/v1")
app.include_router(fixtures_analytics.router, prefix="/api/v1")  # Weather & mini-stats
app.include_router(news.router, prefix="/api/v1")  # News & Injuries (RSS)
app.include_router(players_full.router, prefix="/api/v1")  # FULL player details
app.include_router(teams_full.router, prefix="/api/v1")  # FULL team details
app.include_router(leagues_full.router, prefix="/api/v1")  # FULL league details
app.include_router(realtime_routes.router, prefix="/api/v1")
app.include_router(search_routes.router, prefix="/api/v1")
app.include_router(user_routes.router, prefix="/api/v1")
app.include_router(favorites_routes.router, prefix="/api/v1")
app.include_router(ml_routes.router, prefix="/api/v1")  # ML Model & Training

# Import and include notifications router
from app.api.routes import notifications_routes
app.include_router(notifications_routes.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "GOLEX API v1.0.0 - Football Features Edition",
        "status": "running",
        "docs": "/docs",
        "features": {
            "existing": [
                "AI Predictions (unchanged)",
                "Live Scores",
                "Fixtures",
                "Leagues & Standings",
                "Teams & Players",
                "Search",
                "Favorites",
                "Notifications"
            ],
            "new_football": [
                "Attack Momentum Graph",
                "Player Ratings (0-10)",
                "Expected Goals (xG)",
                "Shot Map",
                "Heatmap",
                "Match Statistics",
                "Lineups & Formations",
                "Player/Team Profiles",
                "Real-time Updates (SSE)",
                "API-Football Integration"
            ]
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "football_features": "active"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
