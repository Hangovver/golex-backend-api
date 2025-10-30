"""
GOLEX - Weather Service (OpenWeather API - Free Tier)
Provides weather data for match analysis
"""

import aiohttp
import os
from typing import Dict, Optional
from datetime import datetime

class WeatherService:
    """
    OpenWeather API Integration
    Free Tier: 1000 calls/day, 60 calls/minute
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            # Default free key (limited, user should add their own)
            self.api_key = "demo"  # User needs to register at openweathermap.org
    
    async def get_weather_by_coords(
        self, 
        lat: float, 
        lon: float
    ) -> Optional[Dict]:
        """
        Get weather data by coordinates
        
        Returns:
        {
            'temp': 18.5,
            'feels_like': 17.2,
            'humidity': 65,
            'wind_speed': 4.5,
            'wind_deg': 180,
            'pressure': 1013,
            'clouds': 40,
            'visibility': 10000,
            'weather': 'Clear',
            'weather_icon': '01d',
            'rain': 0.0,
            'snow': 0.0
        }
        """
        url = f"{self.BASE_URL}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"  # Celsius
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_weather(data)
                    else:
                        print(f"Weather API error: {resp.status}")
                        return None
        except Exception as e:
            print(f"Weather service error: {e}")
            return None
    
    async def get_weather_by_city(self, city: str) -> Optional[Dict]:
        """Get weather by city name"""
        url = f"{self.BASE_URL}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_weather(data)
                    else:
                        return None
        except Exception as e:
            print(f"Weather service error: {e}")
            return None
    
    async def get_forecast(
        self, 
        lat: float, 
        lon: float, 
        hours: int = 3
    ) -> Optional[Dict]:
        """
        Get weather forecast for next N hours
        Free tier: 5 days, 3-hour intervals
        """
        url = f"{self.BASE_URL}/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",
            "cnt": max(1, hours // 3)  # 3-hour intervals
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        forecasts = []
                        for item in data.get("list", []):
                            forecasts.append(self._parse_weather(item))
                        return {
                            "city": data.get("city", {}).get("name"),
                            "forecasts": forecasts
                        }
                    else:
                        return None
        except Exception as e:
            print(f"Forecast service error: {e}")
            return None
    
    def _parse_weather(self, data: Dict) -> Dict:
        """Parse OpenWeather API response"""
        main = data.get("main", {})
        wind = data.get("wind", {})
        clouds = data.get("clouds", {})
        rain = data.get("rain", {})
        snow = data.get("snow", {})
        weather = data.get("weather", [{}])[0]
        
        return {
            "temp": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "wind_deg": wind.get("deg"),
            "pressure": main.get("pressure"),
            "clouds": clouds.get("all", 0),
            "visibility": data.get("visibility", 10000),
            "weather": weather.get("main", "Clear"),
            "weather_description": weather.get("description", ""),
            "weather_icon": weather.get("icon", "01d"),
            "rain_1h": rain.get("1h", 0.0),
            "snow_1h": snow.get("1h", 0.0),
            "timestamp": data.get("dt", int(datetime.now().timestamp()))
        }
    
    def get_weather_impact(self, weather_data: Dict) -> Dict:
        """
        Analyze weather impact on match performance
        
        Returns:
        {
            'impact_score': 0.85,  # 0-1 (1=ideal conditions)
            'factors': {
                'temperature': 'good',
                'wind': 'moderate',
                'rain': 'heavy',
                'visibility': 'good'
            },
            'recommendation': 'Avoid long passes, expect fewer goals'
        }
        """
        if not weather_data:
            return {
                "impact_score": 1.0,
                "factors": {},
                "recommendation": "No weather data available"
            }
        
        impact_score = 1.0
        factors = {}
        recommendations = []
        
        # Temperature (ideal: 15-25°C)
        temp = weather_data.get("temp", 20)
        if temp < 5:
            impact_score -= 0.2
            factors["temperature"] = "very_cold"
            recommendations.append("Cold weather may reduce ball control")
        elif temp < 10:
            impact_score -= 0.1
            factors["temperature"] = "cold"
        elif temp > 35:
            impact_score -= 0.2
            factors["temperature"] = "very_hot"
            recommendations.append("Hot weather may reduce stamina")
        elif temp > 30:
            impact_score -= 0.1
            factors["temperature"] = "hot"
        else:
            factors["temperature"] = "good"
        
        # Wind (problematic if > 20 km/h)
        wind_speed = weather_data.get("wind_speed", 0) * 3.6  # m/s to km/h
        if wind_speed > 40:
            impact_score -= 0.3
            factors["wind"] = "very_strong"
            recommendations.append("Strong wind affects long passes and shots")
        elif wind_speed > 20:
            impact_score -= 0.15
            factors["wind"] = "strong"
            recommendations.append("Moderate wind may affect play")
        else:
            factors["wind"] = "calm"
        
        # Rain
        rain = weather_data.get("rain_1h", 0)
        if rain > 5:
            impact_score -= 0.3
            factors["rain"] = "heavy"
            recommendations.append("Heavy rain: slippery pitch, fewer goals expected")
        elif rain > 1:
            impact_score -= 0.15
            factors["rain"] = "moderate"
            recommendations.append("Wet conditions may affect ball control")
        else:
            factors["rain"] = "none"
        
        # Snow
        snow = weather_data.get("snow_1h", 0)
        if snow > 0:
            impact_score -= 0.4
            factors["snow"] = "snowing"
            recommendations.append("Snow: unpredictable ball movement")
        
        # Visibility
        visibility = weather_data.get("visibility", 10000)
        if visibility < 1000:
            impact_score -= 0.2
            factors["visibility"] = "poor"
            recommendations.append("Poor visibility may affect play quality")
        elif visibility < 5000:
            impact_score -= 0.1
            factors["visibility"] = "moderate"
        else:
            factors["visibility"] = "good"
        
        # Humidity (extreme humidity affects stamina)
        humidity = weather_data.get("humidity", 50)
        if humidity > 90:
            impact_score -= 0.1
            factors["humidity"] = "very_high"
        elif humidity < 20:
            impact_score -= 0.05
            factors["humidity"] = "very_low"
        else:
            factors["humidity"] = "normal"
        
        return {
            "impact_score": max(0.0, min(1.0, impact_score)),
            "factors": factors,
            "recommendation": " | ".join(recommendations) if recommendations else "Ideal conditions"
        }


# Global instance
weather_service = WeatherService()

