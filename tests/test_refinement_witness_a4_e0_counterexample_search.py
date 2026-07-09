"""
Regression tests for refinement_witness_a4_e0_counterexample_search.py.
Locks in the current search results, not a general theorem -- see
docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md: A4/E0 composability
is probed, not proved.
"""

from refinement_witness_a4_e0_counterexample_search import (
    search, verify_n0_theorem_consistency,
)


def test_search_produces_a_nontrivial_number_of_cases():
    results = search()
    assert len(results) >= 20


def test_search_covers_all_four_base_witnesses():
    results = search()
    assert {r["step1"] for r in results} == {
        "subdivide_U1", "subdivide_U2", "subdivide_all", "insert_bridge",
    }


def test_n0_composes_theorem_is_consistent_with_the_search():
    """Every composite N0 failure in the search must trace to an
    individual step's own N0 failing -- cross-checks
    rocq/RefinementWitnessComposition.v's N0_composes against real,
    independently-generated data, not just the two hand-built examples
    the theorem was originally checked against."""
    results = search()
    assert verify_n0_theorem_consistency(results) is True


def test_no_a4_or_e0_counterexample_found_yet():
    """Current state of the search: zero A4 or E0 composite failures
    across all generated cases. This is evidence, not a proof -- if this
    test ever fails, that is a genuine counterexample and should be
    written up, not silently accepted."""
    results = search()
    assert all(r["composite_A4"] for r in results)
    assert all(r["composite_E0"] for r in results)


def test_n0_composite_failures_all_trace_to_insert_bridge_as_step1():
    """The specific, currently-true fact backing the cross-check above:
    every N0 composite failure found so far has insert_bridge as step 1
    (the one base witness whose own N0 already fails)."""
    results = search()
    n0_failures = [r for r in results if not r["composite_N0"]]
    assert len(n0_failures) > 0
    assert all(r["step1"] == "insert_bridge" for r in n0_failures)
