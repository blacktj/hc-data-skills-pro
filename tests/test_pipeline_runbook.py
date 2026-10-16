"""Tests for the pipeline runbook skill."""

from pathlib import Path

from generate_runbook import (
    detect_type,
    extract_airflow_metadata,
    generate_runbook,
)

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "pipeline-runbook" / "fixtures"
)


class TestPipelineRunbook:
    def test_detect_airflow(self):
        ptype = detect_type(FIXTURES / "sample_dag.py")
        assert ptype == "airflow"

    def test_detect_dbt(self):
        ptype = detect_type(FIXTURES / "sample_dbt_project.yml")
        assert ptype == "dbt"

    def test_extract_airflow_metadata(self):
        text = (FIXTURES / "sample_dag.py").read_text()
        meta = extract_airflow_metadata(text)
        assert meta["dag_id"] == "synth_eligibility_load"
        assert "0 6 * * *" in meta["schedule"]
        assert len(meta["tasks"]) >= 4

    def test_generate_airflow_runbook(self):
        runbook = generate_runbook(str(FIXTURES / "sample_dag.py"))
        assert "synth_eligibility_load" in runbook
        assert "Failure Modes" in runbook
        assert "Escalation" in runbook
        assert "Recovery" in runbook

    def test_generate_dbt_runbook(self):
        runbook = generate_runbook(
            str(FIXTURES / "sample_dbt_project.yml")
        )
        assert "synth_eligibility_pipeline" in runbook
        assert "Source Freshness" in runbook

    def test_runbook_has_sections(self):
        runbook = generate_runbook(str(FIXTURES / "sample_dag.py"))
        assert "## Overview" in runbook
        assert "## Tasks" in runbook
        assert "## Monitoring" in runbook
