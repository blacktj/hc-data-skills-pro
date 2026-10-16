"""Benchmark test for member-match at scale (~50K rows).

Generates synthetic datasets and measures runtime with and without blocking.
"""

import random
import time

import pytest
from match_members import match_datasets

SYNTH_FIRST_NAMES = [
    "Synthia", "Tester", "Fakey", "Demo", "Notreal", "Bogus",
    "Pretend", "Mockup", "Simula", "Artifex", "Phantom", "Pseudo",
    "Nominal", "Placeholder", "Specimen", "Exemplar", "Paradigm",
    "Archetype", "Prototype", "Blueprint", "Draft", "Sketch",
    "Outline", "Template", "Model", "Sample", "Instance",
    "Figment", "Fabricat", "Forgery", "Imitation", "Replica",
    "Bill", "Bob", "Liz", "Kate", "Jim", "Mike", "Dave",
    "Joe", "Tom", "Dan", "Rick", "Ed", "Chris", "Tony",
    "Nick", "Matt", "Pat", "Alex", "Andy", "Ben", "Charlie",
    "Frank", "Fred", "Greg", "Jack", "Jerry", "Jeff", "Larry",
    "Pete", "Phil", "Ray", "Ron", "Sam", "Walt",
    "Jen", "Sue", "Meg", "Pam", "Deb", "Barb", "Cindy",
    "Jess", "Judy", "Mandy", "Sandy", "Vicky",
]

SYNTH_LAST_NAMES = [
    "Testworth", "McFakerson", "Notreal", "Demoson", "Fakeley",
    "Boguston", "Pretender", "Mocksworth", "Simulton", "Pseudovic",
    "Phantomson", "Nominalez", "Placeholdr", "Specimento", "Exemplaris",
    "Paradigmov", "Archetypov", "Prototypov", "Blueprintov", "Draftson",
    "Sketchley", "Outlinova", "Templateson", "Modelwitz", "Sampleton",
    "Instanceov", "Figmently", "Fabricato", "Forgeryson", "Imitatov",
    "Smithson", "Johnsonov", "Williamson", "Brownstein", "Jonesberry",
    "Garcialez", "Millerstein", "Davisford", "Rodriguezov", "Martinezov",
    "Hernandez", "Lopezstein", "Gonzalezov", "Wilsonberry", "Anderson",
    "Thomasberg", "Taylorson", "Moorefield", "Jacksonhall", "Martinburg",
]

PLAN_TYPES = ["HMO", "PPO", "EPO", "POS", "HDHP"]


def _random_dob(rng: random.Random) -> str:
    year = rng.randint(1940, 2005)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year}-{month:02d}-{day:02d}"


def _random_zip(rng: random.Random) -> str:
    return f"{rng.randint(10000, 99999)}"


def _generate_dataset(
    n: int, seed: int = 42
) -> list[dict[str, str]]:
    """Generate a synthetic member roster with n rows."""
    rng = random.Random(seed)
    rows = []
    for i in range(n):
        rows.append({
            "member_id": f"SYNTH-{i:06d}",
            "first_name": rng.choice(SYNTH_FIRST_NAMES),
            "last_name": rng.choice(SYNTH_LAST_NAMES),
            "date_of_birth": _random_dob(rng),
            "ssn": "",
            "zip_code": _random_zip(rng),
        })
    return rows


def _generate_matched_pair(
    n: int, match_rate: float = 0.7, seed: int = 42
) -> tuple[list[dict], list[dict]]:
    """Generate left/right datasets where match_rate fraction overlap.

    The right dataset has the same members as left (with slight name
    variations) for the overlap portion, plus unique extras.
    """
    rng = random.Random(seed)
    left = _generate_dataset(n, seed=seed)

    n_match = int(n * match_rate)
    right = []

    for i in range(n_match):
        src = left[i].copy()
        src["member_id"] = f"EXT-{i:06d}"
        if rng.random() < 0.1:
            name = src["first_name"]
            src["first_name"] = name[:-1] if len(name) > 2 else name
        right.append(src)

    for i in range(n - n_match):
        right.append({
            "member_id": f"EXT-X{i:06d}",
            "first_name": rng.choice(SYNTH_FIRST_NAMES),
            "last_name": rng.choice(SYNTH_LAST_NAMES),
            "date_of_birth": _random_dob(rng),
            "ssn": "",
            "zip_code": _random_zip(rng),
        })

    rng.shuffle(right)
    return left, right


