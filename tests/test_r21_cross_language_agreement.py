"""
Cross-language agreement for R21's `repair-or-separator/v1` certificate
pipeline: every case below is run through BOTH `r21_certificate_checker.py`
(Python, `roc-verify`) and `ocaml/r21_verifier.ml` (OCaml, `roc-verify-
ocaml`) as separate subprocesses, and both must agree on ACCEPT vs.
REJECT. Any disagreement is a bug in one of the two independent
implementations (or in this shared corpus/specification) and fails this
suite.

Per the instruction that motivated this file, this is NOT the sole check
of correctness -- Python's own acceptance is not treated as the oracle for
whether a case *should* be accepted. Three separate categories, each with
an outcome reasoned independently of either checker's own behaviour:

1. HAND-AUTHORED fixtures (see `_hand_authored_cases`): the D, r, and
   witness are simple enough that `Db = r` or `D^Ty = 0 /\\ y.r = 1` is
   checked directly in a comment next to each one, by hand arithmetic --
   including R1's own four-cycle witness (already independently
   established by the Rocq development) and zero-/minimal-dimensional
   boundary cases.
2. CONSTRUCTED-VALID certificates (see `_constructed_cases`): D and b (or
   D and y) are chosen first, and r is then *defined* as `D @ b` (or
   chosen so `y.r = 1`) via a plain nested-loop computation written
   directly in this file -- not via `rational_linear_algebra.mat_vec` or
   either checker -- so correctness holds by construction, independently
   of what any checker computes.
3. MALFORMED/TAMPERED/RESOURCE-LIMIT cases (see `_negative_cases`): each
   one deliberately breaks exactly one aspect of a known-good case (schema,
   duplicate keys, unknown fields, a changed matrix/residue/witness entry,
   a changed digest, an oversized rational or dimension, a ragged matrix,
   a shape mismatch, a zero denominator, a non-canonical rational, or
   truncated JSON) -- the expected outcome is REJECT by construction, not
   by consulting either checker.

Skips (not fails) the OCaml-side and agreement tests if `roc-verify-ocaml`
has not been built (`make check-r21-ocaml`) -- `make check-all` builds it
before running this suite (see the Makefile's own comment on check-all's
ordering), so a full run never silently skips this coverage; a plain
`pytest`/`make check-python` without an OCaml/opam toolchain still passes.
"""

import json
import os
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

from r21_certificate_format import MAX_DIMENSION, MAX_RATIONAL_CHARS, canonical_input_digest

REPO_ROOT = Path(__file__).resolve().parent.parent
OCAML_BINARY = REPO_ROOT / "roc-verify-ocaml"

# Every subprocess call in this file passes this timeout: a hung checker
# (deadlock, unexpected interactive prompt, runaway parse) must fail the
# test loudly, not hang the suite indefinitely.
SUBPROCESS_TIMEOUT = 30

