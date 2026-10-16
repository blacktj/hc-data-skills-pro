#!/usr/bin/env python3
"""HIPAA Safe Harbor de-identification for CSV datasets."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

IDENTIFIER_PATTERNS: dict[str, dict] = {
    "name": {
        "columns": re.compile(r"(first|last|middle|given|family|patient|member)[\s_]?name", re.I),
        "action": "redact",
    },
    "geographic": {
        "columns": re.compile(r"(address|street|city|county|zip|postal)", re.I),
        "action": "generalize",
    },
    "date": {
        "columns": re.compile(r"(dob|birth|admit|discharge|service|effective|term)[\s_]?date|date[\s_]?of", re.I),
        "action": "generalize",
    },
    "phone": {
        "columns": re.compile(r"(phone|fax|tel|mobile|cell)", re.I),
        "action": "redact",
    },
    "email": {
        "columns": re.compile(r"e[\s_]?mail", re.I),
        "action": "redact",
    },
    "ssn": {
        "columns": re.compile(r"(ssn|social[\s_]?sec)", re.I),
        "action": "redact",
    },
    "mrn": {
        "columns": re.compile(r"(mrn|medical[\s_]?record|patient[\s_]?id|member[\s_]?id)", re.I),
        "action": "redact",
    },
    "account": {
        "columns": re.compile(r"(account|acct)[\s_]?(num|no|id|#)", re.I),
        "action": "redact",
    },
    "license": {
        "columns": re.compile(r"(license|certificate|dea)[\s_]?(num|no|id|#)", re.I),
        "action": "redact",
    },
    "device_id": {
        "columns": re.compile(r"(device|serial|udi)[\s_]?(id|num|no)", re.I),
        "action": "redact",
    },
    "url": {
        "columns": re.compile(r"(url|uri|website|web[\s_]?address)", re.I),
        "action": "redact",
    },
    "ip": {
        "columns": re.compile(r"(ip[\s_]?addr|ip$)", re.I),
        "action": "redact",
    },
    "beneficiary": {
        "columns": re.compile(r"(beneficiary|hicn|mbi|medicare[\s_]?id)", re.I),
        "action": "redact",
    },
}

SAFE_COLUMNS = re.compile(
    r"(gender|sex|age|race|ethnicity|language|plan[\s_]?(type|name)|"
    r"diagnosis|procedure|icd|cpt|ndc|loinc|drg|"
    r"claim[\s_]?(type|status)|provider[\s_]?type|"
    r"batch|row|record[\s_]?count|flag|status|tier)",
    re.I,
)


def classify_column(col_name: str) -> dict:
    """Classify a column as PHI or safe, return action and confidence."""
    for cat, spec in IDENTIFIER_PATTERNS.items():
        if spec["columns"].search(col_name):
            return {"category": cat, "action": spec["action"], "confidence": 0.9}

    if SAFE_COLUMNS.search(col_name):
        return {"category": "non_phi", "action": "keep", "confidence": 0.95}

    return {"category": "unknown", "action": "review", "confidence": 0.4}


def generalize_value(value: str, category: str) -> str:
    """Apply Safe Harbor generalization rules."""
    if category == "geographic":
        if re.match(r"^\d{5}", value):
            return value[:3] + "XX"
        return "[GENERALIZED]"
    if category == "date":
        match = re.search(r"(\d{4})", value)
        if match:
            return match.group(1)
        return "[GENERALIZED]"
    return "[GENERALIZED]"


def deid_csv(input_path: str) -> dict:
    """De-identify a CSV file. Returns report dict."""
    path = Path(input_path)
    rows = []
    with path.open() as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    report: dict[str, dict] = {}
    uncertain = []

    for col in fieldnames:
        classification = classify_column(col)
        report[col] = classification
        if classification["confidence"] < 0.7:
            uncertain.append(col)

    output_rows = []
    if not uncertain:
        for row in rows:
            new_row = {}
            for col in fieldnames:
                action = report[col]["action"]
                if action == "redact":
                    new_row[col] = "[REDACTED]"
                elif action == "generalize":
                    new_row[col] = generalize_value(row[col], report[col]["category"])
                else:
                    new_row[col] = row[col]
            output_rows.append(new_row)

    return {
        "columns": report,
        "uncertain_columns": uncertain,
        "row_count": len(rows),
        "can_export": len(uncertain) == 0,
        "output_rows": output_rows,
        "output_fieldnames": fieldnames,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: deid_safe_harbor.py <input.csv>")
        sys.exit(1)

    result = deid_csv(sys.argv[1])

    report_out = {k: v for k, v in result.items() if k not in ("output_rows", "output_fieldnames")}
    print(json.dumps(report_out, indent=2))

    if not result["can_export"]:
        print(
            f"\n⚠ EXPORT BLOCKED: {len(result['uncertain_columns'])} column(s) need human review: "
            f"{', '.join(result['uncertain_columns'])}"
        )
        sys.exit(2)

    output_path = Path(sys.argv[1]).stem + "_deid.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=result["output_fieldnames"])
        writer.writeheader()
        writer.writerows(result["output_rows"])
    print(f"\n✓ De-identified file written to {output_path}")


if __name__ == "__main__":
    main()
