"""State-wise Crop Intelligence Agent - Provides region-specific crop intelligence."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services.agriculture_reference import get_crop_reference_note, get_state_crop_reference
from app.utils import logger

class StateCropIntelligenceAgent(BaseAgent):
    """Provides comprehensive state-wise crop intelligence including:
    - Dominant crops and cropping patterns
    - Government MSP and procurement centers
    - Major diseases and pests in the region
    - Soil and climate suitability
    - Success stories and best practices
    """

    def __init__(self):
        super().__init__("StateCropIntelligenceAgent", "Provides state-wise agricultural intelligence")
        self.state_db = self._load_state_database()

    def _load_state_database(self):
        return {
            "punjab": {
                "dominant_crops": ["Wheat", "Rice", "Cotton", "Maize"],
                "cropping_pattern": "Rice-Wheat (most common), Cotton-Wheat, Maize-Wheat",
                "msp_procurement": ["Wheat", "Rice", "Cotton"],
                "major_diseases": ["Yellow Rust (Wheat)", "Blast (Rice)", "Bollworm (Cotton)"],
                "soil_types": ["Alluvial", "Loamy"],
                "avg_farm_size_acres": 3.5,
                "irrigation_coverage": "98% (Canal + Tubewell)",
                "agricultural_universities": ["PAU Ludhiana"],
                "best_practices": ["Direct Seeded Rice (DSR) to save water", "Happy Seeder for residue management", "Drip irrigation in vegetables"],
                "gov_priority": ["Crop diversification from paddy", "Stubble management", "Water conservation"]
            },
            "haryana": {
                "dominant_crops": ["Wheat", "Rice", "Sugarcane", "Bajra", "Mustard"],
                "cropping_pattern": "Rice-Wheat, Bajra-Wheat, Sugarcane-Wheat",
                "msp_procurement": ["Wheat", "Rice", "Bajra", "Mustard"],
                "major_diseases": ["Karnal Bunt (Wheat)", "Blast (Rice)", "Red Rot (Sugarcane)"],
                "soil_types": ["Alluvial", "Sandy Loam"],
                "avg_farm_size_acres": 3.2,
                "irrigation_coverage": "95%",
                "agricultural_universities": ["CCS HAU Hisar"],
                "best_practices": ["Zero Tillage Wheat", "Laser Land Leveling", "Micro-irrigation"],
                "gov_priority": ["Crop diversification", "Micro-irrigation expansion", "Organic farming clusters"]
            },
            "uttar pradesh": {
                "dominant_crops": ["Wheat", "Rice", "Sugarcane", "Potato", "Pulses", "Mustard"],
                "cropping_pattern": "Rice-Wheat, Sugarcane (annual), Potato-Wheat, Maize-Wheat",
                "msp_procurement": ["Wheat", "Rice", "Sugarcane", "Pulses", "Mustard"],
                "major_diseases": ["Yellow Rust (Wheat)", "BLB (Rice)", "Early Blight (Potato)"],
                "soil_types": ["Alluvial", "Loamy", "Clayey"],
                "avg_farm_size_acres": 2.1,
                "irrigation_coverage": "85%",
                "agricultural_universities": ["CSAUA&T Kanpur", "NDUA&T Faizabad", "SHUATS Allahabad"],
                "best_practices": ["SRI method for rice", "Tissue culture in sugarcane", "Seed potato production"],
                "gov_priority": ["Doubling farmer income", "Ethanol production from sugarcane", "Export promotion"]
            },
            "madhya pradesh": {
                "dominant_crops": ["Wheat", "Soybean", "Pulses", "Cotton", "Maize", "Gram"],
                "cropping_pattern": "Soybean-Wheat, Cotton-Wheat, Maize-Wheat, Pigeonpea-Wheat",
                "msp_procurement": ["Wheat", "Soybean", "Pulses", "Cotton"],
                "major_diseases": ["Yellow Mosaic (Soybean)", "Wilt (Cotton)", "Rust (Wheat)"],
                "soil_types": ["Black", "Alluvial", "Red"],
                "avg_farm_size_acres": 4.2,
                "irrigation_coverage": "45%",
                "agricultural_universities": ["JNKVV Jabalpur", "RVSKVV Gwalior"],
                "best_practices": ["Soybean-wheat system", "Intercropping in cotton", "Rainwater harvesting"],
                "gov_priority": ["Irrigation expansion", "Pulse production hub", "Organic corridor"]
            },
            "maharashtra": {
                "dominant_crops": ["Cotton", "Sugarcane", "Soybean", "Jowar", "Onion", "Turmeric"],
                "cropping_pattern": "Cotton-Sorghum, Sugarcane (annual), Soybean-Wheat, Onion-Rice",
                "msp_procurement": ["Cotton", "Sugarcane", "Soybean", "Wheat"],
                "major_diseases": ["Bollworm (Cotton)", "Red Rot (Sugarcane)", "Yellow Mosaic (Soybean)"],
                "soil_types": ["Black", "Laterite", "Alluvial"],
                "avg_farm_size_acres": 3.8,
                "irrigation_coverage": "25% (High in sugarcane belt)",
                "agricultural_universities": ["MPKV Rahuri", "Vasantrao Naik Marathwada Krishi Vidyapeeth", "Dr. BSKKV Dapoli"],
                "best_practices": ["Bollworm resistance management in cotton", "Drip in sugarcane", "Protected cultivation in vegetables"],
                "gov_priority": ["Drought mitigation", "Horticulture expansion", "Farmer Producer Companies"]
            },
            "gujarat": {
                "dominant_crops": ["Cotton", "Groundnut", "Bajra", "Wheat", "Castor", "Cumin"],
                "cropping_pattern": "Cotton-Wheat, Groundnut-Wheat, Bajra-Castor",
                "msp_procurement": ["Cotton", "Groundnut", "Bajra", "Wheat"],
                "major_diseases": ["Bollworm (Cotton)", "PBNDV (Groundnut)", "Downy Mildew (Bajra)"],
                "soil_types": ["Alluvial", "Black", "Saline"],
                "avg_farm_size_acres": 4.5,
                "irrigation_coverage": "40% (Narmada command area high)",
                "agricultural_universities": ["Anand Agricultural University", "Junagadh Agricultural University", "Navsari Agricultural University"],
                "best_practices": ["Bt cotton technology", "Summer groundnut", "Sprinkler irrigation in groundnut"],
                "gov_priority": ["Canal irrigation expansion", "Salinity reclamation", "Coastal agriculture"]
            },
            "rajasthan": {
                "dominant_crops": ["Bajra", "Mustard", "Wheat", "Gram", "Guar", "Cumin"],
                "cropping_pattern": "Bajra-Mustard, Moth Bean-Cluster Bean, Gram-Wheat",
                "msp_procurement": ["Bajra", "Mustard", "Wheat", "Gram"],
                "major_diseases": ["Downy Mildew (Bajra)", "White Rust (Mustard)", "Wilt (Gram)"],
                "soil_types": ["Desert", "Sandy", "Saline"],
                "avg_farm_size_acres": 6.2,
                "irrigation_coverage": "35% (Indira Gandhi Canal area)",
                "agricultural_universities": ["SKRAU Bikaner", "MPUAT Udaipur"],
                "best_practices": ["Drought-resistant varieties", "Water harvesting (tanka, khadin)", "Sand dune stabilization"],
                "gov_priority": ["Water conservation", "Drought-proofing", "Oilseed production"]
            },
            "karnataka": {
                "dominant_crops": ["Ragi", "Jowar", "Maize", "Paddy", "Sugarcane", "Coffee", "Silk"],
                "cropping_pattern": "Ragi-Groundnut, Paddy-Pulses, Maize-Wheat",
                "msp_procurement": ["Paddy", "Maize", "Ragi", "Groundnut"],
                "major_diseases": ["Blast (Ragi)", "Turcicum Blight (Maize)", "Red Rot (Sugarcane)"],
                "soil_types": ["Red", "Black", "Laterite"],
                "avg_farm_size_acres": 3.0,
                "irrigation_coverage": "35%",
                "agricultural_universities": ["UAS Bangalore", "UAS Dharwad", "UAS Raichur"],
                "best_practices": ["System of Rice Intensification", "Organic coffee", "Sericulture integration"],
                "gov_priority": ["Micro-irrigation", "Horticulture development", "Precision farming"]
            },
            "tamil nadu": {
                "dominant_crops": ["Rice", "Sugarcane", "Cotton", "Groundnut", "Turmeric", "Banana"],
                "cropping_pattern": "Rice-Rice (Cauvery delta), Rice-Groundnut, Sugarcane (annual)",
                "msp_procurement": ["Rice", "Sugarcane", "Cotton", "Groundnut"],
                "major_diseases": ["Blast (Rice)", "Bollworm (Cotton)", "Red Rot (Sugarcane)"],
                "soil_types": ["Red", "Black", "Alluvial"],
                "avg_farm_size_acres": 2.0,
                "irrigation_coverage": "55% (Mettur, Cauvery, Vaigai)",
                "agricultural_universities": ["TNAU Coimbatore"],
                "best_practices": ["ADOPT (Agricultural Development and Oriented Programme for Technology)", "Precision farming", "Protected cultivation"],
                "gov_priority": ["Cauvery water management", "Organic farming", "Export-oriented horticulture"]
            },
            "andhra pradesh": {
                "dominant_crops": ["Rice", "Cotton", "Chili", "Tobacco", "Groundnut", "Sugarcane"],
                "cropping_pattern": "Rice-Rice (Godavari/Krishna), Cotton-Chili, Groundnut-Maize",
                "msp_procurement": ["Rice", "Cotton", "Groundnut", "Chili"],
                "major_diseases": ["Blast (Rice)", "Bollworm (Cotton)", "PBNDV (Groundnut)"],
                "soil_types": ["Red", "Black", "Alluvial"],
                "avg_farm_size_acres": 2.8,
                "irrigation_coverage": "48% (Polavaram, Nagarjuna Sagar)",
                "agricultural_universities": ["ANGRAU Guntur", "Dr. YSRHU Venkataramannagudem"],
                "best_practices": ["Direct Seeded Rice", "Micro-irrigation in chili", "Tissue culture banana"],
                "gov_priority": ["Polavaram project", "Horticulture mission", "Aquaculture integration"]
            },
            "telangana": {
                "dominant_crops": ["Rice", "Cotton", "Maize", "Red Gram", "Chili", "Turmeric"],
                "cropping_pattern": "Rice-Maize, Cotton-Red Gram, Turmeric-Rice",
                "msp_procurement": ["Rice", "Cotton", "Maize", "Red Gram"],
                "major_diseases": ["Blast (Rice)", "Bollworm (Cotton)", "Turcicum Blight (Maize)"],
                "soil_types": ["Red", "Black", "Laterite"],
                "avg_farm_size_acres": 3.1,
                "irrigation_coverage": "45% (Kaleshwaram, SRSP)",
                "agricultural_universities": ["PJTSAU Hyderabad"],
                "best_practices": ["Mission Kakatiya (tank restoration)", "Farm ponds", "Drip in cotton"],
                "gov_priority": ["Irrigation expansion", "Oil palm cultivation", "Sheep rearing integration"]
            },
            "west bengal": {
                "dominant_crops": ["Rice", "Jute", "Potato", "Mustard", "Pulses", "Tea"],
                "cropping_pattern": "Rice-Rice (3 crops in some areas), Jute-Rice, Potato-Rice-Mustard",
                "msp_procurement": ["Rice", "Jute", "Potato", "Mustard"],
                "major_diseases": ["Blast (Rice)", "Stem Rot (Jute)", "Late Blight (Potato)"],
                "soil_types": ["Alluvial", "Laterite"],
                "avg_farm_size_acres": 1.8,
                "irrigation_coverage": "60%",
                "agricultural_universities": ["BCKV Mohanpur", "UBKV Cooch Behar"],
                "best_practices": ["SRI in rice", "Jute retting management", "Potato seed production"],
                "gov_priority": ["Crop diversification", "Jute modernization", "Tea rejuvenation"]
            },
            "bihar": {
                "dominant_crops": ["Rice", "Wheat", "Maize", "Pulses", "Vegetables", "Litchi"],
                "cropping_pattern": "Rice-Wheat, Maize-Wheat, Rice-Lentil, Vegetables-Rice",
                "msp_procurement": ["Rice", "Wheat", "Maize", "Pulses"],
                "major_diseases": ["Blast (Rice)", "Yellow Rust (Wheat)", "Turcicum Blight (Maize)"],
                "soil_types": ["Alluvial", "Clayey"],
                "avg_farm_size_acres": 1.5,
                "irrigation_coverage": "65%",
                "agricultural_universities": ["BAU Sabour", "RPCAU Pusa"],
                "best_practices": ["System of Wheat Intensification", "Zero Tillage", "Mushroom cultivation"],
                "gov_priority": ["Organic farming corridor", "Horticulture expansion", "Flood management"]
            },
            "odisha": {
                "dominant_crops": ["Rice", "Pulses", "Oilseeds", "Cotton", "Coconut", "Cashew"],
                "cropping_pattern": "Rice-Fallow (upland), Rice-Pulses, Rice-Oilseeds",
                "msp_procurement": ["Rice", "Pulses", "Oilseeds"],
                "major_diseases": ["Blast (Rice)", "Yellow Mosaic (Pulses)", "Wilt (Cotton)"],
                "soil_types": ["Red", "Laterite", "Alluvial"],
                "avg_farm_size_acres": 2.0,
                "irrigation_coverage": "35%",
                "agricultural_universities": ["OUAT Bhubaneswar"],
                "best_practices": ["Drought-resistant rice varieties", "Watershed development", "Integrated farming"],
                "gov_priority": ["Irrigation expansion", "Tribal agriculture", "Coastal zone management"]
            },
            "assam": {
                "dominant_crops": ["Rice", "Tea", "Jute", "Sugarcane", "Mustard", "Potato"],
                "cropping_pattern": "Rice-Rice (Brahmaputra valley), Rice-Mustard, Tea (perennial)",
                "msp_procurement": ["Rice", "Jute", "Mustard"],
                "major_diseases": ["Blast (Rice)", "Blister Blight (Tea)", "Stem Rot (Jute)"],
                "soil_types": ["Alluvial", "Loamy", "Acidic"],
                "avg_farm_size_acres": 2.5,
                "irrigation_coverage": "25% (Rainfed dominant)",
                "agricultural_universities": ["AAU Jorhat"],
                "best_practices": ["Sali rice cultivation", "Tea pruning management", "Bamboo drip irrigation"],
                "gov_priority": ["Tea industry revival", "Organic farming", "Bamboo mission"]
            },
            "kerala": {
                "dominant_crops": ["Rice", "Coconut", "Rubber", "Spices", "Banana", "Cashew"],
                "cropping_pattern": "Rice-Fallow, Coconut (perennial), Rubber (perennial), Mixed cropping",
                "msp_procurement": ["Rice", "Coconut"],
                "major_diseases": ["Blast (Rice)", "Bud Rot (Coconut)", "Powdery Mildew (Rubber)"],
                "soil_types": ["Laterite", "Alluvial", "Peaty"],
                "avg_farm_size_acres": 0.5,
                "irrigation_coverage": "40%",
                "agricultural_universities": ["KAU Thrissur"],
                "best_practices": ["Multi-tier cropping", "Integrated farming system", "Precision farming in rice"],
                "gov_priority": ["Coconut replanting", "Rubber replanting", "Spice export promotion"]
            },
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        state_name = context.get("state", "").lower()
        regional_reference = get_state_crop_reference(state_name)

        intelligence = self.state_db.get(state_name, {
            "dominant_crops": ["Rice", "Wheat", "Pulses", "Oilseeds"],
            "cropping_pattern": "Rice-Wheat (General)",
            "msp_procurement": ["Rice", "Wheat"],
            "major_diseases": ["Blast (Rice)", "Rust (Wheat)"],
            "soil_types": ["Alluvial"],
            "avg_farm_size_acres": 2.5,
            "irrigation_coverage": "50%",
            "agricultural_universities": ["State Agricultural University"],
            "best_practices": ["Soil testing", "Balanced fertilization", "IPM"],
            "gov_priority": ["Doubling farmer income", "Water conservation"]
        })

        # Add seasonal recommendations
        season = context.get("season", "kharif")
        seasonal_crops = self._get_seasonal_crops(state_name, season)
        dominant_crops = list(intelligence["dominant_crops"])
        if regional_reference:
            for crop in regional_reference["major_crops"]:
                if crop not in dominant_crops:
                    dominant_crops.append(crop)
            if state_name not in self.state_db:
                seasonal_crops = regional_reference["major_crops"]

        state["state_crop_intelligence"] = {
            "state": regional_reference["name"] if regional_reference else state_name.title(),
            "intelligence": intelligence,
            "dominant_crops": dominant_crops,
            "seasonal_recommendations": seasonal_crops,
            "specialty_crops": regional_reference["specialty_crops"] if regional_reference else [],
            "crop_reference_note": get_crop_reference_note(),
            "official_local_validation_required": True,
            "regional_languages": regional_reference["languages"] if regional_reference else [],
            "market_outlook": self._get_market_outlook(state_name),
            "climate_risk": self._get_climate_risk(state_name)
        }

        self._add_message(state, f"State intelligence loaded for {state_name.title()}. {len(intelligence['dominant_crops'])} dominant crops identified.", {"state": state_name}, "high")
        return state

    def _get_seasonal_crops(self, state: str, season: str) -> list:
        seasonal_map = {
            "punjab": {"kharif": ["Rice", "Cotton", "Maize"], "rabi": ["Wheat", "Mustard", "Gram", "Potato"], "zaid": ["Moong", "Vegetables"]},
            "maharashtra": {"kharif": ["Cotton", "Soybean", "Rice", "Groundnut"], "rabi": ["Jowar", "Wheat", "Gram", "Sunflower"], "zaid": ["Vegetables", "Moong"]},
            "karnataka": {"kharif": ["Ragi", "Maize", "Paddy", "Cotton"], "rabi": ["Wheat", "Groundnut", "Sunflower"], "zaid": ["Vegetables", "Watermelon"]},
            "tamil nadu": {"kharif": ["Rice", "Cotton", "Groundnut"], "rabi": ["Rice", "Groundnut", "Sugarcane"], "zaid": ["Vegetables", "Rice (short duration)"]},
        }
        return seasonal_map.get(state, {}).get(season, ["Rice", "Wheat", "Pulses"])

    def _get_market_outlook(self, state: str) -> str:
        return f"Market outlook for {state.title()}: Stable demand for cereals. Increasing demand for pulses and oilseeds. Horticulture exports growing."

    def _get_climate_risk(self, state: str) -> str:
        risks = {
            "punjab": "Water table depletion, Stubble burning air quality",
            "maharashtra": "Drought risk (Marathwada), Erratic monsoon",
            "bihar": "Flood risk (Kosi basin), Heat stress",
            "rajasthan": "Desertification, Water scarcity, Heat waves"
        }
        return risks.get(state, "General climate variability risk")
