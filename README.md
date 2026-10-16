# hc-data-skills Team

**Team tier** — private, licensed pack with **all 10** healthcare data-engineering skills.

This is the paid Team edition (`blacktj/hc-data-skills-pro`). It is a private repository. Skill content is proprietary and all rights reserved. The `hcskills` CLI remains MIT-licensed.

Format-compatible with [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/skills) and [Cursor](https://docs.cursor.com/context/rules-for-ai) skills — one folder per skill with a `SKILL.md` that has name + description frontmatter, when-to-use, steps, plus scripts, templates, and fixtures.

**Your data stays local. We never host your data. No BAA needed.**

Teams install skills into **their own repo**; all memory and working files live as files in the team's repository. There is no hosted service, no data upload, and no external API calls. The CLI is a local file-copy tool.

---

## Quick Start

```bash
# Clone this private Team pack (requires GitHub access)
git clone https://github.com/blacktj/hc-data-skills-pro.git
cd hc-data-skills-pro

# Install the CLI (requires Python 3.10+)
pipx install -e .
# or
uv pip install -e .

# Install skills into your repo
cd your-data-repo/
hcskills install --target cursor   # copies to .cursor/skills/hc-data-skills/
hcskills install --target claude   # copies to .claude/skills/hc-data-skills/

# List available skills (all 10)
hcskills list

# Pull latest Team skills from this repo
hcskills update

# Initialize a local memory folder
hcskills memory init

# Scan files for PHI patterns
hcskills guard path/to/file.csv

# Scan git staged files (pre-commit)
hcskills guard --staged
```

## Skills

This Team pack includes every skill — the three Community skills plus the seven Team-only skills.

### Community (included)

| Skill | Description |
|-------|-------------|
| `hl7v2-parse` | Parse HL7v2 ADT and ORU messages into flat, analysis-ready tables (CSV/JSON). |
| `phi-column-scan` | Scan a schema, dbt model, or sample data to flag columns that likely contain PHI — runs entirely locally. |
| `pipeline-runbook` | Generate an on-call runbook from an Airflow DAG or dbt job manifest. |

### Team

| Skill | Description |
|-------|-------------|
| `834-file-check` | Validate EDI 834 enrollment files — structure, loops, dates, duplicates, add/term reconciliation. |
| `fhir-mapping` | Generate a FHIR R4 mapping specification from a source table schema. |
| `deid-pass` | Apply HIPAA Safe Harbor de-identification — redact/transform all 18 identifier types, refuse export when unsure. |
| `member-match` | Deterministic + fuzzy member matching across datasets with explainable scores. |
| `dbt-healthcare-conventions` | Audit a dbt project for healthcare naming, layering, tests, and docs conventions. |
| `roster-reconcile` | Month-over-month payer roster diff — drops, re-adds, ID changes, new enrollments. |
| `code-set-lookup` | Validate/explain ICD-10, CPT (format only — AMA-licensed), NDC, LOINC codes. |

## PHI Guard

The PHI guard scans files for HIPAA-sensitive patterns (SSN, MRN, DOB+name, phone, email, addresses) and blocks commits when matches are found.

### As a CLI command

```bash
hcskills guard file1.csv file2.json
hcskills guard --staged  # scan git staged files
```

### As a pre-commit hook

Copy the hook into your repo:

```bash
cp $(pip show hc-data-skills | grep Location | cut -d' ' -f2)/hcskills/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### False positive suppression

Add `# phi-safe` as an inline comment to suppress a match on a specific line.

## Memory

The `hcskills memory init` command creates a local `memory/` folder template:

```
memory/
├── decisions/         # Data engineering decision records
├── column-glossary/   # Source-to-canonical column mappings
└── gotchas/           # Known data quality issues and vendor quirks
```

Memory lives in **your repo** — it's never uploaded anywhere. The PHI guard automatically scans `memory/` to prevent accidental PHI commits.

## Architecture & Data Privacy

- **No hosted service**: The CLI copies skill files into your repo's `.cursor/skills/` or `.claude/skills/` directory. That's it.
- **No data transmission**: All scripts run locally. No API calls, no telemetry, no data upload.
- **No BAA needed**: Since we never touch your data, there's no covered entity relationship.
- **Memory is local**: Decision records, column glossaries, and gotchas live as files in your repo.

## Licensing

- **CLI (`hcskills`, `src/hcskills/`)**: MIT License — see [LICENSE](LICENSE).
- **Skill content** (`skills/` directory): Proprietary. All rights reserved. Redistribution requires a Team license.
- **Code set notes**: CPT codes are copyright AMA — the `code-set-lookup` skill validates format only and ships no CPT descriptions. ICD-10-CM, NDC, and LOINC are publicly available.

License-key gating is stubbed (`~/.hcskills/license` or `HCSKILLS_LICENSE_KEY`). All 10 skills are unlocked in this Team pack; a key server may be wired later.

## Updates

`hcskills update` pulls Team skills from this private repository:

`https://github.com/blacktj/hc-data-skills-pro`

## Development

```bash
# Clone this private Team pack
git clone https://github.com/blacktj/hc-data-skills-pro.git
cd hc-data-skills-pro
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
```

## Contributing

1. All fixtures must use **synthetic, obviously fake data**. No real PHI, ever.
2. Each skill must have a working script and at least one fixture test.
3. Mark the tier in SKILL.md frontmatter (`tier: free` or `tier: team`).
