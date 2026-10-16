"""Tests for the roster reconcile skill."""

from pathlib import Path

from reconcile_roster import load_roster, reconcile

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "roster-reconcile" / "fixtures"
)


class TestRosterReconcile:
    def test_load_roster(self):
        rows = load_roster(str(FIXTURES / "roster_prior.csv"))
        assert len(rows) == 4

    def test_reconcile_detects_new(self):
        prior = load_roster(str(FIXTURES / "roster_prior.csv"))
        current = load_roster(str(FIXTURES / "roster_current.csv"))
        result = reconcile(prior, current)
        new_ids = {m["member_id"] for m in result["new"]}
        assert "SYNTH-005" in new_ids

    def test_reconcile_detects_dropped(self):
        prior = load_roster(str(FIXTURES / "roster_prior.csv"))
        current = load_roster(str(FIXTURES / "roster_current.csv"))
        result = reconcile(prior, current)
        dropped_ids = {m["member_id"] for m in result["dropped"]}
        assert "SYNTH-004" in dropped_ids

    def test_reconcile_detects_id_change(self):
        prior = load_roster(str(FIXTURES / "roster_prior.csv"))
        current = load_roster(str(FIXTURES / "roster_current.csv"))
        result = reconcile(prior, current)
        assert len(result["id_changes"]) >= 1
        changed = result["id_changes"][0]
        assert changed["old_member_id"] == "SYNTH-004"
        assert changed["new_member_id"] == "SYNTH-006"

    def test_reconcile_continued(self):
        prior = load_roster(str(FIXTURES / "roster_prior.csv"))
        current = load_roster(str(FIXTURES / "roster_current.csv"))
        result = reconcile(prior, current)
        assert result["continued_count"] == 3

    def test_reconcile_summary(self):
        prior = load_roster(str(FIXTURES / "roster_prior.csv"))
        current = load_roster(str(FIXTURES / "roster_current.csv"))
        result = reconcile(prior, current)
        assert "summary" in result
