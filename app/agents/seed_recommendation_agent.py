"""Seed Recommendation Agent - Recommends best seeds/varieties for crops."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger

class SeedRecommendationAgent(BaseAgent):
    """Recommends certified seeds and varieties based on region, season, and disease resistance."""

    def __init__(self):
        super().__init__("SeedRecommendationAgent", "Recommends best seeds and varieties")
        self.seed_db = self._load_seed_database()

    def _load_seed_database(self):
        return {
            "rice": {
                "varieties": [
                    {"name": "IR 64", "duration": "110-115 days", "yield": "25-30 qtl/acre", "resistance": "BLB, RTV", "region": "All India", "seed_rate": "25-30 kg/acre", "certified_by": "NSC/State Seeds"},
                    {"name": "MTU 1010", "duration": "125-130 days", "yield": "28-32 qtl/acre", "resistance": "Blast, BPH", "region": "South India", "seed_rate": "25 kg/acre", "certified_by": "AP Seeds"},
                    {"name": "Pusa Basmati 1121", "duration": "140-145 days", "yield": "18-22 qtl/acre", "resistance": "BLB", "region": "North India", "seed_rate": "8-10 kg/acre", "certified_by": "IARI"},
                    {"name": "Pusa Basmati 1509", "duration": "115-120 days", "yield": "20-24 qtl/acre", "resistance": "Blast", "region": "Punjab, Haryana, UP", "seed_rate": "8 kg/acre", "certified_by": "IARI"},
                    {"name": "Sambha Mahsuri", "duration": "145-150 days", "yield": "30-35 qtl/acre", "resistance": "BLB, GM", "region": "East & South", "seed_rate": "25 kg/acre", "certified_by": "State Seeds"},
                    {"name": "Swarna Sub-1", "duration": "140-145 days", "yield": "28-32 qtl/acre", "resistance": "Submergence", "region": "Flood-prone areas", "seed_rate": "25 kg/acre", "certified_by": "CRRI"},
                    {"name": "CR Dhan 310", "duration": "125 days", "yield": "26-30 qtl/acre", "resistance": "Drought", "region": "Rainfed areas", "seed_rate": "25 kg/acre", "certified_by": "NRRI"},
                    {"name": "Ranjit", "duration": "135 days", "yield": "27-30 qtl/acre", "resistance": "Blast, BLB", "region": "Assam, NE", "seed_rate": "25 kg/acre", "certified_by": "AAU"},
                ]
            },
            "wheat": {
                "varieties": [
                    {"name": "HD 2967", "duration": "135-140 days", "yield": "22-25 qtl/acre", "resistance": "Rust, Karnal Bunt", "region": "NWPZ", "seed_rate": "40-45 kg/acre", "certified_by": "IARI"},
                    {"name": "DBW 187", "duration": "130-135 days", "yield": "24-27 qtl/acre", "resistance": "Yellow Rust, BLB", "region": "CZ, PZ", "seed_rate": "40 kg/acre", "certified_by": "IARI"},
                    {"name": "PBW 343", "duration": "140 days", "yield": "20-23 qtl/acre", "resistance": "Rust", "region": "Punjab, Haryana", "seed_rate": "40 kg/acre", "certified_by": "PAU"},
                    {"name": "Lok-1", "duration": "150 days", "yield": "18-22 qtl/acre", "resistance": "Drought", "region": "Gujarat, MP, Rajasthan", "seed_rate": "45 kg/acre", "certified_by": "Gujarat Agri Univ"},
                    {"name": "K-9107", "duration": "130 days", "yield": "23-26 qtl/acre", "resistance": "Rust, Powdery Mildew", "region": "UP, Bihar", "seed_rate": "40 kg/acre", "certified_by": "CSAUA&T"},
                    {"name": "Sharbati", "duration": "145 days", "yield": "16-20 qtl/acre", "resistance": "Good chapati quality", "region": "MP", "seed_rate": "40 kg/acre", "certified_by": "RVSKVV"},
                ]
            },
            "cotton": {
                "varieties": [
                    {"name": "RCH 2 BG-II", "duration": "165-170 days", "yield": "10-12 qtl/acre", "resistance": "Bollworm, Jassid", "region": "Central India", "seed_rate": "1.5 kg/acre", "certified_by": "Rasi Seeds"},
                    {"name": "Ankur 651 BG-II", "duration": "160-165 days", "yield": "10-11 qtl/acre", "resistance": "Bollworm", "region": "Gujarat, Maharashtra", "seed_rate": "1.5 kg/acre", "certified_by": "Ankur Seeds"},
                    {"name": "Suraj", "duration": "150 days", "yield": "8-10 qtl/acre", "resistance": "Wilt, Bollworm", "region": "North India", "seed_rate": "12-15 kg/acre (desi)", "certified_by": "CICR"},
                    {"name": "MCU 5", "duration": "170 days", "yield": "6-8 qtl/acre", "resistance": "Wilt", "region": "Tamil Nadu", "seed_rate": "10 kg/acre", "certified_by": "TNAU"},
                ]
            },
            "maize": {
                "varieties": [
                    {"name": "Pioneer 3396", "duration": "95-100 days", "yield": "30-35 qtl/acre", "resistance": "Stalk Rot, Blight", "region": "All India", "seed_rate": "8-10 kg/acre", "certified_by": "Pioneer"},
                    {"name": "DHM 117", "duration": "90-95 days", "yield": "32-36 qtl/acre", "resistance": "Turcicum Blight", "region": "Bihar, UP", "seed_rate": "8 kg/acre", "certified_by": "DHM"},
                    {"name": "HQPM 1", "duration": "95 days", "yield": "28-32 qtl/acre", "resistance": "Quality Protein Maize", "region": "All India", "seed_rate": "8 kg/acre", "certified_by": "IARI"},
                ]
            },
            "groundnut": {
                "varieties": [
                    {"name": "TG 37A", "duration": "105-110 days", "yield": "12-15 qtl/acre", "resistance": "PBNDV, Rust", "region": "Gujarat, Rajasthan", "seed_rate": "35-40 kg/acre", "certified_by": "GAU"},
                    {"name": "Girnar 3", "duration": "110 days", "yield": "14-16 qtl/acre", "resistance": "Drought", "region": "Gujarat", "seed_rate": "35 kg/acre", "certified_by": "Junagadh Univ"},
                    {"name": "Kadiri 6", "duration": "115 days", "yield": "13-15 qtl/acre", "resistance": "Late leaf spot", "region": "AP, Karnataka", "seed_rate": "35 kg/acre", "certified_by": "ANGRAU"},
                ]
            },
            "soybean": {
                "varieties": [
                    {"name": "JS 335", "duration": "95-100 days", "yield": "15-18 qtl/acre", "resistance": "Yellow Mosaic", "region": "MP, Maharashtra", "seed_rate": "25-30 kg/acre", "certified_by": "JNKVV"},
                    {"name": "NRC 37", "duration": "100 days", "yield": "16-20 qtl/acre", "resistance": "Yellow Mosaic, Rust", "region": "Central India", "seed_rate": "25 kg/acre", "certified_by": "NRC Soybean"},
                ]
            },
            "potato": {
                "varieties": [
                    {"name": "Kufri Jyoti", "duration": "90-100 days", "yield": "120-140 qtl/acre", "resistance": "Late Blight", "region": "Hills, Plains", "seed_rate": "800-1000 kg/acre", "certified_by": "CPRI"},
                    {"name": "Kufri Pukhraj", "duration": "90 days", "yield": "140-160 qtl/acre", "resistance": "Early Blight", "region": "UP, Bihar, WB", "seed_rate": "800 kg/acre", "certified_by": "CPRI"},
                    {"name": "Kufri Chandramukhi", "duration": "80-85 days", "yield": "100-120 qtl/acre", "resistance": "Virus X", "region": "Early crop", "seed_rate": "1000 kg/acre", "certified_by": "CPRI"},
                ]
            },
            "tomato": {
                "varieties": [
                    {"name": "Pusa Ruby", "duration": "90 days", "yield": "80-100 qtl/acre", "resistance": "Fusarium Wilt", "region": "North India", "seed_rate": "200 g/acre", "certified_by": "IARI"},
                    {"name": "Arka Vikas", "duration": "140 days", "yield": "100-120 qtl/acre", "resistance": "Bacterial Wilt", "region": "South India", "seed_rate": "200 g/acre", "certified_by": "IIHR"},
                    {"name": "Lakshmi", "duration": "120 days", "yield": "90-110 qtl/acre", "resistance": "ToLCV", "region": "Maharashtra", "seed_rate": "150 g/acre", "certified_by": "MPKV"},
                ]
            },
            "onion": {
                "varieties": [
                    {"name": "N-53", "duration": "150 days", "yield": "100-120 qtl/acre", "resistance": "Thrips", "region": "Maharashtra, Karnataka", "seed_rate": "3-4 kg/acre", "certified_by": "NHRDF"},
                    {"name": "Agrifound Dark Red", "duration": "140 days", "yield": "120-140 qtl/acre", "resistance": "Purple Blotch", "region": "All India", "seed_rate": "4 kg/acre", "certified_by": "NHRDF"},
                    {"name": "Pusa Red", "duration": "150 days", "yield": "110-130 qtl/acre", "resistance": "Good storage", "region": "North India", "seed_rate": "4 kg/acre", "certified_by": "IARI"},
                ]
            },
            "sugarcane": {
                "varieties": [
                    {"name": "Co 0238", "duration": "12 months", "yield": "350-400 qtl/acre", "resistance": "Red Rot, Smut", "region": "UP, Uttarakhand", "seed_rate": "3500 setts/acre", "certified_by": "SBI Coimbatore"},
                    {"name": "Co 86032", "duration": "12 months", "yield": "400-450 qtl/acre", "resistance": "Red Rot", "region": "South India", "seed_rate": "4000 setts/acre", "certified_by": "SBI Coimbatore"},
                    {"name": "CoS 767", "duration": "12 months", "yield": "380-420 qtl/acre", "resistance": "Drought", "region": "UP, Bihar", "seed_rate": "3500 setts/acre", "certified_by": "SBI Coimbatore"},
                ]
            },
            "chickpea": {
                "varieties": [
                    {"name": "JG 11", "duration": "100-110 days", "yield": "10-12 qtl/acre", "resistance": "Wilt, Root Rot", "region": "Central India", "seed_rate": "35-40 kg/acre", "certified_by": "IGKV"},
                    {"name": "Pusa 372", "duration": "130 days", "yield": "12-14 qtl/acre", "resistance": "Ascochyta Blight", "region": "North India", "seed_rate": "40 kg/acre", "certified_by": "IARI"},
                ]
            },
            "mustard": {
                "varieties": [
                    {"name": "Pusa Bold", "duration": "130-135 days", "yield": "12-14 qtl/acre", "resistance": "White Rust", "region": "North India", "seed_rate": "4-5 kg/acre", "certified_by": "IARI"},
                    {"name": "Varuna", "duration": "140 days", "yield": "10-12 qtl/acre", "resistance": "Aphid", "region": "UP, Bihar", "seed_rate": "5 kg/acre", "certified_by": "IARI"},
                ]
            },
            "turmeric": {
                "varieties": [
                    {"name": "Rajendra Sonia", "duration": "240-250 days", "yield": "120-140 qtl/acre", "resistance": "Rhizome Rot", "region": "Bihar", "seed_rate": "800-1000 kg/acre", "certified_by": "RAU"},
                    {"name": "Prabha", "duration": "230 days", "yield": "140-160 qtl/acre", "resistance": "Leaf Blotch", "region": "AP, Telangana", "seed_rate": "1000 kg/acre", "certified_by": "IARI"},
                ]
            },
            "banana": {
                "varieties": [
                    {"name": "Grand Naine (G-9)", "duration": "12 months", "yield": "250-300 qtl/acre", "resistance": "Panama Wilt", "region": "Maharashtra, Gujarat", "seed_rate": "1200 suckers/acre", "certified_by": "NRC Banana"},
                    {"name": "Robusta", "duration": "14 months", "yield": "300-350 qtl/acre", "resistance": "Sigatoka", "region": "South India", "seed_rate": "1000 suckers/acre", "certified_by": "NRC Banana"},
                ]
            },
            "mango": {
                "varieties": [
                    {"name": "Dashehari", "duration": "Perennial", "yield": "60-80 qtl/acre", "resistance": "Mango Malformation", "region": "UP, Bihar", "seed_rate": "40 plants/acre", "certified_by": "CISH Lucknow"},
                    {"name": "Alphonso", "duration": "Perennial", "yield": "50-70 qtl/acre", "resistance": "Anthracnose", "region": "Maharashtra, Karnataka", "seed_rate": "40 plants/acre", "certified_by": "Konkan Krishi Vidyapeeth"},
                    {"name": "Banganapalli", "duration": "Perennial", "yield": "70-90 qtl/acre", "resistance": "Powdery Mildew", "region": "AP, Telangana", "seed_rate": "35 plants/acre", "certified_by": "Dr. YSRHU"},
                ]
            },
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        crop = context.get("target_crop", "").lower()
        state_name = context.get("state", "").lower()

        recommendations = []

        if crop and crop in self.seed_db:
            varieties = self.seed_db[crop]["varieties"]
            # Filter by region if possible
            for v in varieties:
                region_match = any(r.lower() in state_name or state_name in r.lower() for r in v["region"].split(", "))
                score = 85 if region_match else 70
                recommendations.append({
                    "variety_name": v["name"],
                    "crop": crop.title(),
                    "duration": v["duration"],
                    "expected_yield": v["yield"],
                    "disease_resistance": v["resistance"],
                    "suitable_region": v["region"],
                    "seed_rate": v["seed_rate"],
                    "certified_by": v["certified_by"],
                    "relevance_score": score,
                    "price_estimate_inr_per_kg": self._estimate_seed_price(crop, v["name"])
                })
            recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
        elif state.get("crop_recommendations"):
            # Recommend seeds for top recommended crops
            for rec in state["crop_recommendations"][:3]:
                c = rec["crop_name"].lower()
                if c in self.seed_db:
                    top_var = self.seed_db[c]["varieties"][0]
                    recommendations.append({
                        "variety_name": top_var["name"],
                        "crop": rec["crop_name"],
                        "duration": top_var["duration"],
                        "expected_yield": top_var["yield"],
                        "disease_resistance": top_var["resistance"],
                        "suitable_region": top_var["region"],
                        "seed_rate": top_var["seed_rate"],
                        "certified_by": top_var["certified_by"],
                        "relevance_score": rec["confidence_score"] * 100,
                        "price_estimate_inr_per_kg": self._estimate_seed_price(c, top_var["name"])
                    })

        state["seed_recommendations"] = recommendations[:5]
        state["variety_recommendations"] = recommendations[:5]

        self._add_message(state, f"Seed recommendations generated for {crop or 'top crops'}. {len(recommendations)} varieties found.", {"count": len(recommendations)}, "high")
        return state

    def _estimate_seed_price(self, crop: str, variety: str) -> float:
        prices = {
            "rice": 60, "wheat": 35, "cotton": 850, "maize": 180,
            "groundnut": 120, "soybean": 90, "potato": 25, "tomato": 8000,
            "onion": 400, "sugarcane": 15, "chickpea": 85, "mustard": 70,
            "turmeric": 45, "banana": 25, "mango": 35
        }
        base = prices.get(crop, 100)
        # Premium varieties cost more
        premium = ["Basmati", "Pioneer", "G-9", "Alphonso"]
        if any(p in variety for p in premium):
            base *= 1.5
        return round(base, 2)
