#!/usr/bin/env python3
"""
r21_certificate_format.py

Shared, solver-independent primitives for R21 (`rocq/ExactRationalRepairOrSeparator.v`)
certificates: the public schema tag, strict canonical-rational parsing (the
same discipline `first_order_certificate_checker.py` already uses -- see
that module's docstring for why decimal notation is rejected), and a
canonical digest binding a certificate to the exact `(D, r)` it certifies.

This module is imported by both `r21_certificate_emitter.py` (the untrusted
generator side) and `r21_certificate_checker.py` (the independent verifier
side). That is a deliberate, narrow exception to the "checker imports
nothing from the generator" rule `first_order_certificate_checker.py`
documents: canonical serialisation and hashing is not solver logic --
recomputing `Db` or `D^Ty` never touches this module -- it is the same kind
of shared, generic, already-audited primitive `rational_linear_algebra.py`
already is for every checker in this repository. A bug here could at worst
cause a digest mismatch (a false REJECT), never a false ACCEPT of an
unsound repair or separator, because the math check (`r21_certificate_
checker.check_certificate`) verifies `Db = r` or `D^Ty = 0 /\\ y.r = 1`
directly against the caller-supplied `D`, `r`, independently of anything
this module computes.

Certificate schema (`repair-or-separator/v1`):

    {
      "schema": "repair-or-separator/v1",
      "input_digest": "sha256:<hex>",
      "result": "repair" | "separator",
      "repair": [<rational strings>, length n]        -- iff result == "repair"
      "separator": [<rational strings>, length m]      -- iff result == "separator"
    }

Input problem file (`roc-input/v1`), consumed by both `roc-solve` and
`roc-verify`:

    {
      "schema": "roc-input/v1",
      "D": [[<rational strings>, ...], ...]  -- m rows, n columns
      "r": [<rational strings>, ...]         -- length m
    }
"""

import hashlib
import json
import os
import re
from fractions import Fraction
from typing import List

CERTIFICATE_SCHEMA = "repair-or-separator/v1"
INPUT_SCHEMA = "roc-input/v1"

RESULT_REPAIR = "repair"
RESULT_SEPARATOR = "separator"

INPUT_KEYS = frozenset({"schema", "D", "r"})
CERTIFICATE_KEYS = {
    RESULT_REPAIR: frozenset({"schema", "input_digest", "result", "repair"}),
    RESULT_SEPARATOR: frozenset({"schema", "input_digest", "result", "separator"}),
}

# Resource limits, independent of mathematical soundness: fail-closed
# checking of the certificate equations does not by itself protect against
# a certificate or input file crafted to exhaust memory or CPU before any
# equation is even evaluated (e.g. a gigabyte-scale numerator, or a matrix
# with millions of declared rows).
#
# MAX_RATIONAL_CHARS is deliberately small enough to need no special
# configuration on either verifier: CPython's own `int(str)` conversion
# refuses strings over `sys.get_int_max_str_digits()` (4300 by default,
# a CVE-2020-10735 mitigation) regardless of what this module claims, so
# a limit anywhere above that would be fiction on the Python side even
# though Zarith's GMP-backed parser on the OCaml side has no comparable
# ceiling -- exactly the cross-language disagreement an earlier revision
# of this module had at MAX_RATIONAL_CHARS = 100_000. 1,000 characters is
# comfortably under 4300 (no `sys.set_int_max_str_digits` call needed),
# and is already far more digits than any coefficient this repository's
# own examples, or any plausible finite rational system, would use.
#
# MAX_TOTAL_ENTRIES bounds total declared scalars (rows * columns for a
# matrix), independently of MAX_DIMENSION: 10,000 rows and 10,000 columns
# are each individually under MAX_DIMENSION, but their product is 100
# million entries -- MAX_DIMENSION alone does not prevent that.
#
# MAX_INPUT_BYTES bounds the raw file size, checked via check_file_size
# before the file is even opened for JSON parsing, so a request cannot
# force a large read/parse purely by declaring a huge file.
MAX_RATIONAL_CHARS = 1_000
MAX_DIMENSION = 10_000
MAX_TOTAL_ENTRIES = 1_000_000
MAX_INPUT_BYTES = 10 * 1024 * 1024

_RATIONAL_RE = re.compile(r"^-?[0-9]+(/[0-9]+)?$")


def check_file_size(path: str) -> None:
    """Resource limit, checked before any parsing is attempted at all."""
    size = os.path.getsize(path)
    if size > MAX_INPUT_BYTES:
        raise ValueError(f"file {path!r} is {size} bytes, exceeding MAX_INPUT_BYTES={MAX_INPUT_BYTES}")


