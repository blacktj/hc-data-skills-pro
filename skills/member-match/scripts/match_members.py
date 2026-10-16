#!/usr/bin/env python3
"""Deterministic + fuzzy member matching with blocking and nickname aliases."""

from __future__ import annotations

import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    from thefuzz import fuzz
except ImportError:
    fuzz = None

NICKNAME_ALIASES: dict[str, str] = {
    "bill": "william", "will": "william", "willy": "william", "willie": "william",
    "liam": "william",
    "bob": "robert", "rob": "robert", "robbie": "robert", "bobby": "robert",
    "robby": "robert",
    "liz": "elizabeth", "beth": "elizabeth", "eliza": "elizabeth",
    "betsy": "elizabeth", "lizzy": "elizabeth", "betty": "elizabeth",
    "liza": "elizabeth",
    "jim": "james", "jimmy": "james", "jamie": "james",
    "mike": "michael", "mikey": "michael", "mick": "michael",
    "dave": "david", "davy": "david",
    "steve": "steven", "stephen": "steven",
    "joe": "joseph", "joey": "joseph",
    "tom": "thomas", "tommy": "thomas",
    "dan": "daniel", "danny": "daniel",
    "dick": "richard", "rick": "richard", "rich": "richard", "ricky": "richard",
    "ed": "edward", "eddie": "edward", "ted": "edward", "teddy": "edward",
    "ned": "edward",
    "chris": "christopher", "kit": "christopher",
    "tony": "anthony",
    "nick": "nicholas",
    "matt": "matthew", "matty": "matthew",
    "pat": "patrick", "paddy": "patrick",
    "alex": "alexander", "al": "alexander",
    "andy": "andrew", "drew": "andrew",
    "ben": "benjamin", "benny": "benjamin",
    "charlie": "charles", "chuck": "charles", "chas": "charles",
    "frank": "francis", "frankie": "francis",
    "fred": "frederick", "freddy": "frederick",
    "greg": "gregory",
    "hank": "henry", "harry": "henry",
    "jack": "john", "johnny": "john", "jon": "john",
    "jerry": "gerald", "gerry": "gerald",
    "jeff": "jeffrey",
    "larry": "lawrence",
    "pete": "peter",
    "phil": "philip",
    "ray": "raymond",
    "ron": "ronald", "ronnie": "ronald",
    "sam": "samuel", "sammy": "samuel",
    "walt": "walter", "wally": "walter",
    "kate": "katherine", "kathy": "katherine", "cathy": "katherine",
    "katie": "katherine", "kat": "katherine",
    "jen": "jennifer", "jenny": "jennifer",
    "sue": "susan", "suzy": "susan", "susie": "susan",
    "meg": "margaret", "maggie": "margaret", "peggy": "margaret",
    "madge": "margaret",
    "pam": "pamela",
    "deb": "deborah", "debbie": "deborah",
    "barb": "barbara", "barbie": "barbara",
    "cindy": "cynthia",
    "di": "diana",
    "dot": "dorothy", "dottie": "dorothy",
    "fran": "frances", "frannie": "frances",
    "jess": "jessica", "jessie": "jessica",
    "judy": "judith", "judi": "judith",
    "lori": "lorraine",
    "mandy": "amanda",
    "nan": "nancy",
    "nicky": "nicole", "nikki": "nicole",
    "peg": "margaret",
    "sally": "sarah",
    "sandy": "sandra",
    "tina": "christina", "chris": "christina",
    "vicky": "victoria", "vicki": "victoria",
}

_CANONICAL_CACHE: dict[str, str] = {}


def _canonical_name(name: str) -> str:
    """Resolve a name to its canonical form via the alias table."""
    key = name.strip().lower()
    if key in _CANONICAL_CACHE:
        return _CANONICAL_CACHE[key]
    canonical = NICKNAME_ALIASES.get(key, key)
    _CANONICAL_CACHE[key] = canonical
    return canonical


def _soundex(name: str) -> str:
    """Compute American Soundex code for a name."""
    name = name.strip().upper()
    if not name:
        return "0000"
    name = "".join(c for c in name if c.isalpha())
    if not name:
        return "0000"

    coding = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2",
        "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6",
    }

    result = name[0]
    prev_code = coding.get(name[0], "0")
    for ch in name[1:]:
        code = coding.get(ch, "0")
        if code != "0" and code != prev_code:
            result += code
        prev_code = code if code != "0" else prev_code

    result = result[:4].ljust(4, "0")
    return result


WEIGHTS = {
    "last_name": 0.20,
    "first_name": 0.15,
    "date_of_birth": 0.30,
    "ssn": 0.20,
    "member_id": 0.15,
}

