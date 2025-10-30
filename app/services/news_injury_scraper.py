"""
News & Injury Scraper
=====================
Son dakika haberleri ve sakatlık bilgilerini toplar.

Data Sources:
1. Transfermarkt (sakatlıklar) - Web scraping
2. Twitter API (haber akışı) - #FenerbahçeHaberleri vb.
3. RSS Feeds (Sporx, Fanatik) - Son dakika
4. Official club APIs (resmi kulüp siteleri)

Features:
- Real-time injury tracking
- Player status updates (şüpheli, sakatlık, forma)
- News impact on xG predictions
- Automatic notifications
- Lineup prediction updates
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import re


class InjuryStatus(Enum):
    """Sakatlık durumu"""
    HEALTHY = "healthy"  # Sağlıklı
    DOUBTFUL = "doubtful"  # Şüpheli
    INJURED = "injured"  # Sakatlık
    SUSPENDED = "suspended"  # Cezalı


class InjurySeverity(Enum):
    """Sakatlık şiddeti"""
    MINOR = "minor"  # 1-7 gün
    MODERATE = "moderate"  # 1-4 hafta
    MAJOR = "major"  # 1+ ay
    SEASON_ENDING = "season_ending"  # Sezon sonu


@dataclass
class PlayerInjury:
    """Oyuncu sakatlık bilgisi"""
    player_id: str
    player_name: str
    team_id: str
    team_name: str
    status: InjuryStatus
    injury_type: Optional[str]  # "muscle", "knee", "ankle"
    severity: Optional[InjurySeverity]
    expected_return: Optional[datetime]
    last_match: Optional[datetime]
    source: str  # "transfermarkt", "twitter", "official"
    confidence: float  # 0.0-1.0


@dataclass
class NewsItem:
    """Haber öğesi"""
    news_id: str
    title: str
    content: str
    source: str
    published_at: datetime
    fixture_id: Optional[str]
    team_ids: List[str]
    player_ids: List[str]
    keywords: List[str]
    importance: float  # 0.0-1.0


@dataclass
class LineupChange:
    """Kadro değişikliği"""
    fixture_id: str
    team_id: str
    player_out: str
    player_out_name: str
    player_in: Optional[str]
    player_in_name: Optional[str]
    xg_impact: float  # xG değişimi (-0.5, +0.3 vb.)
    market_impacts: Dict[str, float]  # {market: probability_change}


class NewsInjuryScraper:
    """Haber ve sakatlık bilgilerini toplar"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.injury_cache = {}
        self.news_cache = []
    
    # === TRANSFERMARKT SCRAPING ===
    
    async def scrape_transfermarkt_injuries(self, league_id: str) -> List[PlayerInjury]:
        """
        Transfermarkt'tan sakatlık verilerini topla
        
        Args:
            league_id: Lig ID
        
        Returns:
            List[PlayerInjury]
        
        NOTE: Bu gerçek scraping kodu değil, simülasyondur.
        Gerçek implementasyonda BeautifulSoup + requests kullanılır.
        """
        # Transfermarkt URL formatı:
        # https://www.transfermarkt.com.tr/super-lig/verletztespieler/wettbewerb/TR1
        
        injuries = []
        
        # ÖRNEK VERİ (gerçek scraping yerine)
        # Gerçek implementasyonda bu kısım BeautifulSoup ile doldurulur
        
        # Simülasyon: DB'den mevcut sakatlıkları getir
        query = """
        SELECT 
            player_id,
            player_name,
            team_id,
            team_name,
            status,
            injury_type,
            severity,
            expected_return,
            last_match,
            source,
            confidence
        FROM player_injuries
        WHERE league_id = $1
        AND (expected_return IS NULL OR expected_return >= NOW())
        ORDER BY updated_at DESC
        """
        
        rows = await self.db.fetch(query, league_id)
        
        for row in rows:
            injuries.append(PlayerInjury(
                player_id=row['player_id'],
                player_name=row['player_name'],
                team_id=row['team_id'],
                team_name=row['team_name'],
                status=InjuryStatus(row['status']),
                injury_type=row['injury_type'],
                severity=InjurySeverity(row['severity']) if row['severity'] else None,
                expected_return=row['expected_return'],
                last_match=row['last_match'],
                source=row['source'],
                confidence=float(row['confidence'])
            ))
        
        return injuries
    
    async def store_injury(self, injury: PlayerInjury, league_id: str):
        """
        Sakatlık bilgisini kaydet
        
        Args:
            injury: PlayerInjury objesi
            league_id: Lig ID
        """
        query = """
        INSERT INTO player_injuries
        (player_id, player_name, team_id, team_name, league_id,
         status, injury_type, severity, expected_return, last_match,
         source, confidence, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
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
        
        await self.db.execute(
            query,
            injury.player_id,
            injury.player_name,
            injury.team_id,
            injury.team_name,
            league_id,
            injury.status.value,
            injury.injury_type,
            injury.severity.value if injury.severity else None,
            injury.expected_return,
            injury.last_match,
            injury.source,
            injury.confidence
        )
    
    # === TWITTER/RSS SCRAPING ===
    
    async def scrape_twitter_news(self, team_name: str, hours_back: int = 24) -> List[NewsItem]:
        """
        Twitter'dan son dakika haberlerini topla
        
        Args:
            team_name: Takım adı (Fenerbahçe, Galatasaray vb.)
            hours_back: Kaç saat geriye git
        
        Returns:
            List[NewsItem]
        
        NOTE: Bu gerçek Twitter API kullanımı değil, simülasyondur.
        Gerçek implementasyonda tweepy veya Twitter API v2 kullanılır.
        """
        news_items = []
        
        # Twitter arama query'si
        # Örnek: "#Fenerbahçe (sakatlık OR şüpheli OR kadro OR 11)"
        
        # Simülasyon: DB'den son haberleri getir
        query = """
        SELECT 
            news_id,
            title,
            content,
            source,
            published_at,
            fixture_id,
            team_ids,
            player_ids,
            keywords,
            importance
        FROM news_items
        WHERE source = 'twitter'
        AND $1 = ANY(team_ids)
        AND published_at >= NOW() - INTERVAL '1 hour' * $2
        ORDER BY published_at DESC
        LIMIT 50
        """
        
        # team_id'yi team_name'den bul
        team_id = await self._get_team_id_by_name(team_name)
        
        if not team_id:
            return []
        
        rows = await self.db.fetch(query, team_id, hours_back)
        
        for row in rows:
            news_items.append(NewsItem(
                news_id=row['news_id'],
                title=row['title'],
                content=row['content'],
                source=row['source'],
                published_at=row['published_at'],
                fixture_id=row['fixture_id'],
                team_ids=row['team_ids'],
                player_ids=row['player_ids'],
                keywords=row['keywords'],
                importance=float(row['importance'])
            ))
        
        return news_items
    
    async def scrape_rss_feeds(self, feed_url: str) -> List[NewsItem]:
        """
        RSS feed'lerden haber topla (Sporx, Fanatik vb.)
        
        Args:
            feed_url: RSS feed URL
        
        Returns:
            List[NewsItem]
        
        NOTE: Gerçek implementasyonda feedparser kullanılır.
        """
        # RSS Feed URL'leri:
        # - https://www.sporx.com/rss/spor.xml
        # - https://www.fanatik.com.tr/rss/futbol.xml
        
        news_items = []
        
        # Simülasyon kodu
        # Gerçek implementasyonda:
        # import feedparser
        # feed = feedparser.parse(feed_url)
        # for entry in feed.entries:
        #     ...
        
        return news_items
    
    async def store_news(self, news: NewsItem):
        """
        Haber öğesini kaydet
        
        Args:
            news: NewsItem objesi
        """
        query = """
        INSERT INTO news_items
        (news_id, title, content, source, published_at,
         fixture_id, team_ids, player_ids, keywords, importance, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
        ON CONFLICT (news_id) DO NOTHING
        """
        
        await self.db.execute(
            query,
            news.news_id,
            news.title,
            news.content,
            news.source,
            news.published_at,
            news.fixture_id,
            news.team_ids,
            news.player_ids,
            news.keywords,
            news.importance
        )
    
    # === XG IMPACT CALCULATION ===
    
    async def calculate_injury_xg_impact(
        self,
        fixture_id: str,
        team_id: str,
        injured_players: List[PlayerInjury]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Sakatlıkların xG üzerindeki etkisini hesapla
        
        Args:
            fixture_id: Maç ID
            team_id: Takım ID
            injured_players: Sakatlık listesi
        
        Returns:
            (xg_change, market_changes)
            xg_change: xG değişimi (-0.5 = %50 azalma)
            market_changes: {market_code: probability_change}
        """
        if not injured_players:
            return 0.0, {}
        
        # Oyuncuların önemini (xG contribution) hesapla
        total_xg_impact = 0.0
        
        for injury in injured_players:
            # Oyuncu istatistiklerini çek
            player_stats = await self._get_player_stats(injury.player_id, team_id)
            
            if not player_stats:
                continue
            
            # Oyuncunun xG contribution'u
            # Örnek: Dzeko = 0.5 xG/maç, takım ortalama = 1.8 xG/maç
            # Etki: -0.5 / 1.8 = -0.28 (-28%)
            
            player_xg_per_match = player_stats.get('xg_per_match', 0.0)
            
            if injury.status == InjuryStatus.INJURED:
                total_xg_impact -= player_xg_per_match
            elif injury.status == InjuryStatus.DOUBTFUL:
                # Şüpheli oyuncular %50 ihtimal
                total_xg_impact -= player_xg_per_match * 0.5
        
        # Market etkilerini hesapla
        market_changes = {}
        
        if abs(total_xg_impact) > 0.1:  # En az 0.1 xG değişimi
            # KG_YES: xG azalırsa ihtimal düşer
            if total_xg_impact < -0.2:
                market_changes['KG_YES'] = -0.10  # -10%
            
            # BTTS: Her iki takım da etkilenirse BTTS düşer
            # Over/Under: xG değişimine göre
            if total_xg_impact < -0.3:
                market_changes['O2.5'] = -0.08  # -8%
                market_changes['O3.5'] = -0.12  # -12%
        
        return round(total_xg_impact, 2), market_changes
    
    async def get_lineup_changes_for_match(self, fixture_id: str) -> List[LineupChange]:
        """
        Maç için kadro değişikliklerini getir
        
        Args:
            fixture_id: Maç ID
        
        Returns:
            List[LineupChange]
        """
        # Maça katılan takımları bul
        fixture = await self._get_fixture(fixture_id)
        
        if not fixture:
            return []
        
        home_team_id = fixture['home_team_id']
        away_team_id = fixture['away_team_id']
        
        changes = []
        
        # Her iki takım için sakatlıkları kontrol et
        for team_id in [home_team_id, away_team_id]:
            injuries = await self.scrape_transfermarkt_injuries(fixture['league_id'])
            team_injuries = [inj for inj in injuries if inj.team_id == team_id]
            
            if not team_injuries:
                continue
            
            # xG etkisini hesapla
            xg_impact, market_impacts = await self.calculate_injury_xg_impact(
                fixture_id,
                team_id,
                team_injuries
            )
            
            for injury in team_injuries:
                if injury.status in [InjuryStatus.INJURED, InjuryStatus.SUSPENDED]:
                    changes.append(LineupChange(
                        fixture_id=fixture_id,
                        team_id=team_id,
                        player_out=injury.player_id,
                        player_out_name=injury.player_name,
                        player_in=None,  # Yedek oyuncu bilgisi (TODO)
                        player_in_name=None,
                        xg_impact=xg_impact / len(team_injuries),  # Ortalama etki
                        market_impacts=market_impacts
                    ))
        
        return changes
    
    # === NOTIFICATIONS ===
    
    async def send_injury_notification(self, injury: PlayerInjury, fixture_id: Optional[str] = None):
        """
        Sakatlık bildirimi gönder
        
        Args:
            injury: PlayerInjury objesi
            fixture_id: İlgili maç ID (opsiyonel)
        """
        # Notification içeriği
        if injury.status == InjuryStatus.INJURED:
            message = f"🔴 {injury.player_name} sakatlık nedeniyle forma giyemeyecek!"
        elif injury.status == InjuryStatus.DOUBTFUL:
            message = f"🟡 {injury.player_name} şüpheli! Son antrenmanı kaçırdı."
        elif injury.status == InjuryStatus.SUSPENDED:
            message = f"⛔ {injury.player_name} cezalı! Maça çıkamayacak."
        else:
            message = f"✅ {injury.player_name} forma giyecek!"
        
        # Notification kaydet
        query = """
        INSERT INTO notifications
        (type, title, message, fixture_id, team_id, player_id, created_at)
        VALUES ('injury_update', $1, $2, $3, $4, $5, NOW())
        """
        
        await self.db.execute(
            query,
            f"{injury.team_name} - Kadro Güncellemesi",
            message,
            fixture_id,
            injury.team_id,
            injury.player_id
        )
    
    # === HELPER METHODS ===
    
    async def _get_team_id_by_name(self, team_name: str) -> Optional[str]:
        """Takım adından ID bul"""
        query = "SELECT team_id FROM teams WHERE name ILIKE $1 LIMIT 1"
        row = await self.db.fetchrow(query, f"%{team_name}%")
        return row['team_id'] if row else None
    
    async def _get_player_stats(self, player_id: str, team_id: str) -> Optional[Dict]:
        """Oyuncu istatistiklerini getir"""
        query = """
        SELECT 
            AVG(xg) as xg_per_match,
            AVG(goals) as goals_per_match,
            COUNT(*) as matches_played
        FROM player_match_stats
        WHERE player_id = $1
        AND team_id = $2
        AND match_date >= NOW() - INTERVAL '3 months'
        GROUP BY player_id
        """
        
        row = await self.db.fetchrow(query, player_id, team_id)
        
        if not row:
            return None
        
        return {
            'xg_per_match': float(row['xg_per_match'] or 0.0),
            'goals_per_match': float(row['goals_per_match'] or 0.0),
            'matches_played': int(row['matches_played'])
        }
    
    async def _get_fixture(self, fixture_id: str) -> Optional[Dict]:
        """Maç bilgilerini getir"""
        query = """
        SELECT 
            fixture_id,
            home_team_id,
            away_team_id,
            league_id,
            match_date
        FROM fixtures
        WHERE fixture_id = $1
        """
        
        row = await self.db.fetchrow(query, fixture_id)
        
        if not row:
            return None
        
        return {
            'fixture_id': row['fixture_id'],
            'home_team_id': row['home_team_id'],
            'away_team_id': row['away_team_id'],
            'league_id': row['league_id'],
            'match_date': row['match_date']
        }


# === UTILITY FUNCTIONS ===

def parse_injury_from_text(text: str) -> Optional[Dict]:
    """
    Haber metninden sakatlık bilgisi çıkar
    
    Args:
        text: "Dzeko son antrenmanı kaçırdı"
    
    Returns:
        {"player_name": str, "status": str} veya None
    
    Examples:
        "Dzeko sakatlık" -> {"player_name": "Dzeko", "status": "injured"}
        "İcardi şüpheli" -> {"player_name": "İcardi", "status": "doubtful"}
    """
    # Anahtar kelimeler
    injury_keywords = {
        'injured': ['sakatlık', 'sakatlandı', 'sakatlığı', 'tedavi'],
        'doubtful': ['şüpheli', 'kaçırdı', 'antrenmanda yok', 'belirsiz'],
        'suspended': ['cezalı', 'kart cezası', 'disiplin'],
        'healthy': ['forma giyecek', 'hazır', 'sağlıklı', 'oynayacak']
    }
    
    text_lower = text.lower()
    
    for status, keywords in injury_keywords.items():
        if any(kw in text_lower for kw in keywords):
            # İsmi bul (basit regex)
            # Örnek: "Dzeko sakatlık" -> "Dzeko"
            words = text.split()
            if len(words) > 0:
                player_name = words[0].strip()
                return {
                    "player_name": player_name,
                    "status": status
                }
    
    return None


def format_injury_report(
    injuries: List[PlayerInjury],
    lineup_changes: List[LineupChange]
) -> Dict:
    """
    Sakatlık raporunu formatla (frontend için)
    
    Returns:
        {
            "injuries": [...],
            "lineup_changes": [...],
            "total_xg_impact": float
        }
    """
    total_xg_impact = sum(change.xg_impact for change in lineup_changes)
    
    return {
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
        ],
        "lineup_changes": [
            {
                "fixture_id": change.fixture_id,
                "team_id": change.team_id,
                "player_out": change.player_out_name,
                "player_in": change.player_in_name,
                "xg_impact": change.xg_impact,
                "market_impacts": change.market_impacts
            }
            for change in lineup_changes
        ],
        "total_xg_impact": round(total_xg_impact, 2)
    }

