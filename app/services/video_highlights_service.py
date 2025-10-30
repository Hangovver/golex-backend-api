"""
GOLEX - Video Highlights Service (YouTube API - Free)
Fetches match highlights from YouTube
"""

import aiohttp
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class VideoHighlightsService:
    """
    YouTube Data API v3 Integration (Free Tier)
    Quota: 10,000 units/day (100 search requests = 10,000 units)
    """
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    # Popular football channels
    CHANNELS = {
        "skysports": "UCNAf1k0yIjyGu3k9BwAg3lg",
        "btsport": "UC5yPQU0NkG93XkOq1LY6Weg",
        "espnfc": "UCQF0oe5XJ5r68jCvULYy7rQ",
        "beinsports": "UCnJN00J3KK-0MQOG9VVxsKQ",
        "goal": "UCHHsPhQgHNVJZGjdDqf-PLw",
        "433": "UC4i1zoL-h_8-5IUo4Xl8pTg",  # 433 official
        "laliga": "UC6RN4x5GErccw-kXsrxKVbA",
        "bundesliga": "UCjp-vg5-jvb96NxD8m_jgLg",
        "seriea": "UCf3RcSZGRJWyOoXVdMWvRhA",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            # User needs to get free key from: https://console.cloud.google.com/
            self.api_key = "demo"  # Placeholder
    
    async def search_match_highlights(
        self, 
        home_team: str, 
        away_team: str,
        date: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for match highlights on YouTube
        
        Args:
            home_team: Home team name
            away_team: Away team name
            date: Match date (YYYY-MM-DD), searches last 7 days if None
            limit: Max results
        
        Returns:
            List of video highlights with metadata
        """
        # Build search query
        query = f"{home_team} vs {away_team} highlights"
        
        # Date range (YouTube API requires RFC 3339 format)
        if date:
            published_after = f"{date}T00:00:00Z"
            published_before = f"{date}T23:59:59Z"
        else:
            # Last 7 days
            published_after = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT00:00:00Z")
            published_before = datetime.now().strftime("%Y-%m-%dT23:59:59Z")
        
        url = f"{self.BASE_URL}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "videoDuration": "medium",  # 4-20 minutes (typical highlights)
            "publishedAfter": published_after,
            "publishedBefore": published_before,
            "order": "relevance",
            "maxResults": limit,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = []
                        
                        for item in data.get("items", []):
                            video = self._parse_video(item)
                            if video:
                                videos.append(video)
                        
                        return videos
                    elif resp.status == 403:
                        print("YouTube API quota exceeded or invalid key")
                        return []
                    else:
                        print(f"YouTube API error: {resp.status}")
                        return []
        except Exception as e:
            print(f"Video highlights error: {e}")
            return []
    
    async def search_team_highlights(
        self, 
        team_name: str, 
        limit: int = 10
    ) -> List[Dict]:
        """Search for general team highlights (goals, best moments)"""
        query = f"{team_name} highlights goals"
        
        url = f"{self.BASE_URL}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "publishedAfter": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z"),
            "order": "viewCount",  # Most popular
            "maxResults": limit,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = []
                        
                        for item in data.get("items", []):
                            video = self._parse_video(item)
                            if video:
                                videos.append(video)
                        
                        return videos
                    else:
                        return []
        except Exception as e:
            print(f"Team highlights error: {e}")
            return []
    
    async def search_player_highlights(
        self, 
        player_name: str, 
        limit: int = 5
    ) -> List[Dict]:
        """Search for player highlights (goals, skills)"""
        query = f"{player_name} goals skills highlights"
        
        url = f"{self.BASE_URL}/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "publishedAfter": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z"),
            "order": "relevance",
            "maxResults": limit,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        videos = []
                        
                        for item in data.get("items", []):
                            video = self._parse_video(item)
                            if video:
                                videos.append(video)
                        
                        return videos
                    else:
                        return []
        except Exception as e:
            print(f"Player highlights error: {e}")
            return []
    
    def _parse_video(self, item: Dict) -> Optional[Dict]:
        """Parse YouTube API video item"""
        try:
            snippet = item.get("snippet", {})
            video_id = item.get("id", {}).get("videoId")
            
            if not video_id:
                return None
            
            # Parse published date
            published = snippet.get("publishedAt", "")
            try:
                published_dt = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
                published_ts = int(published_dt.timestamp())
                published_str = published_dt.strftime("%Y-%m-%d %H:%M")
            except:
                published_ts = int(datetime.now().timestamp())
                published_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Get thumbnail (best quality available)
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("high", {}).get("url") or
                thumbnails.get("medium", {}).get("url") or
                thumbnails.get("default", {}).get("url") or
                ""
            )
            
            return {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", "")[:200],  # Limit length
                "thumbnail_url": thumbnail_url,
                "channel_title": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published": published_ts,
                "published_date": published_str,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
                "embed_url": f"https://www.youtube.com/embed/{video_id}",
                "duration": "unknown"  # Would need separate API call to get duration
            }
        except Exception as e:
            print(f"Error parsing video: {e}")
            return None
    
    async def get_video_stats(self, video_id: str) -> Optional[Dict]:
        """
        Get detailed video statistics (requires additional API quota)
        
        Returns:
            {
                'views': 1234567,
                'likes': 12345,
                'duration': 'PT8M30S',
                'duration_seconds': 510
            }
        """
        url = f"{self.BASE_URL}/videos"
        params = {
            "part": "statistics,contentDetails",
            "id": video_id,
            "key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        items = data.get("items", [])
                        if items:
                            stats = items[0].get("statistics", {})
                            content = items[0].get("contentDetails", {})
                            duration = content.get("duration", "PT0S")
                            
                            # Parse ISO 8601 duration (PT8M30S -> 510 seconds)
                            duration_seconds = self._parse_duration(duration)
                            
                            return {
                                "views": int(stats.get("viewCount", 0)),
                                "likes": int(stats.get("likeCount", 0)),
                                "duration": duration,
                                "duration_seconds": duration_seconds,
                                "duration_formatted": f"{duration_seconds // 60}:{duration_seconds % 60:02d}"
                            }
                    return None
        except Exception as e:
            print(f"Video stats error: {e}")
            return None
    
    def _parse_duration(self, duration: str) -> int:
        """Parse ISO 8601 duration to seconds (PT8M30S -> 510)"""
        try:
            import re
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return 0


# Global instance
video_service = VideoHighlightsService()

