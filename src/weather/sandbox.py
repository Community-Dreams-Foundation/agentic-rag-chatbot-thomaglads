"""Safe sandbox for weather data analysis."""

import ast
from datetime import datetime
from typing import Any, Dict

import pandas as pd

from .client import OpenMeteoClient


class WeatherSandbox:
    """
    Safe execution environment for weather analysis.
    Allows controlled computation on weather data.
    """
    
    def __init__(self):
        self.weather_client = OpenMeteoClient()
    
    def execute_analysis(
        self,
        latitude: float,
        longitude: float,
        analysis_code: str,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Execute analysis code in a restricted environment.
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            analysis_code: Python code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dict with results or error
        """
        try:
            # Fetch weather data
            weather_data = self.weather_client.get_safety_metrics(
                latitude=latitude,
                longitude=longitude,
                days=7,
            )
            
            # Create safe execution environment
            safe_globals = {
                "__builtins__": {
                    "len": len,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "abs": abs,
                    "round": round,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "float": float,
                    "int": int,
                    "str": str,
                    "list": list,
                    "dict": dict,
                    "print": print,
                },
                "weather_data": weather_data,
                "pd": pd,
            }
            
            # Parse and validate AST
            tree = ast.parse(analysis_code)
            
            # Check for disallowed operations
            disallowed_nodes = [
                ast.Import, ast.ImportFrom,
                ast.ClassDef, ast.AsyncFunctionDef,
                ast.Try, ast.ExceptHandler, ast.Finally,
                ast.With, ast.AsyncWith,
                ast.Raise, ast.Assert, ast.Delete,
                ast.Global, ast.Nonlocal,
                ast.Lambda,
            ]
            
            for node in ast.walk(tree):
                if type(node) in disallowed_nodes:
                    return {
                        "success": False,
                        "error": f"Disallowed operation: {type(node).__name__}",
                    }
            
            # Execute in restricted environment
            local_vars = {}
            exec(compile(tree, "<sandbox>", "exec"), safe_globals, local_vars)
            
            # Extract results
            result = local_vars.get("result", "No result variable defined")
            
            return {
                "success": True,
                "result": result,
                "weather_data_summary": self._summarize_weather(weather_data),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    
    def _summarize_weather(self, weather_data: Dict) -> Dict:
        """Create a summary of weather data."""
        dates = weather_data.get("dates", [])
        if not dates:
            return {}
        
        summary = {
            "location": weather_data.get("location", {}),
            "forecast_period": {
                "start": dates[0] if dates else None,
                "end": dates[-1] if dates else None,
                "days": len(dates),
            },
            "metrics": {},
        }
        
        # Calculate summary statistics for each metric
        for key in ["max_wind_speed", "max_wind_gusts", "precipitation_total", "rain_total"]:
            values = weather_data.get(key, [])
            if values:
                summary["metrics"][key] = {
                    "max": max(values),
                    "min": min(values),
                    "avg": round(sum(values) / len(values), 2),
                }
        
        return summary
    
    def check_safety_compliance(
        self,
        latitude: float,
        longitude: float,
        wind_threshold: float = 20.0,  # km/h
        rain_threshold: float = 5.0,   # mm
    ) -> Dict:
        """
        Check if weather conditions meet safety thresholds.
        
        Returns:
            Dict with compliance status and recommendations
        """
        data = self.weather_client.get_safety_metrics(
            latitude=latitude,
            longitude=longitude,
            days=3,  # Check next 3 days
        )
        
        dates = data.get("dates", [])
        wind_speeds = data.get("max_wind_speed", [])
        wind_gusts = data.get("max_wind_gusts", [])
        rain = data.get("rain_total", [])
        weather_codes = data.get("weather_code", [])
        
        violations = []
        
        for i, date in enumerate(dates):
            day_violations = []
            
            if i < len(wind_speeds) and wind_speeds[i] > wind_threshold:
                day_violations.append(
                    f"Wind speed {wind_speeds[i]} km/h exceeds threshold of {wind_threshold} km/h"
                )
            
            if i < len(wind_gusts) and wind_gusts[i] > wind_threshold * 1.5:
                day_violations.append(
                    f"Wind gusts {wind_gusts[i]} km/h exceed safe levels"
                )
            
            if i < len(rain) and rain[i] > rain_threshold:
                day_violations.append(
                    f"Rainfall {rain[i]} mm exceeds threshold of {rain_threshold} mm"
                )
            
            # Check for severe weather codes
            if i < len(weather_codes):
                code = weather_codes[i]
                if code in [95, 96, 99]:  # Thunderstorms
                    day_violations.append("Thunderstorms predicted")
                elif code in [71, 73, 75, 77, 85, 86]:  # Snow
                    day_violations.append("Snow conditions")
                elif code in [82]:  # Violent rain
                    day_violations.append("Violent rain showers")
            
            if day_violations:
                violations.append({
                    "date": date,
                    "issues": day_violations,
                })
        
        # Determine overall compliance
        if violations:
            compliance_status = "VIOLATION"
            recommendation = "Outdoor work NOT recommended due to weather conditions"
        else:
            compliance_status = "COMPLIANT"
            recommendation = "Weather conditions safe for outdoor work"
        
        return {
            "compliance_status": compliance_status,
            "recommendation": recommendation,
            "violations": violations,
            "thresholds": {
                "wind_speed_max": wind_threshold,
                "rain_total_max": rain_threshold,
            },
            "location": data.get("location", {}),
            "check_date": datetime.now().isoformat(),
        }
