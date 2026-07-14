#!/usr/bin/env python3
"""
r21_certificate_emitter.py

Builds a `repair-or-separator/v1` certificate (see `r21_certificate_
format.py` for the schema) from a rational system `D b = r`, by running
the untrusted generator in `r21_repair_or_separator.py`. This module's
output is never trusted on its own -- see that module's docstring, and
verify any certificate it emits with `r21_certificate_checker.py` (the
`roc-verify` CLI below) before acting on it.

USAGE (roc-solve):
    python r21_certificate_emitter.py input.json --certificate output.json
"""

import argparse
import json
from fractions import Fraction
from typing import List

from r21_certificate_format import (
    CERTIFICATE_SCHEMA,
    INPUT_KEYS,
    INPUT_SCHEMA,
    canonical_input_digest,
    parse_matrix,
    parse_vector,
    strict_json_load,
    validate_closed_keys,
    validate_problem_shape,
)
from r21_repair_or_separator import RESULT_REPAIR, RESULT_SEPARATOR, repair_or_separate


def build_certificate(D: List[List[Fraction]], r: List[Fraction]) -> dict:
    result = repair_or_separate(D, r)
    cert = {
        "schema": CERTIFICATE_SCHEMA,
        "input_digest": canonical_input_digest(D, r),
        "result": result.result,
    }
    if result.result == RESULT_REPAIR:
        cert["repair"] = [str(x) for x in result.repair]
    elif result.result == RESULT_SEPARATOR:
        cert["separator"] = [str(x) for x in result.separator]
    return cert


def read_input(path: str):
    doc = strict_json_load(path)
    if not isinstance(doc, dict) or doc.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"unrecognized input schema: {doc.get('schema') if isinstance(doc, dict) else doc!r}")
    validate_closed_keys(doc, INPUT_KEYS, "input file")
    D = parse_matrix(doc["D"])
    r = parse_vector(doc["r"])
    validate_problem_shape(D, r)
    return D, r


def write_certificate(cert: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(cert, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="path to a roc-input/v1 JSON file (D, r)")
    parser.add_argument("--certificate", required=True, help="path to write the repair-or-separator/v1 certificate")
    args = parser.parse_args()

    D, r = read_input(args.input)
    cert = build_certificate(D, r)
    write_certificate(cert, args.certificate)
    print(f"{cert['result'].upper()}: wrote {args.certificate}")


if __name__ == "__main__":
    main()
