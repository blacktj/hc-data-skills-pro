#!/usr/bin/env python3
"""Generate an on-call runbook from an Airflow DAG or dbt project."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def detect_type(file_path: Path) -> str:
    """Auto-detect pipeline type from file content."""
    text = file_path.read_text(errors="replace")
    if "DAG(" in text or "airflow" in text.lower():
        return "airflow"
    if "dbt_project" in file_path.name or file_path.suffix == ".yml":
        return "dbt"
    return "unknown"


def extract_airflow_metadata(text: str) -> dict:
    """Extract DAG metadata from a Python DAG file."""
    dag_id_match = re.search(r'dag_id\s*=\s*["\']([^"\']+)["\']', text)
    schedule_match = re.search(r'schedule(?:_interval)?\s*=\s*["\']([^"\']+)["\']', text)
    owner_match = re.search(r'owner\s*=\s*["\']([^"\']+)["\']', text)

    task_patterns = [
        re.compile(r'task_id\s*=\s*["\']([^"\']+)["\']'),
        re.compile(r'PythonOperator\s*\(\s*task_id\s*=\s*["\']([^"\']+)["\']'),
        re.compile(r'BashOperator\s*\(\s*task_id\s*=\s*["\']([^"\']+)["\']'),
    ]
    tasks = set()
    for pat in task_patterns:
        tasks.update(pat.findall(text))

    return {
        "dag_id": dag_id_match.group(1) if dag_id_match else "unknown_dag",
        "schedule": schedule_match.group(1) if schedule_match else "not specified",
        "owner": owner_match.group(1) if owner_match else "team",
        "tasks": sorted(tasks) or ["(no tasks detected)"],
    }


def extract_dbt_metadata(text: str) -> dict:
    """Extract dbt project metadata from YAML."""
    import yaml

    try:
        data = yaml.safe_load(text)
    except Exception:
        data = {}

    return {
        "project_name": data.get("name", "unknown_project"),
        "version": data.get("version", ""),
        "model_paths": data.get("model-paths", ["models"]),
        "schedule": "See orchestrator (Airflow/Prefect/dbt Cloud)",
    }


def generate_runbook(file_path: str, pipeline_type: str | None = None) -> str:
    """Generate a Markdown runbook."""
    path = Path(file_path)
    text = path.read_text(errors="replace")

    if not pipeline_type:
        pipeline_type = detect_type(path)

    if pipeline_type == "airflow":
        meta = extract_airflow_metadata(text)
        return _airflow_runbook(meta)
    elif pipeline_type == "dbt":
        meta = extract_dbt_metadata(text)
        return _dbt_runbook(meta)
    else:
        return f"# Runbook\n\nCould not detect pipeline type for `{file_path}`.\n"


def _airflow_runbook(meta: dict) -> str:
    tasks_list = "\n".join(f"- `{t}`" for t in meta["tasks"])
    return f"""# Runbook: {meta['dag_id']}

## Overview

| Field | Value |
|-------|-------|
| DAG ID | `{meta['dag_id']}` |
| Schedule | `{meta['schedule']}` |
| Owner | {meta['owner']} |

## Tasks

{tasks_list}

## SLA

| Metric | Target |
|--------|--------|
| Completion | TODO: fill in expected completion time |
| Data freshness | TODO: max acceptable lag |

## Common Failure Modes

### 1. Source System Unavailable
- **Symptom**: Connection timeout or HTTP 5xx in task logs.
- **Recovery**: Check source system status. Retry the failed task: `airflow tasks run {meta['dag_id']} <task_id> <execution_date>`.
- **Escalation**: If source is down >1 hour, contact the source system team.

### 2. Data Quality Failure
- **Symptom**: Downstream test failures or unexpected row counts.
- **Recovery**: Check source data for schema changes. Review task logs for transformation errors.
- **Escalation**: Contact the data engineering lead.

### 3. Infrastructure Failure
- **Symptom**: Worker pod OOM, disk full, or scheduler crash.
- **Recovery**: Check Airflow worker logs and Kubernetes pod status. Restart the worker if needed.
- **Escalation**: Contact the platform/infra team.

## Recovery Steps

1. Check the Airflow UI for the failed task instance.
2. Review task logs for the specific error.
3. If transient, clear the task and retry: `airflow tasks clear {meta['dag_id']} -t <task_id> -s <start> -e <end>`.
4. If persistent, investigate the root cause before retrying.

## Escalation

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | Any failure during business hours |
| L2 | Data engineering lead | Failure >1 hour or data loss risk |
| L3 | Engineering manager | SLA breach or compliance impact |

## Monitoring

- Airflow UI: TODO: add URL
- Alerting: TODO: add PagerDuty/Slack channel
- Dashboard: TODO: add Grafana/Datadog link
"""


def _dbt_runbook(meta: dict) -> str:
    return f"""# Runbook: {meta['project_name']}

## Overview

| Field | Value |
|-------|-------|
| Project | `{meta['project_name']}` |
| Version | `{meta['version']}` |
| Model Paths | `{', '.join(meta['model_paths'])}` |
| Schedule | {meta['schedule']} |

## Common Failure Modes

### 1. Model Build Failure
- **Symptom**: `dbt run` exits with error on a specific model.
- **Recovery**: Check the model SQL and upstream dependencies. Run `dbt run -s <model_name>` to retry.

### 2. Test Failure
- **Symptom**: `dbt test` reports failures.
- **Recovery**: Check test results with `dbt test -s <model_name>`. Investigate data quality at the source.

### 3. Source Freshness Failure
- **Symptom**: `dbt source freshness` reports stale sources.
- **Recovery**: Verify the upstream pipeline has run. Check source system status.

## Recovery Steps

1. Identify the failed model from dbt logs or the orchestrator.
2. Run `dbt debug` to verify connection and configuration.
3. Run `dbt run -s +<failed_model>` to rebuild with upstream dependencies.
4. Run `dbt test -s <failed_model>` to verify data quality.

## Escalation

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | Any `dbt run` failure |
| L2 | Analytics engineering lead | Test failures affecting dashboards |
| L3 | Engineering manager | SLA breach |

## Monitoring

- dbt Cloud / orchestrator UI: TODO: add URL
- Alerting: TODO: add Slack/PagerDuty
- Dashboard: TODO: add monitoring link
"""


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: generate_runbook.py <pipeline-file> [--type airflow|dbt]")
        sys.exit(1)

    file_path = sys.argv[1]
    ptype = None
    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        ptype = sys.argv[idx + 1]

    runbook = generate_runbook(file_path, ptype)
    print(runbook)


if __name__ == "__main__":
    main()
