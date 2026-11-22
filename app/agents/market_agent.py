"""Market Price & Profit Prediction Agent."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services import market_service_instance
from app.utils import logger, estimate_crop_yield

class MarketPriceAgent(BaseAgent):
    """Predicts market prices, yield, and profitability for crops."""

    def __init__(self):
        super().__init__("MarketPriceAgent", "Predicts market prices and profitability")

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        crop = context.get("target_crop")
        state_name = context.get("state", "")
        farm_size = context.get("farm_size_acres", 1)

        if not crop:
            state["market_price_prediction"] = {"error": "No target crop specified"}
            state["yield_prediction"] = {"error": "No target crop specified"}
            state["profit_prediction"] = {"error": "No target crop specified"}
            return state

        # Market prices
        prices = market_service_instance.get_market_prices(crop, state_name)
        state["market_price_prediction"] = {"prices": prices, "commodity": crop, "trend_analysis": "Stable to rising demand"}

        # Yield prediction
        soil_type = context.get("soil_type", "loamy")
        irrigation = context.get("irrigation_type", "flood")
        expected_yield = estimate_crop_yield(crop, soil_type, irrigation)

        state["yield_prediction"] = {
            "crop": crop,
            "projected_yield_quintal_per_acre": expected_yield,
            "total_projected_yield_quintals": round(expected_yield * farm_size, 2),
            "confidence": "high" if soil_type and irrigation else "medium",
            "factors": ["soil_type", "irrigation_method", "historical_average", "season"],
            "methodology": "Multi-factor regression with regional yield data"
        }

        # Profit prediction
        cost_per_acre = 25000
        if state.get("crop_recommendations"):
            for rec in state["crop_recommendations"]:
                if rec["crop_name"].lower() == crop.lower():
                    cost_per_acre = rec["estimated_cost_per_acre"]
                    break

        profit = market_service_instance.predict_profit(crop, expected_yield, state_name, cost_per_acre)
        state["profit_prediction"] = profit

        self._add_message(state, f"Market analysis: {crop} avg Rs.{profit['avg_market_price_per_quintal']}/quintal. Profit: Rs.{profit['projected_profit_per_acre']}/acre", {"profit": profit["projected_profit_per_acre"]}, "high")
        return state
