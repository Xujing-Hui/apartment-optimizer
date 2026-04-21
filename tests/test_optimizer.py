"""
test_optimizer.py
-----------------
End-to-end tests for optimizer.py

Tests cover:
  - All 5 apartments pass constraints (no filtering for our dataset)
  - Correct winner (#1 = Villas on the Boulevard)
  - Correct last place (#5 = The Harlowe)
  - Score ordering is strictly ascending
  - Chain trip winner matches expected Starbucks per apartment
  - Score values match expected results within tolerance
  - Walk fallback edges reduce costs below transit-only values
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from optimizer import run_optimizer, passes_constraints
from graph     import load_data


TOL = 0.5   # acceptable floating-point tolerance for score comparisons


def test_all_apartments_pass_constraints():
    """All 5 apartments must satisfy rent and walk constraints."""
    apartments, _, _, constraints, _ = load_data()
    failed = [a["name"] for a in apartments if not passes_constraints(a, constraints)]
    assert not failed, f"These apartments failed constraints: {failed}"
    print("PASS  test_all_apartments_pass_constraints  (5/5 pass)")


def test_result_count():
    """Optimizer must return exactly 5 results."""
    results = run_optimizer(verbose=False)
    assert len(results) == 5, f"Expected 5 results, got {len(results)}"
    print("PASS  test_result_count")


def test_winner_is_villas():
    """Villas on the Boulevard must rank #1."""
    results = run_optimizer(verbose=False)
    winner_id = results[0]["apt"]["id"]
    assert winner_id == "villas_on_the_blvd", (
        f"Expected winner=villas_on_the_blvd, got {winner_id}"
    )
    print(f"PASS  test_winner_is_villas  (score={results[0]['score']} min/week)")


def test_last_place_is_harlowe():
    """The Harlowe must rank last (#5) after the S5↔NEU fix."""
    results = run_optimizer(verbose=False)
    last_id = results[-1]["apt"]["id"]
    assert last_id == "the_harlowe", (
        f"Expected last=the_harlowe, got {last_id}"
    )
    print(f"PASS  test_last_place_is_harlowe  (score={results[-1]['score']} min/week)")


def test_scores_strictly_ascending():
    """Results must be sorted in non-decreasing order of score."""
    results = run_optimizer(verbose=False)
    scores  = [r["score"] for r in results]
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i+1], (
            f"Score order violated: {scores[i]} > {scores[i+1]} at index {i}"
        )
    print(f"PASS  test_scores_strictly_ascending  (scores={scores})")


def test_expected_scores():
    """
    Verify computed scores match expected values within tolerance.
    Expected (v2 algorithm + S5↔NEU walk-fallback fix by Jiaxin Liu):
      #1 Villas    220.7
      #2 Cannery   224.1
      #3 Murphy    236.9
      #4 Harlowe   292.5
      #5 Verdant   272.5
    """
    expected = {
        "villas_on_the_blvd": 220.7,
        "cannery_park"      : 224.1,
        "murphy_station"    : 236.9,
        "the_harlowe"       : 292.5,
        "the_verdant"       : 272.5,
    }
    results = run_optimizer(verbose=False)
    for r in results:
        apt_id = r["apt"]["id"]
        if apt_id in expected:
            diff = abs(r["score"] - expected[apt_id])
            assert diff <= TOL, (
                f"{apt_id}: expected {expected[apt_id]}, got {r['score']} "
                f"(diff={diff:.2f})"
            )
    print(f"PASS  test_expected_scores  (tolerance={TOL} min)")


def test_chain_trip_starbucks_winners():
    """
    Verify the algorithm selects the expected optimal Starbucks.
    After the S5↔NEU walk-fallback fix (4.7 min), S5 becomes cheapest
    for the S→NEU leg for most apartments.
    Expected:
      villas_on_the_blvd → S5  (S5→NEU now 4.7 min via walk-fallback)
      murphy_station     → S5
      the_verdant        → S4  (walk-fallback to S4=1.7min still wins overall)
      cannery_park       → S5
      the_harlowe        → S5
    """
    expected_sb = {
        "villas_on_the_blvd": "S5",
        "murphy_station"    : "S5",
        "the_verdant"       : "S4",
        "cannery_park"      : "S5",
        "the_harlowe"       : "S5",
    }
    results = run_optimizer(verbose=False)
    for r in results:
        apt_id = r["apt"]["id"]
        if apt_id in expected_sb:
            assert r["best_sb"] == expected_sb[apt_id], (
                f"{apt_id}: expected SB={expected_sb[apt_id]}, got {r['best_sb']}"
            )
    print("PASS  test_chain_trip_starbucks_winners")


def test_villas_gym_uses_walk_fallback():
    """
    Villas ↔ G2 walk-fallback (4.6 min) must be cheaper than any
    transit route to G2 (which is ≥ 13 min via bus stops).
    """
    results = run_optimizer(verbose=False)
    villas = next(r for r in results if r["apt"]["id"] == "villas_on_the_blvd")
    assert villas["gym"] < 10.0, (
        f"Villas gym cost should use walk-fallback (<10 min), got {villas['gym']}"
    )
    print(f"PASS  test_villas_gym_uses_walk_fallback  (gym={villas['gym']} min)")


# ── Run all tests ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        test_all_apartments_pass_constraints,
        test_result_count,
        test_winner_is_villas,
        test_last_place_is_harlowe,
        test_scores_strictly_ascending,
        test_expected_scores,
        test_chain_trip_starbucks_winners,
        test_villas_gym_uses_walk_fallback,
    ]
    print(f"Running {len(tests)} optimizer tests...\n")
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
