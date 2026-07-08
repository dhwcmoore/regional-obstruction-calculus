#!/usr/bin/env python3
"""
certificate_emitter.py

Assembles a JSON certificate for the associator-generated obstruction
pipeline: per-seam associator defects, the compiled residue vector, and
the repair-solver verdict. Mirrors the certificate shape of
residue_classifier.classify and refinement_checker.check_witness, but for
the associator_residue.py / repair_solver.py pipeline.

The certificate is self-contained by design: it embeds the raw per-seam
correction data (`mu_by_seam`), the coboundary matrices, and the verdict
witness (a correction `b` or a cycle `z`), so `first_order_certificate_
checker.py` can verify it from the JSON alone, without importing
associator_residue.py, regional_composition.py, or finite_algebra.py --
see that module's docstring for exactly what "verify" means and does not
mean here.
"""

import json
from fractions import Fraction
from typing import Dict, List, Optional

from associator_residue import SeamAssociatorInstance, compile_residue
from rational_linear_algebra import mat_vec, is_zero
from repair_solver import RepairResult, attempt_repair


def build_certificate(
    source: str,
    coboundary_0: List[List[Fraction]],
    cycle: List[Fraction],
    seam_order: List[str],
    instances: List[SeamAssociatorInstance],
    coboundary_1: Optional[List[List[Fraction]]] = None,
) -> dict:
    by_seam: Dict[str, Fraction] = compile_residue(instances)
    residue = [by_seam[s] for s in seam_order]

    coboundary_1 = coboundary_1 if coboundary_1 is not None else []
    result: RepairResult = attempt_repair(coboundary_0, residue, cycle, coboundary_1=coboundary_1)

    delta1_r = mat_vec(coboundary_1, residue) if coboundary_1 else []
    closed = is_zero(delta1_r)

    mu_by_seam = {
        inst.seam: {
            "mu_VW": str(inst.mu.mu_VW),
            "mu_UvV_W": str(inst.mu.mu_UvV_W),
            "mu_U_VvW": str(inst.mu.mu_U_VvW),
            "mu_UV": str(inst.mu.mu_UV),
        }
        for inst in instances
    }

    return {
        "source": source,
        "seam_order": seam_order,
        "mu_by_seam": mu_by_seam,
        "computed_associator_defects": {s: str(by_seam[s]) for s in seam_order},
        "seam_residue": [str(x) for x in residue],
        "coboundary_1_matrix": [[str(x) for x in row] for row in coboundary_1],
        "delta1_r": [str(x) for x in delta1_r],
        "closed": closed,
        "coboundary_0_matrix": [[str(x) for x in row] for row in coboundary_0],
        "cycle_vector": [str(x) for x in cycle],
        "pairing": str(result.obstruction_pairing) if result.obstruction_pairing is not None else None,
        "repairable": result.repairable,
        "correction": [str(x) for x in result.correction] if result.correction is not None else None,
        "verdict": result.verdict,
    }


def write_certificate(cert: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(cert, f, indent=2)
