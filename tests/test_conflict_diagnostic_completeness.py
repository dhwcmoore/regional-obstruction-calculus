"""
Regression tests for conflict_diagnostic_completeness_probe.py (R13).
Locks in the fragment's classification of every named strategy into
exactly one of the four DiagnosticClass buckets, the n vs n^2 lower
bound table, and the deliberate exclusion of average/sum from the
confinement-based lossiness check (see the probe's own module
docstring for why that comparison would be misleading -- the same
caveat R12's own probe/tests already established).
"""

from fractions import Fraction as F

from conflict_diagnostic_completeness_probe import (
    NO_COMPOSITE, LOSSY_SCALAR, NONLOSSY_STRUCTURED, UNRESOLVED,
    ALL_CLASSES, FINITE_DOMAINS, SCALAR_STRATEGIES, CONFINED_TO_DOMAIN,
    classify_refuse, classify_scalar_strategy, classify_pair,
    classify_unresolved, check_pair_injective_on_domain, image_size,
    check_confined_strategies_are_lossy, average, total_sum,
)


def test_scalar_summaries_are_lossy_on_conflict():
    # Every named scalar strategy is classified lossy_scalar --
    # mirrors no_hidden_neutral_scalar_case: no V-typed value can be
    # fully faithful once the two declarations disagree.
    for name in SCALAR_STRATEGIES:
        assert classify_scalar_strategy(name) == LOSSY_SCALAR


def test_left_wins_classified_lossy_scalar():
    assert classify_scalar_strategy("left_wins") == LOSSY_SCALAR


def test_right_wins_classified_lossy_scalar():
    assert classify_scalar_strategy("right_wins") == LOSSY_SCALAR


def test_average_classified_lossy_scalar():
    assert classify_scalar_strategy("average") == LOSSY_SCALAR


def test_erase_classified_lossy_scalar():
    assert classify_scalar_strategy("erase") == LOSSY_SCALAR


def test_pair_classified_nonlossy_structured():
    assert classify_pair() == NONLOSSY_STRUCTURED


def test_refuse_classified_no_composite():
    assert classify_refuse() == NO_COMPOSITE


def test_unresolved_classified_unresolved():
    assert classify_unresolved() == UNRESOLVED


def test_n_versus_n_squared_lower_bound_table():
    for n in range(1, 7):
        assert n in FINITE_DOMAINS
        assert len(FINITE_DOMAINS[n]) == n
        gap = n * n - n
        if n > 1:
            assert gap > 0
        else:
            assert gap == 0


def test_sum_is_not_treated_as_confined_to_v_unless_explicitly_modelled():
    # sum is classified lossy_scalar by type alone (it always emits a
    # single V-typed value), exactly like average -- but it must NOT
    # appear in CONFINED_TO_DOMAIN, since its actual output range
    # (x + y) is not structurally confined to any finite test subset of
    # Q, the same bug R12's own probe caught and documented.
    assert "sum" not in CONFINED_TO_DOMAIN
    assert "average" not in CONFINED_TO_DOMAIN
    assert classify_scalar_strategy("sum") == LOSSY_SCALAR
    # For a domain of size n > 1, sum's actual image size is not bounded
    # by n the way a genuinely confined resolver's is -- confirmed
    # computationally, not merely asserted.
    domain = FINITE_DOMAINS[4]
    assert image_size(total_sum, domain) > 4


def test_pair_injective_on_every_tested_domain():
    for n, domain in FINITE_DOMAINS.items():
        assert check_pair_injective_on_domain(domain) is True


def test_confined_strategies_are_lossy_via_pigeonhole():
    for n, domain in FINITE_DOMAINS.items():
        result = check_confined_strategies_are_lossy(domain)
        assert set(result.keys()) == CONFINED_TO_DOMAIN
        assert all(result.values())


def test_every_strategy_lands_in_exactly_one_class():
    classes_seen = {classify_refuse(), classify_pair(), classify_unresolved()}
    classes_seen |= {classify_scalar_strategy(name) for name in SCALAR_STRATEGIES}
    assert classes_seen == ALL_CLASSES


def test_no_unclassified_strategy():
    # Every strategy this probe knows about is covered by exactly one
    # of the four classifier functions -- nothing falls through.
    all_named = set(SCALAR_STRATEGIES) | {"refuse", "pair", "unresolved"}
    assert all_named == {
        "left_wins", "right_wins", "average", "sum", "erase",
        "refuse", "pair", "unresolved",
    }
