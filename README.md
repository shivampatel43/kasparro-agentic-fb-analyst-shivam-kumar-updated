# kasparro-agentic-fb-analyst-shivam-kumar

Agentic Facebook Performance Analyst assignment implementation.

## Quick start

```bash
# create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# install deps
pip install -r requirements.txt

# run main pipeline
python run.py "Analyze ROAS drop"
```

The command above will:

1. Load the sample dataset in `data/sample_fb_ads.csv`.
2. Run the multi‑agent pipeline:
   - Planner → Data → Insight → Evaluator → Creative.
3. Produce:
   - `reports/insights.json`
   - `reports/creatives.json`
   - `reports/report.md`
   - structured JSON logs in `logs/app.log`.

## Project structure

```text
config/
  config.yaml          # thresholds, paths, seeds

data/
  sample_fb_ads.csv    # small sample dataset
  README.md

logs/
  app.log              # structured JSON logs (created at runtime)

prompts/
  planner.md
  data.md
  insight.md
  evaluator.md
  creative.md

reports/
  report.md            # final marketer report
  insights.json        # hypotheses, confidence, evidence
  creatives.json       # creative recommendations

src/
  agents/
    planner_agent.py
    data_agent.py
    insight_agent.py
    evaluator_agent.py
    creative_agent.py
  orchestrator/
    main.py
  utils/
    logging_utils.py
    retry.py
    schema.py
    metrics.py

tests/
  test_planner_agent.py
  test_data_agent.py
  test_insight_agent.py
  test_evaluator_agent.py
  test_creative_agent.py
  test_integration_pipeline.py

run.py
Makefile
requirements.txt
```

## Configuration

The main configuration lives in `config/config.yaml`, including:

- paths to data and report files
- ROAS / CTR thresholds
- sample vs full‑dataset switch
- retry parameters
- random seed

You can tweak thresholds there without changing code.

## Validation & schema safety

- The Data Agent validates the input CSV against an expected schema
  (`src/utils/schema.py`).
- Missing or extra columns are logged as warnings.
- Hard schema violations abort the run before downstream agents execute.

## Logging & observability

- All logs go to `logs/app.log` in **line‑delimited JSON**.
- Each record includes:

  - timestamp
  - level
  - agent
  - stage
  - event
  - status
  - runtime_ms (when applicable)
  - extra (free‑form dict)

- Metrics such as simple runtime timing and number of evaluated hypotheses
  are recorded via `metrics.py`.

## Retry & fallback behaviour

The Insight and Evaluator agents use a common `@retry` decorator with
exponential backoff:

- configurable `max_attempts`, `base_delay`, and `backoff_factor`
- logs every failure with the attempt index
- on permanent failure:
  - a rule‑based fallback is executed so the pipeline still produces output
  - the incident is recorded in logs and reflected as `confidence="low"`.

The retry parameters are defined in `config/config.yaml`.

## Running tests

```bash
# run all tests
pytest

# run with coverage (if pytest-cov installed)
pytest --maxfail=1 --disable-warnings -q
```

The tests cover:

- unit tests for all agents
- edge‑case tests for schema validation & data loading
- an integration test that runs the full
  Planner → Data → Insight → Evaluator → Creative loop
  on the sample dataset.

## Example outputs

After running:

```bash
python run.py "Analyze ROAS drop for last 14 days"
```

You will find:

- `reports/insights.json` – list of hypotheses with confidence & evidence
- `reports/creatives.json` – creative ideas for low‑CTR campaigns
- `reports/report.md` – human‑readable summary for a marketer

These files are committed to the repository as evidence, alongside
`logs/app.log` (or Langfuse traces if you plug Langfuse into
`logging_utils.py`).

## Notes on LLM usage

The agents are implemented so that they **do not hard‑depend on a live LLM**
for basic functionality:

- By default, they run lightweight, rule‑based logic so the system remains
  runnable without external API keys.
- You can plug in an actual LLM client in place of the rule‑based stubs inside
  each agent while reusing the same prompts under `prompts/`.

This keeps the system reproducible for evaluation while still following the
agentic design requested in the assignment.
