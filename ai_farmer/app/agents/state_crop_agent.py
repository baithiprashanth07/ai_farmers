"""State-wise Crop Intelligence Agent - Provides region-specific crop insights."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger


class StateCropIntelligenceAgent(BaseAgent):
    """
    Provides state and district-specific crop intelligence including:
    - Major crops grown in the region
    - Government MSP for the state
    - Regional climate patterns
    - Local market preferences
    - Success stories and best practices
    """

    def __init__(self):
        super().__init__(
            name="StateCropIntelligenceAgent",
            description="Provides state and district-specific agricultural intelligence"
        )
        self.state_intelligence = self._load_state_database()

    def _load_state_database(self) -> dict:
        return {
            "punjab": {
                "major_crops": ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize"],
                "climate": "Semi-arid, hot summers, cold winters",
                "avg_rainfall_mm": 650,
                "soil_predominant": "Alluvial",
                "irrigation_coverage": "95% (canal + tubewell)",
                "msp_highlights": {"wheat": 2275, "rice": 2183, "cotton": 6620},
                "best_practices": [
                    "Direct Seeded Rice (DSR) to save water",
                    "Happy Seeder for residue management",
                    "Crop diversification program active"
                ],
                "challenges": ["Water table depletion", "Stubble burning", "Soil salinity"],
                "gov_priority": "Crop diversification, water conservation"
            },
            "haryana": {
                "major_crops": ["Wheat", "Rice", "Sugarcane", "Bajra", "Mustard"],
                "climate": "Semi-arid to arid",
                "avg_rainfall_mm": 580,
                "soil_predominant": "Alluvial, Sandy",
                "irrigation_coverage": "90%",
                "msp_highlights": {"wheat": 2275, "rice": 2183, "bajra": 2500},
                "best_practices": [
                    "Zero Tillage Wheat",
                    "Bed planting for water saving",
                    "Micro-irrigation adoption"
                ],
                "challenges": ["Groundwater depletion", "Labour shortage"],
                "gov_priority": "Water conservation, horticulture promotion"
            },
            "uttar pradesh": {
                "major_crops": ["Wheat", "Rice", "Sugarcane", "Potato", "Pulses"],
                "climate": "Sub-tropical humid",
                "avg_rainfall_mm": 900,
                "soil_predominant": "Alluvial",
                "irrigation_coverage": "75%",
                "msp_highlights": {"wheat": 2275, "rice": 2183, "sugarcane": 340, "potato": 0},
                "best_practices": [
                    "SRI method for rice",
                    "Intercropping wheat + mustard",
                    "Tissue culture bananas in eastern UP"
                ],
                "challenges": ["Flooding in eastern UP", "Small landholdings", "Post-harvest losses"],
                "gov_priority": "Doubling farmer income, food processing"
            },
            "maharashtra": {
                "major_crops": ["Cotton", "Soybean", "Sugarcane", "Jowar", "Onion"],
                "climate": "Tropical monsoon",
                "avg_rainfall_mm": 1200,
                "soil_predominant": "Black Cotton Soil",
                "irrigation_coverage": "35%",
                "msp_highlights": {"cotton": 6620, "soybean": 4600, "jowar": 2990},
                "best_practices": [
                    "Bt Cotton with refuge crop",
                    "Soybean + Tur intercropping",
                    "Drip irrigation for sugarcane"
                ],
                "challenges": ["Drought-prone areas", "Pest resistance", "Market price fluctuation"],
                "gov_priority": "Drought mitigation, organic farming"
            },
            "karnataka": {
                "major_crops": ["Ragi", "Jowar", "Maize", "Coffee", "Silk"],
                "climate": "Tropical monsoon, moderate",
                "avg_rainfall_mm": 1100,
                "soil_predominant": "Red, Laterite",
                "irrigation_coverage": "40%",
                "msp_highlights": {"maize": 2090, "jowar": 2990, "ragi": 3576},
                "best_practices": [
                    "System of Rice Intensification (SRI)",
                    "Precision farming in Cauvery basin",
                    "Protected cultivation for vegetables"
                ],
                "challenges": ["Erratic rainfall", "Soil erosion in Malnad"],
                "gov_priority": "Micro-irrigation, horticulture"
            },
            "tamil nadu": {
                "major_crops": ["Rice", "Sugarcane", "Cotton", "Groundnut", "Banana"],
                "climate": "Tropical wet and dry",
                "avg_rainfall_mm": 950,
                "soil_predominant": "Red, Alluvial, Laterite",
                "irrigation_coverage": "55%",
                "msp_highlights": {"rice": 2183, "cotton": 6620, "groundnut": 6377},
                "best_practices": [
                    "Kuruvai / Samba rice seasons",
                    "SRI in Cauvery delta",
                    "Tissue culture bananas"
                ],
                "challenges": ["Cauvery water dispute", "Cyclone damage"],
                "gov_priority": "Delta modernization, climate resilience"
            },
            "andhra pradesh": {
                "major_crops": ["Rice", "Chili", "Cotton", "Tobacco", "Mango"],
                "climate": "Hot and humid tropical",
                "avg_rainfall_mm": 1000,
                "soil_predominant": "Red, Black, Alluvial",
                "irrigation_coverage": "50%",
                "msp_highlights": {"rice": 2183, "cotton": 6620, "chili": 0},
                "best_practices": [
                    "Mechanized transplanting for rice",
                    "Drip for chili and cotton",
                    "Ultra-high-density mango plantations"
                ],
                "challenges": ["Cyclones", "Pest outbreaks in chili"],
                "gov_priority": "Aquaculture integration, export promotion"
            },
            "gujarat": {
                "major_crops": ["Cotton", "Groundnut", "Bajra", "Castor", "Cumin"],
                "climate": "Arid to semi-arid",
                "avg_rainfall_mm": 800,
                "soil_predominant": "Alluvial, Black, Saline",
                "irrigation_coverage": "45%",
                "msp_highlights": {"cotton": 6620, "groundnut": 6377, "bajra": 2500},
                "best_practices": [
                    "Bt Cotton success model",
                    "Check dam construction",
                    "Drip + fertigation for horticulture"
                ],
                "challenges": ["Drought", "Salinity ingress", "Groundwater quality"],
                "gov_priority": "Narmada water distribution, salt-tolerant crops"
            },
            "rajasthan": {
                "major_crops": ["Bajra", "Mustard", "Wheat", "Guar", "Cumin"],
                "climate": "Arid, extreme temperatures",
                "avg_rainfall_mm": 350,
                "soil_predominant": "Desert, Sandy",
                "irrigation_coverage": "40% (Indira Gandhi Canal)",
                "msp_highlights": {"bajra": 2500, "mustard": 5450, "wheat": 2275},
                "best_practices": [
                    "Khadin system for water harvesting",
                    "Drought-resistant varieties",
                    "Solar-powered irrigation"
                ],
                "challenges": ["Water scarcity", "Desertification", "Heat waves"],
                "gov_priority": "Water harvesting, drought-resistant varieties"
            },
            "west bengal": {
                "major_crops": ["Rice", "Jute", "Tea", "Potato", "Mango"],
                "climate": "Tropical humid",
                "avg_rainfall_mm": 1500,
                "soil_predominant": "Alluvial, Laterite",
                "irrigation_coverage": "50%",
                "msp_highlights": {"rice": 2183, "jute": 4750, "potato": 0},
                "best_practices": [
                    "SRI in Kharif rice",
                    "Jute retting management",
                    "Darjeeling tea GAP"
                ],
                "challenges": ["Cyclones", "Flooding", "Small holdings"],
                "gov_priority": "Crop insurance, flood-resistant varieties"
            },
            "bihar": {
                "major_crops": ["Rice", "Wheat", "Maize", "Litchi", "Makhana"],
                "climate": "Sub-tropical humid",
                "avg_rainfall_mm": 1100,
                "soil_predominant": "Alluvial",
                "irrigation_coverage": "65%",
                "msp_highlights": {"rice": 2183, "wheat": 2275, "maize": 2090},
                "best_practices": [
                    "Maize + legume intercropping",
                    "Shahi Litchi orchards",
                    "Makhana pond cultivation"
                ],
                "challenges": ["Flooding", "Poor infrastructure", "Labour migration"],
                "gov_priority": "Organic corridor, aquaculture"
            },
            "kerala": {
                "major_crops": ["Rice", "Coconut", "Rubber", "Spices", "Banana"],
                "climate": "Tropical wet",
                "avg_rainfall_mm": 3000,
                "soil_predominant": "Laterite, Alluvial",
                "irrigation_coverage": "30%",
                "msp_highlights": {"rice": 2183, "rubber": 0},
                "best_practices": [
                    "Kole fields rice cultivation",
                    "Multi-story cropping (coconut + pepper + cocoa)",
                    "Organic spice cultivation"
                ],
                "challenges": ["High labour cost", "Wildlife conflict", "Climate change"],
                "gov_priority": "Organic farming, precision agriculture"
            }
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        state_name = context.get("state", "").lower()
        district = context.get("district", "").lower()

        intel = self.state_intelligence.get(state_name, {
            "major_crops": ["Wheat", "Rice", "Pulses"],
            "climate": "Tropical",
            "avg_rainfall_mm": 1000,
            "soil_predominant": "Alluvial",
            "irrigation_coverage": "50%",
            "msp_highlights": {},
            "best_practices": ["Soil testing", "Crop rotation"],
            "challenges": ["General agricultural challenges"],
            "gov_priority": "General development"
        })

        # Add district-specific notes if available (simplified)
        district_notes = f"District: {district.title()}. " if district else ""

        state["state_crop_intelligence"] = {
            "state": state_name.title(),
            "district_notes": district_notes,
            "major_crops": intel["major_crops"],
            "climate_summary": intel["climate"],
            "avg_annual_rainfall_mm": intel["avg_rainfall_mm"],
            "predominant_soil": intel["soil_predominant"],
            "irrigation_coverage": intel["irrigation_coverage"],
            "msp_highlights": intel["msp_highlights"],
            "regional_best_practices": intel["best_practices"],
            "key_challenges": intel["challenges"],
            "government_priority": intel["gov_priority"],
            "recommendation": f"For {state_name.title()}, focus on {', '.join(intel['major_crops'][:3])}. {intel['gov_priority']}."
        }

        self._add_message(
            state,
            f"State intelligence loaded for {state_name.title()}. {len(intel['major_crops'])} major crops identified.",
            {"state": state_name, "major_crops": intel["major_crops"]},
            "medium"
        )

        return state
