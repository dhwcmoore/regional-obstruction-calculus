#!/usr/bin/env python3
"""
conflict_resolution_lower_bound_probe.py

R12. Checks rocq/ConflictResolutionLowerBound.v's claims computationally
over a finite test domain, before/alongside trusting the Rocq proof:
a non-lossy encoding of two declarations must be injective on V x V, and
for finite V with |V| = n, this forces the encoding's codomain to have
at least n^2 elements -- strictly more than the n elements a same-type
("lossy") codomain V could ever offer once n > 1.

A note on scope, checked carefully before writing anything down: this
probe does NOT claim every lossy resolver's image is bounded by n. That
would be FALSE for a resolver like `sum` (conflict_resolution_trilemma_
probe.py), whose codomain is typed as Q but whose actual output values
(x + y) can range over more than n distinct rationals even for a small
finite V, since sums of elements of V need not stay inside V. The
cardinality argument below applies precisely to resolvers whose outputs
are STRUCTURALLY CONFINED to V itself (the codomain is exactly V, not
merely "some Q value") -- `left_wins`, `right_wins`, and `erase` all
have this property by construction (their output is always literally
one of the two inputs, or a fixed sentinel already in V); `average` and
`sum` do not, and are not used for the collision-counting demonstration
below for exactly this reason.

USAGE:
    python conflict_resolution_lower_bound_probe.py
"""

from fractions import Fraction as F
from itertools import product
from typing import Dict, FrozenSet, List, Tuple


def pair_resolver(x: F, y: F) -> Tuple[F, F]:
    """The structured (non-lossy) encoding: V x V -> V x V, keeping
    both declarations verbatim. Mirrors rocq/ConflictResolutionLowerBound
    .v's structured_pair_is_nonlossy exactly."""
    return (x, y)


def left_wins(x: F, y: F) -> F:
    return x


def right_wins(x: F, y: F) -> F:
    return y


def erase(x: F, y: F) -> F:
    return F(0)


# A finite test domain V, closed under nothing in particular -- just a
# fixed finite set of exact rationals, large enough to make the n vs n^2
# gap visible.
FINITE_DOMAINS: Dict[int, List[F]] = {
    n: [F(i) for i in range(n)]
    for n in range(1, 7)
}


def check_pair_resolver_injective_on_domain(domain: List[F]) -> bool:
    """Confirms pair_resolver is injective on domain x domain: every
    ordered pair produces a distinct output. Trivially true (the output
    IS the pair), checked anyway rather than assumed, matching this
    project's standing discipline."""
    outputs = [pair_resolver(x, y) for x, y in product(domain, repeat=2)]
    return len(outputs) == len(set(outputs))


def image_size(resolve, domain: List[F]) -> int:
    """The number of DISTINCT outputs `resolve` produces over
    domain x domain -- meaningful only for resolvers whose outputs are
    structurally confined to `domain` itself (see module docstring)."""
    return len(set(resolve(x, y) for x, y in product(domain, repeat=2)))


def print_report() -> None:
    print("Conflict-resolution lower bound probe (R12)")
    print()

    print("=== The finite pigeonhole gap: |V| = n vs |V x V| = n^2 ===")
    header = f"{'n':<4} {'n^2':<6} {'gap = n^2 - n':<15}"
    print(header)
    print("-" * len(header))
    for n in sorted(FINITE_DOMAINS):
        gap = n * n - n
        print(f"{n:<4} {n * n:<6} {gap:<15}")
    print()
    print("For every n > 1, n^2 > n: a codomain of size n cannot injectively")
    print("receive n^2 distinct ordered pairs, so no lossy (codomain = V)")
    print("resolver can be non-lossy once |V| > 1 -- the cardinality-flavoured")
    print("restatement of the same fact ConflictResolutionTrilemma.v proves")
    print("equationally, for any V, finite or not.")
    print()

    print("=== pair_resolver is injective on V x V, checked per domain size ===")
    for n, domain in sorted(FINITE_DOMAINS.items()):
        ok = check_pair_resolver_injective_on_domain(domain)
        img = image_size(lambda x, y: pair_resolver(x, y), domain)
        print(f"  n={n}: injective={ok}  |image|={img}  (expected {n * n})")
    print()

    print("=== Concrete collision counts for codomain-confined lossy resolvers ===")
    print("(left_wins, right_wins, erase all have output structurally confined")
    print(" to V itself -- NOT average or sum, whose outputs can leave V; see")
    print(" the module docstring for why those are excluded from this table)")
    print()
    header2 = f"{'n':<4} {'|VxV|':<7} {'left_wins img':<15} {'right_wins img':<16} {'erase img':<10}"
    print(header2)
    print("-" * len(header2))
    for n, domain in sorted(FINITE_DOMAINS.items()):
        lw = image_size(left_wins, domain)
        rw = image_size(right_wins, domain)
        er = image_size(erase, domain)
        print(f"{n:<4} {n * n:<7} {lw:<15} {rw:<16} {er:<10}")
    print()
    print("left_wins/right_wins achieve the best a codomain-confined resolver")
    print("can do (image size exactly n, matching |V|) -- still a factor of n")
    print("short of the n^2 pairs that needed distinguishing. erase achieves")
    print("the worst possible (image size exactly 1, regardless of n).")


if __name__ == "__main__":
    print_report()
