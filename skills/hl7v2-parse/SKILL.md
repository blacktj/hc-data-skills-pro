---
name: hl7v2-parse
description: Parse HL7v2 ADT and ORU messages into flat, analysis-ready tables (CSV/JSON).
tier: free
---

# HL7v2 Parse

## When to Use

- You have HL7v2 messages (ADT admit/discharge/transfer or ORU observation results) and need them in a tabular format for analytics or warehouse loading.
- You want to extract patient demographics, visit info, and/or lab results into flat CSVs.
- You need to handle common HL7v2 quirks: repeated segments, varying delimiters, optional fields.

## Steps

1. **Accept the HL7v2 message file** from the user (one or more messages, `\n` or `\r` delimited).

2. **Run the parse script**:
   ```bash
   python skills/hl7v2-parse/scripts/parse_hl7v2.py <hl7-file> [--format csv|json]
   ```

3. **Review the output tables**:
   - **patients**: PID-based demographics (MRN, name, DOB, gender, address).
   - **visits**: PV1-based visit info (visit number, admit date, attending, location).
   - **observations** (ORU only): OBX results (test code, value, units, reference range, status).

4. **Validate** row counts against expected message counts.

## Inputs

| Input | Description |
|-------|-------------|
| `hl7_file` | Path to file containing HL7v2 messages |
| `--format` | Output format: `csv` (default) or `json` |

## Output

Flat tables written to stdout (JSON) or saved as CSVs in the working directory.

## Caveats

- Handles ADT (A01–A08, A28, A31) and ORU (R01) trigger events. Others are parsed best-effort.
- Custom Z-segments are preserved as raw key-value pairs but not mapped to specific fields.
- Does not validate HL7v2 conformance — focuses on practical extraction.
