---
name: roster-reconcile
description: Month-over-month payer roster diff — identify drops, re-adds, ID changes, and new enrollments with a reconciliation summary.
tier: team
---

# Roster Reconcile

## When to Use

- You receive monthly roster files from a payer and need to reconcile them against last month's file.
- You want to identify: new members, dropped members, re-added members (previously dropped and returned), and member ID changes.
- You need a clean summary for operations or account management teams.

## Steps

1. **Provide two roster CSVs**: prior month and current month, with at least `member_id`, `first_name`, `last_name`, `date_of_birth`.

2. **Run the reconciliation**:
   ```bash
   python skills/roster-reconcile/scripts/reconcile_roster.py <prior.csv> <current.csv>
   ```

3. **Review the output**:
   - **NEW**: Members in current but not in prior (by member_id).
   - **DROPPED**: Members in prior but not in current.
   - **CONTINUED**: Members in both months.
   - **RE-ADDED**: Members who were in a historical drop list but reappeared (requires `--history` flag and prior drop records).
   - **ID_CHANGE**: Members matched by name+DOB but with different member_ids across months.

4. **Share the summary** with the operations team and investigate unexpected drops.

## Inputs

| Input | Description |
|-------|-------------|
| `prior_csv` | Prior month's roster CSV |
| `current_csv` | Current month's roster CSV |

## Output

JSON report with categorized member lists and a reconciliation summary.

## Caveats

- ID change detection is fuzzy (name+DOB match); false positives are possible with common names.
- Does not track multi-month history in v0.1 — compares exactly two snapshots.
- Assumes `member_id` is the primary key in each file.
