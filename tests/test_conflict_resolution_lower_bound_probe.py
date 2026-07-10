"""
Regression tests for conflict_resolution_lower_bound_probe.py (R12).
Locks in the finite pigeonhole gap, pair_resolver's injectivity on
V x V, and the concrete collision counts for codomain-confined lossy
resolvers -- deliberately NOT testing average/sum's image sizes, since
their outputs are not confined to V (see the probe's own module
docstring for why that comparison would be misleading).
"""

from fractions import Fraction as F

from conflict_resolution_lower_bound_probe import (
    FINITE_DOMAINS, pair_resolver, left_wins, right_wins, erase,
    check_pair_resolver_injective_on_domain, image_size,
)


def test_pigeonhole_gap_positive_for_every_n_greater_than_one():
    for n, domain in FINITE_DOMAINS.items():
        gap = n * n - n
        if n > 1:
            assert gap > 0
        else:
            assert gap == 0


def test_pair_resolver_injective_on_every_tested_domain():
    for n, domain in FINITE_DOMAINS.items():
        assert check_pair_resolver_injective_on_domain(domain) is True


def test_pair_resolver_image_size_equals_n_squared():
    for n, domain in FINITE_DOMAINS.items():
        img = image_size(lambda x, y: pair_resolver(x, y), domain)
        assert img == n * n


def test_codomain_confined_resolvers_image_sizes():
    """left_wins/right_wins achieve image size exactly n (the best a
    codomain-confined lossy resolver can do); erase achieves exactly 1
    (the worst) -- both strictly less than n^2 once n > 1, confirming
    neither can be injective on V x V."""
    for n, domain in FINITE_DOMAINS.items():
        assert image_size(left_wins, domain) == n
        assert image_size(right_wins, domain) == n
        assert image_size(erase, domain) == 1
        if n > 1:
            assert image_size(left_wins, domain) < n * n
            assert image_size(erase, domain) < n * n


def test_pair_resolver_recovers_both_declarations_exactly():
    """Direct check of the NonLossy property pair_resolver satisfies,
    mirroring rocq/ConflictResolutionLowerBound.v's
    structured_pair_is_nonlossy."""
    x, y = F(5), F(-5)
    encoded = pair_resolver(x, y)
    assert encoded[0] == x
    assert encoded[1] == y
