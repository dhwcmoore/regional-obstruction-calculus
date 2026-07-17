"""
Step 10E.2 of the tracking-adapter implementation order
(docs/design/STONESOUP_TRACK_FUSION_EVALUATOR_SPEC.md): end-to-end
adapter integration test for `tracking_adapter_stonesoup_trackfusion_
emitter.py` -- runs the complete chain (snapshot -> independent
verification -> adapter certificate -> real R21 emitter -> both real
R21 checkers -> complete chain verification) for both the `natural`
(identity transformation) and `artificial_perturbation` (labelled,
evaluator-imposed nonzero offset on one track) policies, matching every
prior Stone-Soup-dependent end-to-end test file's own pattern (see
tests/test_stonesoup_coherence.py).

TOPOLOGY (design doc SS9, checked directly below, not merely cited):
two tracks, one declared comparison -- `D = (-1, 1)` is `1x2`,
`rank(D) = 1 = dim(C^1)`, so `D` is surjective and BOTH policies are
NECESSARILY repairable. This file does not test for an obstructed
verdict on this topology, because SS9 shows none is possible here, with
or without the artificial perturbation.

Skips (not fails) if Stone Soup is not installed, matching every other
Stone-Soup-dependent test file in this repository.
"""

import copy
import importlib.util
import json
import os
import re
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
        [sys.executable, str(REPO_ROOT / "tracking_adapter_stonesoup_trackfusion_emitter.py"),
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
    tmp_dir = tmp_path_factory.mktemp("trackfusion")
    natural = _full_pipeline(tmp_dir, "natural", "natural")
    perturbed = _full_pipeline(tmp_dir, "perturbed", "artificial_perturbation")
    return natural, perturbed


# --- topology: rank(D) = 1 = dim(C^1), checked directly, not assumed --------

@stonesoup_missing
def test_D_is_1x2_and_rank_1_so_the_topology_is_necessarily_repairable(both_policies):
    from rational_linear_algebra import nullspace_over_Q

    for run in both_policies:
        D = [[Fraction(x) for x in row] for row in run["cert"]["D"]]
        assert len(D) == 1
        assert len(D[0]) == 2
        n = len(D[0])
        nullspace_basis = nullspace_over_Q(D)
        rank = n - len(nullspace_basis)
        assert rank == 1
        assert rank == len(D)  # dim(C^1) == 1 == rank(D) -- D is surjective, SS9


# --- 1. genuine installed Stone Soup machinery produced non-trivial evidence -

@stonesoup_missing
def test_captured_covariance_is_genuinely_nontrivial(both_policies):
    """A weak but real sanity check that actual Kalman filtering ran (not
    a stand-in): the captured covariance is not literally all zeros --
    tests/test_stonesoup_trackfusion_reconstruction.py already checks the
    installed classes directly; this checks the SPECIFIC evidence this
    module derived a snapshot from is genuine filter output."""
    natural, _ = both_policies
    for detection in natural["doc"]["detections"]:
        flat = [Fraction(x) for row in detection["covariance"] for x in row]
        assert any(v != 0 for v in flat)


# --- 2. local capture occurs before fusion: the fused track is never a ------
#        parent of the declared comparison, and is not part of the snapshot -

@stonesoup_missing
def test_fused_track_is_provenance_only_never_a_comparison_parent(both_policies):
    for run in both_policies:
        doc = run["doc"]
        nodes_by_id = {n["node_id"]: n for n in doc["provenance"]}
        comparison_node = nodes_by_id["comparison:kf1-kf2"]
        assert comparison_node["parent_ids"] == ["track:kf-1", "track:kf-2"]
        assert "fusion:chernoff-fused" not in comparison_node["parent_ids"]
        # The fusion node exists (a complete, honest ancestry graph, design
        # doc SS7), but is downstream of the tracks, never upstream of the
        # comparison.
        fusion_node = nodes_by_id["fusion:chernoff-fused"]
        assert fusion_node["node_type"] == "fusion_stage_track"
        assert set(fusion_node["parent_ids"]) == {"feeder:chernoff-fusion-input"}


# --- 3. the fused output cannot affect (D, r) -------------------------------

@stonesoup_missing
def test_fused_output_is_absent_from_the_snapshot_and_cannot_affect_D_r(both_policies):
    """The fused track is not a source, detection, track, transformation,
    or comparison_edge anywhere in the snapshot -- the only object that
    even mentions it is the (non-authoritative) `fusion:chernoff-fused`
    provenance node. tracking_adapter_generator.py/tracking_adapter_
    verifier.py never read `doc["provenance"]` when reconstructing
    (D, r) at all (only sources/detections/tracks/transformations/
    comparison_edges), so the fused track structurally cannot reach it."""
    from tracking_adapter_stonesoup_trackfusion_emitter import capture_fused_track_report

    for run in both_policies:
        doc = run["doc"]
        for collection in ("sources", "detections", "tracks", "transformations", "comparison_edges"):
            for item in doc[collection]:
                assert "fusion:chernoff-fused" not in json.dumps(item), (
                    f"fused-track reference leaked into {collection}: {item}"
                )

    fused_report = capture_fused_track_report("natural")
    assert fused_report["stonesoup_fused_track_position_x"] is not None
    # Deleting the entire provenance graph (which is the only place the
    # fused track is even mentioned) must not change the recomputed (D, r)
    # at all -- proves (D, r) has no dependency on it whatsoever.
    from tracking_adapter_verifier import verify_snapshot_doc, compute_payload_digest

    natural, _ = both_policies
    stripped = copy.deepcopy(natural["doc"])
    stripped["provenance"] = []
    del stripped["independence_policy"]
    stripped["payload_digest"] = compute_payload_digest(stripped)
    stripped_result = verify_snapshot_doc(stripped)
    assert stripped_result.accepted, stripped_result.reasons
    original_result = verify_snapshot_doc(natural["doc"])
    assert stripped_result.D == original_result.D
    assert stripped_result.r == original_result.r


# --- 4. covariance changes alter the snapshot digest but not (D, r) ---------

@stonesoup_missing
def test_covariance_tamper_changes_digest_but_not_D_r(both_policies):
    from tracking_adapter_verifier import compute_payload_digest, verify_snapshot_doc

    natural, _ = both_policies
    original = natural["doc"]
    original_result = verify_snapshot_doc(original)
    assert original_result.accepted, original_result.reasons

    tampered = copy.deepcopy(original)
    tampered["detections"][0]["covariance"][0][0] = "999.0"
    tampered_digest = compute_payload_digest(tampered)
    assert tampered_digest != original["payload_digest"]

    tampered["payload_digest"] = tampered_digest
    tampered_result = verify_snapshot_doc(tampered)
    assert tampered_result.accepted, tampered_result.reasons
    assert tampered_result.D == original_result.D
    assert tampered_result.r == original_result.r


# --- 5. both policies are necessarily repairable ----------------------------

@stonesoup_missing
def test_natural_and_perturbed_are_both_necessarily_repairable(both_policies):
    natural, perturbed = both_policies
    for run in (natural, perturbed):
        assert run["r21_cert"]["result"] == "repair"
        D = [[Fraction(x) for x in row] for row in run["cert"]["D"]]
        r = [Fraction(x) for x in run["cert"]["r"]]
        b = [Fraction(s) for s in run["r21_cert"]["repair"]]
        reproduced = [sum(D[i][j] * b[j] for j in range(2)) for i in range(1)]
        assert reproduced == r  # Db = r, checked directly


@stonesoup_missing
def test_perturbation_changes_r_by_exactly_the_declared_offset(both_policies):
    """The perturbation tests transformation HANDLING, not obstruction
    capability (design doc SS9): the two runs' r must differ by EXACTLY
    the declared artificial offset, and both remain repairable."""
    from tracking_adapter_stonesoup_trackfusion_emitter import ARTIFICIAL_PERTURBATION_OFFSET

    natural, perturbed = both_policies
    r_natural = Fraction(natural["cert"]["r"][0])
    r_perturbed = Fraction(perturbed["cert"]["r"][0])
    assert r_perturbed - r_natural == Fraction(ARTIFICIAL_PERTURBATION_OFFSET)


# --- 6. certificates cannot be interchanged ---------------------------------

@stonesoup_missing
def test_certificate_from_one_policy_rejected_against_the_other_snapshot(both_policies):
    from tracking_adapter_certificate import verify_chain

    natural, perturbed = both_policies

    cross_1 = verify_chain(perturbed["doc"], natural["cert"], natural["r21_cert"])
    assert not cross_1.accepted
    assert any("snapshot_payload_digest" in msg for msg in cross_1.reasons)

    cross_2 = verify_chain(natural["doc"], perturbed["cert"], perturbed["r21_cert"])
    assert not cross_2.accepted
    assert any("snapshot_payload_digest" in msg for msg in cross_2.reasons)


# --- both adapter certificates and complete chains verify; both R21 --------
# --- checkers accept ---------------------------------------------------------

@stonesoup_missing
def test_both_adapter_certificates_and_chains_verify(both_policies):
    from tracking_adapter_certificate import verify_chain

    for run in both_policies:
        chain = verify_chain(run["doc"], run["cert"], run["r21_cert"])
        assert chain.accepted, chain.reasons


@stonesoup_missing
@ocaml_missing
def test_both_r21_checkers_accept_both_policies(both_policies):
    for run in both_policies:
        result = _run_ocaml_checker(run["roc_input_path"], run["r21_cert_path"])
        assert result.returncode == 0, result.stdout + result.stderr


# --- provenance: the one comparison is PROVENANCE ACCEPT (disjoint radar ---
# --- source_records), for both policies -------------------------------------

@stonesoup_missing
def test_provenance_accepts_the_one_comparison_as_independent(both_policies):
    from tracking_adapter_provenance import check_independence
    from tracking_adapter_verifier import verify_snapshot_doc

    for run in both_policies:
        result = verify_snapshot_doc(run["doc"])
        assert result.accepted, result.reasons
        provenance_result = check_independence(result)
        assert provenance_result.accepted, (provenance_result.reason, provenance_result.message)
        assert provenance_result.claimed_independent_edges == ["kf1-kf2"]


# --- 7. process-level determinism across fresh subprocesses ----------------

@stonesoup_missing
@pytest.mark.parametrize("policy", ["natural", "artificial_perturbation"])
def test_policy_is_deterministic_across_fresh_subprocesses(tmp_path, policy):
    run_a = _full_pipeline(tmp_path, f"{policy}_a", policy)
    run_b = _full_pipeline(tmp_path, f"{policy}_b", policy)
    assert run_a["doc"] == run_b["doc"]
    assert run_a["cert"] == run_b["cert"]
    assert run_a["r21_cert"] == run_b["r21_cert"]


# --- 8. the ordinary verifier and R21 modules still import no Stone Soup ---

@stonesoup_missing
def test_core_adapter_and_r21_modules_still_import_no_stonesoup():
    """Belt-and-suspenders re-check specific to THIS step's own new file:
    tests/test_stonesoup_import_boundary.py already proves this in
    general (module-by-module AST scan); this confirms adding
    tracking_adapter_stonesoup_trackfusion_emitter.py did not introduce
    any import into a core module."""
    import ast

    from tests.test_stonesoup_import_boundary import CORE_MODULES, _imported_module_names

    for module_name in CORE_MODULES:
        path = REPO_ROOT / f"{module_name}.py"
        tree = ast.parse(path.read_text(), filename=str(path))
        assert "stonesoup" not in _imported_module_names(tree)


def test_the_optional_stonesoup_ci_job_will_pick_up_this_file_automatically():
    """`make check-stonesoup-adapter` selects Stone-Soup-dependent test
    files by keyword (`pytest -k stonesoup`), not an explicit allowlist
    -- confirmed here so a new file named tests/test_stonesoup_*.py
    (this one included) is guaranteed to run in the `stonesoup` CI job
    with zero additional wiring and zero skips once Stone Soup is
    installed there (.github/workflows/formal-verification.yml's own
    `stonesoup` job installs requirements-stonesoup.txt before calling
    this exact Makefile target)."""
    makefile = (REPO_ROOT / "Makefile").read_text()
    assert re.search(r"PYTEST\)\s+-q\s+-k\s+stonesoup", makefile), (
        "check-stonesoup-adapter no longer selects tests by the 'stonesoup' "
        "keyword -- new tests/test_stonesoup_*.py files might silently stop "
        "running in CI"
    )
    workflow = (REPO_ROOT / ".github" / "workflows" / "formal-verification.yml").read_text()
    assert "check-stonesoup-adapter" in workflow
    assert "requirements-stonesoup.txt" in workflow
