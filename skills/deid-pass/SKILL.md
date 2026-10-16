---
name: deid-pass
description: Apply HIPAA Safe Harbor de-identification to a dataset — redact or transform all 18 identifier types, produce a before/after column report, and refuse export when coverage is uncertain.
tier: team
---

# De-identification Pass

## When to Use

- You need to de-identify a dataset according to HIPAA Safe Harbor (45 CFR 164.514(b)(2)).
- You want an auditable before/after report showing which columns were redacted, generalized, or left untouched and why.
- You want a tool that **refuses to export** when it cannot confidently classify a column, forcing a human review.

## Steps

1. **Accept the input CSV** path and an optional column-classification override file.

2. **Run the de-identification script**:
   ```bash
   python skills/deid-pass/scripts/deid_safe_harbor.py <input.csv> [--overrides overrides.yaml]
   ```

3. **The script**:
   - Scans column names and sample values against the 18 HIPAA Safe Harbor identifier categories.
   - Applies transformations: redact (replace with `[REDACTED]`), generalize (e.g., truncate ZIP to 3 digits, replace dates with year-only), or pass through (non-PHI columns).
   - Produces a `deid_report.json` with per-column classification, action taken, and confidence.
   - **Refuses to write output** if any column has confidence < 0.7 — prints the uncertain columns and asks for human override.

4. **Review the report** with the user before sharing the de-identified file.

## The 18 HIPAA Safe Harbor Identifiers

Names, geographic data (below state), dates (except year), phone, fax, email, SSN, MRN, health plan beneficiary numbers, account numbers, certificate/license numbers, vehicle IDs/serial numbers, device IDs, URLs, IPs, biometric IDs, full-face photos, any unique identifying number.

## Inputs

| Input | Description |
|-------|-------------|
| `input_csv` | Path to the CSV to de-identify |
| `--overrides` | Optional YAML mapping column names to actions (`redact`, `generalize`, `keep`) |

## Output

- `deid_output.csv` — the de-identified dataset (only written if all columns classified with confidence >= 0.7)
- `deid_report.json` — per-column classification and action report

## Caveats

- Safe Harbor is a rule-based method; Expert Determination (164.514(a)) is not implemented here.
- Free-text / notes columns should be reviewed manually — the script flags but does not NLP-parse them.
- This tool helps but does NOT constitute legal compliance — always have your privacy officer review.
