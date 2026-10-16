---
name: phi-column-scan
description: Scan a schema, dbt model, or sample data to flag columns that likely contain PHI — runs entirely locally, no data leaves the machine.
tier: free
---

# PHI Column Scan

## When to Use

- You're onboarding a new data source and need to quickly identify which columns might contain PHI before building pipelines.
- You want to audit an existing dbt project or database schema for PHI exposure.
- You need a lightweight, local-only scan that does not transmit any data.

## Steps

1. **Provide a schema file** — CSV with `column_name,data_type,sample_value` or a SQL DDL file.

2. **Run the scan**:
   ```bash
   python skills/phi-column-scan/scripts/scan_phi_columns.py <schema-file>
   ```

3. **Review the report** — each column gets a risk classification:
   - `HIGH`: Column name and/or sample strongly match a HIPAA identifier pattern.
   - `MEDIUM`: Column name is ambiguous but could be PHI (e.g., `id`, `code`, `notes`).
   - `LOW`: Column appears to be non-PHI (clinical codes, flags, counts).

4. **Take action** on HIGH-risk columns: confirm classification with a data steward, apply de-identification, or document why the column is safe.

## Inputs

| Input | Description |
|-------|-------------|
| `schema_file` | CSV with `column_name,data_type,sample_value` or SQL DDL |

## Output

JSON report with per-column risk classification, pattern matched, and recommended action.

## Caveats

- Heuristic-based; will have false positives on columns like `service_date` (clinically useful, not individual-level PHI in aggregate).
- Does not analyze free-text content — flags `notes` columns as MEDIUM but cannot assess content.
- Designed as a triage tool, not a compliance certification.
