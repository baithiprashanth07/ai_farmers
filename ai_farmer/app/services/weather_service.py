"""Weather intelligence service for AI Farmer."""
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import get_settings
from app.utils import logger

settings = get_settings()


class WeatherService:
    """Provides weather forecasts and agricultural weather advisories."""

    def __init__(self):
        self.api_key = settings.weather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.mock_mode = self.api_key is None or self.api_key == "your_weather_api_key_here"

    def get_forecast(self, lat: float, lon: float, days: int = 7) -> Dict[str, Any]:
        """Get weather forecast for farm location."""
        if self.mock_mode:
            try:
                return self._get_open_meteo_forecast(lat, lon, days)
            except (requests.RequestException, KeyError, TypeError, ValueError) as error:
                logger.warning(
                    "Open-Meteo forecast lookup failed ({}); using clearly marked sample weather.",
                    type(error).__name__,
                )
                forecast = self._generate_mock_forecast(days)
                forecast["location"] = "Forecast unavailable"
                return forecast

        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric",
                "cnt": days * 8  # 3-hour intervals
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return self._parse_forecast(response.json())
        except Exception as e:
            logger.error(
                "OpenWeatherMap request failed ({}); falling back to Open-Meteo.",
                type(e).__name__,
            )
            try:
                return self._get_open_meteo_forecast(lat, lon, days)
            except (requests.RequestException, KeyError, TypeError, ValueError) as fallback_error:
                logger.warning(
                    "Open-Meteo forecast lookup also failed ({}); using clearly marked sample weather.",
                    type(fallback_error).__name__,
                )
            forecast = self._generate_mock_forecast(days)
            forecast["location"] = "Forecast unavailable"
            return forecast

    def _get_open_meteo_forecast(self, lat: float, lon: float, days: int) -> Dict[str, Any]:
        """Fetch a location-specific forecast from the free Open-Meteo API."""
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": (
                    "temperature_2m_max,temperature_2m_min,precipitation_probability_max,"
                    "precipitation_sum,wind_speed_10m_max,weather_code"
                ),
                "timezone": "auto",
                "forecast_days": min(max(days, 1), 16),
            },
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
        daily = data["daily"]
        forecast = []
        for index, forecast_date in enumerate(daily["time"]):
            condition = self._open_meteo_condition(daily["weather_code"][index])
            rainfall = daily["precipitation_sum"][index] or 0
            temperature = daily["temperature_2m_max"][index]
            forecast.append({
                "date": forecast_date,
                "temp_max_c": round(temperature, 1),
                "temp_min_c": round(daily["temperature_2m_min"][index], 1),
                "humidity_percent": None,
                "rainfall_probability_percent": daily["precipitation_probability_max"][index],
                "rainfall_mm": round(rainfall, 1),
                "wind_speed_kmh": round(daily["wind_speed_10m_max"][index], 1),
                "condition": condition,
                "advisory": self._generate_advisory(condition, rainfall, temperature),
            })
        return {
            "forecast": forecast,
            "source": "open-meteo",
            "location": "Selected farm location",
            "coordinates": {"latitude": lat, "longitude": lon},
        }

    @staticmethod
    def _open_meteo_condition(code: int) -> str:
        if code == 0:
            return "Clear"
        if code in {1, 2}:
            return "Partly cloudy"
        if code == 3:
            return "Clouds"
        if code in {45, 48}:
            return "Fog"
        if code in {51, 53, 55, 56, 57}:
            return "Drizzle"
        if code in {61, 63, 65, 66, 67, 80, 81, 82}:
            return "Rain"
        if code in {71, 73, 75, 77, 85, 86}:
            return "Snow"
        if code in {95, 96, 99}:
            return "Thunderstorm"
        return "Unknown"

    def _parse_forecast(self, data: Dict) -> Dict[str, Any]:
        """Parse OpenWeatherMap forecast response."""
        daily = {}
        for item in data.get("list", []):
            date = item["dt_txt"].split()[0]
            if date not in daily:
                daily[date] = {
                    "temps": [], "humidity": [], "rain": 0,
                    "wind": [], "conditions": []
                }
            daily[date]["temps"].append(item["main"]["temp"])
            daily[date]["humidity"].append(item["main"]["humidity"])
            daily[date]["wind"].append(item["wind"]["speed"])
            daily[date]["conditions"].append(item["weather"][0]["main"])
            if "rain" in item:
                daily[date]["rain"] += item["rain"].get("3h", 0)

        forecast = []
        for date, vals in sorted(daily.items())[:7]:
            condition = max(set(vals["conditions"]), key=vals["conditions"].count)
            advisory = self._generate_advisory(condition, vals["rain"], max(vals["temps"]))
            forecast.append({
                "date": date,
                "temp_max_c": round(max(vals["temps"]), 1),
                "temp_min_c": round(min(vals["temps"]), 1),
                "humidity_percent": round(sum(vals["humidity"]) / len(vals["humidity"]), 1),
                "rainfall_mm": round(vals["rain"], 1),
                "wind_speed_kmh": round(max(vals["wind"]) * 3.6, 1),
                "condition": condition,
                "advisory": advisory
            })

        return {"forecast": forecast, "source": "openweathermap", "location": data.get("city", {}).get("name", "Unknown")}

    def _generate_mock_forecast(self, days: int) -> Dict[str, Any]:
        """Generate realistic mock weather data for India."""
        import random
        forecast = []
        base_date = datetime.now()
        conditions = ["Clear", "Clouds", "Rain", "Thunderstorm", "Haze"]

        for i in range(days):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            condition = random.choices(conditions, weights=[30, 35, 20, 5, 10])[0]
            temp_max = random.uniform(28, 42)
            temp_min = temp_max - random.uniform(8, 15)
            rainfall = random.uniform(0, 25) if condition in ["Rain", "Thunderstorm"] else 0

            advisory = self._generate_advisory(condition, rainfall, temp_max)

            forecast.append({
                "date": date,
                "temp_max_c": round(temp_max, 1),
                "temp_min_c": round(temp_min, 1),
                "humidity_percent": round(random.uniform(40, 85), 1),
                "rainfall_mm": round(rainfall, 1),
                "wind_speed_kmh": round(random.uniform(5, 25), 1),
                "condition": condition,
                "advisory": advisory
            })

        return {"forecast": forecast, "source": "mock", "location": "Farm Location"}

    def _generate_advisory(self, condition: str, rainfall: float, temp_max: float) -> str:
        """Generate agricultural advisory based on weather."""
        advisories = []
        if condition in ["Rain", "Thunderstorm"]:
            advisories.append("Heavy rainfall expected. Avoid spraying pesticides. Ensure proper drainage.")
        if rainfall == 0 and temp_max > 35:
            advisories.append("High temperature with no rain. Increase irrigation frequency. Mulch soil to retain moisture.")
        if temp_max < 20:
            advisories.append("Low temperatures detected. Protect sensitive crops with covers.")
        if condition == "Clear" and 25 <= temp_max <= 35:
            advisories.append("Ideal weather for field operations. Good time for sowing or harvesting.")
        if not advisories:
            advisories.append("Normal weather conditions. Continue regular farming activities.")
        return " ".join(advisories)

    def get_sowing_window(self, crop: str, lat: float, lon: float) -> Dict[str, Any]:
        """Determine optimal sowing window based on weather forecast."""
        forecast = self.get_forecast(lat, lon, 14)
        return self.get_sowing_window_from_forecast(crop, forecast)

    def get_sowing_window_from_forecast(
        self,
        crop: str,
        forecast: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate sowing suitability using an already-fetched forecast."""
        suitable_days = []

        for day in forecast.get("forecast", []):
            score = 100
            if day["rainfall_mm"] > 15:
                score -= 40
            elif day["rainfall_mm"] > 5:
                score -= 15
            if day["temp_max_c"] > 40:
                score -= 30
            if day["temp_min_c"] < 15:
                score -= 20
            if day["condition"] in ["Thunderstorm"]:
                score -= 25

            if score >= 70:
                suitable_days.append({"date": day["date"], "suitability_score": score})

        return {
            "crop": crop,
            "suitable_days": suitable_days[:5],
            "recommended_window": suitable_days[0]["date"] if suitable_days else "Wait for better conditions",
            "forecast_summary": forecast,
        }


weather_service_instance = WeatherService()
