---
name: 834-file-check
description: Validate EDI 834 enrollment files — structure, loops, dates, duplicates, add/term reconciliation — and produce a plain-English report.
tier: team
---

# 834 File Check

## When to Use

- You receive an EDI 834 (Benefit Enrollment and Maintenance) file and need to verify it before loading into a data warehouse or sending to a downstream system.
- You want to check loop structure (ISA/GS/ST/BGN/INS/REF/DTP/NM1), date validity, duplicate members, and add-vs-term balance.
- You need a plain-English summary suitable for sharing with non-technical stakeholders.

## Steps

1. **Accept the 834 file path** from the user. Confirm it exists and has content.

2. **Run the validation script**:
   ```bash
   python skills/834-file-check/scripts/validate_834.py <path-to-834-file>
   ```

3. **The script checks**:
   - **Envelope structure**: ISA/IEA, GS/GE, ST/SE segment counts match.
   - **Required loops**: Each member (2000) loop has INS, REF, NM1, and at least one DTP segment.
   - **Date validation**: All DTP dates are valid calendar dates and not in the far future (>2 years).
   - **Duplicate detection**: Flags members appearing more than once with the same SSN-substitute (REF*0F) in the same file.
   - **Add/Term reconciliation**: Counts INS*Y (add) vs INS*N (term) records and flags imbalances >20% as a warning.

4. **Review the report output** (JSON + plain-English summary). Share findings with the user.

5. **If errors are found**, recommend specific fixes:
   - Missing segments → contact the sender or check the mapping.
   - Date issues → verify source system date formats.
   - Duplicates → deduplicate at source or confirm intentional corrections.

## Inputs

| Input | Description |
|-------|-------------|
| `file_path` | Path to the EDI 834 file (`.edi`, `.834`, or `.txt`) |

## Output

A JSON report with:
- `valid`: boolean overall pass/fail
- `segment_counts`: counts of each segment type
- `errors`: list of `{type, segment, line, message}`
- `warnings`: list of `{type, message}`
- `summary`: plain-English paragraph summarizing results

## Caveats

- This checks structural validity per the X12 834 standard, not trading-partner-specific companion guides.
- It does not validate code sets (e.g., plan codes, relationship codes) beyond format.
- Real 834 files may have segment terminators other than `~`; the script handles `~` and `\n` terminators.
