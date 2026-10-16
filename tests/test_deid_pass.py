"""Tests for the de-identification pass skill."""

from pathlib import Path

from deid_safe_harbor import classify_column, deid_csv

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "deid-pass" / "fixtures"
)


class TestDeidPass:
    def test_classify_name_columns(self):
        assert classify_column("first_name")["action"] == "redact"
        assert classify_column("last_name")["action"] == "redact"
        assert classify_column("patient_name")["action"] == "redact"

    def test_classify_date_columns(self):
        assert classify_column("date_of_birth")["action"] == "generalize"
        assert classify_column("admit_date")["action"] == "generalize"

    def test_classify_safe_columns(self):
        assert classify_column("gender")["action"] == "keep"
        assert classify_column("diagnosis_code")["action"] == "keep"
        assert classify_column("plan_type")["action"] == "keep"

    def test_deid_csv_produces_output(self):
        result = deid_csv(str(FIXTURES / "sample_members.csv"))
        assert result["can_export"] is True
        assert result["row_count"] == 3
        assert len(result["output_rows"]) == 3

    def test_deid_redacts_names(self):
        result = deid_csv(str(FIXTURES / "sample_members.csv"))
        for row in result["output_rows"]:
            assert row["first_name"] == "[REDACTED]"
            assert row["last_name"] == "[REDACTED]"

    def test_deid_generalizes_zip(self):
        result = deid_csv(str(FIXTURES / "sample_members.csv"))
        for row in result["output_rows"]:
            zv = row["zip_code"]
            assert zv.endswith("XX") or zv == "[GENERALIZED]"

    def test_deid_keeps_safe_columns(self):
        result = deid_csv(str(FIXTURES / "sample_members.csv"))
        for row in result["output_rows"]:
            assert row["gender"] in ("F", "M")
            assert row["diagnosis_code"] in ("Z00.00", "Z23", "Z01.419")