DEFAULT_THRESHOLD = 0.75
DEFAULT_BLOCKING = ["dob_year"]

BLOCKING_STRATEGIES = {
    "dob_year": lambda row: row.get("date_of_birth", "")[:4],
    "zip_prefix": lambda row: row.get("zip_code", row.get("zip", ""))[:3],
    "soundex_last": lambda row: _soundex(row.get("last_name", "")),
    "first_initial_last": lambda row: row.get("last_name", "")[:1].lower(),
}


def _similarity(a: str, b: str) -> float:
    """Compute normalized similarity between two strings."""
    if not a or not b:
        return 0.0
    a, b = a.strip().lower(), b.strip().lower()
    if a == b:
        return 1.0
    if fuzz:
        return fuzz.ratio(a, b) / 100.0
    common = sum(1 for ca, cb in zip(a, b) if ca == cb)
    return common / max(len(a), len(b))


def _name_similarity(a: str, b: str) -> tuple[float, bool]:
    """Compute name similarity, trying alias resolution.

    Returns (score, alias_used).
    """
    if not a or not b:
        return 0.0, False
    a_low, b_low = a.strip().lower(), b.strip().lower()
    if a_low == b_low:
        return 1.0, False

    a_canon = _canonical_name(a_low)
    b_canon = _canonical_name(b_low)
    if a_canon == b_canon:
        return 0.95, True

    base_sim = _similarity(a, b)

    canon_sim = _similarity(a_canon, b_canon)
    if canon_sim > base_sim:
        return canon_sim, True
    return base_sim, False


def _deterministic_match(left: dict, right: dict) -> str | None:
    """Check for exact-key deterministic matches."""
    if (
        left.get("ssn")
        and right.get("ssn")
        and left["ssn"] == right["ssn"]
    ):
        return "SSN"
    if (
        left.get("member_id")
        and right.get("member_id")
        and left["member_id"] == right["member_id"]
    ):
        return "MEMBER_ID"
    return None


def score_pair(left: dict, right: dict) -> dict:
    """Score a pair of records with alias-aware name matching."""
    field_scores = {}
    aliases_used = []

    for field, weight in WEIGHTS.items():
        lv = left.get(field, "")
        rv = right.get(field, "")
        if field in ("first_name", "last_name"):
            sim, alias_used = _name_similarity(lv, rv)
            if alias_used:
                aliases_used.append(
                    f"{field}: '{lv}' matched '{rv}' via alias"
                )
        else:
            sim = _similarity(lv, rv)
        field_scores[field] = {
            "similarity": round(sim, 3),
            "weight": weight,
        }

    overall = sum(
        fs["similarity"] * fs["weight"] for fs in field_scores.values()
    )
    result: dict = {
        "field_scores": field_scores,
        "overall_score": round(overall, 3),
    }
    if aliases_used:
        result["aliases_used"] = aliases_used
    return result


def build_blocks(
    rows: list[dict],
    strategies: list[str],
) -> dict[str, list[int]]:
    """Build blocking index: key -> list of row indices."""
    blocks: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        keys = []
        for strat_name in strategies:
            fn = BLOCKING_STRATEGIES.get(strat_name)
            if fn:
                keys.append(fn(row))
        block_key = "|".join(keys)
        blocks[block_key].append(idx)
    return dict(blocks)


_SENTINEL = object()


def match_datasets(
    left_rows: list[dict],
    right_rows: list[dict],
    threshold: float = DEFAULT_THRESHOLD,
    blocking: list[str] | None | object = _SENTINEL,
) -> list[dict]:
    """Match left records against right records.

    Blocking defaults to ``DEFAULT_BLOCKING`` (``["dob_year"]``) for
    best recall at scale.  Pass an explicit list for tighter blocking
    (faster, lower recall) or ``None`` / ``[]`` for brute-force O(n*m).
    """
    if blocking is _SENTINEL:
        blocking = DEFAULT_BLOCKING
    if blocking:
        return _match_with_blocking(
            left_rows, right_rows, threshold, blocking
        )
    return _match_brute_force(left_rows, right_rows, threshold)


