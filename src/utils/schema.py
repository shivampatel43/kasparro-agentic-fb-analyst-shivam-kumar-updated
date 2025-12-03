from dataclasses import dataclass
from typing import List, Set

import pandas as pd


EXPECTED_COLUMNS: Set[str] = {
    "campaign_name",
    "adset_name",
    "date",
    "spend",
    "impressions",
    "clicks",
    "ctr",
    "purchases",
    "revenue",
    "roas",
    "creative_type",
    "creative_message",
    "audience_type",
    "platform",
    "country",
}


@dataclass
class SchemaValidationResult:
    ok: bool
    missing: List[str]
    extra: List[str]


def validate_schema(df: pd.DataFrame) -> SchemaValidationResult:
    cols = set(df.columns)
    missing = sorted(list(EXPECTED_COLUMNS - cols))
    extra = sorted(list(cols - EXPECTED_COLUMNS))
    ok = len(missing) == 0
    return SchemaValidationResult(ok=ok, missing=missing, extra=extra)
