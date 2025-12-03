import logging
import pandas as pd

from src.agents.creative_agent import CreativeAgent


def test_creative_agent_generates_for_low_ctr_low_roas():
    logger = logging.getLogger("test_creative")
    df = pd.DataFrame(
        {
            "campaign_name": ["Test Campaign"],
            "adset_name": ["Test Adset"],
            "creative_message": ["Buy now"],
            "audience_type": ["prospecting"],
            "ctr": [0.001],
            "roas": [0.5],
        }
    )

    agent = CreativeAgent(logger, low_ctr_threshold=0.01, low_roas_threshold=1.0)
    recs = agent.generate(df)
    assert len(recs) == 1
    assert "Limited time offer" in recs[0].new_headline
