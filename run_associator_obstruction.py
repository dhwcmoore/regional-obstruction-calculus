#!/usr/bin/env python3
"""
run_associator_obstruction.py

CLI entry point for the associator-generated obstruction pipeline:

    local product/correction data (seam_instances)
        -> associator defects (regional_composition.py)
        -> compiled seam residue (associator_residue.py)
        -> repair attempt / obstruction verdict (repair_solver.py)

USAGE:
    python run_associator_obstruction.py examples/four_cycle_associator.json
    python run_associator_obstruction.py examples/four_cycle_associator.json --json out.json
"""

import argparse
import json
from fractions import Fraction
from typing import List

from associator_residue import SeamAssociatorInstance, compile_residue
from certificate_emitter import build_certificate, write_certificate
from regional_composition import SeamCorrectionData
from repair_solver import attempt_repair


def _matrix(rows) -> List[List[Fraction]]:
    return [[Fraction(x) for x in row] for row in rows]


def _vector(xs) -> List[Fraction]:
    return [Fraction(x) for x in xs]


def load_instances(data: dict) -> List[SeamAssociatorInstance]:
    instances = []
    for seam, spec in data["seam_instances"].items():
        mu = SeamCorrectionData(
            mu_VW=Fraction(spec["mu_VW"]),
            mu_UvV_W=Fraction(spec["mu_UvV_W"]),
            mu_U_VvW=Fraction(spec["mu_U_VvW"]),
            mu_UV=Fraction(spec["mu_UV"]),
        )
        instances.append(SeamAssociatorInstance(seam=seam, mu=mu))
    return instances


def run(file_path: str, json_out: str = None) -> dict:
    with open(file_path, "r") as f:
        data = json.load(f)

    seam_order = data["seam_order"]
    coboundary_0 = _matrix(data["coboundary_0"])
    cycle = _vector(data["cycle_witness"])
    instances = load_instances(data)

    by_seam = compile_residue(instances)
    residue = [by_seam[s] for s in seam_order]

    if "expected_residue" in data:
        expected = _vector(data["expected_residue"])
        if residue != expected:
            raise AssertionError(
                f"computed residue {residue} does not match expected_residue {expected}"
            )

    result = attempt_repair(coboundary_0, residue, cycle)

    print(f"computed residue: ({', '.join(str(x) for x in residue)})")
    print(f"pairing with cycle: {result.obstruction_pairing}")
    print(f"verdict: {result.verdict}")

    cert = build_certificate(file_path, coboundary_0, cycle, seam_order, instances)
    if json_out:
        write_certificate(cert, json_out)
        print(f"\nWrote certificate to {json_out}")
    return cert


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file_path", help="path to a four_cycle_associator.json-shaped witness file")
    parser.add_argument("--json", metavar="PATH", help="write the certificate as JSON to PATH")
    args = parser.parse_args()

    run(args.file_path, args.json)
