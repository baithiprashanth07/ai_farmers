"""Farm Risk Predictor Agent."""
import random
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State

class RiskPredictorAgent(BaseAgent):
    """Predicts and mitigates farm risks."""

    def __init__(self):
        super().__init__("RiskPredictorAgent", "Predicts and mitigates farm risks")

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        risks = []

        # Weather risk
        weather = state.get("weather_forecast", {})
        if weather and "forecast" in weather:
            extreme = sum(1 for d in weather["forecast"] if d.get("rainfall_mm", 0) > 20 or d.get("temp_max_c", 0) > 40)
            if extreme > 2:
                risks.append({
                    "risk_category": "weather", "risk_level": "high", "probability": 0.75,
                    "impact": "Crop damage from extreme weather",
                    "mitigation_strategies": ["Install protective netting", "Improve drainage", "Consider PMFBY crop insurance"],
                    "insurance_recommended": True
                })
            else:
                risks.append({
                    "risk_category": "weather", "risk_level": "low", "probability": 0.25,
                    "impact": "Normal weather expected",
                    "mitigation_strategies": ["Continue monitoring", "Maintain insurance coverage"],
                    "insurance_recommended": True
                })

        # Market risk
        market = state.get("market_price_prediction", {})
        if market and "prices" in market:
            trend = market["prices"][0].get("price_trend", "stable") if market["prices"] else "stable"
            if trend == "falling":
                risks.append({
                    "risk_category": "market", "risk_level": "medium", "probability": 0.6,
                    "impact": "Reduced income due to price drop",
                    "mitigation_strategies": ["Consider forward contracts", "Diversify crops", "Store and sell later"],
                    "insurance_recommended": False
                })

        # Pest/Disease risk
        if context.get("season") == "kharif":
            risks.append({
                "risk_category": "pest", "risk_level": "medium", "probability": 0.55,
                "impact": "Increased pest pressure during monsoon",
                "mitigation_strategies": ["Install pheromone traps", "Regular field scouting", "Preventive neem spray"],
                "insurance_recommended": False
            })

        # Financial risk
        if context.get("farm_size_acres", 10) < 2:
            risks.append({
                "risk_category": "financial", "risk_level": "medium", "probability": 0.5,
                "impact": "High fixed cost burden per acre",
                "mitigation_strategies": ["Join FPO for bulk purchase", "Apply for KCC loan", "Share machinery costs"],
                "insurance_recommended": True
            })

        # Soil risk
        soil = state.get("soil_health_report", {})
        if soil and soil.get("health_score", 100) < 50:
            risks.append({
                "risk_category": "soil", "risk_level": "high", "probability": 0.7,
                "impact": "Poor soil health affecting yield",
                "mitigation_strategies": ["Apply organic matter", "Green manuring", "Soil reclamation"],
                "insurance_recommended": False
            })

        if not risks:
            risks.append({
                "risk_category": "general", "risk_level": "low", "probability": 0.2,
                "impact": "Normal farming conditions",
                "mitigation_strategies": ["Continue regular monitoring", "Maintain farm records"],
                "insurance_recommended": True
            })

        state["risk_assessment"] = risks
        self._add_message(state, f"Risk assessment: {len([r for r in risks if r['risk_level'] in ['high','critical']])} high-risk items.", {"total": len(risks)}, "high")
        return state
