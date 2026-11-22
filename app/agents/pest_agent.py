"""Pest Detection Agent - Detects and recommends control for agricultural pests."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.utils import logger

class PestDetectionAgent(BaseAgent):
    """Detects pests from images/symptoms and recommends IPM-based control measures."""

    def __init__(self):
        super().__init__("PestDetectionAgent", "Detects pests and recommends integrated pest management")
        self.pest_db = self._load_pest_database()

    def _load_pest_database(self):
        return {
            "bollworm": {
                "crops": ["cotton", "chickpea", "tomato"],
                "symptoms": ["Holes in bolls/fruits", "Dropping flowers", "Frass on plants"],
                "organic_control": ["Pheromone traps (10/acre)", "HaNPV spray @ 250 LE/ha", "Bt spray", "Bird perches"],
                "chemical_control": ["Spinosad 45 SC", "Emamectin benzoate", "Indoxacarb"],
                "biological_control": ["Trichogramma chilonis release", "Chrysoperla carnea"],
                "preventive": ["Early sowing", "Trap crops (marigold)", "Deep summer ploughing"],
                "economic_threshold": "8-10 larvae/100 plants"
            },
            "aphid": {
                "crops": ["mustard", "wheat", "cotton", "potato"],
                "symptoms": ["Yellowing leaves", "Honeydew secretion", "Sooty mold", "Curled leaves"],
                "organic_control": ["Neem oil 3% spray", "Soap solution", "Yellow sticky traps"],
                "chemical_control": ["Imidacloprid 17.8 SL", "Acetamiprid 20 SP", "Thiamethoxam"],
                "biological_control": ["Ladybird beetles", "Aphidius colemani"],
                "preventive": ["Timely sowing", "Avoid excessive nitrogen", "Remove weeds"],
                "economic_threshold": "20-30 aphids/leaf"
            },
            "whitefly": {
                "crops": ["cotton", "tomato", "brinjal"],
                "symptoms": ["Yellowing", "Honeydew", "Sooty mold", "Viral transmission"],
                "organic_control": ["Neem oil 5%", "Yellow sticky traps", "NSKE 5%"],
                "chemical_control": ["Buprofezin 25 SC", "Pyriproxyfen", "Dinotefuran"],
                "biological_control": ["Encarsia formosa", "Chrysoperla"],
                "preventive": ["Remove alternate hosts", "Use reflective mulch"],
                "economic_threshold": "5-6 adults/leaf"
            },
            "stem_borer": {
                "crops": ["rice", "maize", "sugarcane"],
                "symptoms": ["Dead heart in rice", "Bored stems", "Frass at base", "Lodging"],
                "organic_control": ["Pheromone traps", "Release Trichogramma", "Neem cake application"],
                "chemical_control": ["Chlorantraniliprole", "Flubendiamide", "Cartap hydrochloride"],
                "biological_control": ["Trichogramma japonicum", "Cotesia flavipes"],
                "preventive": ["Destroy stubbles", "Light trap monitoring", "Resistant varieties"],
                "economic_threshold": "10% dead hearts"
            },
            "thrips": {
                "crops": ["cotton", "onion", "chili", "groundnut"],
                "symptoms": ["Silvery streaks on leaves", "Distorted growth", "Flower drop", "Reduced yield"],
                "organic_control": ["Neem oil 3%", "NSKE 5%", "Blue sticky traps"],
                "chemical_control": ["Spinosad", "Fipronil", "Thiamethoxam"],
                "biological_control": ["Predatory mites", "Orius bugs"],
                "preventive": ["Intercropping with maize", "Avoid monocropping", "Reflective mulch"],
                "economic_threshold": "10-12 thrips/leaf"
            },
            "fruit_borer": {
                "crops": ["tomato", "brinjal", "okra", "pigeon pea"],
                "symptoms": ["Holes in fruits", "Frass inside fruits", "Premature fruit drop"],
                "organic_control": ["Pheromone traps", "HaNPV/SlNPV", "Neem oil 3%"],
                "chemical_control": ["Spinosad", "Emamectin benzoate", "Indoxacarb"],
                "biological_control": ["Trichogramma", "Bacillus thuringiensis"],
                "preventive": ["Collection and destruction of infested fruits", "Crop rotation"],
                "economic_threshold": "5% fruit damage"
            },
            "jassid": {
                "crops": ["cotton", "brinjal", "okra"],
                "symptoms": ["Yellowing between veins", "Leaf curling", "Stunted growth"],
                "organic_control": ["Neem oil 3%", "NSKE 5%", "Yellow sticky traps"],
                "chemical_control": ["Acetamiprid", "Thiamethoxam", "Imidacloprid"],
                "biological_control": ["Ladybird beetles", "Lacewings"],
                "preventive": ["Resistant varieties", "Avoid excessive nitrogen"],
                "economic_threshold": "2-3 jassids/leaf"
            },
            "root_knot_nematode": {
                "crops": ["tomato", "brinjal", "okra", "chili"],
                "symptoms": ["Galls on roots", "Yellowing", "Stunted growth", "Wilting"],
                "organic_control": ["Neem cake 200 kg/acre", "Paecilomyces lilacinus", "Marigold intercropping"],
                "chemical_control": ["Carbofuran 3G", "Phorate 10G", "Fosthiazate"],
                "biological_control": ["Pseudomonas fluorescens", "Trichoderma viride"],
                "preventive": ["Soil solarization", "Crop rotation with cereals", "Use resistant varieties"],
                "economic_threshold": "5 galls/plant"
            },
        }

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        crop = context.get("target_crop", "").lower()

        # Find relevant pests for the crop
        relevant_pests = []
        for pest_name, data in self.pest_db.items():
            if crop in [c.lower() for c in data["crops"]]:
                relevant_pests.append({
                    "pest_name": pest_name.replace("_", " ").title(),
                    "symptoms": data["symptoms"],
                    "organic_control": data["organic_control"],
                    "chemical_control": data["chemical_control"],
                    "biological_control": data["biological_control"],
                    "preventive_measures": data["preventive"],
                    "economic_threshold": data["economic_threshold"],
                    "monitoring_schedule": "Weekly scouting during vulnerable stages"
                })

        state["pest_detection"] = {
            "crop": crop.title() if crop else "General",
            "common_pests": relevant_pests,
            "ipm_strategy": self._generate_ipm_plan(crop, relevant_pests),
            "monitoring_calendar": self._get_monitoring_calendar(crop)
        }

        self._add_message(state, f"Pest management plan for {crop}: {len(relevant_pests)} common pests identified.", {"pest_count": len(relevant_pests)}, "high")
        return state

    def _generate_ipm_plan(self, crop: str, pests: list) -> list:
        plan = [
            "🌱 CULTURAL CONTROL: Deep summer ploughing, crop rotation, timely sowing",
            "🪤 MECHANICAL CONTROL: Pheromone traps, light traps, sticky traps, bird perches",
            "🦠 BIOLOGICAL CONTROL: Conservation of natural enemies, release of biocontrol agents",
            "🧪 CHEMICAL CONTROL: Use pesticides only when ETL is crossed. Prefer bio-pesticides.",
            "🌾 RESISTANT VARIETIES: Use pest-resistant varieties where available"
        ]
        return plan

    def _get_monitoring_calendar(self, crop: str) -> list:
        calendars = {
            "cotton": ["Vegetative: Weekly jassid count", "Flowering: Bollworm egg count", "Boll formation: Boll damage assessment"],
            "rice": ["Nursery: Stem borer monitoring", "Tillering: Dead heart count", "Flowering: White earhead count"],
            "tomato": ["Vegetative: Whitefly count", "Flowering: Fruit borer monitoring", "Fruiting: Damage assessment"],
        }
        return calendars.get(crop, ["Weekly general scouting", "Monitor for visible damage", "Count pest population"])
