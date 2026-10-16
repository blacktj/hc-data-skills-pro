#!/usr/bin/env python3
"""Map source table columns to FHIR R4 Patient/Coverage/Encounter resources."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

FHIR_COLUMN_MAP: dict[str, dict[str, str]] = {
    "first_name":       {"resource": "Patient", "path": "Patient.name.given", "type": "string"},
    "last_name":        {"resource": "Patient", "path": "Patient.name.family", "type": "string"},
    "given_name":       {"resource": "Patient", "path": "Patient.name.given", "type": "string"},
    "family_name":      {"resource": "Patient", "path": "Patient.name.family", "type": "string"},
    "date_of_birth":    {"resource": "Patient", "path": "Patient.birthDate", "type": "date"},
    "dob":              {"resource": "Patient", "path": "Patient.birthDate", "type": "date"},
    "birth_date":       {"resource": "Patient", "path": "Patient.birthDate", "type": "date"},
    "gender":           {"resource": "Patient", "path": "Patient.gender", "type": "code"},
    "sex":              {"resource": "Patient", "path": "Patient.gender", "type": "code"},
    "ssn":              {"resource": "Patient", "path": "Patient.identifier (SSN)", "type": "identifier", "note": "Sensitive — confirm use case"},
    "member_id":        {"resource": "Patient", "path": "Patient.identifier (member)", "type": "identifier"},
    "subscriber_id":    {"resource": "Coverage", "path": "Coverage.subscriberId", "type": "string"},
    "plan_id":          {"resource": "Coverage", "path": "Coverage.class.value (plan)", "type": "string"},
    "plan_name":        {"resource": "Coverage", "path": "Coverage.class.name (plan)", "type": "string"},
    "group_id":         {"resource": "Coverage", "path": "Coverage.class.value (group)", "type": "string"},
    "group_number":     {"resource": "Coverage", "path": "Coverage.class.value (group)", "type": "string"},
    "payer_id":         {"resource": "Coverage", "path": "Coverage.payor (reference)", "type": "reference"},
    "payer_name":       {"resource": "Coverage", "path": "Coverage.payor.display", "type": "string"},
    "coverage_start":   {"resource": "Coverage", "path": "Coverage.period.start", "type": "date"},
    "coverage_end":     {"resource": "Coverage", "path": "Coverage.period.end", "type": "date"},
    "effective_date":   {"resource": "Coverage", "path": "Coverage.period.start", "type": "date"},
    "term_date":        {"resource": "Coverage", "path": "Coverage.period.end", "type": "date"},
    "relationship":     {"resource": "Coverage", "path": "Coverage.relationship", "type": "code"},
    "encounter_id":     {"resource": "Encounter", "path": "Encounter.identifier", "type": "identifier"},
    "admit_date":       {"resource": "Encounter", "path": "Encounter.period.start", "type": "dateTime"},
    "discharge_date":   {"resource": "Encounter", "path": "Encounter.period.end", "type": "dateTime"},
    "admission_date":   {"resource": "Encounter", "path": "Encounter.period.start", "type": "dateTime"},
    "encounter_type":   {"resource": "Encounter", "path": "Encounter.type", "type": "CodeableConcept"},
    "facility_id":      {"resource": "Encounter", "path": "Encounter.serviceProvider", "type": "reference"},
    "facility_name":    {"resource": "Encounter", "path": "Encounter.serviceProvider.display", "type": "string"},
    "attending_npi":    {"resource": "Encounter", "path": "Encounter.participant (practitioner)", "type": "reference"},
    "diagnosis_code":   {"resource": "Encounter", "path": "Encounter.diagnosis.condition", "type": "CodeableConcept"},
    "icd10_code":       {"resource": "Encounter", "path": "Encounter.diagnosis.condition (ICD-10)", "type": "CodeableConcept"},
    "address_line1":    {"resource": "Patient", "path": "Patient.address.line", "type": "string"},
    "address_line_1":   {"resource": "Patient", "path": "Patient.address.line", "type": "string"},
    "city":             {"resource": "Patient", "path": "Patient.address.city", "type": "string"},
    "state":            {"resource": "Patient", "path": "Patient.address.state", "type": "string"},
    "zip":              {"resource": "Patient", "path": "Patient.address.postalCode", "type": "string"},
    "zip_code":         {"resource": "Patient", "path": "Patient.address.postalCode", "type": "string"},
    "postal_code":      {"resource": "Patient", "path": "Patient.address.postalCode", "type": "string"},
    "phone":            {"resource": "Patient", "path": "Patient.telecom (phone)", "type": "ContactPoint"},
    "email":            {"resource": "Patient", "path": "Patient.telecom (email)", "type": "ContactPoint"},
}


def parse_schema(file_path: str) -> list[dict[str, str]]:
    """Parse a CSV schema file into a list of column dicts."""
    path = Path(file_path)
    columns = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            columns.append({
                "column_name": row.get("column_name", "").strip().lower(),
                "data_type": row.get("data_type", "").strip(),
                "sample_value": row.get("sample_value", "").strip(),
                "description": row.get("description", "").strip(),
            })
    return columns


def map_columns(columns: list[dict[str, str]]) -> dict:
    """Map source columns to FHIR paths."""
    mappings = []
    unmapped = []

    for col in columns:
        name = col["column_name"]
        normalized = re.sub(r"[^a-z0-9_]", "_", name.lower())

        if normalized in FHIR_COLUMN_MAP:
            entry = FHIR_COLUMN_MAP[normalized]
            mappings.append({
                "source_column": col["column_name"],
                "source_type": col["data_type"],
                "fhir_resource": entry["resource"],
                "fhir_path": entry["path"],
                "fhir_type": entry["type"],
                "note": entry.get("note", ""),
            })
        else:
            unmapped.append({
                "source_column": col["column_name"],
                "source_type": col["data_type"],
                "description": col.get("description", ""),
                "suggestion": "Review manually — may need a FHIR extension or can be excluded.",
            })

    return {"mappings": mappings, "unmapped": unmapped}


def format_report(result: dict) -> str:
    """Format the mapping result as Markdown."""
    lines = ["# FHIR Mapping Specification\n"]

    lines.append("## Mapped Columns\n")
    lines.append("| Source Column | Source Type | FHIR Resource | FHIR Path | FHIR Type | Notes |")
    lines.append("|---|---|---|---|---|---|")
    for m in result["mappings"]:
        lines.append(
            f"| {m['source_column']} | {m['source_type']} | {m['fhir_resource']} "
            f"| {m['fhir_path']} | {m['fhir_type']} | {m['note']} |"
        )

    if result["unmapped"]:
        lines.append("\n## Unmapped Columns (require review)\n")
        lines.append("| Source Column | Source Type | Description | Suggestion |")
        lines.append("|---|---|---|---|")
        for u in result["unmapped"]:
            lines.append(
                f"| {u['source_column']} | {u['source_type']} "
                f"| {u['description']} | {u['suggestion']} |"
            )

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: map_to_fhir.py <schema-csv>")
        sys.exit(1)

    columns = parse_schema(sys.argv[1])
    result = map_columns(columns)
    print(format_report(result))
    print("\n---\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
