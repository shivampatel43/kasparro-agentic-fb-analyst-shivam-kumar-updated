from src.agents.planner_agent import PlannerAgent


def test_planner_builds_four_steps():
    planner = PlannerAgent()
    plan = planner.build_plan("Analyze ROAS drop")
    assert len(plan.steps) == 4
    agents = [s.agent for s in plan.steps]
    assert agents == ["DataAgent", "InsightAgent", "EvaluatorAgent", "CreativeAgent"]
