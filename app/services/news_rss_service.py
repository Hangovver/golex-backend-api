"""
GOLEX - News & Transfer RSS Scraping (Free)
Scrapes football news from popular RSS feeds
"""

import aiohttp
import feedparser
from typing import List, Dict, Optional
from datetime import datetime
import re

class NewsRSSService:
    """
    Free RSS Feed Scraper for Football News
    No API key required
    """
    
    RSS_FEEDS = {
        "bbc_football": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "espn": "https://www.espn.com/espn/rss/soccer/news",
        "goal": "https://www.goal.com/en/feeds/news",
        "skysports": "https://www.skysports.com/rss/12040",
        "transfermarkt_news": "https://www.transfermarkt.com/rss/news",
        "fabrizio_romano": "https://www.fabrizio-romano.com/rss",  # Unofficial aggregator
    }
    
    TEAM_KEYWORDS = [
        "manchester united", "man utd", "liverpool", "chelsea", "arsenal",
        "manchester city", "man city", "tottenham", "spurs", "barcelona", 
        "real madrid", "bayern", "psg", "juventus", "inter", "milan",
        "atletico", "dortmund", "ajax", "benfica", "porto"
    ]
    
    TRANSFER_KEYWORDS = [
        "transfer", "signing", "deal", "contract", "agreement", "bid",
        "offer", "negotiate", "fee", "clause", "loan", "permanent",
        "medical", "unveil", "announce", "confirm"
    ]
    
    INJURY_KEYWORDS = [
        "injury", "injured", "injured", "sidelined", "ruled out", "doubt",
        "fitness", "recover", "return", "miss", "absent", "suspend"
    ]
    
    async def fetch_all_news(self, limit: int = 50) -> List[Dict]:
        """Fetch news from all RSS feeds"""
        all_news = []
        
        for source, url in self.RSS_FEEDS.items():
            try:
                news = await self._fetch_feed(url, source)
                all_news.extend(news)
            except Exception as e:
                print(f"Error fetching {source}: {e}")
        
        # Sort by published date (newest first)
        all_news.sort(key=lambda x: x.get("published", 0), reverse=True)
        
        return all_news[:limit]
    
    async def fetch_team_news(self, team_name: str, limit: int = 20) -> List[Dict]:
        """Fetch news related to a specific team"""
        all_news = await self.fetch_all_news(limit=100)
        
        # Filter by team name
        team_news = [
            news for news in all_news
            if team_name.lower() in news.get("title", "").lower() or
               team_name.lower() in news.get("description", "").lower()
        ]
        
        return team_news[:limit]
    
    async def fetch_transfer_news(self, limit: int = 30) -> List[Dict]:
        """Fetch transfer-related news only"""
        all_news = await self.fetch_all_news(limit=100)
        
        transfer_news = [
            news for news in all_news
            if any(keyword in news.get("title", "").lower() for keyword in self.TRANSFER_KEYWORDS) or
               any(keyword in news.get("description", "").lower() for keyword in self.TRANSFER_KEYWORDS)
        ]
        
        return transfer_news[:limit]
    
    async def fetch_injury_news(self, limit: int = 20) -> List[Dict]:
        """Fetch injury-related news only"""
        all_news = await self.fetch_all_news(limit=100)
        
        injury_news = [
            news for news in all_news
            if any(keyword in news.get("title", "").lower() for keyword in self.INJURY_KEYWORDS) or
               any(keyword in news.get("description", "").lower() for keyword in self.INJURY_KEYWORDS)
        ]
        
        return injury_news[:limit]
    
    async def _fetch_feed(self, url: str, source: str) -> List[Dict]:
        """Fetch and parse a single RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        feed = feedparser.parse(content)
                        
                        news_list = []
                        for entry in feed.entries:
                            news_item = self._parse_entry(entry, source)
                            if news_item:
                                news_list.append(news_item)
                        
                        return news_list
                    else:
                        print(f"Failed to fetch {url}: {resp.status}")
                        return []
        except Exception as e:
            print(f"Error fetching feed {url}: {e}")
            return []
    
    def _parse_entry(self, entry, source: str) -> Optional[Dict]:
        """Parse RSS feed entry"""
        try:
            title = entry.get("title", "")
            description = entry.get("description", "") or entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published_parsed", None)
            
            # Convert published time to timestamp
            if published:
                published_ts = int(datetime(*published[:6]).timestamp())
            else:
                published_ts = int(datetime.now().timestamp())
            
            # Clean HTML tags from description
            description = re.sub(r'<[^>]+>', '', description)
            description = description.strip()
            
            # Categorize
            categories = []
            title_lower = title.lower()
            desc_lower = description.lower()
            
            if any(kw in title_lower or kw in desc_lower for kw in self.TRANSFER_KEYWORDS):
                categories.append("transfer")
            if any(kw in title_lower or kw in desc_lower for kw in self.INJURY_KEYWORDS):
                categories.append("injury")
            
            # Detect teams mentioned
            teams_mentioned = [
                team for team in self.TEAM_KEYWORDS
                if team in title_lower or team in desc_lower
            ]
            
            return {
                "title": title,
                "description": description[:500],  # Limit length
                "link": link,
                "source": source,
                "published": published_ts,
                "published_date": datetime.fromtimestamp(published_ts).strftime("%Y-%m-%d %H:%M"),
                "categories": categories,
                "teams": teams_mentioned,
                "type": "transfer" if "transfer" in categories else "injury" if "injury" in categories else "news"
            }
        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None
    
    def get_news_impact(self, team_name: str, news_list: List[Dict]) -> Dict:
        """
        Analyze news impact on team performance
        
        Returns:
        {
            'impact_score': -0.15,  # -1 to 1 (negative=bad news)
            'key_news': [...],
            'transfers_in': 2,
            'transfers_out': 1,
            'injuries': 3,
            'summary': 'Team weakened due to injuries'
        }
        """
        team_news = [
            news for news in news_list
            if team_name.lower() in " ".join(news.get("teams", [])).lower()
        ]
        
        impact_score = 0.0
        transfers_in = 0
        transfers_out = 0
        injuries = 0
        key_news = []
        
        for news in team_news[:10]:  # Last 10 news items
            title_lower = news.get("title", "").lower()
            
            # Transfer analysis
            if "signing" in title_lower or "joins" in title_lower or "welcome" in title_lower:
                transfers_in += 1
                impact_score += 0.05
                key_news.append(news)
            elif "leaves" in title_lower or "departs" in title_lower or "sold" in title_lower:
                transfers_out += 1
                impact_score -= 0.05
                key_news.append(news)
            
            # Injury analysis
            if any(kw in title_lower for kw in ["injury", "injured", "ruled out", "sidelined"]):
                injuries += 1
                if any(kw in title_lower for kw in ["star", "key", "captain", "striker"]):
                    impact_score -= 0.10  # Key player injury
                else:
                    impact_score -= 0.05  # Regular player injury
                key_news.append(news)
        
        # Summary
        summary_parts = []
        if transfers_in > 0:
            summary_parts.append(f"{transfers_in} new signing(s)")
        if transfers_out > 0:
            summary_parts.append(f"{transfers_out} departure(s)")
        if injuries > 0:
            summary_parts.append(f"{injuries} injury concern(s)")
        
        summary = ", ".join(summary_parts) if summary_parts else "No significant news"
        
        return {
            "impact_score": max(-1.0, min(1.0, impact_score)),
            "key_news": key_news[:5],  # Top 5 most relevant
            "transfers_in": transfers_in,
            "transfers_out": transfers_out,
            "injuries": injuries,
            "summary": summary
        }


# Global instance
news_service = NewsRSSService()

