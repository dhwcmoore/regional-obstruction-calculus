"""
Tests for tracking_adapter_certificate.py -- step 5 of the tracking-
adapter implementation order: certificate emission (only from a
snapshot the independent verifier accepts) and full evidence-chain
verification, including a broad set of mix-and-match substitution and
tamper attacks the design doc explicitly names.
"""

import copy
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from tracking_adapter_certificate import (
    CertificateError,
    emit_certificate,
    verify_chain,
    verify_chain_files,
)
from tracking_adapter_verifier import compute_payload_digest

REPO_ROOT = Path(__file__).resolve().parent.parent
OCAML_BINARY = REPO_ROOT / "roc-verify-ocaml"
SUBPROCESS_TIMEOUT = 30

ocaml_missing = pytest.mark.skipif(
    not os.access(OCAML_BINARY, os.X_OK),
    reason="roc-verify-ocaml not built; run `make check-r21-ocaml` first",
)

QUANTISATION_POLICY = {
    "position_decimal_places": 6,
    "transform_decimal_places": 6,
    "rounding_mode": "half_even",
}


# --- fixture builders (same shape as the generator/verifier test files) --

def _source(source_id):
    return {
        "source_id": source_id, "sensor_modality": "radar", "platform_id": "platform-1",
        "source_data_digest": "sha256:" + "a" * 64, "source_timestamp_utc": "2026-01-01T00:00:00Z",
        "coordinate_frame": "frame-A", "measurement_model_id": "model-1",
    }


def _detection(detection_id, source_id):
    return {
        "detection_id": detection_id, "source_id": source_id, "timestamp_utc": "2026-01-01T00:00:00Z",
        "state_values": ["0"], "coordinate_frame": "frame-A", "transformation_history": [],
        "source_record_digest": "sha256:" + "b" * 64,
    }


def _track(track_id, tracker_id, state_value, detection_ids):
    return {
        "track_id": track_id, "tracker_id": tracker_id, "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_values": [state_value], "state_space": "scalar",
        "contributing_detection_ids": list(detection_ids), "ancestry": [],
        "transformation_record": "identity", "track_digest": "sha256:" + "c" * 64,
    }


def _edge(edge_id, source_track_id, target_track_id, discrepancy):
    return {
        "edge_id": edge_id, "source_track_id": source_track_id, "target_track_id": target_track_id,
        "orientation": "source_to_target", "comparison_space_id": "cmp-1",
        "transformation_id": "family-1", "discrepancy": discrepancy,
        "coreference_provenance": "operator-declared",
    }


def _xf(transformation_id, edge_id, track_id, offset):
    return {
        "transformation_id": transformation_id, "edge_id": edge_id, "track_id": track_id,
        "kind": "additive_offset", "offset": offset,
    }


def _four_cycle(offsets, discrepancies):
    tracks = [_track(f"t{i}", f"tracker-{i}", "100", ["det-1"]) for i in (1, 2, 3, 4)]
    edges_meta = [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]
    transformations = []
    for edge_id, i, j in edges_meta:
        transformations.append(_xf(f"xf-{edge_id}-{i}", edge_id, i, offsets[(edge_id, i)]))
        transformations.append(_xf(f"xf-{edge_id}-{j}", edge_id, j, offsets[(edge_id, j)]))
    edges = [_edge(eid, i, j, discrepancies[eid]) for eid, i, j in edges_meta]
    return tracks, transformations, edges


def _make_doc(scenario_id, tracks, transformations, edges):
    doc = {
        "schema_version": "tracking-adapter/v1",
        "scenario_id": scenario_id,
        "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_space": {"dimension": 1},
        "quantisation_policy": QUANTISATION_POLICY,
        "correction_policy": {"kind": "additive-per-track"},
        "sources": [_source("src-1")],
        "detections": [_detection("det-1", "src-1")],
        "tracks": tracks,
        "transformations": transformations,
        "comparison_edges": edges,
        "provenance": [],
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
    }
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def _coherent_fixture_doc():
    coherent = {"t1": "0", "t2": "1", "t3": "3", "t4": "2"}
    offsets = {}
    for edge_id, i, j in [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]:
        offsets[(edge_id, i)] = coherent[i]
        offsets[(edge_id, j)] = coherent[j]
    discrepancies = {"e12": "1", "e23": "2", "e34": "-1", "e14": "2"}
    tracks, transformations, edges = _four_cycle(offsets, discrepancies)
    return _make_doc("coherent-001", tracks, transformations, edges)


def _obstructed_fixture_doc():
    offsets = {
        ("e12", "t1"): "0", ("e12", "t2"): "1",
        ("e23", "t2"): "0", ("e23", "t3"): "1",
        ("e34", "t3"): "0", ("e34", "t4"): "1",
        ("e14", "t1"): "0", ("e14", "t4"): "-2",
    }
    discrepancies = {"e12": "1", "e23": "1", "e34": "1", "e14": "-2"}
    tracks, transformations, edges = _four_cycle(offsets, discrepancies)
    return _make_doc("obstructed-001", tracks, transformations, edges)


