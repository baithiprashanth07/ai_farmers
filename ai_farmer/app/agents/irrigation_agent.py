"""Irrigation Planner Agent - Optimizes water usage and irrigation schedules."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger


class IrrigationPlannerAgent(BaseAgent):
    """
    Creates irrigation schedules based on:
    - Crop water requirements
    - Weather forecast
    - Soil type and moisture retention
    - Irrigation system type
    """

    def __init__(self):
        super().__init__(
            name="IrrigationPlannerAgent",
            description="Optimizes irrigation schedules and water usage"
        )

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        crop = context.get("target_crop", "general").lower()
        soil_type = context.get("soil_type", "loamy").lower()
        irrigation_type = context.get("irrigation_type", "flood")
        weather = state.get("weather_forecast", {})

        # Crop water requirements (mm per growth stage)
        water_needs = {
            "rice": {"total": 1200, "frequency": "Daily flooding", "critical_stages": ["Tillering", "Flowering", "Grain filling"]},
            "wheat": {"total": 450, "frequency": "Every 7-10 days", "critical_stages": ["Crown root initiation", "Flowering", "Grain filling"]},
            "cotton": {"total": 700, "frequency": "Every 10-12 days", "critical_stages": ["Square formation", "Flowering", "Boll development"]},
            "sugarcane": {"total": 1500, "frequency": "Every 10-15 days", "critical_stages": ["Germination", "Tillering", "Grand growth"]},
            "maize": {"total": 500, "frequency": "Every 7-10 days", "critical_stages": ["Knee-high stage", "Tasseling", "Silking"]},
            "tomato": {"total": 600, "frequency": "Every 5-7 days", "critical_stages": ["Flowering", "Fruit set", "Fruit development"]},
            "potato": {"total": 500, "frequency": "Every 7-10 days", "critical_stages": ["Tuber initiation", "Tuber bulking"]},
            "default": {"total": 500, "frequency": "Every 7-10 days", "critical_stages": ["Flowering", "Fruit/Grain development"]}
        }

        crop_water = water_needs.get(crop, water_needs["default"])

        # Adjust for soil type
        soil_multiplier = {"sandy": 1.3, "loamy": 1.0, "clayey": 0.85, "black": 0.9, "alluvial": 0.95, "red": 1.1}
        multiplier = soil_multiplier.get(soil_type, 1.0)
        adjusted_total = crop_water["total"] * multiplier

        # Adjust for irrigation efficiency
        efficiency = {"drip": 0.9, "sprinkler": 0.75, "flood": 0.5, "rainfed": 0.0, "subsurface": 0.85}
        irr_eff = efficiency.get(irrigation_type, 0.5)

        # Generate schedule
        schedule = []
        if irrigation_type == "rainfed":
            schedule.append({
                "stage": "Full season",
                "irrigation_type": "Rainfed",
                "water_mm": "Dependent on rainfall",
                "frequency": "Monitor soil moisture",
                "advisory": "Install rain gauge. Consider supplemental irrigation during dry spells."
            })
        else:
            stages = crop_water["critical_stages"]
            water_per_stage = adjusted_total / len(stages)

            for i, stage in enumerate(stages):
                schedule.append({
                    "stage": stage,
                    "irrigation_type": irrigation_type.title(),
                    "water_mm_per_application": round(water_per_stage * 0.3, 1),
                    "frequency": crop_water["frequency"],
                    "duration_hours": round((water_per_stage * 0.3 * 4.05) / (15 if irrigation_type == "drip" else 25 if irrigation_type == "sprinkler" else 50), 1),
                    "advisory": f"Critical stage - maintain adequate moisture. Do not allow water stress."
                })

        # Weather-based adjustments
        weather_adjustments = []
        if weather and "forecast" in weather:
            rainy_days = [d for d in weather["forecast"] if d["rainfall_mm"] > 5]
            if rainy_days:
                weather_adjustments.append(f"Skip irrigation on {len(rainy_days)} rainy days: {', '.join([d['date'] for d in rainy_days[:3]])}")
            hot_days = [d for d in weather["forecast"] if d["temp_max_c"] > 38]
            if hot_days:
                weather_adjustments.append(f"Increase irrigation frequency during {len(hot_days)} hot days. Irrigate early morning or evening.")

        state["irrigation_plan"] = {
            "crop": crop,
            "total_water_requirement_mm": round(adjusted_total, 1),
            "irrigation_system": irrigation_type,
            "system_efficiency": f"{irr_eff*100:.0f}%",
            "schedule": schedule,
            "weather_adjustments": weather_adjustments,
            "water_saving_tips": [
                "Use mulch to reduce evaporation" if irrigation_type != "drip" else "Drip irrigation already optimal for water saving",
                "Irrigate during early morning or late evening",
                "Monitor soil moisture before irrigation",
                "Adopt furrow irrigation instead of flood where possible"
            ]
        }

        self._add_message(
            state,
            f"Irrigation plan created for {crop}. Total water need: {round(adjusted_total, 1)}mm. System efficiency: {irr_eff*100:.0f}%.",
            {"water_mm": round(adjusted_total, 1), "efficiency": irr_eff},
            "medium"
        )

        return state
