#!/usr/bin/env python3
"""
first_order_certificate_checker.py

Independent checker for the proof-carrying first-order classifier
certificates emitted by certificate_emitter.build_certificate (the
associator_residue.py / regional_composition.py / repair_solver.py
pipeline, item 7 in the README).

"Independent" means: this module does not import associator_residue.py,
regional_composition.py, finite_algebra.py, repair_solver.py, or
certificate_emitter.py. It verifies a certificate purely from the JSON
data it contains, by recomputing three layers, each independently of the
classifier's own code path:

  Layer 1 (residue construction). For every seam, recomputes the
  closed-form defect

      Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV

  (Proposition prop:four-term / regional_composition.closed_form_delta)
  from the certificate's own recorded `mu_by_seam` data -- using a
  from-scratch copy of the formula in this file, not an import of
  regional_composition.closed_form_delta, so a bug in that function would
  not go undetected here -- and checks it against the certificate's
  recorded per-seam defect and the assembled `seam_residue`. This does
  NOT re-derive the residue from the full literal associator expansion
  (regional_composition.associator_defect) or the square-zero Venn model
  (finite_algebra.py): reimplementing that machinery independently is
  exactly the concrete-instantiation mechanisation step the README (item
  8) already defers, not attempted here either. What this layer does
  check is that the certificate's own declared correction constants
  really do assemble, via the paper's own closed-form formula, into the
  residue the certificate claims.

  Layer 2 (closedness). Recomputes delta^1 r and checks it is zero.

  Layer 3 (verdict). For a `globally_repairable` verdict, recomputes
  delta^0 b and checks it equals the residue. For a
  `nontrivial_associator_obstruction` verdict, recomputes z^T delta^0
  (checking z is a cycle) and <z, r> (checking it is non-zero and
  matches the recorded pairing).

This module reuses `rational_linear_algebra`'s generic matrix/vector
primitives (mat_vec, row_vec_mat, dot, is_zero) -- these are shared,
already-audited exact-rational arithmetic, not classifier-specific logic,
and every other checker in this repository (residue_classifier.py,
refinement_checker.py) reuses the same module rather than reimplementing
matrix multiplication twice. It does NOT reuse solve_over_Q: verifying a
supplied witness never requires solving a linear system, only evaluating
one, which keeps this checker's trusted surface smaller than the
classifier's.

Rational fields in the certificate must be in the canonical `str(Fraction)`
form this repository's tools emit (an optional leading `-`, digits, and an
optional `/digits`) -- not decimal notation. This is stricter than Python's
`Fraction(str)` constructor, which silently accepts (and exactly converts)
decimal strings like "1.5"; rejecting that form here is a certificate
format requirement, not a claim that decimal input would be numerically
unsound.

USAGE:
    python first_order_certificate_checker.py out.json
"""

import argparse
import json
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional

from rational_linear_algebra import mat_vec, row_vec_mat, dot, is_zero

_RATIONAL_RE = re.compile(r"^-?\d+(/\d+)?$")

VERDICT_GLOBALLY_REPAIRABLE = "globally_repairable"
VERDICT_NONTRIVIAL_OBSTRUCTION = "nontrivial_associator_obstruction"


def parse_rational(s) -> Fraction:
    """Strict exact-rational parser: only `-?digits` or `-?digits/digits`,
    matching this repository's canonical str(Fraction) output. Raises
    ValueError on anything else, including decimal notation."""
    if not isinstance(s, str) or not _RATIONAL_RE.match(s):
        raise ValueError(f"not a canonical exact-rational string: {s!r}")
    return Fraction(s)


def parse_vector(xs) -> List[Fraction]:
    if not isinstance(xs, list):
        raise ValueError(f"expected a list of rationals, got {xs!r}")
    return [parse_rational(x) for x in xs]


def parse_matrix(rows) -> List[List[Fraction]]:
    if not isinstance(rows, list):
        raise ValueError(f"expected a matrix (list of rows), got {rows!r}")
    return [parse_vector(row) for row in rows]


def closed_form_delta(mu_VW: Fraction, mu_UvV_W: Fraction, mu_U_VvW: Fraction, mu_UV: Fraction) -> Fraction:
    """From-scratch copy of Proposition prop:four-term's closed form,
    deliberately not imported from regional_composition.py -- see module
    docstring."""
    return mu_VW - mu_UvV_W + mu_U_VvW - mu_UV


@dataclass
class CheckResult:
    accepted: bool = True
    reasons: List[str] = field(default_factory=list)

    def reject(self, msg: str) -> None:
        self.accepted = False
        self.reasons.append(msg)