def _run_r21_emitter(roc_input: dict, tmp_path) -> dict:
    input_path = tmp_path / "roc_input.json"
    cert_path = tmp_path / "r21_cert.json"
    input_path.write_text(json.dumps(roc_input))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(input_path),
         "--certificate", str(cert_path)],
        check=True, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    return json.loads(cert_path.read_text())


def _run_python_checker(roc_input: dict, r21_cert: dict, tmp_path) -> subprocess.CompletedProcess:
    input_path = tmp_path / "roc_input_pycheck.json"
    cert_path = tmp_path / "r21_cert_pycheck.json"
    input_path.write_text(json.dumps(roc_input))
    cert_path.write_text(json.dumps(r21_cert))
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_checker.py"), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


def _run_ocaml_checker(roc_input: dict, r21_cert: dict, tmp_path) -> subprocess.CompletedProcess:
    input_path = tmp_path / "roc_input_mlcheck.json"
    cert_path = tmp_path / "r21_cert_mlcheck.json"
    input_path.write_text(json.dumps(roc_input))
    cert_path.write_text(json.dumps(r21_cert))
    return subprocess.run(
        [str(OCAML_BINARY), str(input_path), str(cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )


# --- 1. Basic emission + chain acceptance --------------------------------

def test_repairable_fixture_certificate_accepted(tmp_path):
    doc = _coherent_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)
    assert r21_cert["result"] == "repair"
    chain = verify_chain(doc, cert, r21_cert)
    assert chain.accepted, chain.reasons


def test_obstructed_fixture_certificate_accepted(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)
    assert r21_cert["result"] == "separator"
    chain = verify_chain(doc, cert, r21_cert)
    assert chain.accepted, chain.reasons


@ocaml_missing
def test_both_complete_chains_accepted_by_both_r21_verifiers(tmp_path):
    for doc, expected_result in [(_coherent_fixture_doc(), "repair"), (_obstructed_fixture_doc(), "separator")]:
        cert = emit_certificate(doc)
        r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)
        assert r21_cert["result"] == expected_result

        chain = verify_chain(doc, cert, r21_cert)
        assert chain.accepted, chain.reasons

        py_result = _run_python_checker(cert["roc_input"], r21_cert, tmp_path)
        assert py_result.returncode == 0, py_result.stdout + py_result.stderr

        ml_result = _run_ocaml_checker(cert["roc_input"], r21_cert, tmp_path)
        assert ml_result.returncode == 0, ml_result.stdout + ml_result.stderr


# --- 2. Determinism -------------------------------------------------------

def test_certificate_determinism():
    doc = _obstructed_fixture_doc()
    cert1 = emit_certificate(doc)
    cert2 = emit_certificate(copy.deepcopy(doc))
    assert cert1 == cert2


# --- 3. Emission authority -------------------------------------------------

def test_emission_refused_for_a_snapshot_the_verifier_rejects():
    doc = _obstructed_fixture_doc()
    doc["comparison_edges"][0]["discrepancy"] = "999"  # breaks residue consistency
    with pytest.raises(CertificateError, match="rejected by independent verifier"):
        emit_certificate(doc)


# --- 4. Mix-and-match substitution attacks --------------------------------

def test_snapshot_substitution_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    other_doc = _coherent_fixture_doc()  # a VALID but DIFFERENT snapshot
    chain = verify_chain(other_doc, cert, r21_cert)
    assert not chain.accepted
    assert any("snapshot_payload_digest" in msg for msg in chain.reasons)


def test_r21_certificate_substitution_rejected(tmp_path):
    doc_a = _obstructed_fixture_doc()
    cert_a = emit_certificate(doc_a)
    r21_cert_a = _run_r21_emitter(cert_a["roc_input"], tmp_path)

    doc_b = _coherent_fixture_doc()
    cert_b = emit_certificate(doc_b)
    r21_cert_b = _run_r21_emitter(cert_b["roc_input"], tmp_path)

    # cert_a paired with r21_cert_b: mismatched input_digest.
    chain = verify_chain(doc_a, cert_a, r21_cert_b)
    assert not chain.accepted
    assert any("input_digest" in msg for msg in chain.reasons)

    # sanity: the "correct" pairings both still accept.
    assert verify_chain(doc_a, cert_a, r21_cert_a).accepted
    assert verify_chain(doc_b, cert_b, r21_cert_b).accepted


# --- 5. Row/column binding tamper -----------------------------------------

def test_row_binding_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["row_bindings"][0]["edge_id"] = "e23"  # swap without changing D/r
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("row_bindings" in msg for msg in chain.reasons)


def test_column_binding_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["column_bindings"][0]["track_id"] = "t2"
    tampered["column_bindings"][1]["track_id"] = "t1"
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("column_bindings" in msg for msg in chain.reasons)


# --- 6. Decimal-source attribution tamper --------------------------------

