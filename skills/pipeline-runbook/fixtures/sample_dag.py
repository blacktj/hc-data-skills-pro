"""Synthetic Airflow DAG for testing runbook generation."""

from datetime import datetime, timedelta

# This is a synthetic fixture — not a real Airflow DAG
DAG_CONFIG = {
    "dag_id": "synth_eligibility_load",
    "schedule_interval": "0 6 * * *",
    "owner": "synth-data-eng",
    "start_date": "2023-01-01",
}


# Simulated task definitions (not real Airflow imports)
class FakeOperator:
    def __init__(self, task_id, **kwargs):
        self.task_id = task_id


# Simulated DAG construction for metadata extraction
dag_id = "synth_eligibility_load"
schedule_interval = "0 6 * * *"
owner = "synth-data-eng"

extract_task = FakeOperator(task_id="extract_eligibility_file")
validate_task = FakeOperator(task_id="validate_834_structure")
transform_task = FakeOperator(task_id="transform_to_staging")
load_task = FakeOperator(task_id="load_to_warehouse")
test_task = FakeOperator(task_id="run_dbt_tests")