def parse_rational(s) -> Fraction:
    """Strict canonical exact-rational parser: only `-?digits` or
    `-?digits/digits`, ASCII digits only (`[0-9]`, not `\\d`, which is
    Unicode-aware and would otherwise accept e.g. Arabic-indic or
    fullwidth digit characters that `ocaml/r21_format.ml`'s hand-written,
    ASCII-only parser rejects -- a real cross-language disagreement an
    earlier revision of this module had). Raises ValueError on anything
    else, including decimal notation, a string longer than
    `MAX_RATIONAL_CHARS` (a resource limit, not a soundness check -- see
    module header), a zero denominator (which the regex alone does not
    exclude, since `[0-9]+` permits `0`), and -- the canonicality check --
    any syntactically valid rational string that is not already in its
    own reduced, positive-denominator, no-leading-zero form: `"03"`,
    `"6/2"`, `"3/1"`, `"02/10"`, `"1/05"`, and `"-0"` are all exact
    rational values, but none is the canonical string this schema
    requires, since `str(Fraction(...))` never produces any of them (an
    earlier revision of this module accepted all of these, silently
    weakening the "canonical" the schema name and this docstring both
    already claimed)."""
    if not isinstance(s, str):
        raise ValueError(f"not a canonical exact-rational string: {s!r}")
    if len(s) > MAX_RATIONAL_CHARS:
        raise ValueError(f"rational string exceeds {MAX_RATIONAL_CHARS} characters")
    if not _RATIONAL_RE.match(s):
        raise ValueError(f"not a canonical exact-rational string: {s!r}")
    if "/" in s and s.split("/", 1)[1].lstrip("0") == "":
        raise ValueError(f"zero denominator: {s!r}")
    value = Fraction(s)
    canonical = str(value)
    if s != canonical:
        raise ValueError(f"non-canonical rational representation: {s!r} (canonical form is {canonical!r})")
    return value


def parse_vector(xs) -> List[Fraction]:
    if not isinstance(xs, list):
        raise ValueError(f"expected a list of rationals, got {xs!r}")
    if len(xs) > MAX_DIMENSION:
        raise ValueError(f"vector length {len(xs)} exceeds MAX_DIMENSION={MAX_DIMENSION}")
    if len(xs) > MAX_TOTAL_ENTRIES:
        raise ValueError(f"vector length {len(xs)} exceeds MAX_TOTAL_ENTRIES={MAX_TOTAL_ENTRIES}")
    return [parse_rational(x) for x in xs]


def parse_matrix(rows) -> List[List[Fraction]]:
    if not isinstance(rows, list):
        raise ValueError(f"expected a matrix (list of rows), got {rows!r}")
    if len(rows) > MAX_DIMENSION:
        raise ValueError(f"row count {len(rows)} exceeds MAX_DIMENSION={MAX_DIMENSION}")
    parsed = [parse_vector(row) for row in rows]
    if parsed:
        n = len(parsed[0])
        if any(len(row) != n for row in parsed):
            raise ValueError("matrix is not rectangular: rows have differing lengths")
        if n > MAX_DIMENSION:
            raise ValueError(f"column count {n} exceeds MAX_DIMENSION={MAX_DIMENSION}")
        total = len(parsed) * n
        if total > MAX_TOTAL_ENTRIES:
            raise ValueError(f"matrix has {total} total entries, exceeding MAX_TOTAL_ENTRIES={MAX_TOTAL_ENTRIES}")
    return parsed


def validate_problem_shape(D: List[List[Fraction]], r: List[Fraction]) -> None:
    """Checks `r`'s length matches `D`'s row count. `parse_matrix` already
    enforces rectangularity across `D`'s own rows; this is the analogous
    check binding `r` to `D`, so a malformed problem is rejected at input
    time rather than surfacing as a confusing later failure (e.g. `dot`'s
    `zip` silently truncating to the shorter of two mismatched-length
    vectors instead of raising)."""
    if len(r) != len(D):
        raise ValueError(f"D has {len(D)} rows but r has length {len(r)}")


def reject_duplicate_keys(pairs):
    """`object_pairs_hook` for `json.load`: raises on a duplicate key at any
    level, rather than silently keeping the last value the way plain
    `json.loads` does -- a JSON document with a repeated key is not
    canonical input for a certificate format that must bind unambiguously
    to one set of values."""
    seen = set()
    result = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key: {key!r}")
        seen.add(key)
        result[key] = value
    return result


def strict_json_load(path: str):
    """Enforces MAX_INPUT_BYTES before opening the file at all, then parses
    with duplicate-key rejection (see reject_duplicate_keys)."""
    check_file_size(path)
    with open(path, "r") as f:
        return json.load(f, object_pairs_hook=reject_duplicate_keys)


def validate_closed_keys(obj: dict, allowed: frozenset, label: str) -> None:
    extra = set(obj.keys()) - allowed
    if extra:
        raise ValueError(f"{label} has unrecognized field(s): {sorted(extra)}")


def canonical_input_digest(D: List[List[Fraction]], r: List[Fraction]) -> str:
    """Binds a certificate to the exact matrix and residue it certifies, so
    a certificate produced for one problem cannot be attached to another.
    Canonical form: dimensions, then each row's rationals in `str(Fraction)`
    form comma-joined, newline-separated, then the residue -- a fixed,
    unambiguous serialisation of exact values, not of the input JSON's own
    (irrelevant) formatting.
    """
    m = len(D)
    n = len(D[0]) if D else 0
    lines = [f"{m}x{n}"]
    lines.extend(",".join(str(x) for x in row) for row in D)
    lines.append(",".join(str(x) for x in r))
    canonical = "\n".join(lines)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
