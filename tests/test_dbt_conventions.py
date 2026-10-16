"""Tests for the dbt healthcare conventions skill."""

from pathlib import Path

from audit_dbt import audit_project

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "dbt-healthcare-conventions"
    / "fixtures" / "sample_dbt_project"
)


class TestDbtConventions:
    def test_audit_project_runs(self):
        report = audit_project(str(FIXTURES))
        assert "findings" in report
        assert report["model_count"] == 2

    def test_catches_bad_naming(self):
        report = audit_project(str(FIXTURES))
        naming = [f for f in report["findings"] if f["category"] == "naming"]
        bad_names = [f["model"] for f in naming]
        assert "bad_naming_model" in bad_names

    def test_catches_missing_tests(self):
        report = audit_project(str(FIXTURES))
        test_findings = [
            f for f in report["findings"] if f["category"] == "tests"
        ]
        assert len(test_findings) > 0
        assert any("unique" in f["message"] for f in test_findings)

    def test_good_model_no_naming_warning(self):
        report = audit_project(str(FIXTURES))
        naming = [f for f in report["findings"] if f["category"] == "naming"]
        flagged = [f["model"] for f in naming]
        assert "stg_payer_alpha__eligibility" not in flagged

    def test_no_dbt_project(self):
        report = audit_project("/nonexistent/path")
        assert "error" in report
