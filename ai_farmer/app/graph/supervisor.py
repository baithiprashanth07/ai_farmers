"""LangGraph-based multi-agent orchestration for AI Farmer."""
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from app.schemas.state import AI_Farmer_State
from app.utils import logger, generate_request_id
from app.agents import (
    CropRecommendationAgent, WeatherAgent, SoilHealthAgent,
    DiseaseDetectionAgent, FertilizerPlannerAgent, IrrigationPlannerAgent,
    MarketPriceAgent, GovSchemeAgent, RiskPredictorAgent, AgronomistAgent,
    SeedRecommendationAgent, SowingPlannerAgent, PestDetectionAgent,
    FarmRecordManagerAgent, StateCropIntelligenceAgent
)

# Initialize the specialized agent workflows.
AGENTS = {
    "crop_recommendation": CropRecommendationAgent(),
    "state_crop_intelligence": StateCropIntelligenceAgent(),
    "seed_recommendation": SeedRecommendationAgent(),
    "sowing_planner": SowingPlannerAgent(),
    "weather_forecast": WeatherAgent(),
    "irrigation_planner": IrrigationPlannerAgent(),
    "fertilizer_planner": FertilizerPlannerAgent(),
    "soil_health_analyzer": SoilHealthAgent(),
    "nutrient_deficiency_detector": SoilHealthAgent(),  # Reuses soil agent for nutrient detection
    "disease_detection": DiseaseDetectionAgent(),
    "pest_detection": PestDetectionAgent(),
    "medicine_recommendation": DiseaseDetectionAgent(),  # Reuses disease agent
    "yield_prediction": MarketPriceAgent(),  # Reuses market agent
    "market_price_prediction": MarketPriceAgent(),
    "profit_prediction": MarketPriceAgent(),
    "government_scheme_advisor": GovSchemeAgent(),
    "farm_risk_predictor": RiskPredictorAgent(),
    "farm_record_manager": FarmRecordManagerAgent(),
    "ai_agronomist_assistant": AgronomistAgent(),
}

# Define routing logic based on user intent
def supervisor_router(state: AI_Farmer_State) -> List[str]:
    """Determine which agents to run based on user intent and farm context."""
    query = state.get("user_query", "").lower()
    context = state.get("farm_context", {})
    target = context.get("target_crop")
    has_image = state.get("uploaded_image_path") is not None

    # Core pipeline - always run for comprehensive analysis
    to_run = [
        "crop_recommendation",
        "state_crop_intelligence",
        "weather_forecast",
        "soil_health_analyzer",
    ]

    # If target crop is specified, run crop-specific agents
    if target:
        to_run.extend([
            "seed_recommendation",
            "sowing_planner",
            "fertilizer_planner",
            "irrigation_planner",
            "yield_prediction",
            "market_price_prediction",
            "profit_prediction",
            "pest_detection",
        ])

    # If image uploaded, run detection agents
    if has_image:
        to_run.extend(["disease_detection", "medicine_recommendation"])

    # Conditional based on query keywords
    if any(kw in query for kw in ["scheme", "subsidy", "government", "pm-kisan", "insurance"]):
        to_run.append("government_scheme_advisor")

    if any(kw in query for kw in ["risk", "insurance", "loss", "danger", "problem"]):
        to_run.append("farm_risk_predictor")

    if any(kw in query for kw in ["record", "history", "expense", "income", "diary"]):
        to_run.append("farm_record_manager")

    if any(kw in query for kw in ["nutrient", "deficiency", "yellow", "chlorosis"]):
        to_run.append("nutrient_deficiency_detector")

    # Always run risk and scheme at least once for comprehensive report
    if "farm_risk_predictor" not in to_run:
        to_run.append("farm_risk_predictor")
    if "government_scheme_advisor" not in to_run:
        to_run.append("government_scheme_advisor")

    # Always end with agronomist for comprehensive advice
    to_run.append("ai_agronomist_assistant")

    # Remove duplicates while preserving order
    seen = set()
    unique_to_run = []
    for x in to_run:
        if x not in seen:
            seen.add(x)
            unique_to_run.append(x)

    logger.info(f"Supervisor routing to {len(unique_to_run)} agents: {unique_to_run}")
    return unique_to_run

def create_agent_node(agent_name: str):
    """Create a LangGraph node for an agent."""
    agent = AGENTS[agent_name]
    def node(state: AI_Farmer_State) -> AI_Farmer_State:
        state["current_agent_name"] = agent_name
        result = agent.run(state)
        result.pop("current_agent_name", None)
        return result
    return node

def build_graph():
    """Build a sequential workflow so each agent can use earlier findings."""
    workflow = StateGraph(AI_Farmer_State)

    # Add all agent nodes
    for name in AGENTS:
        workflow.add_node(name, create_agent_node(name))

    def dispatch(state: AI_Farmer_State) -> AI_Farmer_State:
        queue = state.get("agent_queue", [])
        if queue:
            state["next_agent"] = queue.pop(0)
        else:
            state["next_agent"] = "ai_agronomist_assistant"
        return state

    workflow.add_node("agent_dispatch", dispatch)

    # Add supervisor node
    def supervisor(state: AI_Farmer_State) -> AI_Farmer_State:
        to_run = supervisor_router(state)
        state["agent_queue"] = [
            name for name in to_run if name != "ai_agronomist_assistant"
        ]
        state["active_agents"] = []
        state["completed_agents"] = []
        state["request_id"] = state.get("request_id", generate_request_id())
        logger.info(f"[{state['request_id']}] Supervisor: Routing to {len(to_run)} agents")
        return state

    workflow.add_node("supervisor", supervisor)

    # Agents run one at a time; each handoff receives the updated shared state.
    workflow.set_entry_point("supervisor")
    workflow.add_edge("supervisor", "agent_dispatch")
    workflow.add_conditional_edges(
        "agent_dispatch",
        lambda state: state["next_agent"],
        {name: name for name in AGENTS},
    )
    for name in AGENTS:
        if name == "ai_agronomist_assistant":
            continue
        workflow.add_edge(name, "agent_dispatch")
    workflow.add_edge("ai_agronomist_assistant", END)

    # Compile with memory checkpointing
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Global graph instance
ai_farmer_graph = build_graph()
