from app.graph import supervisor


def test_selected_agents_receive_prior_agent_messages(monkeypatch):
    observed = []

    class StubAgent:
        def __init__(self, name):
            self.name = name

        def run(self, state):
            agent_name = state["current_agent_name"]
            observed.append((agent_name, [message["agent_name"] for message in state["agent_messages"]]))
            state["agent_messages"].append({
                "agent_name": agent_name,
                "message": f"{agent_name} findings",
                "timestamp": "2026-01-01T00:00:00",
                "data": {},
                "priority": "medium",
            })
            state["completed_agents"].append(agent_name)
            state["active_agents"] = []
            return state

    monkeypatch.setattr(supervisor, "AGENTS", {
        "crop_advisor": StubAgent("crop_advisor"),
        "soil_advisor": StubAgent("soil_advisor"),
        "ai_agronomist_assistant": StubAgent("ai_agronomist_assistant"),
    })
    monkeypatch.setattr(
        supervisor,
        "supervisor_router",
        lambda state: ["crop_advisor", "soil_advisor", "ai_agronomist_assistant"],
    )

    graph = supervisor.build_graph()
    result = graph.invoke(
        {"request_id": "workflow-test", "agent_messages": [], "completed_agents": []},
        config={"configurable": {"thread_id": "workflow-test"}},
    )

    assert [name for name, _ in observed] == [
        "crop_advisor",
        "soil_advisor",
        "ai_agronomist_assistant",
    ]
    assert observed[1][1] == ["crop_advisor"]
    assert observed[2][1] == ["crop_advisor", "soil_advisor"]
    assert result["completed_agents"] == [name for name, _ in observed]
