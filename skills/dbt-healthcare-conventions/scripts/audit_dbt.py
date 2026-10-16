#!/usr/bin/env python3
"""Audit a dbt project for healthcare data engineering conventions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

STAGING_PATTERN = re.compile(r"^stg_[a-z0-9_]+__[a-z0-9_]+$")
INTERMEDIATE_PATTERN = re.compile(r"^int_[a-z0-9_]+__[a-z0-9_]+$")

REQUIRED_ELIGIBILITY_COLUMNS = {"member_id", "effective_date", "term_date", "payer_id"}
REQUIRED_ENCOUNTER_COLUMNS = {"encounter_id", "patient_id", "admit_date"}


def load_yaml_files(project_dir: Path) -> list[dict]:
    """Load all YAML files from models/ directory."""
    yaml_files = []
    models_dir = project_dir / "models"
    if not models_dir.exists():
        return []
    for yf in models_dir.rglob("*.yml"):
        with yf.open() as f:
            try:
                data = yaml.safe_load(f)
                if data:
                    yaml_files.append({"path": str(yf), "data": data})
            except yaml.YAMLError:
                pass
    return yaml_files


def get_sql_models(project_dir: Path) -> list[Path]:
    """Find all SQL model files."""
    models_dir = project_dir / "models"
    if not models_dir.exists():
        return []
    return list(models_dir.rglob("*.sql"))


def audit_naming(sql_models: list[Path]) -> list[dict]:
    """Check model naming conventions."""
    findings = []
    for model_path in sql_models:
        name = model_path.stem
        rel_parts = model_path.parts

        in_staging = any(p in ("staging", "stg") for p in rel_parts)
        in_intermediate = any(p in ("intermediate", "int") for p in rel_parts)

        if in_staging and not STAGING_PATTERN.match(name):
            findings.append({
                "severity": "WARNING",
                "category": "naming",
                "model": name,
                "message": f"Staging model '{name}' doesn't follow 'stg_<source>__<entity>' pattern",
            })
        elif in_intermediate and not INTERMEDIATE_PATTERN.match(name):
            findings.append({
                "severity": "WARNING",
                "category": "naming",
                "model": name,
                "message": f"Intermediate model '{name}' doesn't follow 'int_<entity>__<transform>' pattern",
            })

    return findings


def audit_tests(yaml_files: list[dict]) -> list[dict]:
    """Check for required tests on key columns."""
    findings = []
    for yf in yaml_files:
        models = yf["data"].get("models", [])
        for model in models:
            model_name = model.get("name", "unknown")
            columns = {c["name"]: c for c in model.get("columns", [])}

            for col_name, col_spec in columns.items():
                tests = col_spec.get("tests", []) or col_spec.get("data_tests", [])
                test_names = set()
                for t in tests:
                    if isinstance(t, str):
                        test_names.add(t)
                    elif isinstance(t, dict):
                        test_names.update(t.keys())

                if col_name in ("member_id", "encounter_id", "patient_id"):
                    if "unique" not in test_names:
                        findings.append({
                            "severity": "ERROR",
                            "category": "tests",
                            "model": model_name,
                            "message": f"Column '{col_name}' missing 'unique' test",
                        })
                    if "not_null" not in test_names:
                        findings.append({
                            "severity": "ERROR",
                            "category": "tests",
                            "model": model_name,
                            "message": f"Column '{col_name}' missing 'not_null' test",
                        })

    return findings


def audit_documentation(yaml_files: list[dict]) -> list[dict]:
    """Check for model and column documentation."""
    findings = []
    for yf in yaml_files:
        models = yf["data"].get("models", [])
        for model in models:
            model_name = model.get("name", "unknown")
            if not model.get("description"):
                findings.append({
                    "severity": "WARNING",
                    "category": "documentation",
                    "model": model_name,
                    "message": f"Model '{model_name}' missing description",
                })

    return findings


def audit_project(project_dir: str) -> dict:
    """Run all audits on a dbt project."""
    proj = Path(project_dir)
    if not (proj / "dbt_project.yml").exists():
        return {"error": f"No dbt_project.yml found in {project_dir}"}

    sql_models = get_sql_models(proj)
    yaml_files = load_yaml_files(proj)

    findings = []
    findings.extend(audit_naming(sql_models))
    findings.extend(audit_tests(yaml_files))
    findings.extend(audit_documentation(yaml_files))

    errors = [f for f in findings if f["severity"] == "ERROR"]
    warnings = [f for f in findings if f["severity"] == "WARNING"]

    return {
        "project_dir": str(proj),
        "model_count": len(sql_models),
        "yaml_files_scanned": len(yaml_files),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "findings": findings,
        "summary": (
            f"Scanned {len(sql_models)} models. "
            f"Found {len(errors)} error(s) and {len(warnings)} warning(s)."
        ),
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: audit_dbt.py <dbt-project-dir>")
        sys.exit(1)
    report = audit_project(sys.argv[1])
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
