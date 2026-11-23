"""Farm location lookup using the Open-Meteo geocoding service."""
from typing import Any, Dict, List, Optional

import httpx

from app.utils import logger


class LocationService:
    """Resolve farmer-entered place names to useful farm map coordinates."""

    def search(
        self,
        query: str,
        limit: int = 6,
        state: Optional[str] = None,
        district: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cleaned_query = query.strip()
        if len(cleaned_query) < 2:
            return []
        query_parts = []
        seen_parts = set()
        for part in (cleaned_query, district or "", state or ""):
            normalized = part.strip().casefold()
            if normalized and normalized not in seen_parts:
                seen_parts.add(normalized)
                query_parts.append(part.strip())
        contextual_query = ", ".join(query_parts)

        try:
            response = httpx.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": contextual_query,
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
            result_state = result.get("admin1") or ""
            if (
                state
                and result_state
                and result_state.strip().casefold() != state.strip().casefold()
            ):
                continue
            locations.append({
                "name": result.get("name", ""),
                "district": result.get("admin2") or result.get("name", ""),
                "state": result_state,
                "country": result.get("country", ""),
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "timezone": result.get("timezone"),
            })
        return locations


location_service = LocationService()
