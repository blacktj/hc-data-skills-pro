"""Tests for the FHIR mapping skill."""

from pathlib import Path

from map_to_fhir import format_report, map_columns, parse_schema

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "fhir-mapping" / "fixtures"
)


class TestFhirMapping:
    def test_parse_schema(self):
        columns = parse_schema(str(FIXTURES / "sample_schema.csv"))
        assert len(columns) == 12
        assert columns[0]["column_name"] == "member_id"

    def test_maps_known_columns(self):
        columns = parse_schema(str(FIXTURES / "sample_schema.csv"))
        result = map_columns(columns)
        mapped_cols = {m["source_column"] for m in result["mappings"]}
        assert "first_name" in mapped_cols
        assert "date_of_birth" in mapped_cols
        assert "subscriber_id" in mapped_cols

    def test_flags_unmapped_columns(self):
        columns = parse_schema(str(FIXTURES / "sample_schema.csv"))
        result = map_columns(columns)
        unmapped_cols = {u["source_column"] for u in result["unmapped"]}
        assert "custom_risk_score" in unmapped_cols
        assert "internal_batch_id" in unmapped_cols

    def test_format_report_has_tables(self):
        columns = parse_schema(str(FIXTURES / "sample_schema.csv"))
        result = map_columns(columns)
        report = format_report(result)
        assert "FHIR Mapping Specification" in report
        assert "Patient.name.given" in report
        assert "Unmapped" in report
