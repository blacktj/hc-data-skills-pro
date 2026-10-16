"""PHI pattern scanner — detects HIPAA Safe Harbor identifiers in text files."""

from __future__ import annotations

import re
from pathlib import Path

PHI_PATTERNS: list[dict[str, str | re.Pattern[str]]] = [
    {
        "name": "SSN",
        "pattern": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    },
    {
        "name": "SSN (no dashes)",
        "pattern": re.compile(r"\b(?<!\d)\d{9}(?!\d)\b"),
    },
    {
        "name": "Phone number",
        "pattern": re.compile(
            r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b"
        ),
    },
    {
        "name": "Email address",
        "pattern": re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        ),
    },
    {
        "name": "MRN-like ID (MRN prefix)",
        "pattern": re.compile(r"\bMRN[:\s#-]*\d{5,}\b", re.IGNORECASE),
    },
    {
        "name": "Date of birth with label",
        "pattern": re.compile(
            r"\b(?:DOB|date\s*of\s*birth|birth\s*date)[:\s]*"
            r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
            re.IGNORECASE,
        ),
    },
    {
        "name": "Street address",
        "pattern": re.compile(
            r"\b\d{1,6}\s+(?:[A-Z][a-z]+\s+){1,3}"
            r"(?:St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|Ln|Lane|Rd|Road|Ct|Court|Way|Pl|Place)\b",
        ),
    },
    {
        "name": "ZIP+4 code",
        "pattern": re.compile(r"\b\d{5}-\d{4}\b"),
    },
    {
        "name": "Medicare Beneficiary Identifier",
        "pattern": re.compile(
            r"\b[1-9][A-Za-z][A-Za-z0-9]\d[A-Za-z][A-Za-z0-9]\d[A-Za-z]{2}\d{2}\b"
        ),
    },
]

SAFE_COMMENT = re.compile(r"#\s*phi-safe", re.IGNORECASE)

BINARY_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".svg",
    ".pdf", ".zip", ".gz", ".tar", ".whl", ".exe", ".dll",
    ".pyc", ".pyo", ".so", ".o", ".a",
})


def _is_scannable(path: Path) -> bool:
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False
    return path.is_file()


def scan_text(text: str, filename: str = "<input>") -> list[dict[str, str | int]]:
    """Scan a string for PHI patterns. Returns list of findings."""
    findings: list[dict[str, str | int]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if SAFE_COMMENT.search(line):
            continue
        for pat in PHI_PATTERNS:
            for match in pat["pattern"].finditer(line):
                matched_text = match.group()
                if _is_obviously_fake(pat["name"], matched_text):
                    continue
                findings.append({
                    "file": filename,
                    "line": line_no,
                    "pattern_name": pat["name"],
                    "match": matched_text,
                })
    return findings


def _is_obviously_fake(pattern_name: str, text: str) -> bool:
    """Heuristic: skip values that are obviously synthetic/test data.

    We keep this conservative — better to over-flag than miss real PHI.
    """
    if pattern_name == "SSN" and text in ("000-00-0000", "123-45-6789"):
        return True
    return False


def scan_paths(paths: list[Path]) -> list[dict[str, str | int]]:
    """Scan a list of file paths for PHI patterns."""
    all_findings: list[dict[str, str | int]] = []
    for path in paths:
        if not _is_scannable(path):
            continue
        try:
            text = path.read_text(errors="replace")
        except (OSError, PermissionError):
            continue
        all_findings.extend(scan_text(text, filename=str(path)))
    return all_findings