def check_certificate(cert: dict) -> CheckResult:
    result = CheckResult()

    try:
        seam_order = cert["seam_order"]
        mu_by_seam = cert["mu_by_seam"]
        computed_defects = cert["computed_associator_defects"]
        seam_residue = parse_vector(cert["seam_residue"])
        coboundary_1 = parse_matrix(cert["coboundary_1_matrix"])
        delta1_r_recorded = parse_vector(cert["delta1_r"])
        closed_recorded = cert["closed"]
        coboundary_0 = parse_matrix(cert["coboundary_0_matrix"])
        cycle = parse_vector(cert["cycle_vector"])
        pairing_recorded = cert["pairing"]
        repairable = cert["repairable"]
        correction = cert["correction"]
        verdict = cert["verdict"]
    except (KeyError, TypeError, ValueError) as e:
        result.reject(f"malformed certificate: {e}")
        return result

    # --- Layer 1: residue construction -----------------------------------
    reconstructed = []
    for seam in seam_order:
        if seam not in mu_by_seam:
            result.reject(f"seam {seam}: no mu_by_seam entry in certificate")
            continue
        if seam not in computed_defects:
            result.reject(f"seam {seam}: no computed_associator_defects entry in certificate")
            continue
        mu = mu_by_seam[seam]
        try:
            delta = closed_form_delta(
                parse_rational(mu["mu_VW"]),
                parse_rational(mu["mu_UvV_W"]),
                parse_rational(mu["mu_U_VvW"]),
                parse_rational(mu["mu_UV"]),
            )
            recorded = parse_rational(computed_defects[seam])
        except (KeyError, TypeError, ValueError) as e:
            result.reject(f"seam {seam}: malformed mu/defect data ({e})")
            continue
        if delta != recorded:
            result.reject(
                f"seam {seam}: closed-form recomputation Delta={delta} "
                f"disagrees with recorded computed_associator_defects={recorded}"
            )
        reconstructed.append(recorded)

    if len(reconstructed) == len(seam_order) and reconstructed != seam_residue:
        result.reject(
            f"assembled seam_residue {reconstructed} (in seam_order) "
            f"disagrees with recorded seam_residue {seam_residue}"
        )

    # --- Layer 2: closedness (delta^1 r = 0) ------------------------------
    delta1_r = mat_vec(coboundary_1, seam_residue) if coboundary_1 else []
    if delta1_r != delta1_r_recorded:
        result.reject(f"recomputed delta1_r={delta1_r} disagrees with recorded delta1_r={delta1_r_recorded}")
    actually_closed = is_zero(delta1_r)
    if actually_closed != bool(closed_recorded):
        result.reject(f"recomputed closedness={actually_closed} disagrees with recorded closed={closed_recorded}")
    if not actually_closed:
        result.reject("residue is not closed (delta^1 r != 0); classifier soundness requires a closed residue")

    # --- Layer 3: verdict --------------------------------------------------
    if verdict == VERDICT_GLOBALLY_REPAIRABLE:
        if not repairable:
            result.reject("verdict is globally_repairable but repairable=false")
        if correction is None:
            result.reject("globally_repairable verdict has no correction witness b")
        else:
            try:
                b = parse_vector(correction)
            except ValueError as e:
                result.reject(f"malformed correction witness: {e}")
                b = None
            if b is not None:
                reproduced = mat_vec(coboundary_0, b)
                if reproduced != seam_residue:
                    result.reject(
                        f"delta^0 b = {reproduced} does not reproduce seam_residue={seam_residue}"
                    )
    elif verdict == VERDICT_NONTRIVIAL_OBSTRUCTION:
        if repairable:
            result.reject("verdict is nontrivial_associator_obstruction but repairable=true")
        z_delta0 = row_vec_mat(cycle, coboundary_0)
        if not is_zero(z_delta0):
            result.reject(f"cycle_vector is not a cycle: z^T delta^0 = {z_delta0} != 0")
        computed_pairing = dot(cycle, seam_residue)
        if computed_pairing == 0:
            result.reject("pairing <z, r> = 0; does not certify obstruction")
        if pairing_recorded is None:
            result.reject("no recorded pairing for an obstruction verdict")
        else:
            try:
                recorded_pairing = parse_rational(pairing_recorded)
            except ValueError as e:
                result.reject(f"malformed recorded pairing: {e}")
                recorded_pairing = None
            if recorded_pairing is not None and recorded_pairing != computed_pairing:
                result.reject(
                    f"recomputed pairing {computed_pairing} disagrees with recorded pairing {recorded_pairing}"
                )
    else:
        result.reject(f"unrecognized verdict: {verdict!r}")

    return result


def check_file(path: str) -> CheckResult:
    with open(path, "r") as f:
        cert = json.load(f)
    return check_certificate(cert)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", help="path to a first-order classifier certificate JSON file")
    args = parser.parse_args()

    result = check_file(args.certificate)
    if result.accepted:
        print(f"ACCEPT: {args.certificate}")
    else:
        print(f"REJECT: {args.certificate}")
        for reason in result.reasons:
            print(f"  - {reason}")
    raise SystemExit(0 if result.accepted else 1)


if __name__ == "__main__":
    main()
