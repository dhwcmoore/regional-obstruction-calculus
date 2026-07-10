#!/usr/bin/env python3
"""
conflict_diagnostic_completeness_probe.py

R13. Makes rocq/ConflictDiagnosticCompleteness.v's classification
visible over concrete, exact-rational test data -- it does not attempt
to prove the completeness theorem (that is the Rocq file's job); it
classifies a fixed set of named strategies (the same ones
conflict_resolution_trilemma_probe.py and conflict_resolution_lower_
bound_probe.py already use) into the fragment's four buckets --
no_composite, lossy_scalar, nonlossy_structured, unresolved -- and
confirms every strategy tested lands in exactly one bucket, with no
strategy left unclassified.

Strategy -> class mapping, matching docs/design/CONFLICT_DIAGNOSTIC_
COMPLETENESS.md §3-4 exactly:

    refuse                          -> no_composite
    left_wins/right_wins/average/
      sum/erase                     -> lossy_scalar
    pair                            -> nonlossy_structured
    (a placeholder "not yet run")   -> unresolved

A strategy is classified lossy_scalar because it is structurally a
ScalarDiagnostic (it always emits one V-typed value) -- per
no_hidden_neutral_scalar_case, this alone is enough to know it cannot
be fully faithful on a genuinely disagreeing pair, regardless of which
specific strategy it is. This probe additionally verifies, for the
three strategies whose OUTPUT is structurally confined to the tested
finite domain (left_wins, right_wins, erase -- the same three
conflict_resolution_lower_bound_probe.py already restricts its
image-size table to), that their image size falls strictly short of
n^2 -- a second, independent confirmation of lossiness via the R12
pigeonhole argument specialised at codomain = V, not only the R11
argument. `average` and `sum` are classified lossy_scalar by TYPE (they
are ScalarDiagnostic strategies) but deliberately excluded from the
confinement/image-size check, since their outputs are not structurally
confined to any finite test subset of Q -- exactly the caveat conflict_
resolution_lower_bound_probe.py's own module docstring states, carried
forward here rather than silently dropped.

USAGE:
    python conflict_diagnostic_completeness_probe.py
"""

from fractions import Fraction as F
from itertools import product
from typing import Callable, Dict, List, Optional, Tuple

# --------------------------------------------------------------------
# The four DiagnosticClass buckets, matching rocq/
# ConflictDiagnosticCompleteness.v's inductive exactly.
# --------------------------------------------------------------------

NO_COMPOSITE = "no_composite"
LOSSY_SCALAR = "lossy_scalar"
NONLOSSY_STRUCTURED = "nonlossy_structured"
UNRESOLVED = "unresolved"

ALL_CLASSES = frozenset({NO_COMPOSITE, LOSSY_SCALAR, NONLOSSY_STRUCTURED, UNRESOLVED})


# --------------------------------------------------------------------
# Named strategies -- redefined locally (not imported), matching this
# project's existing precedent (conflict_resolution_lower_bound_probe.py
# redefines left_wins/right_wins/erase locally rather than importing
# them from conflict_resolution_trilemma_probe.py).
# --------------------------------------------------------------------

Resolver = Callable[[F, F], F]


def left_wins(x: F, y: F) -> F:
    return x


def right_wins(x: F, y: F) -> F:
    return y


def average(x: F, y: F) -> F:
    return (x + y) / 2


def total_sum(x: F, y: F) -> F:
    return x + y


def erase(x: F, y: F) -> F:
    return F(0)


def pair_diagnostic(x: F, y: F) -> Tuple[F, F]:
    """The structured, non-lossy diagnostic: mirrors rocq/
    ConflictDiagnosticCompleteness.v's pair_diagnostic_is_nonlossy /
    R12's structured_pair_is_nonlossy."""
    return (x, y)


SCALAR_STRATEGIES: Dict[str, Resolver] = {
    "left_wins": left_wins,
    "right_wins": right_wins,
    "average": average,
    "sum": total_sum,
    "erase": erase,
}

# The three scalar strategies whose OUTPUT is structurally confined to
# the tested finite domain -- see the module docstring for why
# average/sum are excluded from this set.
CONFINED_TO_DOMAIN = frozenset({"left_wins", "right_wins", "erase"})

FINITE_DOMAINS: Dict[int, List[F]] = {
    n: [F(i) for i in range(n)]
    for n in range(1, 7)
}


# --------------------------------------------------------------------
# Classification.
# --------------------------------------------------------------------

def classify_refuse() -> str:
    """A strategy that declines to produce any value at all when
    x != y -- no scalar output, no structured output. Matches
    RefuseDiagnostic / interface_conflict."""
    return NO_COMPOSITE


