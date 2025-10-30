# GOLEX Backend API

Football live scores, statistics, and AI predictions API with real-time updates.

## 🚀 Features

### Core Features
- **Live Scores** - Real-time match updates via SSE
- **Fixtures** - Today's matches, date-based queries, live matches
- **AI Predictions** - Advanced prediction engine (existing, not modified)
- **Leagues & Standings** - League tables and rankings
- **Teams & Players** - Comprehensive profiles and statistics
- **Search** - Fast search across teams, players, and competitions
- **Favorites & Notifications** - User preferences and alerts

### NEW Football Features
- **Attack Momentum** - Minute-by-minute momentum calculation
- **Player Ratings** - 0-10 rating system with color coding
- **Expected Goals (xG)** - Shot-by-shot xG calculation
- **Shot Map** - Visual representation of all shots
- **Heatmap** - Player and team heat maps
- **Lineups & Formations** - Detailed lineup data with field positions
- **Match Statistics** - Comprehensive match stats (possession, passes, shots, etc.)
- **Player/Team Profiles** - Detailed profiles with season statistics
- **Real-time Updates** - Server-Sent Events (SSE) for live data
- **API-Football Integration** - Full integration with API-Football data source

## 📋 Requirements

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- API-Football API Key (from RapidAPI)

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/golex.git
cd golex/backend-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the `backend-api` directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/golex
REDIS_URL=redis://localhost:6379/0
API_FOOTBALL_KEY=your-rapidapi-key-here
SECRET_KEY=your-secret-key-change-this
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

Or run SQL migrations manually:

```bash
psql -U user -d golex -f migrations/sql/030_player_team_statistics.sql
psql -U user -d golex -f migrations/sql/031_lineups.sql
```

### 6. Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Key Endpoints

### Live Data
```
GET  /api/v1/fixtures/live                    # All live matches
GET  /api/v1/fixtures/today                   # Today's matches
GET  /api/v1/fixtures/{id}                    # Match details
```

### Real-time (SSE)
```
GET  /api/v1/realtime/fixtures/{id}/live      # Live match updates
GET  /api/v1/realtime/matches/live            # All live matches stream
GET  /api/v1/realtime/fixtures/{id}/attack-momentum  # Momentum stream
```

### Football Features
```
GET  /api/v1/fixtures/{id}/attack-momentum    # Attack momentum graph
GET  /api/v1/fixtures/{id}/lineups            # Match lineups
GET  /api/v1/fixtures/{id}/statistics         # Match statistics
GET  /api/v1/fixtures/{id}/xg                 # Expected goals data
GET  /api/v1/players/{id}/rating              # Player rating
GET  /api/v1/players/{id}/statistics/season   # Season stats
GET  /api/v1/teams/{id}/statistics/season     # Team season stats
```

### Profiles
```
GET  /api/v1/players/{id}                     # Player profile
GET  /api/v1/teams/{id}                       # Team profile
GET  /api/v1/teams/{id1}/h2h/{id2}            # Head-to-head
```

## 🔥 Real-time Updates (SSE)

Example JavaScript client:

```javascript
const eventSource = new EventSource('http://localhost:8000/api/v1/realtime/fixtures/12345/live');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Live update:', data);
    
    if (data.type === 'match_update') {
        updateScore(data.score);
        updateEvents(data.events);
    }
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
    eventSource.close();
};
```

## 🧪 Testing

```bash
pytest
pytest --cov=app tests/
```

## 🏗️ Architecture

```
backend-api/
├── app/
│   ├── api/
│   │   └── routes/              # API endpoints
│   ├── core/
│   │   └── config.py            # Configuration
│   ├── db/
│   │   └── database.py          # Database connection
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   └── services/                # Business logic
│       ├── attack_momentum.py
│       ├── player_rating.py
│       ├── xg_calculator.py
│       ├── statistics_service.py
│       └── api_football_service.py
├── migrations/
│   └── sql/                     # SQL migrations
├── tests/                       # Test files
└── main.py                      # FastAPI app entry point
```

## 📊 Database Schema

### Core Tables
- `fixtures` - Match fixtures
- `teams` - Team information
- `players` - Player information
- `leagues` - League/competition data

### Statistics Tables
- `player_statistics` - Match-level player stats
- `team_statistics` - Match-level team stats
- `shots` - Individual shot data for shot maps
- `event_graph_data` - Attack momentum data

### Lineup Tables
- `lineups` - Team lineups with formations
- `lineup_players` - Individual player positions

## 🔒 Important Notes

### AI Prediction Engine
⚠️ **The existing AI prediction engine is NOT modified!** All new football features are additions only. The existing `/api/v1/predictions` endpoints remain unchanged.

### API-Football Rate Limits
- Free tier: 100 requests/day
- Be mindful of rate limits when testing
- Consider caching responses for development

### Excluded Features
As requested by the user, the following features are **NOT** included:
- Market values (player/team valuations)
- Betting odds and predictions
- Gambling-related features

## 🚀 Deployment

### Docker

```bash
docker build -t golex-backend .
docker run -p 8000:8000 golex-backend
```

### Production

Use `gunicorn` with `uvicorn` workers:

```bash
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

## 📝 License

[Add your license here]

## 👥 Contributors

[Add contributors]
