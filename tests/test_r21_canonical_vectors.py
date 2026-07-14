"""
Canonical-digest test vectors for R21's `repair-or-separator/v1`
certificate format: `tests/r21_canonical_vectors.json` is a small,
frozen, checked-in fixture -- each entry is `{name, input, canonical,
digest}`, where `canonical` is the exact expected canonical byte string
and `digest` is its SHA-256, both computed independently of either
checker implementation (see the generation note below), covering
negative rationals, zero normalisation, denominators, row order, column
order, empty collections, multi-digit dimensions, and large integers near
the configured resource limits.

This is a stronger check than asking whether the two checkers happen to
agree with each other: both `r21_certificate_format.canonical_input_
digest` (Python) and `roc-verify-ocaml --digest` (OCaml) are tested
against the SAME frozen third value, not against each other's live
output. A bug shared by both implementations (e.g. both getting the
canonicalisation rule itself wrong in the same way) would not be caught
by cross-language agreement alone, but would be caught here, since the
vectors were generated with a from-scratch reimplementation of the
canonicalisation rule (`fractions.Fraction` and `hashlib.sha256` called
directly, not through `canonical_input_digest`) -- see the generation
script's own comment in this file's git history / the fixture's
provenance note below.

Generation method (for reproducibility, not re-run automatically): a
one-off script built each `canonical` string directly from the documented
rule ("MxN", newline, each D row's Fraction-reduced entries comma-joined,
newline-separated, newline, r's entries comma-joined -- no trailing
newline) and hashed it with `hashlib.sha256(canonical.encode()).hexdigest()`
directly, never calling `canonical_input_digest` itself.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

from r21_certificate_format import canonical_input_digest, parse_matrix, parse_vector

REPO_ROOT = Path(__file__).resolve().parent.parent
VECTORS_PATH = Path(__file__).resolve().parent / "r21_canonical_vectors.json"
OCAML_BINARY = REPO_ROOT / "roc-verify-ocaml"

with open(VECTORS_PATH) as f:
    VECTORS = json.load(f)

ocaml_missing = pytest.mark.skipif(
    not os.access(OCAML_BINARY, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)

# A hung checker must fail the test loudly, not hang the suite indefinitely.
SUBPROCESS_TIMEOUT = 30


@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_python_digest_matches_frozen_vector(vector):
    D = parse_matrix(vector["input"]["D"])
    r = parse_vector(vector["input"]["r"])
    assert canonical_input_digest(D, r) == vector["digest"]


@ocaml_missing
@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_ocaml_digest_matches_frozen_vector(vector, tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(vector["input"]))
    result = subprocess.run(
        [str(OCAML_BINARY), "--digest", str(input_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == vector["digest"]


def test_row_order_changes_the_digest():
    """row_order_a and row_order_b_swapped are the same values in
    different row order -- confirms the digest is sensitive to row order,
    not just to the multiset of entries."""
    a = next(v for v in VECTORS if v["name"] == "row_order_a")
    b = next(v for v in VECTORS if v["name"] == "row_order_b_swapped")
    assert a["digest"] != b["digest"]
