from pathlib import Path

from src.agents.data_agent import DataAgent
from src.utils.schema import EXPECTED_COLUMNS


def test_data_agent_loads_and_summarizes(tmp_path):
    # copy sample csv to tmp to avoid path issues
    src = Path("data/sample_fb_ads.csv")
    dst = tmp_path / "sample.csv"
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    agent = DataAgent()
    summary = agent.load_and_validate(str(dst))

    assert set(summary.full_df.columns) >= EXPECTED_COLUMNS
    assert summary.roas_by_date  # non-empty
    assert summary.ctr_by_date
    assert summary.schema_result.ok