ocaml_missing = pytest.mark.skipif(
    not os.access(OCAML_BINARY, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)


# --------------------------------------------------------------------------
# Low-level helpers: build input/certificate files, run each checker.
# --------------------------------------------------------------------------

def to_str_matrix(D):
    return [[str(F(x)) for x in row] for row in D]


def to_str_vector(v):
    return [str(F(x)) for x in v]


def write_json_file(path, obj):
    path.write_text(json.dumps(obj))
    return path


def write_input(tmp_path, D, r, name="input.json"):
    return write_json_file(tmp_path / name, {"schema": "roc-input/v1", "D": to_str_matrix(D), "r": to_str_vector(r)})


def make_repair_cert(D, r, b):
    """Builds a certificate directly from a caller-chosen witness `b`,
    without running the untrusted generator (r21_repair_or_separator.py)
    at all -- the point of the constructed/hand-authored categories is
    that the witness is ours, not the generator's."""
    return {
        "schema": "repair-or-separator/v1",
        "input_digest": canonical_input_digest(D, r),
        "result": "repair",
        "repair": to_str_vector(b),
    }


def make_separator_cert(D, r, y):
    return {
        "schema": "repair-or-separator/v1",
        "input_digest": canonical_input_digest(D, r),
        "result": "separator",
        "separator": to_str_vector(y),
    }


def mat_vec_reference(D, b):
    """A from-scratch, independent computation of D @ b -- deliberately
    NOT rational_linear_algebra.mat_vec (which both checkers' own test
    suites already exercise) -- used only to define r for the constructed-
    valid repair cases, so `Db = r` holds by construction."""
    return [sum((D[i][j] * b[j] for j in range(len(b))), F(0)) for i in range(len(D))]


def dot_reference(u, v):
    return sum((a * b for a, b in zip(u, v)), F(0))


def run_python_checker(input_path, cert_path) -> int:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    return result.returncode


def run_ocaml_checker(input_path, cert_path) -> int:
    result = subprocess.run(
        [str(OCAML_BINARY), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    return result.returncode


# --------------------------------------------------------------------------
# 1. Hand-authored mathematical fixtures. Each Db=r or D^Ty=0,y.r=1 claim
#    is checked directly in the comment, not delegated to either checker.
# --------------------------------------------------------------------------

def _case_simple_repair(tmp_path):
    # D = I_2, b = (3,5). Db = (1*3+0*5, 0*3+1*5) = (3,5) = r. Exact.
    D = [[F(1), F(0)], [F(0), F(1)]]
    r = [F(3), F(5)]
    b = [F(3), F(5)]
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_repair_cert(D, r, b))
    return input_path, cert_path


def _case_simple_separator(tmp_path):
    # D = [[1],[1]] (2x1), y = (1,-1), r = (1,0).
    # D^T y: D^T = [[1,1]] (1x2); (D^T y)_0 = 1*1 + 1*(-1) = 0. Zero vector, length 1 (=n). OK.
    # y.r = 1*1 + (-1)*0 = 1. Exact.
    D = [[F(1)], [F(1)]]
    r = [F(1), F(0)]
    y = [F(1), F(-1)]
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_separator_cert(D, r, y))
    return input_path, cert_path


def _case_four_cycle_separator(tmp_path):
    # R1's own canonical witness (RESULTS.md/STATUS.md/README.md): z=(-1,-1,-1,1),
    # pairing c=-5, normalised y = -1/5 z = (1/5,1/5,1/5,-1/5). Independently
    # established by the Rocq development (FourCycleObstruction.v), not
    # computed here.
    D = [[F(-1), F(1), F(0), F(0)], [F(0), F(-1), F(1), F(0)], [F(0), F(0), F(-1), F(1)], [F(-1), F(0), F(0), F(1)]]
    r = [F(1), F(1), F(1), F(-2)]
    y = [F(1, 5), F(1, 5), F(1, 5), F(-1, 5)]
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_separator_cert(D, r, y))
    return input_path, cert_path


def _case_zero_dimensional_repair(tmp_path):
    # D = [] (0x0), r = [], b = []. Db=r holds vacuously: both sides are
    # the empty vector, by definition, no arithmetic needed.
    D, r, b = [], [], []
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_repair_cert(D, r, b))
    return input_path, cert_path


def _case_minimal_dimensional_separator(tmp_path):
    # D = [[],[]] (2 rows, 0 columns -- m=2, n=0), r = (5,3), y = (1/5, 0).
    # D^T y: D^T has n=0 rows, so it is the empty vector -- "the zero
    # vector of length 0" holds vacuously, for ANY y, since there are no
    # columns of D to fail to annihilate.
    # y.r = (1/5)*5 + 0*3 = 1. Exact.
    D = [[], []]
    r = [F(5), F(3)]
    y = [F(1, 5), F(0)]
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_separator_cert(D, r, y))
    return input_path, cert_path


# --------------------------------------------------------------------------
# 2. Constructed-valid certificates: D and the witness are chosen first;
#    r is DEFINED from them via mat_vec_reference/dot_reference, an
#    independent computation, not either checker's own code path.
# --------------------------------------------------------------------------

def _case_constructed_repair(tmp_path):
    D = [[F(2), F(1)], [F(0), F(3)], [F(1), F(1)]]
    b = [F(1), F(2)]
    r = mat_vec_reference(D, b)  # = [4, 6, 3], defined, not asserted
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_repair_cert(D, r, b))
    return input_path, cert_path


def _case_constructed_separator(tmp_path):
    # y = (1,1,-1). Columns of D chosen so each column dots to 0 with y:
    # col0=(1,2,3): 1+2-3=0. col1=(2,0,2): 2+0-2=0. So D^T y = 0 by
    # construction (verified by the arithmetic in this comment).
    D = [[F(1), F(2)], [F(2), F(0)], [F(3), F(2)]]
    y = [F(1), F(1), F(-1)]
    r = [F(1), F(0), F(0)]
    assert dot_reference(y, r) == F(1)  # y.r = 1*1+1*0+(-1)*0 = 1, by construction
    input_path = write_input(tmp_path, D, r)
    cert_path = write_json_file(tmp_path / "cert.json", make_separator_cert(D, r, y))
    return input_path, cert_path


# --------------------------------------------------------------------------
# 3. Malformed / tampered / resource-limit cases: each breaks exactly one
#    thing relative to a known-good base case. Expected = reject, by
#    construction (we are the ones breaking it), not by consulting either
#    checker.
# --------------------------------------------------------------------------

_BASE_D = [[F(1), F(0)], [F(0), F(1)]]
_BASE_R = [F(3), F(5)]
_BASE_B = [F(3), F(5)]


