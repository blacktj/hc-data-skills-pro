"""Tests for the code set lookup skill."""

from pathlib import Path

from validate_codes import validate_code, validate_csv

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "code-set-lookup" / "fixtures"
)


class TestCodeSetLookup:
    def test_valid_icd10(self):
        result = validate_code("E11.9", "icd10")
        assert result["valid"] is True
        assert "Endocrine" in result.get("category_hint", "")

    def test_invalid_icd10(self):
        result = validate_code("ZZZZZ", "icd10")
        assert result["valid"] is False

    def test_valid_cpt(self):
        result = validate_code("99213", "cpt")
        assert result["valid"] is True
        assert "AMA" in result["license_note"]

    def test_invalid_cpt(self):
        result = validate_code("9921", "cpt")
        assert result["valid"] is False

    def test_valid_ndc(self):
        result = validate_code("0002-1433-80", "ndc")
        assert result["valid"] is True

    def test_valid_loinc(self):
        result = validate_code("2160-0", "loinc")
        assert result["valid"] is True

    def test_invalid_loinc(self):
        result = validate_code("99999", "loinc")
        assert result["valid"] is False

    def test_unknown_system(self):
        result = validate_code("ABC", "unknown_system")
        assert result["valid"] is False

    def test_validate_csv(self):
        results = validate_csv(str(FIXTURES / "sample_codes.csv"))
        assert len(results) == 9
        valid = [r for r in results if r["valid"]]
        invalid = [r for r in results if not r["valid"]]
        assert len(valid) >= 5
        assert len(invalid) >= 3
