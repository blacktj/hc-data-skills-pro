"""Tests for the 834 file check skill."""

from pathlib import Path

from validate_834 import parse_segments, validate_834

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "834-file-check" / "fixtures"
)


class TestParse834:
    def test_parse_segments_tilde(self):
        raw = "ISA*00~GS*HP~"
        segs = parse_segments(raw)
        assert len(segs) == 2
        assert segs[0][0] == "ISA"

    def test_valid_file_passes(self):
        report = validate_834(str(FIXTURES / "sample_834_valid.edi"))
        assert report["valid"] is True
        assert report["member_count"] == 3
        assert report["adds"] == 2
        assert report["terms"] == 1
        assert len(report["errors"]) == 0

    def test_error_file_fails(self):
        report = validate_834(str(FIXTURES / "sample_834_errors.edi"))
        assert report["valid"] is False
        error_types = {e["type"] for e in report["errors"]}
        assert "ENVELOPE" in error_types or "DATE" in error_types or "LOOP" in error_types

    def test_missing_file(self):
        report = validate_834("/nonexistent/file.edi")
        assert report["valid"] is False
        assert report["errors"][0]["type"] == "FILE"

    def test_duplicate_warning(self):
        report = validate_834(str(FIXTURES / "sample_834_errors.edi"))
        has_dup = any(
            w["type"] == "DUPLICATE" for w in report.get("warnings", [])
        )
        assert has_dup

    def test_summary_present(self):
        report = validate_834(str(FIXTURES / "sample_834_valid.edi"))
        assert "summary" in report
        assert len(report["summary"]) > 20
