#!/usr/bin/env python3
"""Validate an EDI 834 enrollment file and produce a plain-English report."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_segments(raw: str) -> list[list[str]]:
    """Split raw EDI text into segments, handling ~ and newline terminators."""
    raw = raw.strip()
    if "~" in raw:
        parts = raw.split("~")
    else:
        parts = raw.split("\n")
    segments = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        elements = part.split("*")
        segments.append(elements)
    return segments


def validate_834(file_path: str) -> dict:
    """Run all validation checks on an 834 file. Returns a report dict."""
    path = Path(file_path)
    if not path.exists():
        return {"valid": False, "errors": [{"type": "FILE", "message": f"File not found: {file_path}"}]}

    raw = path.read_text(errors="replace")
    segments = parse_segments(raw)

    errors: list[dict] = []
    warnings: list[dict] = []
    seg_counts: dict[str, int] = {}

    for seg in segments:
        seg_id = seg[0] if seg else ""
        seg_counts[seg_id] = seg_counts.get(seg_id, 0) + 1

    # --- Envelope checks ---
    isa_count = seg_counts.get("ISA", 0)
    iea_count = seg_counts.get("IEA", 0)
    if isa_count != iea_count:
        errors.append({
            "type": "ENVELOPE",
            "message": f"ISA/IEA mismatch: {isa_count} ISA vs {iea_count} IEA",
        })

    gs_count = seg_counts.get("GS", 0)
    ge_count = seg_counts.get("GE", 0)
    if gs_count != ge_count:
        errors.append({
            "type": "ENVELOPE",
            "message": f"GS/GE mismatch: {gs_count} GS vs {ge_count} GE",
        })

    st_count = seg_counts.get("ST", 0)
    se_count = seg_counts.get("SE", 0)
    if st_count != se_count:
        errors.append({
            "type": "ENVELOPE",
            "message": f"ST/SE mismatch: {st_count} ST vs {se_count} SE",
        })

    # --- Member loop checks ---
    ins_segments = [s for s in segments if s[0] == "INS"]
    member_refs: list[str] = []
    current_member_has_nm1 = False
    current_member_has_dtp = False
    current_member_has_ref = False
    member_index = 0

    for i, seg in enumerate(segments):
        seg_id = seg[0]
        if seg_id == "INS":
            if member_index > 0:
                if not current_member_has_nm1:
                    errors.append({
                        "type": "LOOP",
                        "message": f"Member {member_index} missing NM1 segment",
                    })
                if not current_member_has_dtp:
                    errors.append({
                        "type": "LOOP",
                        "message": f"Member {member_index} missing DTP segment",
                    })
                if not current_member_has_ref:
                    errors.append({
                        "type": "LOOP",
                        "message": f"Member {member_index} missing REF segment",
                    })
            member_index += 1
            current_member_has_nm1 = False
            current_member_has_dtp = False
            current_member_has_ref = False
        elif seg_id == "NM1":
            current_member_has_nm1 = True
        elif seg_id == "DTP":
            current_member_has_dtp = True
            if len(seg) >= 4:
                _validate_date(seg[3], i + 1, errors)
        elif seg_id == "REF":
            current_member_has_ref = True
            if len(seg) >= 3 and seg[1] == "0F":
                member_refs.append(seg[2])

    if member_index > 0:
        if not current_member_has_nm1:
            errors.append({"type": "LOOP", "message": f"Member {member_index} missing NM1 segment"})
        if not current_member_has_dtp:
            errors.append({"type": "LOOP", "message": f"Member {member_index} missing DTP segment"})
        if not current_member_has_ref:
            errors.append({"type": "LOOP", "message": f"Member {member_index} missing REF segment"})

    # --- Duplicate detection ---
    seen: dict[str, int] = {}
    for ref_id in member_refs:
        seen[ref_id] = seen.get(ref_id, 0) + 1
    for ref_id, count in seen.items():
        if count > 1:
            warnings.append({
                "type": "DUPLICATE",
                "message": f"Member ref {ref_id} appears {count} times",
            })

    # --- Add/Term reconciliation ---
    adds = sum(1 for s in ins_segments if len(s) > 1 and s[1] == "Y")
    terms = sum(1 for s in ins_segments if len(s) > 1 and s[1] == "N")
    total = adds + terms
    if total > 0 and terms > 0:
        term_ratio = terms / total
        if term_ratio > 0.8:
            warnings.append({
                "type": "RECONCILIATION",
                "message": f"High termination ratio: {terms} terms vs {adds} adds ({term_ratio:.0%})",
            })

    valid = len(errors) == 0
    summary = _build_summary(valid, seg_counts, errors, warnings, adds, terms, member_index)

    return {
        "valid": valid,
        "segment_counts": seg_counts,
        "member_count": member_index,
        "adds": adds,
        "terms": terms,
        "errors": errors,
        "warnings": warnings,
        "summary": summary,
    }


def _validate_date(date_str: str, line: int, errors: list[dict]) -> None:
    """Check that a DTP date value is a valid calendar date."""
    date_str = date_str.strip()
    if "-" in date_str:
        date_str = date_str.split("-")[0]
    if not re.match(r"^\d{8}$", date_str):
        errors.append({
            "type": "DATE",
            "line": line,
            "message": f"Invalid date format: {date_str}",
        })
        return
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        if dt > datetime.now() + timedelta(days=730):
            errors.append({
                "type": "DATE",
                "line": line,
                "message": f"Date too far in future: {date_str}",
            })
    except ValueError:
        errors.append({
            "type": "DATE",
            "line": line,
            "message": f"Invalid calendar date: {date_str}",
        })


def _build_summary(
    valid: bool,
    seg_counts: dict[str, int],
    errors: list[dict],
    warnings: list[dict],
    adds: int,
    terms: int,
    member_count: int,
) -> str:
    status = "PASSED" if valid else "FAILED"
    parts = [f"834 Validation {status}."]
    parts.append(
        f"File contains {member_count} member record(s): "
        f"{adds} enrollment(s), {terms} termination(s)."
    )
    if errors:
        parts.append(f"Found {len(errors)} error(s): " + "; ".join(e["message"] for e in errors[:5]))
        if len(errors) > 5:
            parts.append(f"...and {len(errors) - 5} more.")
    if warnings:
        parts.append(f"Found {len(warnings)} warning(s): " + "; ".join(w["message"] for w in warnings[:3]))
    if valid and not warnings:
        parts.append("No issues detected.")
    return " ".join(parts)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate_834.py <path-to-834-file>")
        sys.exit(1)
    report = validate_834(sys.argv[1])
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
