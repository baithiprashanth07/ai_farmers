"""Government Scheme Advisor Agent."""
from app.agents.base_agent import BaseAgent
from app.schemas.state import AI_Farmer_State
from app.services import gov_scheme_service_instance

class GovSchemeAgent(BaseAgent):
    """Recommends relevant government agricultural schemes."""

    def __init__(self):
        super().__init__("GovSchemeAgent", "Recommends relevant government schemes")

    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        context = self._get_farm_context(state)
        schemes = gov_scheme_service_instance.get_relevant_schemes(
            context.get("state", ""), 
            context.get("target_crop"), 
            context.get("farm_size_acres")
        )
        state["government_schemes"] = schemes
        self._add_message(state, f"Found {len(schemes)} relevant government schemes for farmer.", {"count": len(schemes)}, "medium")
        return state
