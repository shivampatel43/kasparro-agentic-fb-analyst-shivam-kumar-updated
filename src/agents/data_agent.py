from dataclasses import dataclass
from typing import Dict, Any

import pandas as pd

from src.utils.schema import validate_schema, SchemaValidationResult


@dataclass
class DataSummary:
    roas_by_date: Dict[str, float]
    ctr_by_date: Dict[str, float]
    top_roas_campaigns: Dict[str, float]
    bottom_roas_campaigns: Dict[str, float]
    low_ctr_rows: pd.DataFrame
    full_df: pd.DataFrame
    schema_result: SchemaValidationResult


class DataAgent:
    def __init__(self, date_column: str = "date") -> None:
        self.date_column = date_column

    def load_and_validate(self, path: str) -> DataSummary:
        df = pd.read_csv(path)
        schema_result = validate_schema(df)

        if not schema_result.ok:
            # We still return the summary but the orchestrator may decide to abort.
            # This makes behaviour explicit and testable.
            pass

        # compute basic summaries
        if self.date_column in df.columns:
            roas_by_date = df.groupby(self.date_column)["roas"].mean().to_dict()
            ctr_by_date = df.groupby(self.date_column)["ctr"].mean().to_dict()
        else:
            roas_by_date = {}
            ctr_by_date = {}

        top = (
            df.groupby("campaign_name")["roas"]
            .mean()
            .sort_values(ascending=False)
            .head(3)
            .to_dict()
        )
        bottom = (
            df.groupby("campaign_name")["roas"]
            .mean()
            .sort_values(ascending=True)
            .head(3)
            .to_dict()
        )

        # low CTR subset is computed by orchestrator based on thresholds;
        # here we just keep the full DF, but we use a dummy empty frame for the type.
        low_ctr_rows = df.iloc[0:0].copy()

        return DataSummary(
            roas_by_date=roas_by_date,
            ctr_by_date=ctr_by_date,
            top_roas_campaigns=top,
            bottom_roas_campaigns=bottom,
            low_ctr_rows=low_ctr_rows,
            full_df=df,
            schema_result=schema_result,
        )

    def summarize_for_insight(self, summary: DataSummary) -> Dict[str, Any]:
        return {
            "roas_by_date": summary.roas_by_date,
            "ctr_by_date": summary.ctr_by_date,
            "top_roas_campaigns": summary.top_roas_campaigns,
            "bottom_roas_campaigns": summary.bottom_roas_campaigns,
        }
