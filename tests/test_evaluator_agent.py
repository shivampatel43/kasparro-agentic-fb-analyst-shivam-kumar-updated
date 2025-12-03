import logging
import pandas as pd

from src.agents.insight_agent import Hypothesis
from src.agents.evaluator_agent import EvaluatorAgent


def test_evaluator_agent_evaluates_trend():
    logger = logging.getLogger("test_eval")
    agent = EvaluatorAgent(logger)

    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-10"],
            "roas": [5.0, 2.0],
        }
    )

    hypotheses = [
        Hypothesis(
            id="h1",
            statement="ROAS decreased over time, possibly due to creative fatigue or audience saturation.",
            mechanism="",
            expected_signals="",
            confidence="medium",
        )
    ]

    evaluated = agent.evaluate(df, hypotheses)
    assert evaluated[0].validation_result == "supported"
    assert evaluated[0].confidence_score > 0.5
