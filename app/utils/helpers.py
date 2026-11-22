"""Utility functions for AI Farmer."""
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
import random


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"AIF-{uuid.uuid4().hex[:12].upper()}"


def get_current_season() -> str:
    """Determine current agricultural season based on month."""
    month = datetime.now().month
    if month in [6, 7, 8, 9, 10]:
        return "kharif"
    elif month in [11, 12, 1, 2, 3]:
        return "rabi"
    else:
        return "zaid"


def get_state_soil_types(state: str) -> List[str]:
    """Return common soil types for a given Indian state."""
    soil_map = {
        "punjab": ["alluvial", "loamy"],
        "haryana": ["alluvial", "sandy"],
        "uttar pradesh": ["alluvial", "loamy", "clayey"],
        "bihar": ["alluvial", "clayey"],
        "west bengal": ["alluvial", "laterite"],
        "odisha": ["red", "laterite", "alluvial"],
        "madhya pradesh": ["black", "alluvial", "red"],
        "maharashtra": ["black", "laterite", "alluvial"],
        "gujarat": ["alluvial", "black", "saline"],
        "rajasthan": ["desert", "sandy", "saline"],
        "karnataka": ["red", "black", "laterite"],
        "tamil nadu": ["red", "black", "alluvial"],
        "andhra pradesh": ["red", "black", "alluvial"],
        "telangana": ["red", "black", "laterite"],
        "kerala": ["laterite", "alluvial"],
        "assam": ["alluvial", "loamy"],
    }
    return soil_map.get(state.lower(), ["alluvial", "loamy"])


def get_crop_seasonality(crop: str) -> List[str]:
    """Return suitable seasons for a crop."""
    season_map = {
        "rice": ["kharif"],
        "wheat": ["rabi"],
        "maize": ["kharif", "rabi"],
        "cotton": ["kharif"],
        "sugarcane": ["year_round"],
        "pulses": ["rabi", "zaid"],
        "mustard": ["rabi"],
        "groundnut": ["kharif", "rabi"],
        "soybean": ["kharif"],
        "potato": ["rabi", "zaid"],
        "tomato": ["year_round"],
        "onion": ["rabi", "kharif"],
        "chili": ["kharif", "rabi"],
        "turmeric": ["kharif"],
        "banana": ["year_round"],
        "mango": ["year_round"],
    }
    return season_map.get(crop.lower(), ["kharif", "rabi"])


def estimate_crop_yield(crop: str, soil_type: str, irrigation: str) -> float:
    """Estimate yield in quintals per acre based on crop and conditions."""
    base_yields = {
        "rice": 25, "wheat": 20, "maize": 30, "cotton": 8,
        "sugarcane": 350, "pulses": 8, "mustard": 10, "groundnut": 12,
        "soybean": 15, "potato": 120, "tomato": 80, "onion": 100,
        "chili": 15, "turmeric": 12, "banana": 200, "mango": 60
    }
    base = base_yields.get(crop.lower(), 15)

    # Soil modifier
    soil_mod = {"alluvial": 1.2, "black": 1.1, "loamy": 1.15, "red": 0.9, "sandy": 0.8, "clayey": 0.95}
    mod = soil_mod.get(soil_type.lower(), 1.0)

    # Irrigation modifier
    irr_mod = {"drip": 1.3, "sprinkler": 1.2, "flood": 1.0, "rainfed": 0.7, "subsurface": 1.25}
    mod *= irr_mod.get(irrigation.lower(), 1.0)

    return round(base * mod, 2)


def format_agent_message(agent_name: str, message: str, data: Dict[str, Any] = None, priority: str = "medium") -> Dict[str, Any]:
    """Format an agent message for the state."""
    return {
        "agent_name": agent_name,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
        "priority": priority
    }
