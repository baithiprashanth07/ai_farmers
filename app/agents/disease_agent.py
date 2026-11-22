"""Disease Detection Agent - Detects crop diseases from images or symptoms."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services import disease_service_instance
from app.utils import logger


class DiseaseDetectionAgent(BaseAgent):
    """
    Detects diseases and pests from uploaded images or described symptoms.
    Provides treatment recommendations and preventive measures.
    """

    def __init__(self):
        super().__init__(
            name="DiseaseDetectionAgent",
            description="Detects crop diseases and pests using computer vision and symptom analysis"
        )

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        image_path = state.get("uploaded_image_path")
        crop = context.get("target_crop")

        if image_path:
            # Image-based detection
            result = disease_service_instance.detect_from_image(image_path, crop)
            state["disease_detection"] = result

            # Also get medicine recommendations
            if result.get("disease_name") and result["disease_name"] != "Unable to detect":
                medicine = disease_service_instance.get_medicine_recommendation(
                    result["disease_name"], 
                    preference="integrated"
                )
                state["medicine_recommendations"] = [medicine]
        else:
            # Symptom-based or preventive analysis
            state["disease_detection"] = {
                "message": "No image uploaded. Please upload a crop image for disease detection or describe symptoms.",
                "preventive_measures": [
                    "Practice crop rotation",
                    "Use disease-resistant varieties",
                    "Maintain field sanitation",
                    "Ensure proper spacing for air circulation"
                ]
            }

        self._add_message(
            state,
            f"Disease analysis complete. Detected: {state['disease_detection'].get('disease_name', 'N/A')}.",
            {"detection_method": state["disease_detection"].get("detection_method", "none")},
            "high"
        )

        return state