def classify_scalar_strategy(name: str) -> str:
    """Every named strategy in SCALAR_STRATEGIES always emits a single
    V-typed value (a ScalarDiagnostic, by construction) -- always
    lossy_scalar. This classification does not depend on running the
    strategy at all: it follows from the strategy's own type signature
    (V x V -> V), matching no_hidden_neutral_scalar_case's scope (it
    is stated for an ARBITRARY z : V, not for any specific strategy)."""
    if name not in SCALAR_STRATEGIES:
        raise ValueError(f"{name!r} is not a named scalar strategy")
    return LOSSY_SCALAR


def classify_pair() -> str:
    """The structured diagnostic -- always nonlossy_structured, verified
    below (not merely asserted) via injectivity on V x V."""
    return NONLOSSY_STRUCTURED


def classify_unresolved() -> str:
    """No diagnostic has been produced yet -- a bookkeeping state, not
    a claim about what the eventual diagnostic would say. Matches
    ReportSource.UNRESOLVED in veribound-fce."""
    return UNRESOLVED


def check_pair_injective_on_domain(domain: List[F]) -> bool:
    outputs = [pair_diagnostic(x, y) for x, y in product(domain, repeat=2)]
    return len(outputs) == len(set(outputs))


def image_size(strategy: Resolver, domain: List[F]) -> int:
    return len(set(strategy(x, y) for x, y in product(domain, repeat=2)))


def check_confined_strategies_are_lossy(domain: List[F]) -> Dict[str, bool]:
    """For each strategy in CONFINED_TO_DOMAIN, confirms its image size
    on domain x domain is strictly less than n^2 (n = len(domain)) once
    n > 1 -- an independent, R12-flavoured confirmation of lossiness
    (pigeonhole on a codomain confined to V) alongside the R11-flavoured
    one classify_scalar_strategy already relies on by type alone."""
    n = len(domain)
    result = {}
    for name in CONFINED_TO_DOMAIN:
        img = image_size(SCALAR_STRATEGIES[name], domain)
        result[name] = (n <= 1) or (img < n * n)
    return result


def print_report() -> None:
    print("Conflict-diagnostic completeness probe (R13)")
    print()

    print("=== Classification: every named strategy lands in exactly one bucket ===")
    header = f"{'strategy':<12} {'class':<20}"
    print(header)
    print("-" * len(header))
    print(f"{'refuse':<12} {classify_refuse():<20}")
    for name in SCALAR_STRATEGIES:
        print(f"{name:<12} {classify_scalar_strategy(name):<20}")
    print(f"{'pair':<12} {classify_pair():<20}")
    print(f"{'unresolved':<12} {classify_unresolved():<20}")
    print()

    classes_seen = {classify_refuse(), classify_pair(), classify_unresolved()}
    classes_seen |= {classify_scalar_strategy(name) for name in SCALAR_STRATEGIES}
    print(f"Distinct classes seen: {sorted(classes_seen)}")
    print(f"All four fragment classes represented: {classes_seen == ALL_CLASSES}")
    print()

    print("=== pair_diagnostic is injective on V x V, per domain size ===")
    for n, domain in sorted(FINITE_DOMAINS.items()):
        print(f"  n={n}: injective={check_pair_injective_on_domain(domain)}")
    print()

    print("=== n vs n^2: the R12 finite corollary, restated for this fragment ===")
    header2 = f"{'n':<4} {'n^2':<6} {'gap = n^2 - n':<15}"
    print(header2)
    print("-" * len(header2))
    for n in sorted(FINITE_DOMAINS):
        gap = n * n - n
        print(f"{n:<4} {n * n:<6} {gap:<15}")
    print()

    print("=== Confinement check: left_wins/right_wins/erase are lossy via pigeonhole ===")
    print("(average/sum are classified lossy_scalar by TYPE alone -- see module")
    print(" docstring for why their image size is NOT checked here)")
    print()
    header3 = f"{'n':<4} {'left_wins':<11} {'right_wins':<12} {'erase':<8}"
    print(header3)
    print("-" * len(header3))
    for n, domain in sorted(FINITE_DOMAINS.items()):
        result = check_confined_strategies_are_lossy(domain)
        print(f"{n:<4} {str(result['left_wins']):<11} {str(result['right_wins']):<12} {str(result['erase']):<8}")
    print()

    print("=== average/sum: classified lossy_scalar by type, confinement N/A ===")
    for n, domain in sorted(FINITE_DOMAINS.items()):
        avg_img = image_size(average, domain)
        sum_img = image_size(total_sum, domain)
        print(f"  n={n}: average image size={avg_img} (not compared to n^2 -- see docstring), "
              f"sum image size={sum_img} (not compared to n^2 -- see docstring)")


if __name__ == "__main__":
    print_report()
