import json
import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import yaml

from src.agents.planner_agent import PlannerAgent
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.creative_agent import CreativeAgent
from src.utils.logging_utils import setup_logger, log_event
from src.utils.metrics import timed


def load_config(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs(config: Dict[str, Any]) -> None:
    for key in ("insights_json", "creatives_json", "report_md", "log_file"):
        p = Path(config["paths"][key])
        p.parent.mkdir(parents=True, exist_ok=True)


def run_pipeline(user_query: str, config_path: str = "config/config.yaml") -> None:
    config = load_config(config_path)
    ensure_dirs(config)

    logger = setup_logger(config["paths"]["log_file"])
    log_event(
        logger,
        agent="Orchestrator",
        stage="start",
        event="pipeline_start",
        extra={"user_query": user_query},
    )

    metrics: Dict[str, float] = {}

    with timed(metrics, "data_agent_ms"):
        data_agent = DataAgent(date_column=config["data"]["date_column"])
        data_summary = data_agent.load_and_validate(config["data"]["path"])

    if not data_summary.schema_result.ok:
        log_event(
            logger,
            level=logging.ERROR,
            agent="DataAgent",
            stage="schema",
            event="schema_validation_failed",
            status="error",
            extra={
                "missing_columns": data_summary.schema_result.missing,
                "extra_columns": data_summary.schema_result.extra,
            },
        )
        raise SystemExit("Schema validation failed. See logs for details.")

    with timed(metrics, "planner_ms"):
        planner = PlannerAgent()
        plan = planner.build_plan(user_query)
        plan_dict = planner.to_dict(plan)
        log_event(
            logger,
            agent="PlannerAgent",
            stage="plan",
            event="plan_built",
            extra={"plan": plan_dict},
        )

    with timed(metrics, "insight_agent_ms"):
        insight_agent = InsightAgent(logger)
        insight_input = data_agent.summarize_for_insight(data_summary)
        hypotheses = insight_agent.generate(user_query, insight_input)
        hypotheses_dict = insight_agent.to_dict(hypotheses)

    with timed(metrics, "evaluator_agent_ms"):
        evaluator_agent = EvaluatorAgent(logger)
        evaluated = evaluator_agent.evaluate(data_summary.full_df, hypotheses)
        evaluated_dict = evaluator_agent.to_dict(evaluated)

    with timed(metrics, "creative_agent_ms"):
        creative_agent = CreativeAgent(
            logger,
            low_ctr_threshold=config["thresholds"]["low_ctr"],
            low_roas_threshold=config["thresholds"]["low_roas"],
        )
        creatives = creative_agent.generate(data_summary.full_df)
        creatives_dict = creative_agent.to_dict(creatives)

    insights_path = Path(config["paths"]["insights_json"])
    creatives_path = Path(config["paths"]["creatives_json"])
    report_path = Path(config["paths"]["report_md"])

    with insights_path.open("w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    **item,
                    "evaluated": next(
                        (
                            ed
                            for ed in evaluated_dict
                            if ed["id"] == item["id"]
                        ),
                        None,
                    ),
                }
                for item in hypotheses_dict
            ],
            f,
            indent=2,
        )

    with creatives_path.open("w", encoding="utf-8") as f:
        json.dump(creatives_dict, f, indent=2)

    with report_path.open("w", encoding="utf-8") as f:
        f.write(
            _build_report_md(
                user_query,
                data_summary.full_df,
                evaluated_dict,
                creatives_dict,
                metrics,
            )
        )

    log_event(
        logger,
        agent="Orchestrator",
        stage="end",
        event="pipeline_finished",
        extra={"metrics": metrics},
    )


def _build_report_md(
    user_query: str,
    df: pd.DataFrame,
    evaluated_hypotheses: list[dict[str, Any]],
    creatives: list[dict[str, Any]],
    metrics: Dict[str, float],
) -> str:
    lines: list[str] = []
    lines.append("# Facebook ROAS Analysis\n")
    lines.append("## User query\n\n")
    lines.append(f"> {user_query}\n")
    lines.append("## Data overview\n")
    lines.append(f"- Rows: **{len(df)}**\n")
    if "campaign_name" in df.columns:
        lines.append(f"- Campaigns: **{df['campaign_name'].nunique()}**\n")
    if "date" in df.columns:
        lines.append(f"- Date range: **{df['date'].min()}** → **{df['date'].max()}**\n")
    if "roas" in df.columns:
        lines.append(f"- ROAS: mean={df['roas'].mean():.2f}, min={df['roas'].min():.2f}, max={df['roas'].max():.2f}\n")

    lines.append("\n## Hypotheses & evaluation\n")
    for h in evaluated_hypotheses:
        lines.append(f"### {h['id']}: {h['statement']}\n")
        lines.append(f"- Result: **{h['validation_result']}**\n")
        lines.append(f"- Confidence: **{h['confidence_score']:.2f}**\n")
        lines.append(f"- Evidence: {h['evidence']}\n\n")

    lines.append("## Creative recommendations (for low CTR / low ROAS)\n")
    if not creatives:
        lines.append("No underperforming ads met the low CTR / low ROAS thresholds.\n")
    else:
        for c in creatives:
            lines.append(f"### {c['campaign_name']} / {c['adset_name']}\n")
            lines.append(f"- Old message: {c['old_message']}\n")
            lines.append(f"- New headline: {c['new_headline']}\n")
            lines.append(f"- New primary text: {c['new_primary_text']}\n")
            lines.append(f"- New CTA: **{c['new_cta']}**\n")
            lines.append(f"- Rationale: {c['rationale']}\n\n")

    lines.append("## Runtime metrics (ms)\n")
    for k, v in metrics.items():
        lines.append(f"- {k}: {v:.1f}\n")

    return "".join(lines)
