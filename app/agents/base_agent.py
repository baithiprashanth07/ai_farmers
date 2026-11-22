"""Base agent class for AI Farmer multi-agent system."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable
from datetime import datetime
import time
from app.schemas.state import AI_Farmer_State, format_agent_message
from app.utils import logger
from app.services.database import db_service


class BaseAgent(ABC):
    """
    Abstract base class for all AI Farmer agents.
    Each agent is a node in the LangGraph that reads from and writes to shared state.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.execution_count = 0

    def run(self, state: AI_Farmer_State) -> AI_Farmer_State:
        """
        Execute the agent with logging and error handling.
        This is the entry point called by LangGraph.
        """
        start_time = time.time()
        request_id = state.get("request_id", "unknown")
        agent_name = state.get("current_agent_name", self.name)
        messages_before = len(state.get("agent_messages", []))

        logger.info(f"[{request_id}] Executing agent: {agent_name}")

        try:
            # Mark agent as active
            state["active_agents"] = state.get("active_agents", []) + [agent_name]

            # Execute agent-specific logic
            result_state = self._execute(state)

            if len(result_state.get("agent_messages", [])) == messages_before:
                self._add_message(
                    result_state,
                    f"{agent_name} completed its analysis; findings are available to downstream agents.",
                    {"completed": True},
                )

            # Mark as completed
            result_state["completed_agents"] = result_state.get("completed_agents", []) + [agent_name]
            result_state["active_agents"] = [a for a in result_state.get("active_agents", []) if a != agent_name]

            execution_time = int((time.time() - start_time) * 1000)

            # Log execution
            db_service.log_agent_execution({
                "request_id": request_id,
                "agent_name": agent_name,
                "input": {"farm_context": state.get("farm_context", {})},
                "output": {"status": "success"},
                "execution_time_ms": execution_time,
                "status": "success"
            })

            self.execution_count += 1
            logger.info(f"[{request_id}] Agent {agent_name} completed in {execution_time}ms")

            return result_state

        except Exception as e:
            logger.error(f"[{request_id}] Agent {agent_name} failed: {e}")
            state["errors"] = state.get("errors", []) + [f"{agent_name}: {str(e)}"]
            state["active_agents"] = [a for a in state.get("active_agents", []) if a != agent_name]
            state["completed_agents"] = state.get("completed_agents", []) + [agent_name]
            if len(state.get("agent_messages", [])) == messages_before:
                self._add_message(
                    state,
                    f"{agent_name} could not complete its analysis.",
                    {"error": str(e)},
                    "high",
                )

            db_service.log_agent_execution({
                "request_id": request_id,
                "agent_name": self.name,
                "input": {},
                "output": {"error": str(e)},
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "status": "error"
            })

            return state

    @abstractmethod
    def _execute(self, state: AI_Farmer_State) -> AI_Farmer_State:
        """
        Implement agent-specific logic here.
        Must return the updated state.
        """
        pass

    def _get_farm_context(self, state: AI_Farmer_State) -> Dict[str, Any]:
        """Extract farm context from state."""
        return state.get("farm_context", {})

    def _add_message(self, state: AI_Farmer_State, message: str, data: Dict[str, Any] = None, priority: str = "medium"):
        """Add a message to the agent communication log."""
        msg = format_agent_message(state.get("current_agent_name", self.name), message, data, priority)
        state["agent_messages"] = state.get("agent_messages", []) + [msg]


    
