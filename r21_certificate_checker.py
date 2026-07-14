#!/usr/bin/env python3
"""
r21_certificate_checker.py

Independent checker for `repair-or-separator/v1` certificates (see
`r21_certificate_format.py` for the schema) emitted by `r21_certificate_
emitter.py` for the rational system `D b = r` that R21
(`rocq/ExactRationalRepairOrSeparator.v`) proves the alternative
`(exists b, Db = r) \\/ (exists y, D^Ty = 0 /\\ y.r = 1)` for.

"Independent" means: this module does not import `r21_repair_or_
separator.py` or `r21_certificate_emitter.py`. It recomputes, from the
caller-supplied `D`/`r` and the certificate's own claimed witness, only
the two equations R21 proves are mutually exclusive and jointly exhaustive:

  - a claimed repair `b` is accepted only if `mat_vec(D, b) == r` exactly;
  - a claimed separator `y` is accepted only if `mat_vec(transpose(D), y)`
    is the all-zero vector AND `dot(y, r) == 1` exactly.

It reuses `rational_linear_algebra.py`'s `mat_vec`/`transpose`/`dot`/
`is_zero` -- shared, already-audited exact-rational primitives every other
checker in this repository reuses rather than reimplementing matrix
multiplication again -- and `r21_certificate_format.py`'s canonical
parsing/digest helpers, which are not solver logic (see that module's
docstring for exactly why sharing them does not weaken independence). It
does NOT reuse `r21_repair_or_separator.repair_or_separate`: verifying a
supplied witness never requires solving a linear system, only evaluating
one, and this checker's soundness does not depend on that solver being
correct at all -- a solver bug can only produce a certificate this checker
then rejects, never one it wrongly accepts.

Fail-closed: `check_certificate` starts from `accepted = True` and only
ever calls `.reject(...)`; any exception during parsing -- or any other
unexpected exception, caught at the outer boundary -- is converted to a
rejection, never treated as a pass-through accept or allowed to propagate
as a crash. The `roc-verify` CLI's exit code is 1 unless every check
explicitly passed.

Beyond the two certificate equations, this module also enforces, via
`r21_certificate_format.py`: a closed certificate schema (no fields beyond
the ones the declared `result` allows), rejection of a JSON document with
a duplicate key at any level (rather than silently keeping `json`'s
last-value-wins behaviour), and resource limits on rational-string length
and matrix/vector dimension -- fail-closed mathematical checking is not
the same as resistance to a certificate or input file crafted to exhaust
memory or CPU before any equation is even evaluated.

USAGE (roc-verify):
    python r21_certificate_checker.py input.json output.json
"""

import argparse
from dataclasses import dataclass, field
from fractions import Fraction
from typing import List

from rational_linear_algebra import dot, is_zero, mat_vec, transpose
from r21_certificate_format import (
    CERTIFICATE_KEYS,
    CERTIFICATE_SCHEMA,
    INPUT_KEYS,
    INPUT_SCHEMA,
    RESULT_REPAIR,
    RESULT_SEPARATOR,
    canonical_input_digest,
    parse_matrix,
    parse_vector,
    strict_json_load,
    validate_closed_keys,
    validate_problem_shape,
)


@dataclass
class CheckResult:
    accepted: bool = True
    reasons: List[str] = field(default_factory=list)

    def reject(self, msg: str) -> None:
        self.accepted = False
        self.reasons.append(msg)


def check_certificate(D: List[List[Fraction]], r: List[Fraction], cert: dict) -> CheckResult:
    """Fail-closed: any unexpected exception during verification (e.g. from
    a malformed `D`/`r` the caller supplied directly, bypassing `read_
    input`'s own validation) is caught at the outer boundary and converted
    into a rejection, never allowed to propagate as a crash that a caller
    could mistake for "no verdict" rather than "REJECT"."""
    result = CheckResult()
    try:
        _check_certificate(D, r, cert, result)
    except Exception as e:
        result.reject(f"unexpected error during verification: {e}")
    return result


def _check_certificate(D: List[List[Fraction]], r: List[Fraction], cert: dict, result: CheckResult) -> None:
    if not isinstance(cert, dict):
        result.reject(f"certificate is not a JSON object: {cert!r}")
        return

    if cert.get("schema") != CERTIFICATE_SCHEMA:
        result.reject(f"unrecognized certificate schema: {cert.get('schema')!r}")
        return

    try:
        expected_digest = canonical_input_digest(D, r)
    except Exception as e:
        result.reject(f"could not compute input digest: {e}")
        return

    recorded_digest = cert.get("input_digest")
    if recorded_digest != expected_digest:
        result.reject(
            f"input_digest mismatch: certificate is bound to {recorded_digest!r}, "
            f"but the supplied (D, r) digests to {expected_digest!r} -- this "
            f"certificate does not certify this problem"
        )
        return

    n = len(D[0]) if D else 0
    m = len(D)
    verdict = cert.get("result")

    if verdict == RESULT_REPAIR:
        try:
            validate_closed_keys(cert, CERTIFICATE_KEYS[RESULT_REPAIR], "certificate")
            b = parse_vector(cert.get("repair"))
        except (ValueError, TypeError) as e:
            result.reject(f"malformed repair witness: {e}")
            return
        if len(b) != n:
            result.reject(f"repair witness has length {len(b)}, expected {n}")
            return
        reproduced = mat_vec(D, b)
        if reproduced != r:
            result.reject(f"D b = {reproduced} does not equal r = {r}")
    elif verdict == RESULT_SEPARATOR:
        try:
            validate_closed_keys(cert, CERTIFICATE_KEYS[RESULT_SEPARATOR], "certificate")
            y = parse_vector(cert.get("separator"))
        except (ValueError, TypeError) as e:
            result.reject(f"malformed separator witness: {e}")
            return
        if len(y) != m:
            result.reject(f"separator witness has length {len(y)}, expected {m}")
            return
        dty = mat_vec(transpose(D), y)
        if not is_zero(dty):
            result.reject(f"D^T y = {dty} is not the zero vector")
        pairing = dot(y, r)
        if pairing != 1:
            result.reject(f"y.r = {pairing}, expected exactly 1")
    else:
        result.reject(f"unrecognized result: {verdict!r}")


def read_input(path: str):
    doc = strict_json_load(path)
    if not isinstance(doc, dict) or doc.get("schema") != INPUT_SCHEMA:
        raise ValueError(f"unrecognized input schema: {doc.get('schema') if isinstance(doc, dict) else doc!r}")
    validate_closed_keys(doc, INPUT_KEYS, "input file")
    D = parse_matrix(doc["D"])
    r = parse_vector(doc["r"])
    validate_problem_shape(D, r)
    return D, r


def check_files(input_path: str, certificate_path: str) -> CheckResult:
    try:
        D, r = read_input(input_path)
    except Exception as e:
        result = CheckResult()
        result.reject(f"malformed input file: {e}")
        return result
    try:
        cert = strict_json_load(certificate_path)
    except Exception as e:
        result = CheckResult()
        result.reject(f"malformed certificate file: {e}")
        return result
    return check_certificate(D, r, cert)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="path to the roc-input/v1 JSON file (D, r) this certificate is claimed to certify")
    parser.add_argument("certificate", help="path to a repair-or-separator/v1 certificate JSON file")
    args = parser.parse_args()

    result = check_files(args.input, args.certificate)
    if result.accepted:
        print(f"ACCEPT: {args.certificate}")
    else:
        print(f"REJECT: {args.certificate}")
        for reason in result.reasons:
            print(f"  - {reason}")
    raise SystemExit(0 if result.accepted else 1)


if __name__ == "__main__":
    main()
