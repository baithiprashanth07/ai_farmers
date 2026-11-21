"""Farm location lookup using the Open-Meteo geocoding service."""
from typing import Any, Dict, List

import httpx

from app.utils import logger


class LocationService:
    """Resolve farmer-entered place names to useful farm map coordinates."""

    def search(self, query: str, limit: int = 6) -> List[Dict[str, Any]]:
        cleaned_query = query.strip()
        if len(cleaned_query) < 2:
            return []

        try:
            response = httpx.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": cleaned_query,
                    "count": min(max(limit, 1), 10),
                    "language": "en",
                    "format": "json",
                    "countryCode": "IN",
                },
                timeout=httpx.Timeout(8.0, connect=3.0),
            )
            response.raise_for_status()
            results = response.json().get("results", [])
        except (httpx.HTTPError, ValueError) as error:
            logger.warning(
                "Farm location lookup failed ({}).",
                type(error).__name__,
            )
            return []

        locations = []
        for result in results:
            if not isinstance(result, dict):
                continue
            locations.append({
                "name": result.get("name", ""),
                "district": result.get("admin2") or result.get("name", ""),
                "state": result.get("admin1") or "",
                "country": result.get("country", ""),
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "timezone": result.get("timezone"),
            })
        return locations


location_service = LocationService()