class TestBenchmark:
    """Benchmark tests — measure runtime at scale.

    These tests validate that blocking dramatically reduces runtime
    compared to brute-force matching. They also verify match quality
    is maintained.
    """

    @pytest.fixture
    def large_dataset(self):
        """Generate a 50K-row matched pair."""
        return _generate_matched_pair(50_000, match_rate=0.6, seed=99)

    @pytest.fixture
    def medium_dataset(self):
        """Generate a 5K-row matched pair for faster CI."""
        return _generate_matched_pair(5_000, match_rate=0.6, seed=77)

    def test_blocking_scales_5k(self, medium_dataset):
        """Verify blocking on 5K rows completes in <5s."""
        left, right = medium_dataset

        t0 = time.perf_counter()
        results = match_datasets(
            left, right, threshold=0.5,
            blocking=["dob_year", "soundex_last"],
        )
        elapsed = time.perf_counter() - t0

        assert len(results) == len(left)
        matched = sum(
            1 for r in results if r["match_type"] != "NO_MATCH"
        )
        assert matched > 0
        assert elapsed < 5.0, f"5K blocking took {elapsed:.2f}s"
        print(
            f"\n  5K blocking: {elapsed:.3f}s, "
            f"{matched}/{len(left)} matched"
        )

    def test_default_blocking_scales_10k(self):
        """Verify default blocking (dob_year) on 10K rows.

        dob_year-only blocking has larger blocks than compound strategies,
        so we test at 10K to keep CI fast. At 50K, dob_year-only takes
        ~4 min (vs ~5.5s for dob_year,soundex_last) — the trade-off
        for best recall.
        """
        left, right = _generate_matched_pair(
            10_000, match_rate=0.6, seed=55
        )

        t0 = time.perf_counter()
        results = match_datasets(
            left, right, threshold=0.5,
        )
        elapsed = time.perf_counter() - t0

        assert len(results) == len(left)
        matched = sum(
            1 for r in results if r["match_type"] != "NO_MATCH"
        )
        assert matched > 0
        assert elapsed < 30.0, (
            f"10K dob_year took {elapsed:.2f}s"
        )
        print(
            f"\n  10K default (dob_year): {elapsed:.3f}s, "
            f"{matched}/{len(left)} matched"
        )

    def test_blocking_scales_50k_compound(self, large_dataset):
        """Verify compound blocking on 50K rows completes faster."""
        left, right = large_dataset

        t0 = time.perf_counter()
        results = match_datasets(
            left, right, threshold=0.5,
            blocking=["dob_year", "soundex_last"],
        )
        elapsed = time.perf_counter() - t0

        assert len(results) == len(left)
        matched = sum(
            1 for r in results if r["match_type"] != "NO_MATCH"
        )
        assert matched > 0
        assert elapsed < 60.0, (
            f"50K compound took {elapsed:.2f}s"
        )
        print(
            f"\n  50K compound (dob_year,soundex_last): "
            f"{elapsed:.3f}s, {matched}/{len(left)} matched"
        )

    def test_blocking_vs_brute_force_speedup(self, medium_dataset):
        """Show that blocking is faster than brute force on 5K rows."""
        left, right = medium_dataset

        t0 = time.perf_counter()
        match_datasets(
            left[:500], right[:500], threshold=0.5,
            blocking=None,
        )
        brute_elapsed = time.perf_counter() - t0

        t0 = time.perf_counter()
        match_datasets(
            left[:500], right[:500], threshold=0.5,
            blocking=["dob_year", "soundex_last"],
        )
        block_elapsed = time.perf_counter() - t0

        assert block_elapsed < brute_elapsed, (
            f"Blocking ({block_elapsed:.3f}s) should be faster "
            f"than brute force ({brute_elapsed:.3f}s)"
        )
        print(
            f"\n  500-row comparison: brute={brute_elapsed:.3f}s, "
            f"blocking={block_elapsed:.3f}s, "
            f"speedup={brute_elapsed / max(block_elapsed, 0.001):.1f}x"
        )

    def test_match_quality_with_blocking(self):
        """Verify blocking finds true matches that share a block.

        Uses a small controlled dataset where we know the ground truth
        (same DOB, same names) so blocking by dob_year preserves recall.
        """
        left = [
            {
                "member_id": f"L{i}", "first_name": f"Synth{i}",
                "last_name": f"Test{i}", "date_of_birth": f"1985-0{(i%9)+1}-15",
                "ssn": "", "zip_code": "000XX",
            }
            for i in range(100)
        ]
        right = [
            {
                "member_id": f"R{i}", "first_name": f"Synth{i}",
                "last_name": f"Test{i}", "date_of_birth": f"1985-0{(i%9)+1}-15",
                "ssn": "", "zip_code": "000XX",
            }
            for i in range(100)
        ]

        results_brute = match_datasets(
            left, right, threshold=0.5,
            blocking=None,
        )
        results_block = match_datasets(
            left, right, threshold=0.5,
            blocking=["dob_year"],
        )

        brute_matched = sum(
            1 for r in results_brute
            if r["match_type"] != "NO_MATCH"
        )
        block_matched = sum(
            1 for r in results_block
            if r["match_type"] != "NO_MATCH"
        )

        assert brute_matched > 0
        assert block_matched > 0
        recall = block_matched / brute_matched
        assert recall >= 0.8, (
            f"Blocking recall {recall:.2%} too low "
            f"(brute={brute_matched}, blocked={block_matched})"
        )
        print(
            f"\n  100-row quality: brute={brute_matched}, "
            f"blocking={block_matched}, "
            f"recall={recall:.1%}"
        )

    def test_dob_year_plus_first_initial_blocking(self, medium_dataset):
        """Test alternative blocking strategy."""
        left, right = medium_dataset

        t0 = time.perf_counter()
        results = match_datasets(
            left, right, threshold=0.5,
            blocking=["dob_year", "first_initial_last"],
        )
        elapsed = time.perf_counter() - t0

        assert len(results) == len(left)
        matched = sum(
            1 for r in results if r["match_type"] != "NO_MATCH"
        )
        print(
            f"\n  5K dob_year+first_initial: {elapsed:.3f}s, "
            f"{matched}/{len(left)} matched"
        )
