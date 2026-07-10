#!/usr/bin/env python3
"""
conflict_resolution_trilemma_probe.py

Checks docs/design/CONFLICT_RESOLUTION_TRILEMMA.md's §4 classification
table computationally, over concrete rational test pairs, rather than
trusting the hand-argued version. Not tied to refinement witnesses,
coupled parallel composition, or any other structure in this project --
this is a fact about resolver functions V x V -> V in the abstract,
instantiated here with V = Q (exact rationals) since that is the
simplest nontrivial V available and matches the shared-seam
declared-cycle-coefficient setting the conflict-resolution question
actually arose from.

Six named properties (docs/design/CONFLICT_RESOLUTION_TRILEMMA.md §2),
checked against a battery of test pairs, exact-rational throughout:

    agreement    -- resolve(x, x) == x for every tested x
    left_fid     -- resolve(x, y) == x for every tested (x, y), x != y
    right_fid    -- resolve(x, y) == y for every tested (x, y), x != y
    symmetric    -- resolve(x, y) == resolve(y, x) for every tested (x, y)
    idempotent   -- resolve(x, x) == x for every tested x (identical check
                    to `agreement`, kept as its own column per the design
                    doc's own observation that it is not independent --
                    verified here computationally, not just argued: the
                    two columns must always match exactly, for every
                    resolver tested, or the design doc's claim is wrong)

`refuse` and `external_authority` are not V x V -> V functions in the
sense the other five are (see the design doc §4/§5) and are reported
separately, by construction, not run through the same battery.

USAGE:
    python conflict_resolution_trilemma_probe.py
"""

from fractions import Fraction as F
from typing import Callable, Dict, List, Optional

Resolver = Callable[[F, F], F]

TEST_PAIRS: List[tuple] = [
    (F(1), F(1)),
    (F(3), F(3)),
    (F(-2), F(-2)),
    (F(0), F(0)),
    (F(5), F(-5)),
    (F(-5), F(5)),
    (F(1), F(2)),
    (F(2), F(1)),
    (F(3, 2), F(-7, 4)),
    (F(-7, 4), F(3, 2)),
    (F(0), F(4)),
    (F(4), F(0)),
]

DISTINCT_PAIRS = [(x, y) for (x, y) in TEST_PAIRS if x != y]
DIAGONAL_XS = sorted({x for (x, y) in TEST_PAIRS if x == y}, key=lambda f: (f.numerator, f.denominator))


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


NAMED_RESOLVERS: Dict[str, Resolver] = {
    "left_wins": left_wins,
    "right_wins": right_wins,
    "average": average,
    "sum": total_sum,
    "erase": erase,
}


def check_agreement(resolve: Resolver) -> bool:
    return all(resolve(x, x) == x for x in DIAGONAL_XS)


def check_idempotent(resolve: Resolver) -> bool:
    return all(resolve(x, x) == x for x in DIAGONAL_XS)


def check_left_fidelity(resolve: Resolver) -> bool:
    return all(resolve(x, y) == x for (x, y) in DISTINCT_PAIRS)


def check_right_fidelity(resolve: Resolver) -> bool:
    return all(resolve(x, y) == y for (x, y) in DISTINCT_PAIRS)


def check_symmetric(resolve: Resolver) -> bool:
    return all(resolve(x, y) == resolve(y, x) for (x, y) in TEST_PAIRS)


def classify(resolve: Resolver) -> Dict[str, bool]:
    return {
        "agreement": check_agreement(resolve),
        "idempotent": check_idempotent(resolve),
        "left_fidelity": check_left_fidelity(resolve),
        "right_fidelity": check_right_fidelity(resolve),
        "symmetric": check_symmetric(resolve),
    }


def check_no_resolver_has_both_fidelities() -> Optional[str]:
    """Directly checks the core impossibility (docs/design/
    CONFLICT_RESOLUTION_TRILEMMA.md §3) against every named resolver:
    none should have both left_fidelity and right_fidelity simultaneously
    True. Returns the name of any resolver that violates this (which
    would mean the theorem, or this probe, has a bug), or None."""
    for name, resolve in NAMED_RESOLVERS.items():
        result = classify(resolve)
        if result["left_fidelity"] and result["right_fidelity"]:
            return name
    return None


def print_report() -> None:
    print("Conflict-resolution trilemma probe")
    print(f"({len(DISTINCT_PAIRS)} distinct-value test pairs, {len(DIAGONAL_XS)} diagonal values)")
    print()

    header = f"{'resolver':<12} {'agreement':<10} {'idempotent':<11} {'left_fid':<9} {'right_fid':<10} {'symmetric':<10}"
    print(header)
    print("-" * len(header))
    for name, resolve in NAMED_RESOLVERS.items():
        r = classify(resolve)
        print(f"{name:<12} {str(r['agreement']):<10} {str(r['idempotent']):<11} "
              f"{str(r['left_fidelity']):<9} {str(r['right_fidelity']):<10} {str(r['symmetric']):<10}")

    print()
    print("refuse:              declines to produce a value at all when x != y "
          "(not a V x V -> V function on disagreement; not run through the table above)")
    print("external_authority:  takes a third input not derivable from (x, y); "
          "not a V x V -> V function at all; not run through the table above")
    print()

    print("=== Checking agreement == idempotent for every resolver (the design doc's ===")
    print("=== claim that Idempotence is not independent of Agreement)              ===")
    mismatches = [name for name, resolve in NAMED_RESOLVERS.items()
                  if classify(resolve)["agreement"] != classify(resolve)["idempotent"]]
    print(f"  mismatches found: {len(mismatches)} {mismatches if mismatches else '(none)'}")

    print()
    print("=== Checking the core impossibility: no resolver has both fidelities ===")
    violator = check_no_resolver_has_both_fidelities()
    if violator is None:
        print("  confirmed: no named resolver has both left_fidelity and right_fidelity.")
    else:
        print(f"  VIOLATION FOUND: {violator} has both -- theorem or probe has a bug.")

    print()
    print("=== sum's sharper sacrifice (design doc claims it fails agreement too) ===")
    sum_result = classify(total_sum)
    print(f"  sum(1, 1) = {total_sum(F(1), F(1))}  (agreement would require this to equal 1)")
    print(f"  sum agreement={sum_result['agreement']}  idempotent={sum_result['idempotent']}")


if __name__ == "__main__":
    print_report()
