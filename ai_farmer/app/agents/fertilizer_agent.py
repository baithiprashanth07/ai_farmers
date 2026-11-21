"""Fertilizer Planner Agent - Recommends optimal fertilizer plans."""
from copy import deepcopy
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger


class FertilizerPlannerAgent(BaseAgent):
    """
    Creates customized fertilizer plans based on:
    - Crop type
    - Soil health report
    - Growth stage
    - Budget constraints
    """

    def __init__(self):
        super().__init__(
            name="FertilizerPlannerAgent",
            description="Creates customized fertilizer and nutrient management plans"
        )
        self.fertilizer_database = self._load_fertilizer_database()

    def _load_fertilizer_database(self) -> dict:
        return {
            "rice": {
                "basal": [{"name": "DAP", "qty_kg_per_acre": 50, "timing": "At sowing", "method": "Broadcast and incorporate"}],
                "top_dress": [
                    {"name": "Urea", "qty_kg_per_acre": 60, "timing": "30 DAS", "method": "Broadcast in standing water"},
                    {"name": "Urea", "qty_kg_per_acre": 40, "timing": "60 DAS", "method": "Broadcast in standing water"}
                ],
                "micronutrient": [{"name": "Zinc Sulfate", "qty_kg_per_acre": 10, "timing": "Basal", "method": "Soil application"}]
            },
            "wheat": {
                "basal": [{"name": "DAP", "qty_kg_per_acre": 55, "timing": "At sowing", "method": "Drill placement"}],
                "top_dress": [
                    {"name": "Urea", "qty_kg_per_acre": 55, "timing": "First irrigation (21 DAS)", "method": "Broadcast"},
                    {"name": "Urea", "qty_kg_per_acre": 30, "timing": "Second irrigation (45 DAS)", "method": "Broadcast"}
                ],
                "micronutrient": [{"name": "Boron", "qty_kg_per_acre": 2, "timing": "Flowering stage", "method": "Foliar spray"}]
            },
            "cotton": {
                "basal": [{"name": "DAP", "qty_kg_per_acre": 50, "timing": "At sowing", "method": "Band placement"}],
                "top_dress": [
                    {"name": "Urea", "qty_kg_per_acre": 50, "timing": "Square formation", "method": "Side dressing"},
                    {"name": "MOP", "qty_kg_per_acre": 25, "timing": "Flowering", "method": "Side dressing"}
                ],
                "micronutrient": [{"name": "Ferrous Sulfate", "qty_kg_per_acre": 5, "timing": "Vegetative stage", "method": "Foliar spray"}]
            },
            "default": {
                "basal": [{"name": "NPK 12:32:16", "qty_kg_per_acre": 100, "timing": "At sowing", "method": "Broadcast and mix"}],
                "top_dress": [
                    {"name": "Urea", "qty_kg_per_acre": 50, "timing": "30 days after sowing", "method": "Broadcast"}
                ],
                "micronutrient": [{"name": "Micronutrient Mixture", "qty_kg_per_acre": 10, "timing": "Vegetative stage", "method": "Soil application"}]
            }
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        crop = context.get("target_crop", "default").lower()
        soil_report = state.get("soil_health_report", {})

        plan = deepcopy(self.fertilizer_database.get(crop, self.fertilizer_database["default"]))

        # Adjust based on soil deficiencies
        if soil_report:
            deficiencies = soil_report.get("deficiencies", [])
            for deficiency in deficiencies:
                if "Nitrogen" in deficiency:
                    plan["top_dress"][0]["qty_kg_per_acre"] += 20
                if "Phosphorus" in deficiency:
                    plan["basal"][0]["qty_kg_per_acre"] += 15
                if "Potassium" in deficiency:
                    plan["top_dress"].append({
                        "name": "MOP", "qty_kg_per_acre": 25, 
                        "timing": "Flowering stage", "method": "Broadcast"
                    })

        # Calculate costs
        total_cost = 0
        all_fertilizers = plan["basal"] + plan["top_dress"] + plan.get("micronutrient", [])
        prices = {"DAP": 35, "Urea": 30, "MOP": 32, "Zinc Sulfate": 120, "Boron": 200, 
                  "Ferrous Sulfate": 80, "NPK 12:32:16": 40, "Micronutrient Mixture": 150}

        fertilizer_plan = []
        for fert in all_fertilizers:
            cost = fert["qty_kg_per_acre"] * prices.get(fert["name"], 50)
            total_cost += cost
            fertilizer_plan.append({
                "fertilizer_name": fert["name"],
                "quantity_kg_per_acre": fert["qty_kg_per_acre"],
                "application_timing": fert["timing"],
                "application_method": fert["method"],
                "estimated_cost_inr": round(cost, 2),
                "organic_alternative": self._get_organic_alternative(fert["name"])
            })

        state["fertilizer_plan"] = {
            "crop": crop,
            "fertilizers": fertilizer_plan,
            "total_estimated_cost_inr": round(total_cost, 2),
            "soil_based_adjustments": len(deficiencies) if soil_report else 0,
            "general_advice": [
                "Apply fertilizers based on soil test recommendations",
                "Split nitrogen application to improve efficiency",
                "Incorporate organic matter regularly",
                "Avoid fertilizer application before expected heavy rainfall"
            ]
        }

        self._add_message(
            state,
            f"Fertilizer plan created for {crop}. Total cost: Rs. {round(total_cost, 2)}/acre. {len(fertilizer_plan)} applications scheduled.",
            {"total_cost": round(total_cost, 2), "applications": len(fertilizer_plan)},
            "medium"
        )

        return state

    def _get_organic_alternative(self, chemical_fert: str) -> str:
        alternatives = {
            "Urea": "Vermicompost (5 tonnes/acre) or Farmyard Manure",
            "DAP": "Rock Phosphate + Compost",
            "MOP": "Wood Ash or Banana Peel compost",
            "Zinc Sulfate": "Zinc-enriched compost",
            "Boron": "Boron-rich organic amendments"
        }
        return alternatives.get(chemical_fert, "Organic compost")
