---
name: code-set-lookup
description: Validate and explain ICD-10, CPT (format only), NDC, and LOINC codes — checks format, flags invalid codes, notes licensing restrictions.
tier: team
---

# Code Set Lookup

## When to Use

- You need to validate a list of diagnosis, procedure, drug, or lab codes against known formats.
- You want to check if codes are well-formed (correct length, character pattern, check digits where applicable).
- You need a quick explanation of what a code's format indicates (ICD-10 category, NDC structure, etc.).

## Steps

1. **Provide codes** as a CSV or a list, specifying the code system.

2. **Run the validation**:
   ```bash
   python skills/code-set-lookup/scripts/validate_codes.py <codes.csv>
   ```

3. **Review the report**:
   - Each code is validated against the format rules for its code system.
   - ICD-10-CM: 3–7 characters, alpha first character, valid category structure.
   - CPT: 5 digits (format validation ONLY — no descriptions due to AMA licensing).
   - NDC: 10–11 digits in 4-4-2, 5-3-2, or 5-4-1 format.
   - LOINC: Numeric with check digit, formatted as `NNNNN-N`.

4. **Note licensing restrictions** in the report.

## Licensing Notes

- **CPT**: CPT codes are copyrighted by the American Medical Association. This tool validates the 5-digit format ONLY. No CPT descriptions are included. To use CPT descriptions, obtain a license from the AMA.
- **ICD-10**: ICD-10-CM is maintained by CMS/NCHS and is publicly available. Format structure is validated; full code lookup requires the CMS code tables.
- **NDC**: NDC directory is publicly available from FDA. Format is validated here.
- **LOINC**: LOINC is maintained by the Regenstrief Institute and is freely available with attribution. Format is validated here.

## Inputs

| Input | Description |
|-------|-------------|
| `codes_csv` | CSV with columns `code,system` where system is `icd10`, `cpt`, `ndc`, or `loinc` |

## Output

JSON report with per-code validation result, format explanation, and any warnings.

## Caveats

- Format validation only — does not verify a code is a real, active code in the code set.
- CPT descriptions are intentionally omitted (AMA license required).
- For production code validation, use the official CMS/AMA/FDA/Regenstrief code files.
