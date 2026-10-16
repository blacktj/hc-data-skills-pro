# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Packaged as the private **Team tier** (`blacktj/hc-data-skills-pro`) with all 10 skills.
- Skill content is proprietary (all rights reserved). The `hcskills` CLI remains MIT.
- `hcskills update` pulls Team skills from `https://github.com/blacktj/hc-data-skills-pro`.

## [0.1.1] - 2026-10-14

### Changed

- **member-match**: Default blocking is now `dob_year` (best recall). Previously there
  was no default blocking (brute-force O(n*m)). Compound strategies like
  `dob_year,soundex_last` are available via `--blocking` for faster runtime when recall
  trade-offs are acceptable. Use `--no-blocking` to opt into brute force for small datasets.
- **member-match**: Added configurable blocking strategies (`dob_year`, `zip_prefix`,
  `soundex_last`, `first_initial_last`) to scale past 10K rows. Benchmarked at 50K × 50K:
  ~23s with default `dob_year`, ~5.5s with compound `dob_year,soundex_last`.
- **member-match**: Added nickname/alias table (~90 entries: Bill/William, Bob/Robert,
  Liz/Elizabeth, Kate/Katherine, etc.) with explainable output noting when an alias matched.
- **member-match**: Added American Soundex implementation for phonetic blocking.
- **member-match**: Updated SKILL.md with blocking strategies, recall vs speed guidance,
  performance benchmarks, alias table documentation, and revised caveats.

## [0.1.0] - 2026-10-14

### Added

- Initial release of hc-data-skills with 10 healthcare data engineering skills.
- `hcskills` CLI with `install`, `update`, `list`, `memory init`, and `guard` commands.
- PHI guard: pre-commit hook and `hcskills guard` for scanning staged files.
- Free-tier skills: `hl7v2-parse`, `phi-column-scan`, `pipeline-runbook`.
- Team-tier skills: `834-file-check`, `fhir-mapping`, `deid-pass`, `member-match`,
  `dbt-healthcare-conventions`, `roster-reconcile`, `code-set-lookup`.
- Synthetic fixtures and tests for every skill.
- GitHub Actions CI for lint and tests.
