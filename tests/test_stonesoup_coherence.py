"""
Step 10C of the tracking-adapter implementation order: evaluates Stone
Soup tracking coherence -- the SAME deterministic Stone Soup track
evidence under two declared transformation policies, `coherent` and
`canonical_obstruction`, proving the applied claim precisely:

    Identical deterministic Stone Soup track evidence can yield either a
    repairable or obstructed comparison system depending on whether the
    declared pairwise transformation family is globally coherent. The
    obstruction is derived from those transformations and independently
    certified, not assigned as an expected verdict.

Stone Soup did not produce an obstruction -- it produced the tracks. The
adapter analysed the structural coherence of the declared comparisons
among them. Neither claim is conflated with the other anywhere in this
file: every assertion about `r`, `b`, or `y` compares an INDEPENDENTLY
RECONSTRUCTED value against an expectation, never inserts one directly
into a snapshot.

Skips (not fails) if Stone Soup is not installed, matching every other
Stone-Soup-dependent test file in this repository.
"""

import importlib.util
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
OCAML_CHECKER = REPO_ROOT / "roc-verify-ocaml"
SUBPROCESS_TIMEOUT = 60

stonesoup_missing = pytest.mark.skipif(
    importlib.util.find_spec("stonesoup") is None,
    reason="stonesoup not installed; pip install -r requirements-stonesoup.txt first",
)
ocaml_missing = pytest.mark.skipif(
    not os.access(OCAML_CHECKER, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)


def _run_emitter(policy: str, output_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_stonesoup_emitter.py"),
         "--output", str(output_path), "--policy", policy],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _run_verify(snapshot_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(snapshot_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_emit_cert(snapshot_path: Path, cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"), "emit",
         str(snapshot_path), "--output", str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_r21_emitter(roc_input_path: Path, r21_cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(roc_input_path),
         "--certificate", str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_python_checker(roc_input_path: Path, r21_cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(roc_input_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_ocaml_checker(roc_input_path: Path, r21_cert_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(OCAML_CHECKER), str(roc_input_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _full_pipeline(tmp_dir: Path, tag: str, policy: str) -> dict:
    snapshot_path = tmp_dir / f"{tag}_snapshot.json"
    cert_path = tmp_dir / f"{tag}_certificate.json"
    roc_input_path = tmp_dir / f"{tag}_roc_input.json"
    r21_cert_path = tmp_dir / f"{tag}_r21_certificate.json"

    _run_emitter(policy, snapshot_path)
    doc = json.loads(snapshot_path.read_text())

    verify_result = _run_verify(snapshot_path)
    assert verify_result.returncode == 0, verify_result.stdout + verify_result.stderr

    emit_result = _run_emit_cert(snapshot_path, cert_path)
    assert emit_result.returncode == 0, emit_result.stdout + emit_result.stderr
    cert = json.loads(cert_path.read_text())

    roc_input_path.write_text(json.dumps(cert["roc_input"]))
    r21_result = _run_r21_emitter(roc_input_path, r21_cert_path)
    assert r21_result.returncode == 0, r21_result.stdout + r21_result.stderr
    r21_cert = json.loads(r21_cert_path.read_text())

    py_check = _run_python_checker(roc_input_path, r21_cert_path)
    assert py_check.returncode == 0, py_check.stdout + py_check.stderr

    return {
        "doc": doc, "cert": cert, "r21_cert": r21_cert,
        "snapshot_path": snapshot_path, "roc_input_path": roc_input_path, "r21_cert_path": r21_cert_path,
    }


@pytest.fixture(scope="module")
def both_policies(tmp_path_factory):
    if importlib.util.find_spec("stonesoup") is None:
        pytest.skip("stonesoup not installed; pip install -r requirements-stonesoup.txt first")
    tmp_dir = tmp_path_factory.mktemp("coherence")
    coherent = _full_pipeline(tmp_dir, "coherent", "coherent")
    obstructed = _full_pipeline(tmp_dir, "obstructed", "canonical_obstruction")
    return coherent, obstructed


# --- 1. Stone Soup evidence portions are identical -----------------------

@stonesoup_missing
def test_shared_stonesoup_evidence_is_identical(both_policies):
    coherent, obstructed = both_policies
    assert coherent["doc"]["sources"] == obstructed["doc"]["sources"]
    assert coherent["doc"]["detections"] == obstructed["doc"]["detections"]
    assert coherent["doc"]["tracks"] == obstructed["doc"]["tracks"]
    assert coherent["doc"]["evaluation_timestamp_utc"] == obstructed["doc"]["evaluation_timestamp_utc"]
    for t in coherent["doc"]["tracks"]:
        assert t["ancestry"]
    assert coherent["doc"]["tracks"][0]["ancestry"] == obstructed["doc"]["tracks"][0]["ancestry"]

    # Only these differ.
    assert coherent["doc"]["scenario_id"] != obstructed["doc"]["scenario_id"]
    assert coherent["doc"]["transformations"] != obstructed["doc"]["transformations"]
    assert coherent["doc"]["comparison_edges"] != obstructed["doc"]["comparison_edges"]
    assert coherent["doc"]["derived_problem"] == obstructed["doc"]["derived_problem"] == {"D": [], "r": []}
    assert coherent["doc"]["payload_digest"] != obstructed["doc"]["payload_digest"]


# --- 2. Every transformation is individually well formed ------------------

@stonesoup_missing
def test_every_transformation_is_well_formed(both_policies):
    from tracking_adapter_format import parse_transformation

    coherent, obstructed = both_policies
    for doc in (coherent["doc"], obstructed["doc"]):
        for xf in doc["transformations"]:
            parsed = parse_transformation(xf)
            assert parsed.kind == "additive_offset"


# --- 3-4. Coherent case: existing repairable (D, r), valid witness in the
#          correct gauge class (NOT byte-exact -- ker(D) is 1-dimensional) --

@stonesoup_missing
def test_coherent_case_derives_existing_repairable_D_r(both_policies):
    coherent, _ = both_policies
    assert coherent["cert"]["D"] == [
        ["-1", "1", "0", "0"], ["0", "-1", "1", "0"], ["0", "0", "-1", "1"], ["-1", "0", "0", "1"],
    ]
    assert coherent["cert"]["r"] == ["1", "2", "-1", "2"]
    # Matches examples/tracking_adapter/repairable_*.json's own (D, r) --
    # an independent cross-check, not merely internal self-consistency.
    tracked = json.loads((REPO_ROOT / "examples" / "tracking_adapter" / "repairable_roc_input.json").read_text())
    assert coherent["cert"]["roc_input"]["D"] == tracked["D"]
    assert coherent["cert"]["roc_input"]["r"] == tracked["r"]


@stonesoup_missing
def test_coherent_case_r21_witness_valid_and_in_expected_gauge_class(both_policies):
    coherent, _ = both_policies
    assert coherent["r21_cert"]["result"] == "repair"
    b = [Fraction(s) for s in coherent["r21_cert"]["repair"]]
    D = [[Fraction(x) for x in row] for row in coherent["cert"]["D"]]
    r = [Fraction(x) for x in coherent["cert"]["r"]]
    reproduced = [sum(D[i][j] * b[j] for j in range(4)) for i in range(4)]
    assert reproduced == r  # Db = r, the only thing "valid witness" requires

    # Gauge class: differs from the ALREADY-KNOWN R21 witness for this
    # exact D/r (examples/tracking_adapter/repairable_r21_certificate.json,
    # (-2,-1,1,0)) by a multiple of the all-ones vector, or is identical
    # to it -- either is a valid member of the same coset, never asserted
    # byte-exact independent of that relationship.
    known = [Fraction(s) for s in
             json.loads((REPO_ROOT / "examples" / "tracking_adapter" / "repairable_r21_certificate.json")
                        .read_text())["repair"]]
    diff = [a - k for a, k in zip(b, known)]
    assert len(set(diff)) == 1  # all four components equal -- a multiple of (1,1,1,1)


# --- 5-7. Obstructed case: independently derives r=(1,1,1,-2),
#          y=(1/5,1/5,1/5,-1/5), D^Ty=0, y.r=1 -------------------------

@stonesoup_missing
def test_obstructed_case_independently_derives_canonical_residue(both_policies):
    _, obstructed = both_policies
    assert obstructed["cert"]["r"] == ["1", "1", "1", "-2"]


@stonesoup_missing
def test_obstructed_case_r21_emits_canonical_separator(both_policies):
    _, obstructed = both_policies
    assert obstructed["r21_cert"]["result"] == "separator"
    assert obstructed["r21_cert"]["separator"] == ["1/5", "1/5", "1/5", "-1/5"]


@stonesoup_missing
def test_obstructed_case_separator_satisfies_its_defining_equations(both_policies):
    _, obstructed = both_policies
    D = [[Fraction(x) for x in row] for row in obstructed["cert"]["D"]]
    r = [Fraction(x) for x in obstructed["cert"]["r"]]
    y = [Fraction(s) for s in obstructed["r21_cert"]["separator"]]
    DT_y = [sum(D[row][col] * y[row] for row in range(4)) for col in range(4)]
    assert DT_y == [Fraction(0)] * 4
    assert sum(a * b for a, b in zip(y, r)) == Fraction(1)


# --- 8-9. Both adapter certificates verify; both complete chains verify --

@stonesoup_missing
def test_both_adapter_certificates_and_chains_verify(both_policies):
    from tracking_adapter_certificate import verify_chain

    coherent, obstructed = both_policies
    for run in (coherent, obstructed):
        chain = verify_chain(run["doc"], run["cert"], run["r21_cert"])
        assert chain.accepted, chain.reasons


# --- 10. Both R21 checkers accept -----------------------------------------

@stonesoup_missing
@ocaml_missing
def test_both_r21_checkers_accept_both_policies(both_policies):
    coherent, obstructed = both_policies
    for run in (coherent, obstructed):
        result = _run_ocaml_checker(run["roc_input_path"], run["r21_cert_path"])
        assert result.returncode == 0, result.stdout + result.stderr


# --- 11. Both policies are deterministic across fresh subprocesses -------

@stonesoup_missing
@pytest.mark.parametrize("policy", ["coherent", "canonical_obstruction"])
def test_policy_is_deterministic_across_fresh_subprocesses(tmp_path, policy):
    run_a = _full_pipeline(tmp_path, f"{policy}_a", policy)
    run_b = _full_pipeline(tmp_path, f"{policy}_b", policy)
    assert run_a["doc"] == run_b["doc"]
    assert run_a["cert"] == run_b["cert"]
    assert run_a["r21_cert"] == run_b["r21_cert"]


# --- 12. A certificate from either policy is rejected against the other --

@stonesoup_missing
def test_certificate_from_one_policy_rejected_against_the_other_snapshot(both_policies):
    from tracking_adapter_certificate import verify_chain

    coherent, obstructed = both_policies

    cross_1 = verify_chain(obstructed["doc"], coherent["cert"], coherent["r21_cert"])
    assert not cross_1.accepted
    assert any("snapshot_payload_digest" in msg for msg in cross_1.reasons)

    cross_2 = verify_chain(coherent["doc"], obstructed["cert"], obstructed["r21_cert"])
    assert not cross_2.accepted
    assert any("snapshot_payload_digest" in msg for msg in cross_2.reasons)
