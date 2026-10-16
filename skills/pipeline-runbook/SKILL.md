---
name: pipeline-runbook
description: Generate an on-call runbook from an Airflow DAG definition or dbt job manifest — documents failure modes, escalation paths, and recovery steps.
tier: free
---

# Pipeline Runbook

## When to Use

- You have an Airflow DAG or dbt job and need to create or update an on-call runbook for the data engineering team.
- You want to document: what the pipeline does, SLA, common failure modes, recovery steps, escalation contacts, and monitoring links.
- You need a structured template that's easy to maintain alongside the pipeline code.

## Steps

1. **Provide the pipeline definition**:
   - Airflow: Python DAG file.
   - dbt: `dbt_project.yml` or a specific model's SQL + YAML.

2. **Run the runbook generator**:
   ```bash
   python skills/pipeline-runbook/scripts/generate_runbook.py <pipeline-file> [--type airflow|dbt]
   ```

3. **Review and customize** the generated runbook:
   - Fill in team-specific escalation contacts.
   - Add monitoring dashboard links.
   - Customize recovery steps for your infrastructure.

4. **Save the runbook** alongside the pipeline code (e.g., `runbooks/<dag_name>.md`).

## Inputs

| Input | Description |
|-------|-------------|
| `pipeline_file` | Path to Airflow DAG (.py) or dbt project/model file |
| `--type` | Pipeline type: `airflow` or `dbt` (auto-detected if omitted) |

## Output

A Markdown runbook with sections: Overview, Schedule/SLA, Tasks, Failure Modes, Recovery Steps, Escalation, Monitoring.

## Caveats

- The generator extracts metadata heuristically (DAG ID, schedule, task names) — it does not execute the DAG.
- Failure modes are templated based on task type; customize for your specific infrastructure.
- For complex DAGs with dynamic task generation, the runbook will cover the static structure.
