#!/usr/bin/env python3
"""Parse HL7v2 ADT/ORU messages into flat tables."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def split_messages(raw: str) -> list[str]:
    """Split a file containing multiple HL7v2 messages."""
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    messages = []
    current: list[str] = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("MSH") and current:
            messages.append("\n".join(current))
            current = []
        current.append(line)
    if current:
        messages.append("\n".join(current))
    return messages


def parse_segment(line: str) -> dict[str, str]:
    """Parse an HL7v2 segment into a dict keyed by SEG.index."""
    fields = line.split("|")
    seg_id = fields[0]
    result: dict[str, str] = {"segment": seg_id}
    for i, val in enumerate(fields[1:], start=1):
        result[f"{seg_id}.{i}"] = val
    return result


def extract_patient(segments: list[dict[str, str]]) -> dict[str, str]:
    """Extract patient demographics from PID segment."""
    pid = next((s for s in segments if s["segment"] == "PID"), None)
    if not pid:
        return {}
    name_parts = pid.get("PID.5", "").split("^")
    return {
        "mrn": pid.get("PID.3", "").split("^")[0] if pid.get("PID.3") else "",
        "last_name": name_parts[0] if name_parts else "",
        "first_name": name_parts[1] if len(name_parts) > 1 else "",
        "dob": pid.get("PID.7", ""),
        "gender": pid.get("PID.8", ""),
        "address": pid.get("PID.11", "").replace("^", " "),
        "phone": pid.get("PID.13", ""),
    }


def extract_visit(segments: list[dict[str, str]]) -> dict[str, str]:
    """Extract visit info from PV1 segment."""
    pv1 = next((s for s in segments if s["segment"] == "PV1"), None)
    if not pv1:
        return {}
    return {
        "patient_class": pv1.get("PV1.2", ""),
        "location": pv1.get("PV1.3", "").replace("^", " "),
        "attending": pv1.get("PV1.7", "").split("^")[0] if pv1.get("PV1.7") else "",
        "visit_number": pv1.get("PV1.19", ""),
        "admit_date": pv1.get("PV1.44", ""),
        "discharge_date": pv1.get("PV1.45", ""),
    }


def extract_observations(segments: list[dict[str, str]]) -> list[dict[str, str]]:
    """Extract OBX observation results."""
    results = []
    for s in segments:
        if s["segment"] != "OBX":
            continue
        results.append({
            "set_id": s.get("OBX.1", ""),
            "value_type": s.get("OBX.2", ""),
            "test_code": s.get("OBX.3", "").split("^")[0] if s.get("OBX.3") else "",
            "test_name": s.get("OBX.3", "").split("^")[1] if "^" in s.get("OBX.3", "") else "",
            "value": s.get("OBX.5", ""),
            "units": s.get("OBX.6", ""),
            "reference_range": s.get("OBX.7", ""),
            "status": s.get("OBX.11", ""),
        })
    return results


def parse_messages(raw: str) -> dict:
    """Parse all messages and return structured result."""
    messages = split_messages(raw)
    patients = []
    visits = []
    observations = []

    for msg_text in messages:
        lines = msg_text.strip().split("\n")
        segments = [parse_segment(line) for line in lines if line.strip()]

        patient = extract_patient(segments)
        if patient:
            patients.append(patient)

        visit = extract_visit(segments)
        if visit and patient:
            visit["mrn"] = patient.get("mrn", "")
            visits.append(visit)

        obs = extract_observations(segments)
        for o in obs:
            o["mrn"] = patient.get("mrn", "")
        observations.extend(obs)

    return {
        "patients": patients,
        "visits": visits,
        "observations": observations,
        "message_count": len(messages),
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: parse_hl7v2.py <hl7-file> [--format csv|json]")
        sys.exit(1)

    path = Path(sys.argv[1])
    raw = path.read_text(errors="replace")
    result = parse_messages(raw)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
