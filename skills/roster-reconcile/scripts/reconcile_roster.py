#!/usr/bin/env python3
"""Month-over-month payer roster reconciliation."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def load_roster(path: str) -> list[dict[str, str]]:
    """Load a roster CSV with normalized column names."""
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items()})
    return rows


def _member_key(row: dict) -> str:
    """Natural key for ID change detection: name + DOB."""
    return (
        f"{row.get('first_name', '').lower()}|"
        f"{row.get('last_name', '').lower()}|"
        f"{row.get('date_of_birth', '')}"
    )


def reconcile(prior_rows: list[dict], current_rows: list[dict]) -> dict:
    """Reconcile two roster snapshots."""
    prior_ids = {r["member_id"]: r for r in prior_rows if r.get("member_id")}
    current_ids = {r["member_id"]: r for r in current_rows if r.get("member_id")}

    prior_set = set(prior_ids.keys())
    current_set = set(current_ids.keys())

    new_ids = current_set - prior_set
    dropped_ids = prior_set - current_set
    continued_ids = prior_set & current_set

    new_members = [current_ids[mid] for mid in sorted(new_ids)]
    dropped_members = [prior_ids[mid] for mid in sorted(dropped_ids)]
    continued_members = [current_ids[mid] for mid in sorted(continued_ids)]

    # ID change detection: same name+DOB but different member_id
    prior_by_key = {}
    for mid, row in prior_ids.items():
        key = _member_key(row)
        prior_by_key.setdefault(key, []).append((mid, row))

    id_changes = []
    for mid in new_ids:
        row = current_ids[mid]
        key = _member_key(row)
        if key in prior_by_key:
            for old_mid, old_row in prior_by_key[key]:
                if old_mid in dropped_ids:
                    id_changes.append({
                        "old_member_id": old_mid,
                        "new_member_id": mid,
                        "name": f"{row.get('first_name', '')} {row.get('last_name', '')}",
                        "date_of_birth": row.get("date_of_birth", ""),
                    })

    summary = (
        f"Roster reconciliation: {len(prior_rows)} prior → {len(current_rows)} current. "
        f"{len(new_members)} new, {len(dropped_members)} dropped, "
        f"{len(continued_members)} continued, {len(id_changes)} possible ID change(s)."
    )

    return {
        "prior_count": len(prior_rows),
        "current_count": len(current_rows),
        "new": new_members,
        "dropped": dropped_members,
        "continued_count": len(continued_members),
        "id_changes": id_changes,
        "summary": summary,
    }


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: reconcile_roster.py <prior.csv> <current.csv>")
        sys.exit(1)

    prior = load_roster(sys.argv[1])
    current = load_roster(sys.argv[2])
    result = reconcile(prior, current)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
