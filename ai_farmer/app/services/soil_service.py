"""Soil health analysis and nutrient deficiency detection service."""
from typing import Dict, Any, List, Optional
from app.utils import logger


class SoilService:
    """Analyzes soil health and detects nutrient deficiencies."""

    def __init__(self):
        self.soil_database = self._load_soil_database()

    def _load_soil_database(self) -> Dict[str, Any]:
        """Load soil characteristics database."""
        return {
            "alluvial": {"ph": (6.5, 7.5), "n": "medium", "p": "medium", "k": "high", "organic": "medium", "texture": "loamy"},
            "black": {"ph": (7.0, 8.5), "n": "low", "p": "medium", "k": "high", "organic": "medium", "texture": "clayey"},
            "red": {"ph": (5.5, 7.0), "n": "low", "p": "low", "k": "low", "organic": "low", "texture": "sandy_loam"},
            "laterite": {"ph": (4.5, 6.0), "n": "low", "p": "low", "k": "low", "organic": "low", "texture": "sandy"},
            "desert": {"ph": (8.0, 9.0), "n": "very_low", "p": "low", "k": "medium", "organic": "very_low", "texture": "sandy"},
            "loamy": {"ph": (6.0, 7.0), "n": "medium", "p": "medium", "k": "medium", "organic": "medium", "texture": "loamy"},
            "sandy": {"ph": (6.0, 7.5), "n": "low", "p": "low", "k": "low", "organic": "low", "texture": "sandy"},
            "clayey": {"ph": (6.5, 8.0), "n": "medium", "p": "high", "k": "high", "organic": "medium", "texture": "clayey"},
        }

    def analyze_soil(self, soil_type: str, ph: Optional[float] = None) -> Dict[str, Any]:
        """Analyze soil health based on type and optional pH."""
        soil_info = self.soil_database.get(soil_type.lower(), self.soil_database["loamy"])

        if ph is None:
            ph = round(sum(soil_info["ph"]) / 2, 2)

        health_score = self._calculate_health_score(soil_info, ph)

        deficiencies = []
        recommendations = []

        if soil_info["n"] in ["low", "very_low"]:
            deficiencies.append("Nitrogen (N)")
            recommendations.append("Apply organic compost or urea (46kg N/ha)")
        if soil_info["p"] in ["low", "very_low"]:
            deficiencies.append("Phosphorus (P)")
            recommendations.append("Apply Single Super Phosphate or DAP")
        if soil_info["k"] in ["low", "very_low"]:
            deficiencies.append("Potassium (K)")
            recommendations.append("Apply Muriate of Potash (MOP)")
        if soil_info["organic"] in ["low", "very_low"]:
            deficiencies.append("Organic Matter")
            recommendations.append("Add farmyard manure or green manure crops")

        return {
            "soil_type": soil_type.title(),
            "ph_level": round(ph, 2),
            "texture": soil_info["texture"],
            "nutrient_status": {
                "nitrogen": soil_info["n"],
                "phosphorus": soil_info["p"],
                "potassium": soil_info["k"],
                "organic_matter": soil_info["organic"]
            },
            "deficiencies": deficiencies,
            "recommendations": recommendations,
            "health_score": health_score,
            "health_status": "Excellent" if health_score > 80 else "Good" if health_score > 60 else "Fair" if health_score > 40 else "Poor",
            "suitable_crops": self._get_suitable_crops(soil_type, ph)
        }

    def detect_nutrient_deficiency(self, crop: str, symptoms: List[str]) -> Dict[str, Any]:
        """Detect nutrient deficiency from crop symptoms."""
        deficiency_map = {
            "nitrogen": {
                "symptoms": ["yellowing leaves", "stunted growth", "older leaves yellow", "pale green color"],
                "treatment": ["Apply urea or ammonium sulfate", "Add organic compost", "Plant leguminous cover crops"]
            },
            "phosphorus": {
                "symptoms": ["purple leaves", "dark green color", "delayed maturity", "poor root development"],
                "treatment": ["Apply DAP or SSP", "Add bone meal", "Maintain soil pH 6.0-7.0"]
            },
            "potassium": {
                "symptoms": ["brown leaf edges", "yellowing between veins", "weak stems", "poor fruit quality"],
                "treatment": ["Apply MOP", "Add wood ash", "Use potassium-rich organic fertilizers"]
            },
            "iron": {
                "symptoms": ["interveinal chlorosis", "yellow young leaves", "veins remain green"],
                "treatment": ["Apply ferrous sulfate", "Foliar spray of iron chelates", "Improve soil drainage"]
            },
            "zinc": {
                "symptoms": ["small leaves", "rosetting", "interveinal chlorosis", "stunted growth"],
                "treatment": ["Apply zinc sulfate", "Foliar spray of 0.5% zinc sulfate", "Add organic matter"]
            }
        }

        detected = []
        for nutrient, info in deficiency_map.items():
            match_count = sum(1 for s in symptoms if any(sym in s.lower() for sym in info["symptoms"]))
            if match_count > 0:
                detected.append({
                    "nutrient": nutrient.title(),
                    "confidence": min(match_count / len(info["symptoms"]) * 100 + 30, 95),
                    "matched_symptoms": [s for s in symptoms if any(sym in s.lower() for sym in info["symptoms"])],
                    "treatment": info["treatment"]
                })

        if not detected:
            detected.append({
                "nutrient": "Unknown / Multiple",
                "confidence": 50,
                "matched_symptoms": symptoms,
                "treatment": ["Conduct detailed soil test", "Consult local agricultural officer", "Apply balanced NPK fertilizer"]
            })

        return {
            "crop": crop,
            "reported_symptoms": symptoms,
            "detected_deficiencies": sorted(detected, key=lambda x: x["confidence"], reverse=True),
            "general_recommendation": "Based on symptoms, apply micronutrient mixture and conduct soil testing for confirmation."
        }

    def _calculate_health_score(self, soil_info: Dict, ph: float) -> int:
        """Calculate overall soil health score."""
        score = 50
        nutrient_scores = {"very_low": 5, "low": 15, "medium": 25, "high": 30}
        score += nutrient_scores.get(soil_info["n"], 15)
        score += nutrient_scores.get(soil_info["p"], 15)
        score += nutrient_scores.get(soil_info["k"], 15)
        score += nutrient_scores.get(soil_info["organic"], 15)

        if 6.0 <= ph <= 7.5:
            score += 10
        elif 5.5 <= ph <= 8.0:
            score += 5

        return min(score, 100)

    def _get_suitable_crops(self, soil_type: str, ph: float) -> List[str]:
        """Get crops suitable for given soil type."""
        crop_map = {
            "alluvial": ["rice", "wheat", "sugarcane", "maize", "pulses"],
            "black": ["cotton", "sugarcane", "soybean", "chickpea", "sunflower"],
            "red": ["groundnut", "millet", "pulses", "cotton", "potato"],
            "laterite": ["tea", "coffee", "rubber", "cashew", "coconut"],
            "desert": ["bajra", "cluster bean", "moth bean", "date palm"],
            "loamy": ["tomato", "onion", "brinjal", "okra", "cucumber"],
            "sandy": ["watermelon", "muskmelon", "carrot", "radish", "groundnut"],
            "clayey": ["rice", "wheat", "sugarcane", "cabbage", "cauliflower"]
        }
        return crop_map.get(soil_type.lower(), ["wheat", "rice", "pulses"])


soil_service_instance = SoilService()
