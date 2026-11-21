"""Crop Recommendation Agent - Recommends optimal crops based on farm conditions."""
import random
from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger, get_current_season, get_state_soil_types, get_crop_seasonality, estimate_crop_yield
from app.services import soil_service_instance
from app.services.agriculture_reference import get_state_crop_reference


class CropRecommendationAgent(BaseAgent):
    """
    Recommends the best crops for a given farm based on:
    - Location (state/district)
    - Soil type
    - Season
    - Water availability
    - Market demand
    """

    def __init__(self):
        super().__init__(
            name="CropRecommendationAgent",
            description="Recommends optimal crops based on farm conditions and market trends"
        )
        self.crop_database = self._load_crop_database()

    def _load_crop_database(self) -> Dict[str, Any]:
        """Load comprehensive crop database."""
        return {
            "rice": {
                "water_requirement": "high", "soil": ["alluvial", "clayey", "loamy"],
                "season": ["kharif"], "duration_days": 120, "market_demand": "high",
                "cost_per_acre": 25000, "msp_inr_per_quintal": 2183
            },
            "wheat": {
                "water_requirement": "medium", "soil": ["alluvial", "loamy", "clayey"],
                "season": ["rabi"], "duration_days": 140, "market_demand": "high",
                "cost_per_acre": 20000, "msp_inr_per_quintal": 2275
            },
            "maize": {
                "water_requirement": "medium", "soil": ["alluvial", "loamy", "red"],
                "season": ["kharif", "rabi"], "duration_days": 100, "market_demand": "medium",
                "cost_per_acre": 18000, "msp_inr_per_quintal": 2090
            },
            "cotton": {
                "water_requirement": "medium", "soil": ["black", "alluvial", "loamy"],
                "season": ["kharif"], "duration_days": 180, "market_demand": "high",
                "cost_per_acre": 35000, "msp_inr_per_quintal": 6620
            },
            "sugarcane": {
                "water_requirement": "high", "soil": ["alluvial", "black", "loamy"],
                "season": ["year_round"], "duration_days": 365, "market_demand": "high",
                "cost_per_acre": 60000, "msp_inr_per_quintal": 340
            },
            "groundnut": {
                "water_requirement": "low", "soil": ["red", "sandy", "loamy"],
                "season": ["kharif", "rabi"], "duration_days": 110, "market_demand": "high",
                "cost_per_acre": 22000, "msp_inr_per_quintal": 6377
            },
            "soybean": {
                "water_requirement": "medium", "soil": ["black", "alluvial"],
                "season": ["kharif"], "duration_days": 100, "market_demand": "medium",
                "cost_per_acre": 15000, "msp_inr_per_quintal": 4600
            },
            "potato": {
                "water_requirement": "medium", "soil": ["alluvial", "loamy", "sandy"],
                "season": ["rabi", "zaid"], "duration_days": 90, "market_demand": "high",
                "cost_per_acre": 40000, "msp_inr_per_quintal": 1200
            },
            "tomato": {
                "water_requirement": "medium", "soil": ["loamy", "alluvial", "sandy"],
                "season": ["year_round"], "duration_days": 90, "market_demand": "high",
                "cost_per_acre": 35000, "msp_inr_per_quintal": 2500
            },
            "onion": {
                "water_requirement": "medium", "soil": ["loamy", "alluvial", "sandy"],
                "season": ["rabi", "kharif"], "duration_days": 120, "market_demand": "high",
                "cost_per_acre": 30000, "msp_inr_per_quintal": 1800
            },
            "chickpea": {
                "water_requirement": "low", "soil": ["black", "alluvial", "loamy"],
                "season": ["rabi"], "duration_days": 110, "market_demand": "high",
                "cost_per_acre": 12000, "msp_inr_per_quintal": 5440
            },
            "mustard": {
                "water_requirement": "low", "soil": ["alluvial", "loamy", "sandy"],
                "season": ["rabi"], "duration_days": 120, "market_demand": "medium",
                "cost_per_acre": 14000, "msp_inr_per_quintal": 5450
            },
            "turmeric": {
                "water_requirement": "medium", "soil": ["red", "alluvial", "loamy"],
                "season": ["kharif"], "duration_days": 270, "market_demand": "high",
                "cost_per_acre": 45000, "msp_inr_per_quintal": 9000
            },
            "banana": {
                "water_requirement": "high", "soil": ["alluvial", "loamy", "laterite"],
                "season": ["year_round"], "duration_days": 365, "market_demand": "high",
                "cost_per_acre": 80000, "msp_inr_per_quintal": 2200
            },
            "mango": {
                "water_requirement": "medium", "soil": ["alluvial", "loamy", "laterite"],
                "season": ["year_round"], "duration_days": 1095, "market_demand": "high",
                "cost_per_acre": 50000, "msp_inr_per_quintal": 4500
            }
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        state_name = context.get("state", "").lower()
        district = context.get("district", "").lower()
        soil_type = context.get("soil_type", "")
        season = context.get("season", get_current_season())
        irrigation = context.get("irrigation_type", "flood")
        farm_size = context.get("farm_size_acres", 1)
        region = get_state_crop_reference(context.get("state", ""))
        regional_crops = {
            crop.casefold()
            for crop in region["major_crops"]
        } if region else set()

        if not soil_type:
            soil_types = get_state_soil_types(state_name)
            soil_type = soil_types[0] if soil_types else "alluvial"

        recommendations = []

        for crop_name, crop_info in self.crop_database.items():
            score = 0
            reasons = []

            if crop_name.casefold() in regional_crops:
                score += 12
                reasons.append(f"Commonly grown in {region['name']}")

            # Season match
            if season in crop_info["season"] or "year_round" in crop_info["season"]:
                score += 30
                reasons.append(f"Suitable for {season} season")

            # Soil match
            if soil_type.lower() in [s.lower() for s in crop_info["soil"]]:
                score += 25
                reasons.append(f"Compatible with {soil_type} soil")
            else:
                score -= 10

            # Water requirement vs irrigation
            if crop_info["water_requirement"] == "low" and irrigation in ["rainfed", "drip"]:
                score += 20
                reasons.append("Low water requirement matches available irrigation")
            elif crop_info["water_requirement"] == "high" and irrigation in ["flood", "sprinkler", "drip"]:
                score += 15
                reasons.append("Adequate water availability")
            elif crop_info["water_requirement"] == "medium":
                score += 18
                reasons.append("Moderate water needs manageable")

            # Market demand
            if crop_info["market_demand"] == "high":
                score += 15
                reasons.append("High market demand ensures good price")

            # Farm size suitability
            if farm_size < 2 and crop_info["duration_days"] < 120:
                score += 10
                reasons.append("Quick turnover suitable for small farms")

            if score > 40:
                expected_yield = estimate_crop_yield(crop_name, soil_type, irrigation)
                revenue = expected_yield * crop_info["msp_inr_per_quintal"]
                profit = revenue - crop_info["cost_per_acre"]

                recommendations.append({
                    "crop_name": crop_name.title(),
                    "confidence_score": round(min(score / 100, 0.98), 2),
                    "expected_yield_quintal_per_acre": expected_yield,
                    "market_demand": crop_info["market_demand"],
                    "water_requirement": crop_info["water_requirement"],
                    "suitable_soil": crop_info["soil"],
                    "season": ", ".join(crop_info["season"]),
                    "estimated_cost_per_acre": crop_info["cost_per_acre"],
                    "estimated_revenue_per_acre": round(revenue, 2),
                    "estimated_profit_per_acre": round(profit, 2),
                    "duration_days": crop_info["duration_days"],
                    "reasoning": "; ".join(reasons)
                })

        recommendations.sort(key=lambda x: x["confidence_score"], reverse=True)
        state["crop_recommendations"] = recommendations[:5]

        self._add_message(
            state,
            f"Analyzed {len(self.crop_database)} crops for {state_name.title()}. Top recommendation: {recommendations[0]['crop_name'] if recommendations else 'None'}.",
            {"top_crop": recommendations[0]["crop_name"] if recommendations else None, "total_analyzed": len(self.crop_database)},
            "high"
        )

        return state
