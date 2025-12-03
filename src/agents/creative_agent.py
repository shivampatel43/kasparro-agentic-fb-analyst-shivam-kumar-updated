from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd
import logging

from src.utils.logging_utils import log_event


@dataclass
class CreativeRecommendation:
    campaign_name: str
    adset_name: str
    old_message: str
    new_headline: str
    new_primary_text: str
    new_cta: str
    rationale: str


class CreativeAgent:
    def __init__(self, logger: logging.Logger, low_ctr_threshold: float, low_roas_threshold: float) -> None:
        self.logger = logger
        self.low_ctr_threshold = low_ctr_threshold
        self.low_roas_threshold = low_roas_threshold

    def _generate_for_row(self, row: pd.Series) -> CreativeRecommendation:
        base_message = str(row.get("creative_message", "")).strip()
        if not base_message:
            base_message = "Our new collection is here."

        campaign_name = str(row.get("campaign_name", "Unknown Campaign"))
        adset_name = str(row.get("adset_name", "Unknown Adset"))

        new_headline = f"{campaign_name}: Limited time offer"
        new_primary_text = f"{base_message} Now with special pricing for {row.get('audience_type', 'your audience')}."
        new_cta = "Shop now"

        rationale = (
            "Existing message appears to underperform on CTR/ROAS. "
            "Headline emphasises urgency, body text adds value, CTA is explicit."
        )

        return CreativeRecommendation(
            campaign_name=campaign_name,
            adset_name=adset_name,
            old_message=base_message,
            new_headline=new_headline,
            new_primary_text=new_primary_text,
            new_cta=new_cta,
            rationale=rationale,
        )

    def generate(self, df: pd.DataFrame) -> List[CreativeRecommendation]:
        mask_low = (df["ctr"] < self.low_ctr_threshold) | (df["roas"] < self.low_roas_threshold)
        candidates = df[mask_low]

        recs = [self._generate_for_row(row) for _, row in candidates.iterrows()]
        log_event(
            self.logger,
            agent="CreativeAgent",
            stage="generate",
            event="generated_creatives",
            extra={"count": len(recs)},
        )
        return recs

    def to_dict(self, recs: List[CreativeRecommendation]) -> List[Dict[str, Any]]:
        return [
            {
                "campaign_name": r.campaign_name,
                "adset_name": r.adset_name,
                "old_message": r.old_message,
                "new_headline": r.new_headline,
                "new_primary_text": r.new_primary_text,
                "new_cta": r.new_cta,
                "rationale": r.rationale,
            }
            for r in recs
        ]