def _base_input_and_cert(tmp_path):
    input_path = write_input(tmp_path, _BASE_D, _BASE_R)
    cert_path = write_json_file(tmp_path / "cert.json", make_repair_cert(_BASE_D, _BASE_R, _BASE_B))
    return input_path, cert_path


def _case_malformed_schema(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["schema"] = "something-else/v1"
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _case_duplicate_keys_input(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text('{"schema": "roc-input/v1", "D": [["1","0"],["0","1"]], "r": ["3","5"], "r": ["9","9"]}')
    cert_path = write_json_file(tmp_path / "cert.json", make_repair_cert(_BASE_D, _BASE_R, _BASE_B))
    return input_path, cert_path


def _case_duplicate_keys_certificate(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    digest = canonical_input_digest(_BASE_D, _BASE_R)
    cert_path.write_text(
        '{"schema": "repair-or-separator/v1", "input_digest": "' + digest + '", '
        '"result": "repair", "repair": ["3","5"], "result": "separator"}'
    )
    return input_path, cert_path


def _case_unknown_field(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["extra"] = "unexpected"
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _case_changed_matrix_entry(tmp_path):
    _, cert_path = _base_input_and_cert(tmp_path)
    mutated_D = [[F(1), F(0)], [F(0), F(7)]]
    input_path = write_input(tmp_path, mutated_D, _BASE_R)
    return input_path, cert_path


def _case_changed_residue_entry(tmp_path):
    _, cert_path = _base_input_and_cert(tmp_path)
    mutated_r = [F(3), F(9)]
    input_path = write_input(tmp_path, _BASE_D, mutated_r)
    return input_path, cert_path


def _case_changed_witness(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["repair"][0] = "999"
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _case_changed_digest(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["input_digest"] = "sha256:" + "0" * 64
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _case_oversized_rational(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["repair"][0] = "1" * (MAX_RATIONAL_CHARS + 1)
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _dummy_cert_path(tmp_path):
    return write_json_file(
        tmp_path / "cert.json",
        {"schema": "repair-or-separator/v1", "input_digest": "sha256:" + "0" * 64, "result": "repair", "repair": []},
    )


def _case_oversized_dimension(tmp_path):
    input_path = write_json_file(
        tmp_path / "input.json",
        {"schema": "roc-input/v1", "D": [], "r": [str(i) for i in range(MAX_DIMENSION + 1)]},
    )
    cert_path = _dummy_cert_path(tmp_path)
    return input_path, cert_path


def _case_ragged_matrix(tmp_path):
    input_path = write_json_file(
        tmp_path / "input.json",
        {"schema": "roc-input/v1", "D": [["1", "0"], ["0", "1", "2"]], "r": ["3", "5"]},
    )
    cert_path = _dummy_cert_path(tmp_path)
    return input_path, cert_path


def _case_shape_mismatch(tmp_path):
    input_path = write_json_file(
        tmp_path / "input.json",
        {"schema": "roc-input/v1", "D": [["1", "0"], ["0", "1"]], "r": ["3", "5", "7"]},
    )
    cert_path = _dummy_cert_path(tmp_path)
    return input_path, cert_path


def _case_denominator_zero(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["repair"][0] = "3/0"
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _case_noncanonical_rational(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert = json.loads(cert_path.read_text())
    cert["repair"][0] = "1.5"
    write_json_file(cert_path, cert)
    return input_path, cert_path


def _case_truncated_json_certificate(tmp_path):
    input_path, cert_path = _base_input_and_cert(tmp_path)
    cert_path.write_text('{"schema": "repair-or-separator/v1", "result": "rep')
    return input_path, cert_path


def _case_truncated_json_input(tmp_path):
    input_path = tmp_path / "input.json"
    input_path.write_text('{"schema": "roc-input/v1", "D": [["1"')
    cert_path = _dummy_cert_path(tmp_path)
    return input_path, cert_path


def _noncanonical_case(value):
    """Builds a case mutating the base certificate's witness to a
    syntactically valid but non-canonical rational representation --
    each of these is an exact value equal to a value the schema already
    accepts, but not in the one canonical string form `str(Fraction(...))`
    (Python) / `q_to_canonical_string` (OCaml) would produce for it."""
    def build(tmp_path):
        input_path, cert_path = _base_input_and_cert(tmp_path)
        cert = json.loads(cert_path.read_text())
        cert["repair"][0] = value
        write_json_file(cert_path, cert)
        return input_path, cert_path
    return build


def _case_oversized_total_entries(tmp_path):
    # 1001 x 1000 = 1,001,000 entries, exceeding MAX_TOTAL_ENTRIES (1,000,000)
    # while each dimension (1001, 1000) individually stays under
    # MAX_DIMENSION (10,000) -- isolates the total-entry-count limit from
    # the per-dimension one.
    rows = [["1"] * 1000 for _ in range(1001)]
    input_path = write_json_file(tmp_path / "input.json", {"schema": "roc-input/v1", "D": rows, "r": ["0"]})
    cert_path = _dummy_cert_path(tmp_path)
    return input_path, cert_path


def _case_oversized_file_size(tmp_path):
    # ~11,000 legitimately-sized (999-char, under MAX_RATIONAL_CHARS=1000)
    # entries: roughly 11 MB of raw JSON bytes, exceeding MAX_INPUT_BYTES
    # (10 MB), checked before the file is even parsed as JSON -- so this
    # fires regardless of what MAX_DIMENSION/MAX_TOTAL_ENTRIES would
    # separately say about 11,000 entries in one vector.
    big_number = "9" * 999
    input_path = write_json_file(
        tmp_path / "input.json", {"schema": "roc-input/v1", "D": [], "r": [big_number] * 11_000}
    )
    cert_path = _dummy_cert_path(tmp_path)
    return input_path, cert_path


# --------------------------------------------------------------------------
# The full corpus.
# --------------------------------------------------------------------------

CASES = [
    ("simple_repair", _case_simple_repair, "accept"),
    ("simple_separator", _case_simple_separator, "accept"),
    ("four_cycle_separator", _case_four_cycle_separator, "accept"),
    ("zero_dimensional_repair", _case_zero_dimensional_repair, "accept"),
    ("minimal_dimensional_separator", _case_minimal_dimensional_separator, "accept"),
    ("constructed_repair", _case_constructed_repair, "accept"),
    ("constructed_separator", _case_constructed_separator, "accept"),
    ("malformed_schema", _case_malformed_schema, "reject"),
    ("duplicate_keys_input", _case_duplicate_keys_input, "reject"),
    ("duplicate_keys_certificate", _case_duplicate_keys_certificate, "reject"),
    ("unknown_field", _case_unknown_field, "reject"),
    ("changed_matrix_entry", _case_changed_matrix_entry, "reject"),
    ("changed_residue_entry", _case_changed_residue_entry, "reject"),
    ("changed_witness", _case_changed_witness, "reject"),
    ("changed_digest", _case_changed_digest, "reject"),
    ("oversized_rational", _case_oversized_rational, "reject"),
    ("oversized_dimension", _case_oversized_dimension, "reject"),
    ("ragged_matrix", _case_ragged_matrix, "reject"),
    ("shape_mismatch", _case_shape_mismatch, "reject"),
    ("denominator_zero", _case_denominator_zero, "reject"),
    ("noncanonical_rational", _case_noncanonical_rational, "reject"),
    ("truncated_json_certificate", _case_truncated_json_certificate, "reject"),
    ("truncated_json_input", _case_truncated_json_input, "reject"),
    ("noncanonical_leading_zero", _noncanonical_case("03"), "reject"),
    ("noncanonical_unreduced_fraction", _noncanonical_case("6/2"), "reject"),
    ("noncanonical_denominator_one", _noncanonical_case("3/1"), "reject"),
    ("noncanonical_denominator_leading_zero", _noncanonical_case("1/05"), "reject"),
    ("noncanonical_negative_zero", _noncanonical_case("-0"), "reject"),
    ("unicode_arabic_indic_digits", _noncanonical_case("١/٢"), "reject"),
    ("unicode_fullwidth_digits", _noncanonical_case("１２/３"), "reject"),
    ("oversized_total_entries", _case_oversized_total_entries, "reject"),
    ("oversized_file_size", _case_oversized_file_size, "reject"),
]

CASE_IDS = [name for name, _, _ in CASES]


@pytest.mark.parametrize("name,build,expected", CASES, ids=CASE_IDS)
def test_python_checker_verdict(name, build, expected, tmp_path):
    input_path, cert_path = build(tmp_path)
    rc = run_python_checker(input_path, cert_path)
    assert (rc == 0) == (expected == "accept"), f"{name}: python exit={rc}, expected {expected}"


@ocaml_missing
@pytest.mark.parametrize("name,build,expected", CASES, ids=CASE_IDS)
def test_ocaml_checker_verdict(name, build, expected, tmp_path):
    input_path, cert_path = build(tmp_path)
    rc = run_ocaml_checker(input_path, cert_path)
    assert (rc == 0) == (expected == "accept"), f"{name}: ocaml exit={rc}, expected {expected}"


@ocaml_missing
@pytest.mark.parametrize("name,build,expected", CASES, ids=CASE_IDS)
def test_cross_language_agreement(name, build, expected, tmp_path):
    input_path, cert_path = build(tmp_path)
    py_rc = run_python_checker(input_path, cert_path)
    oc_rc = run_ocaml_checker(input_path, cert_path)
    assert (py_rc == 0) == (oc_rc == 0), f"{name}: DISAGREEMENT -- python exit={py_rc}, ocaml exit={oc_rc}"
