---
name: member-match
description: Deterministic + fuzzy member matching across datasets with configurable blocking, nickname aliases, and explainable scores.
tier: team
---

# Member Match

## When to Use

- You need to link member records across two datasets (e.g., eligibility file from one payer vs. your internal roster).
- You want both deterministic (exact key) and probabilistic (fuzzy name + DOB) matching.
- You need explainable match scores showing which fields matched, how strongly, and whether a nickname alias was used.
- You have datasets of 10K+ rows and need blocking to keep runtime manageable.

## Steps

1. **Provide two CSV files**: a "left" (source) and "right" (target) dataset, each with at minimum `first_name`, `last_name`, and `date_of_birth`.

2. **Run the matching script**:
   ```bash
   # Default: uses dob_year blocking (best recall)
   python skills/member-match/scripts/match_members.py <left.csv> <right.csv>

   # Faster with compound blocking (trades some recall for speed)
   python skills/member-match/scripts/match_members.py <left.csv> <right.csv> \
       --blocking dob_year,soundex_last

   # Brute-force O(n*m) — only for small datasets
   python skills/member-match/scripts/match_members.py <left.csv> <right.csv> \
       --no-blocking
   ```

3. **Review the output**:
   - Each row shows the left record, best-matching right record, overall score, and per-field scores.
   - Deterministic matches (exact SSN or member ID) are marked `DETERMINISTIC`.
   - Fuzzy matches use weighted field similarity (name: 0.35, DOB: 0.30, other fields: 0.35).
   - Records below threshold are flagged as `NO_MATCH`.
   - When a nickname alias matched (e.g., "Bill" ↔ "William"), the `aliases_used` field explains it.

4. **Validate edge cases**: common issues include maiden-name mismatches, date format differences, and transposed digits.

## Blocking Strategies

Blocking reduces the number of candidate pairs compared (from O(n*m) to roughly O(n*b) where b is the average block size).

**Default: `dob_year`** — chosen for best recall. Two records can only match if they share the same DOB year. This is the safest default because DOB year is rarely miskeyed across systems, and it still provides significant speedup.

| Strategy | Key Function | Example Block | Speed | Recall |
|----------|-------------|---------------|-------|--------|
| `dob_year` (default) | First 4 chars of date_of_birth | `1985` | Good | **Best** |
| `zip_prefix` | First 3 chars of zip_code | `100` | Good | Good |
| `soundex_last` | American Soundex of last_name | `S530` (Smith/Smyth) | Good | Good |
| `first_initial_last` | First letter of last_name | `s` | Moderate | Good |

Combine strategies for finer blocks: `--blocking dob_year,soundex_last` creates compound keys like `1985|S530`.

### When to Use Compound Blocking

Use compound blocking (e.g., `dob_year,soundex_last`) when:
- Your datasets are very large (>50K rows) and you need faster runtime.
- You are confident that the blocking fields are accurate in both datasets (no DOB typos + no name transliterations).
- You can tolerate missing matches where *both* blocking fields differ.

Stick with the default `dob_year` when:
- You want the highest recall (fewest missed matches).
- Your datasets are <50K rows and runtime is acceptable.
- DOB data quality is good across both systems.

Use `--no-blocking` only for small datasets (<1K rows) or when you need to guarantee every pair is compared.

### Performance (synthetic benchmarks)

| Dataset Size | Blocking | Runtime | Notes |
|-------------|----------|---------|-------|
| 5K × 5K | `dob_year` (default) | ~0.1s | Best recall |
| 10K × 10K | `dob_year` (default) | ~1–10s | Best recall |
| 50K × 50K | `dob_year` (default) | ~4 min | Best recall, large blocks |
| 50K × 50K | `dob_year,soundex_last` | ~5.5s | Recommended for >10K rows |
| 500 × 500 | `--no-blocking` (brute force) | ~1.6s | Small datasets only |
| 500 × 500 | `dob_year,soundex_last` | ~0.003s | 520x faster |

**Guidance**: For datasets up to ~10K rows, the default `dob_year` is fast enough with best recall. For larger datasets, use `--blocking dob_year,soundex_last` — it's ~40x faster at 50K with minimal recall loss (records must share DOB year *and* Soundex of last name to be compared).

## Nickname / Alias Matching

The script includes a built-in alias table (~90 entries) covering common English nicknames:
- William ↔ Bill, Will, Willy, Liam
- Robert ↔ Bob, Rob, Bobby, Robbie
- Elizabeth ↔ Liz, Beth, Betsy, Betty, Eliza
- Katherine ↔ Kate, Kathy, Katie, Kat
- And many more (James/Jim, Michael/Mike, etc.)

When an alias match is found, the output includes an `aliases_used` field explaining the match, e.g.:
```json
"aliases_used": ["first_name: 'Bill' matched 'William' via alias"]
```

Alias matches score 0.95 (vs 1.0 for exact match) to reflect the slight uncertainty.

## Inputs

| Input | Description |
|-------|-------------|
| `left_csv` | Source dataset CSV |
| `right_csv` | Target dataset CSV |
| `--threshold` | Minimum score to consider a match (default: 0.75) |
| `--blocking` | Comma-separated blocking strategies (default: `dob_year`) |
| `--no-blocking` | Disable blocking; brute-force O(n*m) comparison |

## Output

JSON list of match results with per-field scores, alias explanations, and blocking keys.

## Caveats

- Blocking trades recall for speed: records that differ on all blocking fields will not be compared. The default (`dob_year`) minimizes this risk since DOB year is rarely miskeyed.
- The nickname alias table covers common English names; non-English names, transliterations, and organization-specific aliases should be added by the team.
- Soundex is designed for English names; consider NYSIIS or Metaphone for broader coverage.
- For very large datasets (>100K rows), consider adding a pre-filter on additional fields or using a dedicated record linkage library like `splink`.
