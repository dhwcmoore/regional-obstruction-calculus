#!/usr/bin/env python3
"""
residue_classifier.py

Computational classifier for finite H^1 obstruction witnesses.

This script implements the "exact rational classifier" described in Section 9
of the paper "Associator Fields and Local-to-Global Failure in Finite
Regional Cohomology".

It takes a JSON file describing a finite cochain complex and a residue,
and determines whether the residue represents a non-trivial H^1 class.

It provides two certificates for the verdict:
1. Linear System Inconsistency: exact Gauss-Jordan elimination over Q
   determines whether delta^0 b = r has a solution.
2. Cycle Pairing: computes <z, r> for a given cycle witness z.

Both checks are exact rational arithmetic throughout (Python `Fraction`,
via rational_linear_algebra.py) -- there is no floating-point step
anywhere in this classifier.

USAGE:
    python residue_classifier.py path/to/your_complex.json
    python residue_classifier.py path/to/your_complex.json --json out.json
"""

import argparse
import json
from fractions import Fraction
from typing import List

from rational_linear_algebra import mat_vec, dot, is_zero, solve_over_Q


def matrix_from_strings(m: List[List[str]]) -> List[List[Fraction]]:
    """Convert string matrix to a matrix of Fractions."""
    return [[Fraction(x) for x in row] for row in m]


def vector_from_strings(v: List[str]) -> List[Fraction]:
    """Convert string vector to a vector of Fractions."""
    return [Fraction(x) for x in v]


def classify(data: dict) -> dict:
    """
    Runs the classifier against a loaded witness record (the parsed JSON
    of a four_cycle.json-shaped file) and returns a certificate dict.
    Does no I/O and no printing, so it can be called directly by tests.
    """
    complex_data = data["complex"]
    d0 = matrix_from_strings(complex_data["coboundary_0"])
    d1 = matrix_from_strings(complex_data["coboundary_1"])
    r = vector_from_strings(data["residue"])
    z = vector_from_strings(data["cycle_witness"])

    # 1. Check if residue is a cocycle (delta^1 r = 0)
    d1r = mat_vec(d1, r) if d1 else []
    is_cocycle = is_zero(d1r)

    # 2. Check if residue is a coboundary (r in im(delta^0)), by exact
    #    Gauss-Jordan elimination over Q -- no floating point.
    is_removable, b = solve_over_Q(d0, r)

    # 3. Cycle pairing certificate <z, r>
    pairing = dot(z, r)

    is_obstruction = is_cocycle and not is_removable

    return {
        "name": data["name"],
        "complex_name": complex_data["name"],
        "residue": data["residue"],
        "cycle_witness": data["cycle_witness"],
        "is_cocycle": is_cocycle,
        "coboundary_1_r": [str(x) for x in d1r],
        "is_coboundary": is_removable,
        "coboundary_0_solution": [str(x) for x in b] if b is not None else None,
        "pairing": str(pairing),
        "is_obstruction": is_obstruction,
        "verdict": "nontrivial_H1_obstruction" if is_obstruction else "trivial",
    }


def print_certificate(cert: dict) -> None:
    print("\n" + "=" * 50)
    print("FINITE OBSTRUCTION CERTIFICATE")
    print("=" * 50)
    print(f"Witness: {cert['name']}")
    print(f"Complex: {cert['complex_name']}")
    print(f"Residue r: {cert['residue']}")
    print("-" * 50)

    print("1. Cocycle Check (δ¹r = 0):")
    if not cert["is_cocycle"]:
        print(f"  - FAIL: Residue is not a cocycle. δ¹r = {cert['coboundary_1_r']}")
    else:
        print("  - PASS: Residue is a cocycle (δ¹r = 0).")

    print("\n2. Coboundary Check (r ∈ im(δ⁰)):")
    if cert["is_coboundary"]:
        print("  - REMOVABLE: Residue is a coboundary.")
        print(f"    Found solution b = {cert['coboundary_0_solution']} such that δ⁰b = r.")
    else:
        print("  - NOT REMOVABLE: Residue is not a coboundary.")
        print("    Linear system δ⁰b = r is inconsistent (exact Gauss-Jordan elimination over Q).")

    print("\n3. Cycle Pairing Certificate (<z, r>):")
    print(f"  Cycle witness z: {cert['cycle_witness']}")
    print(f"  Pairing <z, r> = {cert['pairing']}")
    if cert["pairing"] == "0":
        print("  - VERDICT: Pairing is zero. This does not prove non-exactness.")
    else:
        print("  - VERDICT: Pairing is non-zero, certifying r is not a coboundary.")

    print("-" * 50)
    print("FINAL VERDICT:")
    if cert["is_obstruction"]:
        print("  => Nontrivial H¹ Obstruction")
    else:
        print("  => Trivial (Removable or Not a Cocycle)")
    print("=" * 50)
    print("=" * 50)


def run_classifier(file_path: str, json_out: str = None) -> None:
    """Loads a complex and residue, runs the classification, and prints it."""
    print(f"Loading witness file: {file_path}")
    with open(file_path, "r") as f:
        data = json.load(f)

    cert = classify(data)
    print_certificate(cert)

    if json_out:
        with open(json_out, "w") as f:
            json.dump(cert, f, indent=2)
        print(f"\nWrote certificate to {json_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_path", help="path to a four_cycle.json-shaped witness file")
    parser.add_argument("--json", metavar="PATH", help="write the certificate as JSON to PATH")
    args = parser.parse_args()

    run_classifier(args.file_path, args.json)
