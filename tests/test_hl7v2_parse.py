"""Tests for the HL7v2 parse skill."""

from pathlib import Path

from parse_hl7v2 import parse_messages, split_messages

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "hl7v2-parse" / "fixtures"
)


class TestHl7v2Parse:
    def test_split_messages(self):
        raw = (FIXTURES / "sample_adt.hl7").read_text()
        messages = split_messages(raw)
        assert len(messages) == 2

    def test_parse_adt_patients(self):
        raw = (FIXTURES / "sample_adt.hl7").read_text()
        result = parse_messages(raw)
        assert result["message_count"] == 2
        assert len(result["patients"]) == 2
        assert result["patients"][0]["last_name"] == "TESTLAST"
        assert result["patients"][0]["mrn"] == "SYNTHMRN001"

    def test_parse_adt_visits(self):
        raw = (FIXTURES / "sample_adt.hl7").read_text()
        result = parse_messages(raw)
        assert len(result["visits"]) == 2
        assert result["visits"][0]["patient_class"] == "I"

    def test_parse_oru_observations(self):
        raw = (FIXTURES / "sample_oru.hl7").read_text()
        result = parse_messages(raw)
        assert len(result["observations"]) == 3
        obs0 = result["observations"][0]
        assert obs0["test_name"] == "White Blood Cell Count"
        assert obs0["value"] == "7.5"

    def test_patient_demographics(self):
        raw = (FIXTURES / "sample_adt.hl7").read_text()
        result = parse_messages(raw)
        p = result["patients"][1]
        assert p["first_name"] == "DEMOFIRST"
        assert p["gender"] == "M"
