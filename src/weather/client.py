"""Open-Meteo API client for weather data."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


class OpenMeteoClient:
    """
    Client for Open-Meteo API (no API key required).
    https://open-meteo.com/
    """
    
    BASE_URL = "https://api.open-meteo.com/v1"
    
    def __init__(self):
        self.session = requests.Session()
    
    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7,
        hourly: bool = True,
        daily: bool = True,
    ) -> Dict:
        """
        Get weather forecast for a location.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of forecast days
            hourly: Include hourly data
            daily: Include daily aggregates
            
        Returns:
            Weather data dictionary
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
        }
        
        # Set forecast range
        today = datetime.now().date()
        end_date = today + timedelta(days=days)
        params["start_date"] = today.isoformat()
        params["end_date"] = end_date.isoformat()
        
        # Weather variables for construction safety
        hourly_vars = [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "wind_speed_10m",
            "wind_speed_80m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ]
        
        daily_vars = [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum",
            "showers_sum",
            "snowfall_sum",
            "precipitation_hours",
            "weather_code",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
        ]
        
        if hourly:
            params["hourly"] = ",".join(hourly_vars)
        if daily:
            params["daily"] = ",".join(daily_vars)
        
        response = self.session.get(
            f"{self.BASE_URL}/forecast",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_current_weather(
        self,
        latitude: float,
        longitude: float,
    ) -> Dict:
        """Get current weather conditions."""
        data = self.get_forecast(
            latitude=latitude,
            longitude=longitude,
            days=1,
            hourly=True,
            daily=False,
        )
        
        # Extract current hour data
        current_hour = datetime.now().hour
        hourly = data.get("hourly", {})
        
        current = {}
        for key, values in hourly.items():
            if isinstance(values, list) and len(values) > current_hour:
                current[key] = values[current_hour]
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": data.get("timezone"),
            "current": current,
        }
    
    def get_safety_metrics(
        self,
        latitude: float,
        longitude: float,
        days: int = 1,
    ) -> Dict:
        """
        Get weather metrics relevant to construction safety.
        
        Returns:
            Dict with max wind speed, precipitation, etc.
        """
        data = self.get_forecast(
            latitude=latitude,
            longitude=longitude,
            days=days,
            hourly=False,
            daily=True,
        )
        
        daily = data.get("daily", {})
        
        # Extract key safety metrics
        metrics = {
            "location": {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "timezone": data.get("timezone"),
            },
            "dates": daily.get("time", []),
            "max_wind_speed": daily.get("wind_speed_10m_max", []),
            "max_wind_gusts": daily.get("wind_gusts_10m_max", []),
            "precipitation_total": daily.get("precipitation_sum", []),
            "rain_total": daily.get("rain_sum", []),
            "max_temperature": daily.get("temperature_2m_max", []),
            "min_temperature": daily.get("temperature_2m_min", []),
            "weather_code": daily.get("weather_code", []),
        }
        
        return metrics
    
    @staticmethod
    def weather_code_description(code: int) -> str:
        """Get description for WMO weather code."""
        codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail",
        }
        return codes.get(code, "Unknown")
    
    def geocode_location(self, location_name: str) -> Optional[Dict]:
        """
        Geocode a location name to coordinates.
        Uses Open-Meteo Geocoding API.
        Tries multiple query variations for robustness.
        """
        url = "https://geocoding-api.open-meteo.com/v1/search"

        # Build a list of query variations to try in order
        queries = [location_name]

        # If it has a comma, also try just the part before the comma
        if "," in location_name:
            queries.append(location_name.split(",")[0].strip())

        # If it has a space (e.g. "Boston MA"), also try just the first word
        parts = location_name.split()
        if len(parts) > 1:
            queries.append(parts[0])

        # Also try removing common site prefixes like "Site Alpha -"
        import re
        cleaned = re.sub(r'^(site\s+\w+\s*[-–]?\s*)', '', location_name, flags=re.IGNORECASE).strip()
        if cleaned and cleaned != location_name:
            queries.append(cleaned)

        for query in queries:
            if not query:
                continue
            params = {
                "name": query,
                "count": 1,
                "language": "en",
                "format": "json",
            }
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])

                if results:
                    result = results[0]
                    return {
                        "name": result.get("name"),
                        "latitude": result.get("latitude"),
                        "longitude": result.get("longitude"),
                        "country": result.get("country"),
                        "admin1": result.get("admin1"),  # State/Province
                    }
            except Exception:
                continue

        return None
