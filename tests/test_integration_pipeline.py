from pathlib import Path

from src.orchestrator.main import run_pipeline


def test_full_pipeline_runs(tmp_path, monkeypatch):
    # copy config and data into tmpdir so we don't touch real paths
    (tmp_path / "config").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "reports").mkdir()

    (tmp_path / "config" / "config.yaml").write_text(
        Path("config/config.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "data" / "sample_fb_ads.csv").write_text(
        Path("data/sample_fb_ads.csv").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # patch cwd-relative paths
    monkeypatch.chdir(tmp_path)

    run_pipeline("Analyze ROAS drop", config_path="config/config.yaml")

    assert (tmp_path / "reports" / "insights.json").exists()
    assert (tmp_path / "reports" / "creatives.json").exists()
    assert (tmp_path / "reports" / "report.md").exists()
