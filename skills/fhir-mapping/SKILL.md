---
name: fhir-mapping
description: Generate a FHIR R4 mapping specification from a source table schema — maps columns to Patient, Coverage, and Encounter resources, flags unmappable fields.
tier: team
---

# FHIR Mapping

## When to Use

- You have a source table (CSV, SQL DDL, or dbt model) and need to map it to FHIR R4 resources (Patient, Coverage, Encounter).
- You want a structured mapping spec with source column, FHIR resource, FHIR path, data type, and transformation notes.
- You need to identify columns that don't map cleanly to FHIR and require custom extensions or should be dropped.

## Steps

1. **Accept the source schema** — a CSV file, SQL DDL, or column list from the user.

2. **Run the mapping script**:
   ```bash
   python skills/fhir-mapping/scripts/map_to_fhir.py <schema-file>
   ```

3. **Review the output** — a Markdown table mapping each source column to a FHIR path, plus a list of unmapped/flagged columns.

4. **Iterate with the user** — adjust mappings, add custom extensions, or mark columns as intentionally excluded.

## Inputs

| Input | Description |
|-------|-------------|
| `schema_file` | Path to a CSV with columns `column_name,data_type,sample_value,description` or a SQL DDL file |

## Output

A Markdown mapping spec with:
- Source column → FHIR Resource.path
- Data type transformation notes
- Flagged columns (unmappable, ambiguous, or needing extensions)

## Caveats

- Mapping is heuristic-based and requires human review.
- Only covers Patient, Coverage, and Encounter; other resources can be added manually.
- Does not validate against FHIR profiles or implementation guides — produces a starting-point spec.
