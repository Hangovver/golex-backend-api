"""
GOLEX - Automatic Market Analyzer
Analyzes all 466 markets automatically, filters high-confidence predictions (60%+)
NO MANUAL SELECTION - fully automated background analysis
"""

from typing import Dict, List, Optional
from datetime import datetime
import asyncio

# Import existing prediction engine
from app.services.predictions import PredictionEngine
from app.services.markets_466 import Markets466Calculator
from app.services.weather_service import weather_service
from app.services.news_rss_service import news_service


class AutoMarketAnalyzer:
    """
    Automatic market analysis for all 466 markets
    - Runs in background
    - Filters predictions with confidence >= 60%
    - No manual intervention required
    """
    
    CONFIDENCE_THRESHOLD = 0.60  # 60% minimum confidence
    
    def __init__(self):
        self.prediction_engine = PredictionEngine()
        self.markets_calculator = Markets466Calculator()
    
    async def analyze_match(
        self, 
        fixture_id: str,
        home_team: str,
        away_team: str,
        home_stats: Dict,
        away_stats: Dict,
        stadium_coords: Optional[tuple] = None,
        match_date: Optional[str] = None
    ) -> Dict:
        """
        Analyze a single match across all 466 markets
        
        Returns:
        {
            'fixture_id': '12345',
            'analyzed_markets': 466,
            'high_confidence_markets': 23,
            'predictions': [
                {
                    'market': 'Over 2.5 Goals',
                    'prediction': 'Yes',
                    'confidence': 0.78,
                    'base_confidence': 0.85,
                    'weather_impact': -0.05,
                    'news_impact': -0.02,
                    'kelly_stake': 0.035,
                    'ev': 1.15
                },
                ...
            ],
            'weather_summary': {...},
            'news_summary': {...}
        }
        """
        
        # 1. Get base predictions from existing engine (466 markets)
        base_predictions = await self._get_base_predictions(
            home_team, away_team, home_stats, away_stats
        )
        
        # 2. Get weather impact (if stadium coordinates available)
        weather_impact = 0.0
        weather_summary = None
        if stadium_coords:
            weather_data = await weather_service.get_weather_by_coords(
                lat=stadium_coords[0],
                lon=stadium_coords[1]
            )
            if weather_data:
                weather_analysis = weather_service.get_weather_impact(weather_data)
                weather_impact = weather_analysis["impact_score"] - 1.0  # Convert 0-1 to -1 to 0
                weather_summary = {
                    "temp": weather_data.get("temp"),
                    "weather": weather_data.get("weather"),
                    "wind_speed": weather_data.get("wind_speed"),
                    "rain": weather_data.get("rain_1h", 0),
                    "impact": weather_analysis["recommendation"]
                }
        
        # 3. Get news/injury impact
        news_impact_home = 0.0
        news_impact_away = 0.0
        news_summary = None
        
        try:
            # Fetch recent news
            all_news = await news_service.fetch_all_news(limit=100)
            
            # Analyze home team
            home_analysis = news_service.get_news_impact(home_team, all_news)
            news_impact_home = home_analysis["impact_score"]
            
            # Analyze away team
            away_analysis = news_service.get_news_impact(away_team, all_news)
            news_impact_away = away_analysis["impact_score"]
            
            news_summary = {
                "home_team": {
                    "injuries": home_analysis["injuries"],
                    "transfers_in": home_analysis["transfers_in"],
                    "transfers_out": home_analysis["transfers_out"],
                    "summary": home_analysis["summary"]
                },
                "away_team": {
                    "injuries": away_analysis["injuries"],
                    "transfers_in": away_analysis["transfers_in"],
                    "transfers_out": away_analysis["transfers_out"],
                    "summary": away_analysis["summary"]
                }
            }
        except Exception as e:
            print(f"News analysis error: {e}")
        
        # 4. Adjust predictions based on external factors
        adjusted_predictions = []
        high_confidence_count = 0
        
        for pred in base_predictions:
            # Apply adjustment factors
            base_conf = pred["confidence"]
            
            # Weather affects total goals, corners, cards
            weather_factor = 1.0
            if "goals" in pred["market"].lower() or "corners" in pred["market"].lower():
                weather_factor = 1.0 + (weather_impact * 0.5)  # 50% weight
            
            # News affects team-specific markets
            news_factor = 1.0
            if "home" in pred["market"].lower() or home_team.lower() in pred["market"].lower():
                news_factor = 1.0 + (news_impact_home * 0.3)  # 30% weight
            elif "away" in pred["market"].lower() or away_team.lower() in pred["market"].lower():
                news_factor = 1.0 + (news_impact_away * 0.3)
            
            # Calculate final confidence
            final_confidence = base_conf * weather_factor * news_factor
            final_confidence = max(0.0, min(1.0, final_confidence))  # Clamp to 0-1
            
            # Only include if >= 60% confidence
            if final_confidence >= self.CONFIDENCE_THRESHOLD:
                adjusted_pred = {
                    **pred,
                    "base_confidence": base_conf,
                    "confidence": final_confidence,
                    "weather_impact": weather_impact,
                    "news_impact": (news_impact_home + news_impact_away) / 2,
                    "adjustments": {
                        "weather_factor": weather_factor,
                        "news_factor": news_factor
                    }
                }
                adjusted_predictions.append(adjusted_pred)
                high_confidence_count += 1
        
        # 5. Sort by confidence (highest first)
        adjusted_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "fixture_id": fixture_id,
            "home_team": home_team,
            "away_team": away_team,
            "analyzed_at": datetime.now().isoformat(),
            "analyzed_markets": len(base_predictions),
            "high_confidence_markets": high_confidence_count,
            "predictions": adjusted_predictions,
            "weather_summary": weather_summary,
            "news_summary": news_summary,
            "threshold": self.CONFIDENCE_THRESHOLD
        }
    
    async def _get_base_predictions(
        self, 
        home_team: str, 
        away_team: str,
        home_stats: Dict,
        away_stats: Dict
    ) -> List[Dict]:
        """
        Get base predictions from existing 466 markets calculator
        Uses: xG, Poisson, Dixon-Coles, Kelly Criterion
        """
        try:
            # Calculate all 466 markets using existing engine
            all_markets = self.markets_calculator.calculate_all_markets(
                home_stats=home_stats,
                away_stats=away_stats
            )
            
            predictions = []
            for market_name, market_data in all_markets.items():
                if isinstance(market_data, dict) and "confidence" in market_data:
                    predictions.append({
                        "market": market_name,
                        "prediction": market_data.get("prediction"),
                        "confidence": market_data.get("confidence", 0.0),
                        "odds": market_data.get("odds"),
                        "kelly_stake": market_data.get("kelly_stake", 0.0),
                        "ev": market_data.get("expected_value", 0.0),
                        "formula": market_data.get("formula", "Dixon-Coles")
                    })
            
            return predictions
        except Exception as e:
            print(f"Base predictions error: {e}")
            return []
    
    async def analyze_multiple_matches(
        self, 
        fixtures: List[Dict]
    ) -> List[Dict]:
        """
        Analyze multiple matches in parallel
        
        Args:
            fixtures: List of fixture data dicts
        
        Returns:
            List of analysis results
        """
        tasks = []
        for fixture in fixtures:
            task = self.analyze_match(
                fixture_id=fixture["id"],
                home_team=fixture["home_team"],
                away_team=fixture["away_team"],
                home_stats=fixture.get("home_stats", {}),
                away_stats=fixture.get("away_stats", {}),
                stadium_coords=fixture.get("stadium_coords"),
                match_date=fixture.get("date")
            )
            tasks.append(task)
        
        # Run all analyses in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors
        valid_results = [r for r in results if isinstance(r, dict)]
        
        return valid_results
    
    def get_top_predictions(
        self, 
        analysis_result: Dict, 
        limit: int = 10
    ) -> List[Dict]:
        """
        Get top N predictions from analysis result
        Already sorted by confidence (highest first)
        """
        return analysis_result.get("predictions", [])[:limit]
    
    def filter_by_market_type(
        self, 
        analysis_result: Dict, 
        market_types: List[str]
    ) -> List[Dict]:
        """
        Filter predictions by market type
        
        market_types examples:
        - ["goals"] → Over/Under goals markets
        - ["btts"] → Both Teams To Score
        - ["corners"] → Corner markets
        - ["cards"] → Card markets
        """
        predictions = analysis_result.get("predictions", [])
        filtered = []
        
        for pred in predictions:
            market_lower = pred["market"].lower()
            if any(mt.lower() in market_lower for mt in market_types):
                filtered.append(pred)
        
        return filtered
    
    def get_summary_stats(self, analysis_result: Dict) -> Dict:
        """
        Get summary statistics for analysis result
        """
        predictions = analysis_result.get("predictions", [])
        
        if not predictions:
            return {
                "total_predictions": 0,
                "avg_confidence": 0.0,
                "top_confidence": 0.0,
                "total_kelly_stake": 0.0,
                "avg_ev": 0.0
            }
        
        confidences = [p["confidence"] for p in predictions]
        kelly_stakes = [p.get("kelly_stake", 0) for p in predictions]
        evs = [p.get("ev", 0) for p in predictions]
        
        return {
            "total_predictions": len(predictions),
            "avg_confidence": sum(confidences) / len(confidences),
            "top_confidence": max(confidences),
            "total_kelly_stake": sum(kelly_stakes),
            "avg_ev": sum(evs) / len(evs) if evs else 0.0,
            "weather_impact": analysis_result.get("weather_summary", {}).get("impact", "N/A"),
            "news_impact": analysis_result.get("news_summary", {})
        }


# Global instance
auto_analyzer = AutoMarketAnalyzer()