def _match_with_blocking(
    left_rows: list[dict],
    right_rows: list[dict],
    threshold: float,
    blocking: list[str],
) -> list[dict]:
    """Match using blocking to reduce candidate pairs."""
    right_blocks = build_blocks(right_rows, blocking)

    results = []
    for li, left in enumerate(left_rows):
        left_keys = []
        for strat_name in blocking:
            fn = BLOCKING_STRATEGIES.get(strat_name)
            if fn:
                left_keys.append(fn(left))
        block_key = "|".join(left_keys)

        candidates = right_blocks.get(block_key, [])

        best_match = None
        best_score = -1.0
        best_detail = None
        found_deterministic = False

        for ri in candidates:
            right = right_rows[ri]
            det = _deterministic_match(left, right)
            if det:
                detail = score_pair(left, right)
                detail["overall_score"] = 1.0
                results.append({
                    "left_index": li,
                    "right_index": ri,
                    "match_type": "DETERMINISTIC",
                    "deterministic_key": det,
                    "block_key": block_key,
                    **detail,
                })
                found_deterministic = True
                break

            detail = score_pair(left, right)
            if detail["overall_score"] > best_score:
                best_score = detail["overall_score"]
                best_match = ri
                best_detail = detail

        if found_deterministic:
            continue

        if best_match is not None and best_score >= threshold:
            results.append({
                "left_index": li,
                "right_index": best_match,
                "match_type": "FUZZY",
                "block_key": block_key,
                **best_detail,
            })
        else:
            result_entry: dict = {
                "left_index": li,
                "right_index": best_match,
                "match_type": "NO_MATCH",
                "block_key": block_key,
            }
            if best_detail:
                result_entry.update(best_detail)
            else:
                result_entry["overall_score"] = 0.0
            results.append(result_entry)

    return results


def _match_brute_force(
    left_rows: list[dict],
    right_rows: list[dict],
    threshold: float,
) -> list[dict]:
    """Original O(n*m) matching — no blocking."""
    results = []
    for li, left in enumerate(left_rows):
        best_match = None
        best_score = -1.0
        best_detail = None
        found_deterministic = False

        for ri, right in enumerate(right_rows):
            det = _deterministic_match(left, right)
            if det:
                detail = score_pair(left, right)
                detail["overall_score"] = 1.0
                results.append({
                    "left_index": li,
                    "right_index": ri,
                    "match_type": "DETERMINISTIC",
                    "deterministic_key": det,
                    **detail,
                })
                found_deterministic = True
                break

            detail = score_pair(left, right)
            if detail["overall_score"] > best_score:
                best_score = detail["overall_score"]
                best_match = (ri, right)
                best_detail = detail

        if found_deterministic:
            continue

        if best_match and best_score >= threshold:
            ri, right = best_match
            results.append({
                "left_index": li,
                "right_index": ri,
                "match_type": "FUZZY",
                **best_detail,
            })
        elif best_match:
            ri, right = best_match
            results.append({
                "left_index": li,
                "right_index": ri,
                "match_type": "NO_MATCH",
                **best_detail,
            })
        else:
            results.append({
                "left_index": li,
                "right_index": None,
                "match_type": "NO_MATCH",
                "overall_score": 0.0,
            })

    return results


def load_csv(path: str) -> list[dict]:
    """Load a CSV, normalizing column names to lowercase."""
    rows = []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({
                k.strip().lower().replace(" ", "_"): v.strip()
                for k, v in row.items()
            })
    return rows


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: match_members.py <left.csv> <right.csv> "
            "[--threshold 0.75] "
            "[--blocking dob_year,soundex_last] "
            "[--no-blocking]"
        )
        print(
            f"\nDefault blocking: {','.join(DEFAULT_BLOCKING)} "
            f"(best recall). Use --blocking to override or "
            f"--no-blocking for brute-force O(n*m)."
        )
        sys.exit(1)

    left = load_csv(sys.argv[1])
    right = load_csv(sys.argv[2])

    threshold = DEFAULT_THRESHOLD
    if "--threshold" in sys.argv:
        idx = sys.argv.index("--threshold")
        threshold = float(sys.argv[idx + 1])

    if "--no-blocking" in sys.argv:
        blocking: list[str] | None = None
    elif "--blocking" in sys.argv:
        idx = sys.argv.index("--blocking")
        blocking = sys.argv[idx + 1].split(",")
    else:
        blocking = DEFAULT_BLOCKING

    t0 = time.perf_counter()
    results = match_datasets(left, right, threshold, blocking)
    elapsed = time.perf_counter() - t0

    print(json.dumps(results, indent=2))

    matched = sum(
        1 for r in results if r["match_type"] != "NO_MATCH"
    )
    print(
        f"\n{matched}/{len(results)} records matched "
        f"(threshold={threshold}, elapsed={elapsed:.3f}s)"
    )
    if blocking:
        print(f"Blocking: {', '.join(blocking)}")
    else:
        print("Blocking: none (brute force)")


if __name__ == "__main__":
    main()
