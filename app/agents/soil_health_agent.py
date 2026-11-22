"""Soil Health Analyzer Agent - Analyzes soil conditions and recommends improvements."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services import soil_service_instance
from app.utils import logger


class SoilHealthAgent(BaseAgent):
    """
    Analyzes soil health based on soil type and optional test data.
    Detects nutrient deficiencies and recommends soil amendments.
    """

    def __init__(self):
        super().__init__(
            name="SoilHealthAgent",
            description="Analyzes soil health and recommends improvements"
        )

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        soil_type = (
            context.get("soil_type")
            or state.get("state_crop_intelligence", {}).get("predominant_soil")
            or "loamy"
        )

        # Analyze soil health
        soil_report = soil_service_instance.analyze_soil(soil_type)
        soil_report["data_source"] = (
            "farmer-provided soil type and sample dataset"
            if context.get("soil_type")
            else "regional soil estimate; not a soil test"
        )
        soil_report["is_estimate"] = True
        state["soil_health_report"] = soil_report

        # Check for nutrient deficiencies if crop is specified
        crop = context.get("target_crop")
        if crop:
            # In a real system, this would use actual symptom data or image analysis
            deficiency_report = soil_service_instance.detect_nutrient_deficiency(
                crop, ["general yellowing", "stunted growth"]
            )
            state["nutrient_deficiency"] = deficiency_report

        self._add_message(
            state,
            f"Soil analysis complete. Health score: {soil_report['health_score']}/100 ({soil_report['health_status']}). Deficiencies found: {len(soil_report['deficiencies'])}.",
            {"health_score": soil_report["health_score"], "deficiencies": soil_report["deficiencies"]},
            "high"
        )

        return state
