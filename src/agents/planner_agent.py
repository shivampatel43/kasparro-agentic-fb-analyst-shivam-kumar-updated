from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class PlanStep:
    id: str
    agent: str
    action: str
    depends_on: List[str]


@dataclass
class Plan:
    overall_goal: str
    steps: List[PlanStep]


class PlannerAgent:
    """Very small, deterministic planner.

    In a real system this could call an LLM; here we keep it simple and testable.
    """

    def build_plan(self, user_query: str) -> Plan:
        steps = [
            PlanStep(
                id="step-data",
                agent="DataAgent",
                action="summarize_data",
                depends_on=[],
            ),
            PlanStep(
                id="step-insight",
                agent="InsightAgent",
                action="generate_hypotheses",
                depends_on=["step-data"],
            ),
            PlanStep(
                id="step-evaluator",
                agent="EvaluatorAgent",
                action="evaluate_hypotheses",
                depends_on=["step-insight"],
            ),
            PlanStep(
                id="step-creative",
                agent="CreativeAgent",
                action="generate_creatives",
                depends_on=["step-evaluator"],
            ),
        ]
        goal = f"Diagnose ROAS changes and recommend creatives for query: {user_query}"
        return Plan(overall_goal=goal, steps=steps)

    def to_dict(self, plan: Plan) -> Dict[str, Any]:
        return {
            "overall_goal": plan.overall_goal,
            "steps": [
                {
                    "id": s.id,
                    "agent": s.agent,
                    "action": s.action,
                    "depends_on": s.depends_on,
                }
                for s in plan.steps
            ],
        }
