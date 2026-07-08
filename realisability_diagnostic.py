#!/usr/bin/env python3
"""
realisability_diagnostic.py

A single diagnostic computation for the realisability question raised as
future work (item 14 in the README; see docs/REALISABILITY_ROADMAP.md):
which seam residues can the associator-generation pipeline
(associator_residue.py's four_cycle_instances-style construction) actually
produce?

This is deliberately NOT a realisability theorem, an analyser module, or a
proof-carrying certificate format -- see docs/REALISABILITY_ROADMAP.md for
why not yet. It answers one question about the *current* generator before
any theorem is attempted, using the actual literal-expansion-verified
compute_seam_residue path (via associator_residue.compile_residue), not a
hand derivation or the closed-form shortcut:

    A : Q^16 -> Q^4

is the linear map from sixteen parameters (four seams, each with its own
independent mu_VW/mu_UvV_W/mu_U_VvW/mu_UV) to the assembled seam residue
vector, built one column at a time by evaluating the real generator on
each unit parameter vector.

The result, computed and locked in by tests/test_realisability_diagnostic.py:
A has full rank 4, i.e. is surjective onto all of C^1(N;Q). Every residue
-- obstructed, exact, or anything else -- is realisable by the current
generator. This is a genuine result, and a negative one: the current
four_cycle_instances()-style construction imposes no structural
constraint at all, because its four seams are fully independent local
Venn-triple instances (see regional_composition.VennTriple) with no
shared data -- not even though seams e12 and e23 share the coarse vertex
U2. A non-trivial realisability theorem needs a generator where seams
sharing regional data are actually constrained by each other; that
generator does not exist in this repository yet.

USAGE:
    python realisability_diagnostic.py
"""

from fractions import Fraction
from typing import Dict, List, Tuple

from associator_residue import SeamAssociatorInstance, compile_residue, SEAM_ORDER
from regional_composition import SeamCorrectionData
from rational_linear_algebra import nullspace_over_Q, transpose, in_span_over_Q

PARAM_NAMES = ("mu_VW", "mu_UvV_W", "mu_U_VvW", "mu_UV")


def _zero_params() -> Dict[str, Fraction]:
    return {name: Fraction(0) for name in PARAM_NAMES}


def _residue_for_params(param_by_seam: Dict[str, Dict[str, Fraction]]) -> List[Fraction]:
    instances = [
        SeamAssociatorInstance(seam=seam, mu=SeamCorrectionData(**param_by_seam[seam]))
        for seam in SEAM_ORDER
    ]
    by_seam = compile_residue(instances)
    return [by_seam[s] for s in SEAM_ORDER]


def realisability_columns() -> Tuple[List[List[Fraction]], List[str]]:
    """
    The 16 columns of A (each a length-4 Fraction vector: the seam residue
    produced by setting exactly one (seam, mu-parameter) to 1 and every
    other parameter to 0), and their labels, in the order
    seam x PARAM_NAMES. Each column is computed by actually running the
    generator (compile_residue), not derived algebraically.
    """
    columns: List[List[Fraction]] = []
    labels: List[str] = []
    for seam in SEAM_ORDER:
        for pname in PARAM_NAMES:
            param_by_seam = {s: _zero_params() for s in SEAM_ORDER}
            param_by_seam[seam][pname] = Fraction(1)
            columns.append(_residue_for_params(param_by_seam))
            labels.append(f"{seam}.{pname}")
    return columns, labels


def realisability_matrix() -> Tuple[List[List[Fraction]], List[str]]:
    """A as a dense matrix (4 rows = C^1(N;Q) coordinates, 16 columns =
    parameters), plus the column labels."""
    columns, labels = realisability_columns()
    return transpose(columns), labels


def diagnose() -> dict:
    """
    Computes rank(A) via nullspace_over_Q (exact rational elimination,
    not a determinant or floating-point SVD), and records enough of the
    computation to be independently checked, not just the headline claim.
    """
    A, labels = realisability_matrix()
    n_params = len(labels)
    dim_C1 = len(A)
    ker = nullspace_over_Q(A)
    rank = n_params - len(ker)

    return {
        "n_params": n_params,
        "dim_C1": dim_C1,
        "rank_A": rank,
        "dim_ker_A": len(ker),
        "full_rank": rank == dim_C1,
        "column_labels": labels,
    }


def is_realisable(residue: List[Fraction]) -> bool:
    """Whether `residue` lies in image(A) for the current generator, by
    exact subspace-membership test -- not inferred from the rank alone."""
    columns, _ = realisability_columns()
    return in_span_over_Q(columns, residue)


def print_report() -> None:
    result = diagnose()
    print("Realisability diagnostic: current four_cycle_instances-style generator")
    print(f"  parameters: {result['n_params']} (4 seams x 4 mu-constants each)")
    print(f"  dim C^1(N;Q): {result['dim_C1']}")
    print(f"  rank(A): {result['rank_A']}")
    print(f"  dim ker(A): {result['dim_ker_A']}")
    print(f"  full rank (every residue realisable): {result['full_rank']}")
    if result["full_rank"]:
        print()
        print("  NEGATIVE RESULT: the current generator imposes no structural")
        print("  constraint. Every residue in C^1(N;Q) -- obstructed or not -- is")
        print("  realisable, because its four seams are fully independent local")
        print("  Venn-triple instances with no shared data. See")
        print("  docs/REALISABILITY_ROADMAP.md for what a non-trivial")
        print("  realisability theorem would require.")


if __name__ == "__main__":
    print_report()
