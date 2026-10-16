#!/usr/bin/env python3
"""Validate healthcare code formats: ICD-10, CPT, NDC, LOINC."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

VALIDATORS: dict[str, dict] = {
    "icd10": {
        "pattern": re.compile(r"^[A-TV-Z]\d{2}(\.\d{1,4})?$", re.I),
        "description": "ICD-10-CM: Letter + 2 digits, optionally dot + 1-4 digits",
        "example": "E11.9, Z00.00, S72.001A",
        "license": "Public domain (CMS/NCHS). Full code tables at cms.gov.",
    },
    "cpt": {
        "pattern": re.compile(r"^\d{5}$"),
        "description": "CPT: Exactly 5 digits (Category I). Format validation only.",
        "example": "99213, 99214",
        "license": "CPT is copyright AMA. NO descriptions shipped — format validation only.",
    },
    "ndc": {
        "pattern": re.compile(r"^\d{4}-\d{4}-\d{2}$|^\d{5}-\d{3}-\d{2}$|^\d{5}-\d{4}-\d{1}$|^\d{10,11}$"),
        "description": "NDC: 10-11 digits in 4-4-2, 5-3-2, or 5-4-1 format (or unformatted)",
        "example": "0002-1433-80, 12345-678-90",
        "license": "Public (FDA NDC Directory).",
    },
    "loinc": {
        "pattern": re.compile(r"^\d{1,5}-\d$"),
        "description": "LOINC: 1-5 digits, dash, 1 check digit",
        "example": "2160-0, 718-7",
        "license": "Free with attribution (Regenstrief Institute).",
    },
}


def validate_code(code: str, system: str) -> dict:
    """Validate a single code against its code system format."""
    code = code.strip()
    system = system.strip().lower()

    if system not in VALIDATORS:
        return {
            "code": code,
            "system": system,
            "valid": False,
            "message": f"Unknown code system '{system}'. Supported: {', '.join(VALIDATORS.keys())}",
        }

    spec = VALIDATORS[system]
    is_valid = bool(spec["pattern"].match(code))

    result = {
        "code": code,
        "system": system,
        "valid": is_valid,
        "format_description": spec["description"],
        "license_note": spec["license"],
    }

    if is_valid:
        result["message"] = f"Valid {system.upper()} format"
        if system == "icd10":
            category = code[0]
            categories = {
                "A": "Infectious diseases", "B": "Infectious diseases",
                "C": "Neoplasms", "D": "Blood/immune diseases",
                "E": "Endocrine/metabolic", "F": "Mental/behavioral",
                "G": "Nervous system", "H": "Eye/ear",
                "I": "Circulatory", "J": "Respiratory",
                "K": "Digestive", "L": "Skin",
                "M": "Musculoskeletal", "N": "Genitourinary",
                "O": "Pregnancy", "P": "Perinatal",
                "Q": "Congenital", "R": "Symptoms/signs",
                "S": "Injury", "T": "Injury/poisoning",
                "V": "External causes", "Z": "Health status/contact",
            }
            cat_desc = categories.get(category.upper(), "Unknown category")
            result["category_hint"] = f"{category}: {cat_desc}"
    else:
        result["message"] = f"Invalid {system.upper()} format. Expected: {spec['example']}"

    return result


def validate_csv(file_path: str) -> list[dict]:
    """Validate codes from a CSV file."""
    results = []
    with open(file_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get("code", "").strip()
            system = row.get("system", "").strip()
            if code and system:
                results.append(validate_code(code, system))
    return results


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate_codes.py <codes.csv>")
        sys.exit(1)

    results = validate_csv(sys.argv[1])
    print(json.dumps(results, indent=2))

    valid_count = sum(1 for r in results if r["valid"])
    print(f"\n{valid_count}/{len(results)} codes valid")


if __name__ == "__main__":
    main()
