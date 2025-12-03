import logging

from src.agents.insight_agent import InsightAgent


def test_insight_agent_generates_hypotheses():
    logger = logging.getLogger("test_insight")
    agent = InsightAgent(logger)
    data_summary = {
        "roas_by_date": {"2024-01-01": 5.0, "2024-01-10": 2.0},
        "ctr_by_date": {"2024-01-01": 0.02, "2024-01-10": 0.01},
    }
    hypotheses = agent.generate("Analyze ROAS drop", data_summary)
    assert len(hypotheses) >= 1
    assert any("ROAS decreased" in h.statement for h in hypotheses)