def test_decimal_source_attribution_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    # Attribute t2's ACTUAL attestation to a value that is really t3's.
    for att in tampered["conversion_attestations"]:
        if att["source_object"] == "track:t2":
            att["canonical_decimal"] = "100"  # still matches numerically (all tracks start at 100)...
            break
    # ...so instead attribute a WRONG value that does not match t2's actual state.
    for att in tampered["conversion_attestations"]:
        if att["source_object"] == "track:t2":
            att["canonical_decimal"] = "12345"
            att["converted_rational"] = "12345"
            break
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("claims canonical_decimal" in msg for msg in chain.reasons)


# --- 7. Conversion-policy tamper (same resulting value, different declared policy) ---

def test_conversion_policy_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    for att in tampered["conversion_attestations"]:
        if att["source_object"] == "track:t1":
            att["decimal_places"] = 2  # differs from the snapshot's declared 6, though "100" rounds the same either way
            break
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("inconsistent with the snapshot's own" in msg for msg in chain.reasons)


# --- 8. D / r / roc_input tamper ------------------------------------------

def test_reconstructed_D_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["D"][0][0] = "999"
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("certificate's D does not match" in msg for msg in chain.reasons)


def test_reconstructed_r_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["r"][0] = "999"
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("certificate's r does not match" in msg for msg in chain.reasons)


def test_roc_input_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["roc_input"]["r"][0] = "999"
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("roc_input does not match" in msg for msg in chain.reasons)


# --- 9. Digest tamper (R21 input digest, certificate's own digest) -------

def test_r21_input_digest_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["r21_input_digest"] = "sha256:" + "0" * 64
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("r21_input_digest does not match" in msg for msg in chain.reasons)


def test_adapter_certificate_digest_tamper_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    tampered["certificate_payload_digest"] = "sha256:" + "0" * 64  # NOT recomputed -- the point of this test

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("certificate payload digest mismatch" in msg for msg in chain.reasons)


# --- 10. Unknown / duplicate fields ---------------------------------------

def test_unknown_certificate_field_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = dict(cert)
    tampered["mystery_field"] = 1
    # Deliberately do NOT recompute certificate_payload_digest -- this
    # should be rejected on unrecognized-field grounds before the digest
    # check is even reached.
    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("unrecognized field" in msg for msg in chain.reasons)


def test_duplicate_json_key_in_certificate_file_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    snapshot_path = tmp_path / "snapshot.json"
    cert_path = tmp_path / "cert.json"
    r21_cert_path = tmp_path / "r21_cert.json"
    snapshot_path.write_text(json.dumps(doc))
    r21_cert_path.write_text(json.dumps(r21_cert))
    cert_path.write_text('{"schema_version": "tracking-adapter-certificate/v1", "schema_version": "tracking-adapter-certificate/v1"}')

    chain = verify_chain_files(str(snapshot_path), str(cert_path), str(r21_cert_path))
    assert not chain.accepted
    assert any("duplicate" in msg.lower() for msg in chain.reasons)


# --- 11. Malformed / excessive attestations -------------------------------

def test_malformed_attestation_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    del tampered["conversion_attestations"][0]["converted_rational"]  # missing required field
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("missing field" in msg for msg in chain.reasons)


def test_excessive_attestations_rejected(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered = copy.deepcopy(cert)
    from tracking_adapter_certificate import MAX_ATTESTATIONS
    filler = dict(tampered["conversion_attestations"][0])
    tampered["conversion_attestations"] = [filler] * (MAX_ATTESTATIONS + 1)
    tampered["certificate_payload_digest"] = _recompute_cert_digest(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("exceeds MAX_ATTESTATIONS" in msg for msg in chain.reasons)


# --- 12. Evidence-change distinction: affects (D, r) vs. does not --------

def test_evidence_change_affecting_r_fails_at_reconstruction(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered_doc = copy.deepcopy(doc)
    for t in tampered_doc["tracks"]:
        if t["track_id"] == "t2":
            t["state_values"] = ["999"]
    tampered_doc["payload_digest"] = compute_payload_digest(tampered_doc)  # attacker controls the whole doc

    chain = verify_chain(tampered_doc, cert, r21_cert)
    assert not chain.accepted
    # Rejected at snapshot verification (residue no longer matches the
    # edge's own declared discrepancy) before chain-level checks even run.
    assert any("rejected by independent verifier" in msg for msg in chain.reasons)


def test_evidence_change_not_affecting_D_r_fails_via_snapshot_digest_binding(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _run_r21_emitter(cert["roc_input"], tmp_path)

    tampered_doc = copy.deepcopy(doc)
    tampered_doc["sources"][0]["sensor_modality"] = "tampered-modality"
    # payload_digest intentionally NOT recomputed -- this field affects
    # no residue, no D entry, no r entry at all.

    chain = verify_chain(tampered_doc, cert, r21_cert)
    assert not chain.accepted
    # Rejected at snapshot verification, via the payload_digest binding --
    # test_tracking_adapter_verifier.py's own sensor_modality test covers
    # the exact rejection message; here we only need chain-level rejection.
    assert any("rejected by independent verifier" in msg for msg in chain.reasons)


def _recompute_cert_digest(cert: dict) -> str:
    from tracking_adapter_certificate import _compute_certificate_digest
    body = {k: v for k, v in cert.items() if k != "certificate_payload_digest"}
    return _compute_certificate_digest(body)
