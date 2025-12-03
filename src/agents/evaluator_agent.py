from dataclasses import dataclass
from typing import List, Dict, Any

import pandas as pd
import logging

from src.agents.insight_agent import Hypothesis
from src.utils.retry import retry
from src.utils.logging_utils import log_event


@dataclass
class EvaluatedHypothesis:
    id: str
    statement: str
    validation_result: str  # "supported" | "inconclusive" | "rejected"
    confidence_score: float
    evidence: str


class EvaluatorAgent:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def _fallback_evaluate(
        self, df: pd.DataFrame, hypotheses: List[Hypothesis]
    ) -> List[EvaluatedHypothesis]:
        # Simple rule-based evaluation: check ROAS trend overall.
        results: List[EvaluatedHypothesis] = []
        if "date" not in df.columns or "roas" not in df.columns:
            for h in hypotheses:
                results.append(
                    EvaluatedHypothesis(
                        id=h.id,
                        statement=h.statement,
                        validation_result="inconclusive",
                        confidence_score=0.3,
                        evidence="Required columns for trend analysis are missing.",
                    )
                )
            return results

        roas_by_date = df.groupby("date")["roas"].mean().sort_index()
        dates = list(roas_by_date.index)
        if len(dates) >= 2:
            first, last = dates[0], dates[-1]
            roas_change = roas_by_date.loc[last] - roas_by_date.loc[first]
        else:
            roas_change = 0.0

        for h in hypotheses:
            if "decreased" in h.statement.lower():
                if roas_change < 0:
                    result = "supported"
                    score = 0.8
                    evidence = f"Average ROAS decreased from {roas_by_date.iloc[0]:.2f} to {roas_by_date.iloc[-1]:.2f}."
                else:
                    result = "rejected"
                    score = 0.4
                    evidence = "ROAS did not show a clear downward trend over time."
            elif "improved" in h.statement.lower():
                if roas_change > 0:
                    result = "supported"
                    score = 0.8
                    evidence = f"Average ROAS increased from {roas_by_date.iloc[0]:.2f} to {roas_by_date.iloc[-1]:.2f}."
                else:
                    result = "rejected"
                    score = 0.4
                    evidence = "ROAS did not show a clear upward trend over time."
            else:
                result = "inconclusive"
                score = 0.5
                evidence = "Hypothesis is generic; data neither strongly supports nor rejects it."

            results.append(
                EvaluatedHypothesis(
                    id=h.id,
                    statement=h.statement,
                    validation_result=result,
                    confidence_score=score,
                    evidence=evidence,
                )
            )
        return results

    @retry(on_retry=lambda attempt, exc: logging.getLogger("kasparro").warning(
        "EvaluatorAgent retry", extra={"extra_fields": {"agent": "EvaluatorAgent", "stage": "evaluate", "event": "retry", "status": "retrying", "attempt": attempt, "error": str(exc)}}  # type: ignore[arg-type]
    ))
    def _evaluate_internal(
        self, df: pd.DataFrame, hypotheses: List[Hypothesis]
    ) -> List[EvaluatedHypothesis]:
        # Place for LLM + stats combo; here we keep deterministic.
        return self._fallback_evaluate(df, hypotheses)

    def evaluate(
        self, df: pd.DataFrame, hypotheses: List[Hypothesis]
    ) -> List[EvaluatedHypothesis]:
        try:
            evaluated = self._evaluate_internal(df, hypotheses)
            log_event(
                self.logger,
                agent="EvaluatorAgent",
                stage="evaluate",
                event="evaluated_hypotheses",
                extra={"count": len(evaluated)},
            )
            return evaluated
        except Exception as exc:  # noqa: BLE001
            log_event(
                self.logger,
                level=logging.ERROR,
                agent="EvaluatorAgent",
                stage="evaluate",
                event="fallback_after_error",
                status="error",
                extra={"error": str(exc)},
            )
            return self._fallback_evaluate(df, hypotheses)

    def to_dict(self, evaluated: List[EvaluatedHypothesis]) -> List[Dict[str, Any]]:
        return [
            {
                "id": e.id,
                "statement": e.statement,
                "validation_result": e.validation_result,
                "confidence_score": e.confidence_score,
                "evidence": e.evidence,
            }
            for e in evaluated
        ]
