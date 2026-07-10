"""
Regression tests for conflict_resolution_trilemma_probe.py. Locks in
docs/design/CONFLICT_RESOLUTION_TRILEMMA.md §4's classification table
and the two claims that table depends on: idempotence is not
independent of agreement (they always coincide), and no named resolver
has both fidelities. Also locks in §8's structured (non-lossy)
resolver finding.
"""

from fractions import Fraction as F

from conflict_resolution_trilemma_probe import (
    NAMED_RESOLVERS, classify, check_no_resolver_has_both_fidelities,
    left_wins, right_wins, average, total_sum, erase,
    pair_resolver, check_pair_resolver_preserves_both_claims, DISTINCT_PAIRS,
)


def test_left_wins_classification():
    r = classify(left_wins)
    assert r == {
        "agreement": True, "idempotent": True,
        "left_fidelity": True, "right_fidelity": False, "symmetric": False,
    }


def test_right_wins_classification():
    r = classify(right_wins)
    assert r == {
        "agreement": True, "idempotent": True,
        "left_fidelity": False, "right_fidelity": True, "symmetric": False,
    }


def test_average_classification():
    r = classify(average)
    assert r == {
        "agreement": True, "idempotent": True,
        "left_fidelity": False, "right_fidelity": False, "symmetric": True,
    }


def test_sum_classification_fails_agreement_and_idempotence():
    """sum is the sharper sacrifice the design doc calls out: it fails
    agreement/idempotence too, not only the two fidelities."""
    r = classify(total_sum)
    assert r == {
        "agreement": False, "idempotent": False,
        "left_fidelity": False, "right_fidelity": False, "symmetric": True,
    }
    assert total_sum(F(1), F(1)) == F(2)


def test_erase_classification_fails_everything_except_symmetry():
    r = classify(erase)
    assert r == {
        "agreement": False, "idempotent": False,
        "left_fidelity": False, "right_fidelity": False, "symmetric": True,
    }


def test_idempotence_never_independent_of_agreement():
    """The design doc's own observation, checked computationally for
    every named resolver, not just argued: agreement and idempotence
    must always coincide, since idempotence is literally agreement
    restricted to the diagonal (x, x)."""
    for name, resolve in NAMED_RESOLVERS.items():
        r = classify(resolve)
        assert r["agreement"] == r["idempotent"], f"{name} broke the agreement/idempotence link"


def test_no_named_resolver_has_both_fidelities():
    assert check_no_resolver_has_both_fidelities() is None


def test_pair_resolver_preserves_both_claims_on_every_pair():
    """The structured (non-lossy) resolver recovers both original
    values exactly, including on disagreeing pairs -- unlike every
    lossy resolver in NAMED_RESOLVERS, none of which can."""
    assert check_pair_resolver_preserves_both_claims() is True
    for (x, y) in DISTINCT_PAIRS:
        assert pair_resolver(x, y) == (x, y)


def test_pair_resolver_codomain_is_not_the_lossy_shape():
    """Sanity check that pair_resolver's output is a pair, not a Q --
    it is deliberately outside the V x V -> V shape the impossibility
    theorem is about."""
    result = pair_resolver(F(5), F(-5))
    assert isinstance(result, tuple)
    assert len(result) == 2
