---
name: dbt-healthcare-conventions
description: Audit a dbt project for healthcare data engineering conventions — naming, layering, tests, and documentation for eligibility, encounters, and roster snapshots (no claims).
tier: team
---

# dbt Healthcare Conventions

## When to Use

- You're building or reviewing a dbt project that models healthcare data (eligibility, encounters, roster snapshots).
- You want to enforce consistent naming, layering (staging/intermediate/mart), test coverage, and documentation standards.
- You need a checklist or automated audit of convention adherence.

## Steps

1. **Provide the dbt project path** (directory containing `dbt_project.yml`).

2. **Run the conventions audit**:
   ```bash
   python skills/dbt-healthcare-conventions/scripts/audit_dbt.py <dbt-project-dir>
   ```

3. **Review the findings**, organized by category:
   - **Naming**: Models follow `stg_<source>__<entity>`, `int_<entity>__<transform>`, `<entity>` (mart) patterns.
   - **Layering**: Staging models reference only sources; intermediates reference staging/other intermediates; marts are the public API.
   - **Required tests**: Primary keys have `unique` + `not_null`; foreign keys have `relationships`; date columns have `accepted_values` or range tests.
   - **Documentation**: All mart models have descriptions; key columns have descriptions; sources are documented.
   - **Healthcare-specific**: Eligibility models have `effective_date`/`term_date`; encounter models have `admit_date`/`discharge_date`; roster snapshots use dbt snapshots or SCD logic.

4. **Fix issues** using the recommendations in the report.

## Conventions Reference

### Naming

| Layer | Pattern | Example |
|-------|---------|---------|
| Staging | `stg_<source>__<entity>` | `stg_payer_alpha__eligibility` |
| Intermediate | `int_<entity>__<transform>` | `int_eligibility__deduplicated` |
| Mart | `<entity>` | `member_eligibility_current` |

### Required Tests (Eligibility)

- `member_id`: unique, not_null
- `effective_date`, `term_date`: not_null, `effective_date <= term_date`
- `payer_id`: not_null, relationships to payer reference

### Required Tests (Encounters)

- `encounter_id`: unique, not_null
- `admit_date`: not_null
- `patient_id`: not_null, relationships to member

## Inputs

| Input | Description |
|-------|-------------|
| `dbt_project_dir` | Path to the dbt project root |

## Output

JSON audit report with findings categorized by severity (ERROR, WARNING, INFO).

## Caveats

- Focused on eligibility, encounters, and roster snapshots — does not cover claims models.
- Checks are heuristic-based on file names and YAML structure; does not parse SQL.
- Compatible with dbt-core 1.5+ project structure.
