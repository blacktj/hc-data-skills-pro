"""Tests for the member match skill."""

from pathlib import Path

from match_members import (
    DEFAULT_BLOCKING,
    _canonical_name,
    _name_similarity,
    _soundex,
    build_blocks,
    load_csv,
    match_datasets,
    score_pair,
)

FIXTURES = (
    Path(__file__).resolve().parent.parent
    / "skills" / "member-match" / "fixtures"
)


class TestMemberMatch:
    def test_load_csv(self):
        rows = load_csv(str(FIXTURES / "roster_left.csv"))
        assert len(rows) == 4
        assert rows[0]["first_name"] == "Synthia"

    def test_exact_match_high_score(self):
        left = {
            "first_name": "Synthia", "last_name": "Testworth",
            "date_of_birth": "1985-03-15", "ssn": "", "member_id": "",
        }
        right = {
            "first_name": "Synthia", "last_name": "Testworth",
            "date_of_birth": "1985-03-15", "ssn": "", "member_id": "",
        }
        score = score_pair(left, right)
        assert score["overall_score"] >= 0.6

    def test_fuzzy_match_close_name(self):
        left = {
            "first_name": "Tester", "last_name": "McFakerson",
            "date_of_birth": "1990-07-22", "ssn": "", "member_id": "",
        }
        right = {
            "first_name": "Testr", "last_name": "McFakerson",
            "date_of_birth": "1990-07-22", "ssn": "", "member_id": "",
        }
        score = score_pair(left, right)
        assert score["overall_score"] >= 0.5

    def test_match_datasets(self):
        left = load_csv(str(FIXTURES / "roster_left.csv"))
        right = load_csv(str(FIXTURES / "roster_right.csv"))
        results = match_datasets(left, right, threshold=0.5)
        assert len(results) == 4
        matched = [
            r for r in results if r["match_type"] != "NO_MATCH"
        ]
        assert len(matched) >= 3

    def test_no_match_different_people(self):
        left = [{
            "first_name": "Demo", "last_name": "Person",
            "date_of_birth": "1975-05-30", "ssn": "", "member_id": "",
        }]
        right = [{
            "first_name": "Totally", "last_name": "Different",
            "date_of_birth": "2000-01-01", "ssn": "", "member_id": "",
        }]
        results = match_datasets(left, right, threshold=0.75)
        assert results[0]["match_type"] == "NO_MATCH"


class TestNicknameAliases:
    def test_canonical_resolves_nickname(self):
        assert _canonical_name("Bill") == "william"
        assert _canonical_name("bob") == "robert"
        assert _canonical_name("liz") == "elizabeth"

    def test_canonical_passthrough(self):
        assert _canonical_name("Synthia") == "synthia"

    def test_name_similarity_alias_match(self):
        sim, alias_used = _name_similarity("Bill", "William")
        assert sim >= 0.9
        assert alias_used is True

    def test_name_similarity_exact(self):
        sim, alias_used = _name_similarity("Alice", "Alice")
        assert sim == 1.0
        assert alias_used is False

    def test_name_similarity_unrelated_names(self):
        sim, alias_used = _name_similarity("Alice", "Zephyr")
        assert sim < 0.5

    def test_alias_in_score_pair(self):
        left = {
            "first_name": "Bill", "last_name": "Testworth",
            "date_of_birth": "1985-03-15", "ssn": "", "member_id": "",
        }
        right = {
            "first_name": "William", "last_name": "Testworth",
            "date_of_birth": "1985-03-15", "ssn": "", "member_id": "",
        }
        result = score_pair(left, right)
        assert "aliases_used" in result
        assert any("first_name" in a for a in result["aliases_used"])
        assert result["overall_score"] >= 0.6

    def test_multiple_aliases_same_canonical(self):
        sim1, _ = _name_similarity("Bob", "Robert")
        sim2, _ = _name_similarity("Bobby", "Robert")
        assert sim1 >= 0.9
        assert sim2 >= 0.9

    def test_female_aliases(self):
        sim, alias = _name_similarity("Liz", "Elizabeth")
        assert sim >= 0.9
        assert alias is True
        sim2, alias2 = _name_similarity("Kate", "Katherine")
        assert sim2 >= 0.9
        assert alias2 is True


class TestSoundex:
    def test_basic_soundex(self):
        assert _soundex("Robert") == "R163"
        assert _soundex("Rupert") == "R163"

    def test_soundex_smith(self):
        assert _soundex("Smith") == "S530"
        assert _soundex("Smyth") == "S530"

    def test_soundex_empty(self):
        assert _soundex("") == "0000"


class TestBlocking:
    def test_build_blocks_dob_year(self):
        rows = [
            {"date_of_birth": "1985-03-15", "last_name": "A"},
            {"date_of_birth": "1985-07-22", "last_name": "B"},
            {"date_of_birth": "1990-01-01", "last_name": "C"},
        ]
        blocks = build_blocks(rows, ["dob_year"])
        assert len(blocks["1985"]) == 2
        assert len(blocks["1990"]) == 1

    def test_build_blocks_compound(self):
        rows = [
            {
                "date_of_birth": "1985-03-15",
                "last_name": "Smith",
            },
            {
                "date_of_birth": "1985-07-22",
                "last_name": "Smyth",
            },
        ]
        blocks = build_blocks(rows, ["dob_year", "soundex_last"])
        key = "1985|S530"
        assert key in blocks
        assert len(blocks[key]) == 2

    def test_match_with_blocking(self):
        left = load_csv(str(FIXTURES / "roster_left.csv"))
        right = load_csv(str(FIXTURES / "roster_right.csv"))
        results = match_datasets(
            left, right, threshold=0.5,
            blocking=["dob_year"],
        )
        assert len(results) == 4
        matched = [
            r for r in results if r["match_type"] != "NO_MATCH"
        ]
        assert len(matched) >= 3

    def test_blocking_adds_block_key(self):
        left = load_csv(str(FIXTURES / "roster_left.csv"))
        right = load_csv(str(FIXTURES / "roster_right.csv"))
        results = match_datasets(
            left, right, threshold=0.5,
            blocking=["dob_year"],
        )
        for r in results:
            assert "block_key" in r

    def test_default_blocking_is_dob_year(self):
        assert DEFAULT_BLOCKING == ["dob_year"]

    def test_default_blocking_used_when_omitted(self):
        left = load_csv(str(FIXTURES / "roster_left.csv"))
        right = load_csv(str(FIXTURES / "roster_right.csv"))
        results = match_datasets(left, right, threshold=0.5)
        for r in results:
            assert "block_key" in r

    def test_brute_force_with_none_blocking(self):
        left = load_csv(str(FIXTURES / "roster_left.csv"))
        right = load_csv(str(FIXTURES / "roster_right.csv"))
        results = match_datasets(
            left, right, threshold=0.5, blocking=None,
        )
        assert len(results) == 4
        for r in results:
            assert "block_key" not in r
