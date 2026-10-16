#!/usr/bin/env python3
"""Scan schema columns for likely PHI — local-only, no data transmitted."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HIGH_RISK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("name", re.compile(r"(first|last|middle|given|family|patient|member|person)[\s_]?name", re.I)),
    ("ssn", re.compile(r"(ssn|social[\s_]?sec)", re.I)),
    ("dob", re.compile(r"(dob|date[\s_]?of[\s_]?birth|birth[\s_]?date)", re.I)),
    ("mrn", re.compile(r"(mrn|medical[\s_]?record[\s_]?num)", re.I)),
    ("phone", re.compile(r"(phone|fax|mobile|cell)[\s_]?(num|no|#)?$", re.I)),
    ("email", re.compile(r"e[\s_]?mail", re.I)),
    ("address", re.compile(r"(street|address[\s_]?line|addr)", re.I)),
    ("beneficiary_id", re.compile(r"(hicn|mbi|beneficiary[\s_]?id|medicare[\s_]?id)", re.I)),
    ("account_num", re.compile(r"(account|acct)[\s_]?(num|no|id|#)", re.I)),
    ("license_num", re.compile(r"(license|certificate|dea)[\s_]?(num|no|id)", re.I)),
    ("ip_address", re.compile(r"ip[\s_]?(addr|address)$", re.I)),
    ("url", re.compile(r"(url|uri|web[\s_]?site)", re.I)),
    ("device_id", re.compile(r"(device|serial|udi)[\s_]?(id|num|no)", re.I)),
]

MEDIUM_RISK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("generic_id", re.compile(r"^(patient|member|person|subscriber)[\s_]?id$", re.I)),
    ("date_field", re.compile(r"(admit|discharge|service|effective|term)[\s_]?date", re.I)),
    ("notes", re.compile(r"(notes?|comments?|free[\s_]?text|narrative)", re.I)),
    ("zip", re.compile(r"(zip|postal)[\s_]?(code)?$", re.I)),
    ("city_state", re.compile(r"^(city|county|state)$", re.I)),
]

LOW_RISK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("clinical_code", re.compile(r"(icd|cpt|ndc|loinc|drg|hcpcs|snomed)", re.I)),
    ("demographic_safe", re.compile(r"^(gender|sex|race|ethnicity|language|age)$", re.I)),
    ("plan_info", re.compile(r"(plan[\s_]?(type|name|id)|payer|lob|product)", re.I)),
    ("flag_status", re.compile(r"(flag|status|indicator|type|category|tier|batch)", re.I)),
]

SAMPLE_VALUE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssn_value", re.compile(r"\d{3}-\d{2}-\d{4}")),
    ("phone_value", re.compile(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")),
    ("email_value", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}")),
    ("dob_value", re.compile(r"\d{4}-\d{2}-\d{2}")),
]


def scan_column(col_name: str, sample_value: str = "") -> dict:
    """Classify a single column for PHI risk."""
    for label, pat in HIGH_RISK_PATTERNS:
        if pat.search(col_name):
            return {
                "column": col_name,
                "risk": "HIGH",
                "pattern": label,
                "action": "Redact or de-identify before sharing",
            }

    for label, pat in SAMPLE_VALUE_PATTERNS:
        if sample_value and pat.search(sample_value):
            return {
                "column": col_name,
                "risk": "HIGH",
                "pattern": f"{label} (from sample value)",
                "action": "Redact or de-identify before sharing",
            }

    for label, pat in MEDIUM_RISK_PATTERNS:
        if pat.search(col_name):
            return {
                "column": col_name,
                "risk": "MEDIUM",
                "pattern": label,
                "action": "Review with data steward — may need de-identification",
            }

    for label, pat in LOW_RISK_PATTERNS:
        if pat.search(col_name):
            return {
                "column": col_name,
                "risk": "LOW",
                "pattern": label,
                "action": "Likely safe — verify with context",
            }

    return {
        "column": col_name,
        "risk": "LOW",
        "pattern": "no match",
        "action": "Likely safe — verify with context",
    }


def scan_schema_file(file_path: str) -> list[dict]:
    """Scan a CSV schema file and return per-column risk report."""
    path = Path(file_path)
    results = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            col_name = row.get("column_name", "").strip()
            sample = row.get("sample_value", "").strip()
            if col_name:
                results.append(scan_column(col_name, sample))
    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: scan_phi_columns.py <schema-csv>")
        sys.exit(1)

    results = scan_schema_file(sys.argv[1])
    print(json.dumps(results, indent=2))

    high_count = sum(1 for r in results if r["risk"] == "HIGH")
    med_count = sum(1 for r in results if r["risk"] == "MEDIUM")
    print(f"\nSummary: {high_count} HIGH, {med_count} MEDIUM, {len(results) - high_count - med_count} LOW")


if __name__ == "__main__":
    main()
