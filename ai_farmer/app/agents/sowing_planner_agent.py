"""Sowing Planner Agent - Determines optimal sowing schedule."""
from datetime import datetime, timedelta
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger, get_current_season
from app.services import weather_service_instance

class SowingPlannerAgent(BaseAgent):
    """Creates optimal sowing schedules based on crop, weather, soil temperature, and regional practices."""

    def __init__(self):
        super().__init__("SowingPlannerAgent", "Determines optimal sowing windows and schedules")
        self.sowing_calendar = self._load_sowing_calendar()

    def _load_sowing_calendar(self):
        return {
            "rice": {
                "kharif": {"north": "June 15 - July 15", "south": "May 15 - June 15", "east": "June 1 - July 1"},
                "soil_temp_c": "20-25", "seed_treatment": "Carbendazim + Streptocycline", "spacing": "20x15 cm"
            },
            "wheat": {
                "rabi": {"north": "Nov 1 - Nov 25", "central": "Oct 25 - Nov 15", "peninsula": "Nov 1 - Nov 20"},
                "soil_temp_c": "15-20", "seed_treatment": "Carbendazim 2g/kg seed", "spacing": "22.5 cm row"
            },
            "maize": {
                "kharif": {"north": "June 20 - July 10", "south": "May 20 - June 20"},
                "rabi": {"peninsula": "Oct 15 - Nov 15"},
                "soil_temp_c": "18-25", "seed_treatment": "Thiram 2g/kg", "spacing": "60x20 cm"
            },
            "cotton": {
                "kharif": {"north": "April 15 - May 15", "central": "May 1 - May 31", "south": "June 1 - July 15"},
                "soil_temp_c": "25-30", "seed_treatment": "Bavistin + Streptocycline", "spacing": "90x60 cm (hybrid), 60x30 cm (desi)"
            },
            "groundnut": {
                "kharif": {"north": "June 15 - July 15", "south": "June 1 - July 15"},
                "rabi": {"peninsula": "Nov 15 - Dec 15"},
                "soil_temp_c": "20-25", "seed_treatment": "Thiram 3g/kg + Rhizobium", "spacing": "30x10 cm"
            },
            "soybean": {
                "kharif": {"central": "June 15 - July 10", "south": "June 1 - July 1"},
                "soil_temp_c": "20-25", "seed_treatment": "Thiram + Carbendazim + Rhizobium", "spacing": "45x5 cm"
            },
            "potato": {
                "rabi": {"north": "Oct 15 - Nov 15", "hills": "Feb 15 - Mar 15"},
                "soil_temp_c": "15-20", "seed_treatment": "Mancozeb + Streptocycline", "spacing": "60x20 cm"
            },
            "tomato": {
                "kharif": {"all": "June - July"}, "rabi": {"all": "Oct - Nov"}, "zaid": {"all": "Jan - Feb"},
                "soil_temp_c": "20-25", "seed_treatment": "Hot water 50C for 25 min", "spacing": "60x45 cm"
            },
            "onion": {
                "kharif": {"all": "May - June"}, "rabi": {"all": "Oct - Nov"},
                "soil_temp_c": "15-25", "seed_treatment": "Carbendazim 2g/kg", "spacing": "15x10 cm"
            },
            "chickpea": {
                "rabi": {"north": "Oct 15 - Nov 15", "central": "Oct 20 - Nov 10"},
                "soil_temp_c": "15-20", "seed_treatment": "Thiram + Carbendazim + Rhizobium", "spacing": "30x10 cm"
            },
            "mustard": {
                "rabi": {"north": "Sept 25 - Oct 25", "central": "Oct 15 - Nov 15"},
                "soil_temp_c": "15-20", "seed_treatment": "Thiram 2g/kg", "spacing": "30x10 cm"
            },
            "turmeric": {
                "kharif": {"south": "May - June", "east": "April - May"},
                "soil_temp_c": "25-30", "seed_treatment": "Mancozeb 3g/kg + Quinalphos", "spacing": "45x15 cm"
            },
            "sugarcane": {
                "planting": {"north": "Feb - Mar", "south": "Dec - Jan", "east": "Oct - Nov"},
                "soil_temp_c": "20-25", "seed_treatment": "Hot water 52C for 30 min", "spacing": "90 cm row"
            },
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        crop = context.get("target_crop", "").lower()
        state_name = context.get("state", "").lower()
        season = context.get("season", get_current_season())
        lat = context.get("latitude")
        lon = context.get("longitude")

        plan = {
            "crop": crop.title() if crop else "Not specified",
            "season": season,
            "recommended_sowing_window": "",
            "soil_temperature_required": "",
            "seed_treatment": "",
            "spacing": "",
            "step_by_step_plan": [],
            "weather_based_adjustment": "",
            "pre_sowing_operations": []
        }

        if crop in self.sowing_calendar:
            cal = self.sowing_calendar[crop]
            plan["soil_temperature_required"] = cal.get("soil_temp_c", "N/A")
            plan["seed_treatment"] = cal.get("seed_treatment", "Standard treatment")
            plan["spacing"] = cal.get("spacing", "As per package of practices")

            # Determine region
            region = self._get_region(state_name)
            season_data = cal.get(season, cal.get("planting", {}))

            if season_data:
                window = season_data.get(region, season_data.get("all", "Consult local KVK"))
                plan["recommended_sowing_window"] = window

            # Weather-based adjustment
            if lat and lon:
                sowing_data = weather_service_instance.get_sowing_window(crop, lat, lon)
                plan["weather_based_adjustment"] = sowing_data.get("recommended_window", "")
                plan["suitable_dates_next_14_days"] = [d["date"] for d in sowing_data.get("suitable_days", [])[:5]]

            # Step-by-step plan
            plan["step_by_step_plan"] = self._generate_sowing_steps(crop, season)
            plan["pre_sowing_operations"] = self._get_pre_sowing_ops(crop, context.get("soil_type", "loamy"))

        state["sowing_plan"] = plan
        self._add_message(state, f"Sowing plan created for {crop}. Window: {plan['recommended_sowing_window']}", {"window": plan["recommended_sowing_window"]}, "high")
        return state

    def _get_region(self, state: str) -> str:
        north = ["punjab", "haryana", "himachal pradesh", "uttarakhand", "uttar pradesh", "bihar", "jharkhand", "rajasthan"]
        central = ["madhya pradesh", "chhattisgarh"]
        south = ["karnataka", "tamil nadu", "andhra pradesh", "telangana", "kerala"]
        east = ["west bengal", "odisha", "assam", "tripura", "meghalaya", "manipur", "nagaland", "mizoram"]
        peninsula = ["gujarat", "maharashtra", "goa"]
        hills = ["jammu and kashmir", "ladakh", "himachal pradesh", "uttarakhand", "northeast"]

        if state in north: return "north"
        if state in central: return "central"
        if state in south: return "south"
        if state in east: return "east"
        if state in peninsula: return "peninsula"
        if state in hills: return "hills"
        return "all"

    def _generate_sowing_steps(self, crop: str, season: str) -> list:
        return [
            f"1. Land Preparation: 2-3 ploughings followed by planking to achieve fine tilth",
            f"2. Seed Treatment: Treat seeds with recommended fungicide/insecticide",
            f"3. Fertilizer Application: Apply basal dose of NPK as per soil test",
            f"4. Sowing: Sow at recommended spacing and depth",
            f"5. First Irrigation: Light irrigation immediately after sowing (if not rainfed)",
            f"6. Weed Management: First weeding at 20-25 DAS",
            f"7. Top Dressing: Split application of nitrogen as per crop stage"
        ]

    def _get_pre_sowing_ops(self, crop: str, soil_type: str) -> list:
        ops = ["Deep ploughing (15-20 cm)", "Leveling the field", "Soil testing"]
        if soil_type in ["sandy", "desert"]:
            ops.append("Add organic matter/FYM (10 tonnes/acre)")
        if crop in ["rice", "sugarcane"]:
            ops.append("Field bunding and leveling for water retention")
        if crop in ["potato", "turmeric"]:
            ops.append("Ridge and furrow preparation")
        return ops
