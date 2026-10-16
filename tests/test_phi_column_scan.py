"""Tests for the PHI column scan skill."""

from pathlib import Path

from scan_phi_columns import scan_column, scan_schema_file

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "phi-column-scan" / "fixtures"
)


class TestPhiColumnScan:
    def test_high_risk_name(self):
        result = scan_column("patient_name")
        assert result["risk"] == "HIGH"

    def test_high_risk_ssn(self):
        result = scan_column("ssn")
        assert result["risk"] == "HIGH"

    def test_high_risk_email(self):
        result = scan_column("email")
        assert result["risk"] == "HIGH"

    def test_high_risk_from_sample(self):
        result = scan_column("custom_field", "987-65-4320")
        assert result["risk"] == "HIGH"

    def test_medium_risk_notes(self):
        result = scan_column("notes")
        assert result["risk"] == "MEDIUM"

    def test_medium_risk_zip(self):
        result = scan_column("zip_code")
        assert result["risk"] == "MEDIUM"

    def test_low_risk_clinical(self):
        result = scan_column("diagnosis_code")
        assert result["risk"] == "LOW"

    def test_low_risk_gender(self):
        result = scan_column("gender")
        assert result["risk"] == "LOW"

    def test_scan_schema_file(self):
        results = scan_schema_file(str(FIXTURES / "sample_schema.csv"))
        assert len(results) == 16
        high = [r for r in results if r["risk"] == "HIGH"]
        assert len(high) >= 5
