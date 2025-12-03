from dataclasses import dataclass
from typing import List, Dict, Any

from src.utils.retry import retry
from src.utils.logging_utils import log_event
import logging


@dataclass
class Hypothesis:
    id: str
    statement: str
    mechanism: str
    expected_signals: str
    confidence: str  # "low" | "medium" | "high"


class InsightAgent:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def _fallback_generate(
        self, user_query: str, data_summary: Dict[str, Any]
    ) -> List[Hypothesis]:
        # Very simple, deterministic hypotheses based on trends
        roas_by_date = data_summary.get("roas_by_date", {})
        ctr_by_date = data_summary.get("ctr_by_date", {})

        hypothesis_list: List[Hypothesis] = []

        if len(roas_by_date) >= 2:
            sorted_dates = sorted(roas_by_date.keys())
            first, last = sorted_dates[0], sorted_dates[-1]
            roas_change = roas_by_date[last] - roas_by_date[first]
            if roas_change < 0:
                hypothesis_list.append(
                    Hypothesis(
                        id="h1",
                        statement="ROAS decreased over time, possibly due to creative fatigue or audience saturation.",
                        mechanism="Later dates show lower average ROAS than earlier dates, while spend stays similar.",
                        expected_signals="Declining ROAS and CTR for the same creative_message or audience_type.",
                        confidence="medium",
                    )
                )
            else:
                hypothesis_list.append(
                    Hypothesis(
                        id="h1",
                        statement="ROAS improved over time, possibly due to better audience targeting or creatives.",
                        mechanism="Later dates show higher average ROAS than earlier dates.",
                        expected_signals="Increasing ROAS and CTR for key campaigns/adsets.",
                        confidence="medium",
                    )
                )

        if not hypothesis_list:
            hypothesis_list.append(
                Hypothesis(
                    id="h-generic",
                    statement="ROAS variation seems stable; small fluctuations may be noise.",
                    mechanism="No strong monotonic trend visible in ROAS by date.",
                    expected_signals="ROAS by date roughly flat.",
                    confidence="low",
                )
            )
        return hypothesis_list

    @retry(on_retry=lambda attempt, exc: logging.getLogger("kasparro").warning(
        "InsightAgent retry", extra={"extra_fields": {"agent": "InsightAgent", "stage": "generate", "event": "retry", "status": "retrying", "attempt": attempt, "error": str(exc)}}  # type: ignore[arg-type]
    ))
    def _generate_internal(
        self, user_query: str, data_summary: Dict[str, Any]
    ) -> List[Hypothesis]:
        # This is where you'd call an LLM; we keep it deterministic and safe.
        # To simulate occasional transient failure for retry testing, you could
        # deliberately raise an exception based on input; we keep it stable here.
        return self._fallback_generate(user_query, data_summary)

    def generate(
        self, user_query: str, data_summary: Dict[str, Any]
    ) -> List[Hypothesis]:
        try:
            hypotheses = self._generate_internal(user_query, data_summary)
            log_event(
                self.logger,
                agent="InsightAgent",
                stage="generate",
                event="generated_hypotheses",
                extra={"count": len(hypotheses)},
            )
            return hypotheses
        except Exception as exc:  # noqa: BLE001
            log_event(
                self.logger,
                level=logging.ERROR,
                agent="InsightAgent",
                stage="generate",
                event="fallback_after_error",
                status="error",
                extra={"error": str(exc)},
            )
            # Last-resort fallback to keep pipeline running
            return self._fallback_generate(user_query, data_summary)

    def to_dict(self, hypotheses: List[Hypothesis]) -> List[Dict[str, Any]]:
        return [
            {
                "id": h.id,
                "statement": h.statement,
                "mechanism": h.mechanism,
                "expected_signals": h.expected_signals,
                "confidence": h.confidence,
            }
            for h in hypotheses
        ]
