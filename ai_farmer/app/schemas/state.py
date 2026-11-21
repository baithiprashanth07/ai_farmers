"""Shared state definition for the AI Farmer multi-agent graph."""
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


class FarmContext(TypedDict, total=False):
    """Farm-specific context passed between agents."""
    farmer_id: str
    farm_location: Dict[str, float]  # lat, lon
    state: str
    district: str
    soil_type: Optional[str]
    farm_size_acres: Optional[float]
    season: Optional[str]
    budget_inr: Optional[float]
    previous_crop: Optional[str]
    irrigation_type: Optional[str]  # drip, sprinkler, flood, rainfed
    language_preference: Optional[str]


class AgentMessage(TypedDict):
    """Message format for inter-agent communication."""
    agent_name: str
    message: str
    timestamp: str
    data: Dict[str, Any]
    priority: str  # low, medium, high, critical


class AI_Farmer_State(TypedDict, total=False):
    """
    Central state object for the LangGraph multi-agent system.
    All agents read from and write to this shared state.
    """
    # Input
    user_query: str
    farm_context: FarmContext
    uploaded_image_path: Optional[str]
    request_id: str
    language_preference: str

    # Agent Outputs
    crop_recommendations: List[Dict[str, Any]]
    state_crop_intelligence: Dict[str, Any]
    variety_recommendations: List[Dict[str, Any]]
    seed_recommendations: List[Dict[str, Any]]
    sowing_plan: Dict[str, Any]
    weather_forecast: Dict[str, Any]
    irrigation_plan: Dict[str, Any]
    fertilizer_plan: Dict[str, Any]
    soil_health_report: Dict[str, Any]
    nutrient_deficiency: Dict[str, Any]
    disease_detection: Dict[str, Any]
    pest_detection: Dict[str, Any]
    medicine_recommendations: List[Dict[str, Any]]
    yield_prediction: Dict[str, Any]
    market_price_prediction: Dict[str, Any]
    profit_prediction: Dict[str, Any]
    government_schemes: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    farm_records: List[Dict[str, Any]]
    agronomist_advice: str

    # Workflow
    active_agents: List[str]
    completed_agents: List[str]
    agent_queue: List[str]
    next_agent: str
    current_agent_name: str
    agent_messages: List[AgentMessage]
    errors: List[str]

    # Final Output
    final_report: Dict[str, Any]
    response_to_user: str


def format_agent_message(agent_name: str, message: str, data: Dict[str, Any] = None, priority: str = "medium") -> Dict[str, Any]:
    """Format an agent message for the state."""
    return {
        "agent_name": agent_name,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data or {},
        "priority": priority
    }
