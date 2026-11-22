"""Weather Forecast Agent - Provides agricultural weather intelligence."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services import weather_service_instance
from app.utils import logger


class WeatherAgent(BaseAgent):
    """
    Provides weather forecasts and agricultural advisories.
    Integrates with weather APIs to provide actionable farming recommendations.
    """

    def __init__(self):
        super().__init__(
            name="WeatherAgent",
            description="Provides weather forecasts and agricultural weather advisories"
        )

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        lat = context.get("latitude", 20.5937)  # Default: India center
        lon = context.get("longitude", 78.9629)
        crop = context.get("target_crop")

        # Get 7-day forecast
        forecast_data = weather_service_instance.get_forecast(lat, lon, days=7)
        state["weather_forecast"] = forecast_data

        # If crop specified, get sowing window
        if crop:
            sowing_window = weather_service_instance.get_sowing_window_from_forecast(
                crop,
                forecast_data,
            )
            state["sowing_plan"] = {
                "crop": crop,
                "recommended_sowing_dates": sowing_window.get("suitable_days", []),
                "weather_based_advisory": sowing_window.get("recommended_window", "")
            }

        # Generate overall weather advisory
        rainy_days = sum(1 for d in forecast_data["forecast"] if d["rainfall_mm"] > 5)
        hot_days = sum(1 for d in forecast_data["forecast"] if d["temp_max_c"] > 38)

        advisory = []
        if rainy_days >= 3:
            advisory.append(f"Expect {rainy_days} rainy days. Prepare drainage and avoid chemical spraying.")
        if hot_days >= 3:
            advisory.append(f"Heat wave expected ({hot_days} days). Increase irrigation, use mulching.")
        if not advisory:
            advisory.append("Weather conditions favorable for normal farming operations.")

        self._add_message(
            state,
            f"Weather forecast retrieved for next 7 days. Source: {forecast_data['source']}. {len(advisory)} advisory items generated.",
            {"rainy_days": rainy_days, "hot_days": hot_days, "location": forecast_data.get("location", "Unknown")},
            "high"
        )

        return state
