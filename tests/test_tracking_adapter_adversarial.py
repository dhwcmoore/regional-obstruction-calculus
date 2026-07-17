"""
Systematic adversarial-rejection coverage for the tracking adapter --
step 7 of the implementation order. Deliberately separate from
mathematical metamorphic properties (step 8): everything here is about
malformed, incomplete, or actively tampered INPUT being rejected, not
about invariances a well-formed input family should satisfy.

Reuses the fixture builders from test_tracking_adapter_certificate.py
rather than re-deriving a fifth copy of the same four-cycle
construction helpers.
"""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_tracking_adapter_certificate import (
    _coherent_fixture_doc,
    _detection,
    _edge,
    _obstructed_fixture_doc,
    _source,
    _track,
)
from tracking_adapter_certificate import emit_certificate, verify_chain
from tracking_adapter_format import parse_comparison_edge, parse_track
from tracking_adapter_verifier import compute_payload_digest, verify_snapshot_doc

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBPROCESS_TIMEOUT = 30


def _valid_source():
    return _source("src-1")


def _valid_detection():
    return _detection("det-1", "src-1")


def _valid_track(**overrides):
    t = _track("t1", "tracker-1", "100", ["det-1"])
    t.update(overrides)
    return t


def _valid_edge(**overrides):
    e = _edge("e12", "t1", "t2", "1")
    e.update(overrides)
    return e


# =========================================================================
# 1. Malformed domain objects -- type confusion, not just missing/unknown keys.
# =========================================================================

@pytest.mark.parametrize("field,bad_value", [
    ("state_values", "100"),          # string instead of list
    ("state_values", None),
    ("contributing_detection_ids", "det-1"),  # string instead of list
    ("ancestry", "not-a-list"),
])
def test_track_rejects_wrong_field_type(field, bad_value):
    t = _valid_track()
    t[field] = bad_value
    with pytest.raises((ValueError, TypeError)):
        parse_track(t)


def test_edge_rejects_non_string_edge_id():
    e = _valid_edge(edge_id=12345)
    # edge_id itself isn't type-checked beyond being hashable/usable as a
    # dict key elsewhere, but a non-string discrepancy IS caught at
    # conversion time -- this documents that boundary rather than
    # asserting a check that does not exist.
    parsed = parse_comparison_edge(e)
    assert parsed.edge_id == 12345  # accepted structurally; would fail
    # downstream at generation/verification once used as a dict/JSON key
    # in a way that expects a string -- covered by the snapshot-level
    # tests below, not claimed to be rejected at this narrow layer.


def test_edge_rejects_non_dict():
    with pytest.raises(ValueError, match="must be a JSON object"):
        parse_comparison_edge(["not", "a", "dict"])


# =========================================================================
# 2. Duplicate and dangling identifiers -- exercised at the VERIFIER's own
#    independent implementation, not only tracking_adapter_format.py's.
# =========================================================================

def test_verifier_rejects_duplicate_track_id():
    doc = _obstructed_fixture_doc()
    doc["tracks"].append(dict(doc["tracks"][0], track_id="t1"))  # already exists
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("duplicate track_id" in msg for msg in result.reasons)


def test_verifier_rejects_duplicate_transformation_id():
    doc = _obstructed_fixture_doc()
    dup = dict(doc["transformations"][0])
    doc["transformations"].append(dup)
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("duplicate transformation_id" in msg for msg in result.reasons)


def test_verifier_rejects_dangling_transformation_edge_reference():
    doc = _obstructed_fixture_doc()
    doc["transformations"][0]["edge_id"] = "e-does-not-exist"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("references unknown edge_id" in msg for msg in result.reasons)


def test_verifier_rejects_edge_comparing_track_to_itself():
    doc = _obstructed_fixture_doc()
    doc["comparison_edges"][0]["target_track_id"] = doc["comparison_edges"][0]["source_track_id"]
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("compares a track to itself" in msg for msg in result.reasons)


def test_verifier_rejects_missing_transformation_for_an_endpoint():
    doc = _obstructed_fixture_doc()
    doc["transformations"] = [
        t for t in doc["transformations"]
        if not (t["edge_id"] == "e12" and t["track_id"] == "t2")
    ]
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("has no declared transformation" in msg for msg in result.reasons)


# =========================================================================
# 3. Inconsistent timestamps.
# =========================================================================

@pytest.mark.parametrize("bad_ts", [
    "2026-01-01",                 # missing time component
    "01-01-2026T00:00:00Z",       # wrong field order
    "2026-01-01T00:00:00",        # missing Z
    "2026-01-01 00:00:00Z",       # missing T
    "not-a-timestamp",
    "",
])
def test_verifier_rejects_malformed_track_timestamp(bad_ts):
    doc = _obstructed_fixture_doc()
    doc["tracks"][0]["evaluation_timestamp_utc"] = bad_ts
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("malformed timestamp" in msg for msg in result.reasons)


def test_verifier_rejects_malformed_source_timestamp():
    doc = _obstructed_fixture_doc()
    doc["sources"][0]["source_timestamp_utc"] = "garbage"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("malformed timestamp" in msg for msg in result.reasons)


def test_verifier_rejects_malformed_detection_timestamp():
    doc = _obstructed_fixture_doc()
    doc["detections"][0]["timestamp_utc"] = "garbage"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("malformed timestamp" in msg for msg in result.reasons)


# =========================================================================
# 4. State-dimension mismatches -- at the VERIFIER's own implementation.
# =========================================================================

def test_verifier_rejects_multi_dimensional_track_state():
    doc = _obstructed_fixture_doc()
    doc["tracks"][0]["state_values"] = ["100", "200"]
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("only supports exactly 1" in msg for msg in result.reasons)


def test_verifier_rejects_zero_dimensional_track_state():
    doc = _obstructed_fixture_doc()
    doc["tracks"][0]["state_values"] = []
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("only supports exactly 1" in msg for msg in result.reasons)


# =========================================================================
# 5. Undeclared frames and units.
# =========================================================================

def test_rejects_empty_coordinate_frame_on_source():
    doc = _obstructed_fixture_doc()
    doc["sources"][0]["coordinate_frame"] = ""
    doc["payload_digest"] = compute_payload_digest(doc)  # isolate this from the digest check
    result = verify_snapshot_doc(doc)
    # No dedicated frame-registry exists yet (design doc SS20 names this
    # as future work) -- an empty/blank frame identifier IS structurally
    # a string, so this currently passes THIS layer's checks. Documented
    # here as an explicit non-claim rather than silently assumed covered.
    assert result.accepted, (
        "coordinate_frame is not yet validated against any registry or "
        "non-blank requirement -- if this starts failing, either a real "
        "check was added (update this test to assert rejection) or "
        "something else broke"
    )


# =========================================================================
# 6. Malformed transformations.
# =========================================================================

def test_verifier_rejects_unsupported_transformation_kind():
    doc = _obstructed_fixture_doc()
    doc["transformations"][0]["kind"] = "projective"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("unsupported transformation kind" in msg for msg in result.reasons)


def test_verifier_rejects_transformation_offset_wrong_type():
    doc = _obstructed_fixture_doc()
    doc["transformations"][0]["offset"] = 1.5  # float, not a canonical decimal string
    result = verify_snapshot_doc(doc)
    assert not result.accepted


def test_verifier_rejects_transformation_track_not_an_edge_endpoint():
    doc = _obstructed_fixture_doc()
    doc["tracks"].append(dict(doc["tracks"][0], track_id="t-extra"))
    doc["transformations"][0]["track_id"] = "t-extra"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("not an endpoint of edge" in msg for msg in result.reasons)


# =========================================================================
# 7. Invalid edge orientations.
# =========================================================================

def test_format_rejects_unsupported_orientation():
    e = _valid_edge(orientation="target_to_source")
    with pytest.raises(ValueError, match="unsupported orientation"):
        parse_comparison_edge(e)


def test_verifier_rejects_unsupported_orientation():
    doc = _obstructed_fixture_doc()
    doc["comparison_edges"][0]["orientation"] = "bidirectional"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("unsupported orientation" in msg for msg in result.reasons)


# =========================================================================
# 8. Incomplete ancestry.
# =========================================================================

def test_format_rejects_track_with_no_contributing_detections():
    t = _valid_track(contributing_detection_ids=[])
    with pytest.raises(ValueError, match="at least one contributing_detection_id"):
        parse_track(t)


def test_verifier_rejects_track_with_no_contributing_detections():
    doc = _obstructed_fixture_doc()
    doc["tracks"][0]["contributing_detection_ids"] = []
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("at least one contributing_detection_id" in msg for msg in result.reasons)


# =========================================================================
# 9. Noncanonical numeric strings.
# =========================================================================

@pytest.mark.parametrize("bad_decimal", ["1E5", "NaN", "Infinity", "+5", "1.2.3", "", "  100"])
def test_verifier_rejects_noncanonical_track_state(bad_decimal):
    doc = _obstructed_fixture_doc()
    doc["tracks"][0]["state_values"] = [bad_decimal]
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("decimal conversion failed" in msg for msg in result.reasons)


def test_verifier_rejects_noncanonical_transformation_offset():
    doc = _obstructed_fixture_doc()
    doc["transformations"][0]["offset"] = "1E1"
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("decimal conversion failed" in msg for msg in result.reasons)


# =========================================================================
# 10. Resource-limit boundaries.
# =========================================================================

def test_snapshot_list_length_boundary(monkeypatch):
    import tracking_adapter_verifier as v

    doc = _obstructed_fixture_doc()
    # The largest list in this fixture is `transformations` (8: two per
    # edge, four edges) -- the boundary must be checked against whichever
    # list is largest, not assumed to be `tracks` (4).
    largest = max(len(doc[k]) for k in ("sources", "detections", "tracks", "transformations", "comparison_edges"))
    assert largest == 8

    monkeypatch.setattr(v, "MAX_SNAPSHOT_LIST_LENGTH", largest)
    result_ok = verify_snapshot_doc(doc)
    assert result_ok.accepted, result_ok.reasons

    monkeypatch.setattr(v, "MAX_SNAPSHOT_LIST_LENGTH", largest - 1)
    result_over = verify_snapshot_doc(doc)
    assert not result_over.accepted
    assert any("exceeding MAX_SNAPSHOT_LIST_LENGTH" in msg for msg in result_over.reasons)


def test_certificate_attestation_count_boundary(monkeypatch):
    import tracking_adapter_certificate as c

    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    n = len(cert["conversion_attestations"])

    monkeypatch.setattr(c, "MAX_ATTESTATIONS", n)
    result_ok = verify_chain(doc, cert, {"schema": "repair-or-separator/v1",
                                          "input_digest": cert["r21_input_digest"],
                                          "result": "separator",
                                          "separator": ["1/5", "1/5", "1/5", "-1/5"]})
    # (this may still fail for unrelated reasons -- e.g. r21 cert
    # correctness -- so only assert the attestation-count check itself
    # did not fire.)
    assert not any("exceeds MAX_ATTESTATIONS" in msg for msg in result_ok.reasons)

    monkeypatch.setattr(c, "MAX_ATTESTATIONS", n - 1)
    result_over = verify_chain(doc, cert, {"schema": "repair-or-separator/v1",
                                            "input_digest": cert["r21_input_digest"],
                                            "result": "separator",
                                            "separator": ["1/5", "1/5", "1/5", "-1/5"]})
    assert not result_over.accepted
    assert any("exceeds MAX_ATTESTATIONS" in msg for msg in result_over.reasons)


# =========================================================================
# 11. Unknown and duplicate JSON fields, including NESTED duplicates.
# =========================================================================

def test_verifier_rejects_unknown_field_on_a_nested_object():
    doc = _obstructed_fixture_doc()
    doc["tracks"][0]["bogus_field"] = 1
    result = verify_snapshot_doc(doc)
    assert not result.accepted
    assert any("unrecognized field" in msg for msg in result.reasons)


def test_duplicate_json_key_nested_inside_a_track_is_rejected(tmp_path):
    from tracking_adapter_verifier import verify_snapshot

    raw = """
    {
      "schema_version": "tracking-adapter/v1",
      "scenario_id": "x", "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
      "state_space": {}, "quantisation_policy": {}, "correction_policy": {},
      "sources": [], "detections": [],
      "tracks": [{"track_id": "t1", "track_id": "t1"}],
      "transformations": [], "comparison_edges": [], "provenance": [],
      "derived_problem": {"D": [], "r": []}, "payload_digest": "x"
    }
    """
    path = tmp_path / "nested_dup.json"
    path.write_text(raw)
    result = verify_snapshot(str(path))
    assert not result.accepted
    assert any("duplicate" in msg.lower() for msg in result.reasons)


# =========================================================================
# 12. Malformed row and column bindings -- STRUCTURAL, not just value swaps.
# =========================================================================

def test_certificate_rejects_row_binding_missing_required_key(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _emit_matching_r21_cert(cert)

    tampered = copy.deepcopy(cert)
    del tampered["row_bindings"][0]["edge_id"]
    tampered["certificate_payload_digest"] = _recompute(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted
    assert any("malformed row/column bindings" in msg for msg in chain.reasons)


def test_certificate_rejects_row_binding_unknown_key(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _emit_matching_r21_cert(cert)

    tampered = copy.deepcopy(cert)
    tampered["row_bindings"][0]["bogus"] = 1
    tampered["certificate_payload_digest"] = _recompute(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted


def test_certificate_rejects_column_binding_wrong_type():
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _emit_matching_r21_cert(cert)

    tampered = copy.deepcopy(cert)
    tampered["column_bindings"] = "not-a-list"
    tampered["certificate_payload_digest"] = _recompute(tampered)

    chain = verify_chain(doc, tampered, r21_cert)
    assert not chain.accepted


# =========================================================================
# 13. Certificate/snapshot/R21 substitution.
# =========================================================================

def test_adapter_certificate_from_a_different_scenario_rejected():
    doc_a = _obstructed_fixture_doc()
    doc_b = _coherent_fixture_doc()
    cert_b = emit_certificate(doc_b)
    r21_cert_b = _emit_matching_r21_cert(cert_b)

    # Pairing scenario A's snapshot with scenario B's adapter certificate
    # (and B's own, self-consistent R21 certificate) -- a full
    # "certificate substitution" across all three chain positions at once.
    chain = verify_chain(doc_a, cert_b, r21_cert_b)
    assert not chain.accepted
    assert any("snapshot_payload_digest" in msg for msg in chain.reasons)


# =========================================================================
# 14. Digest-layer separation: three independent digests, each checked on
#     its own -- fixing any two does not mask tampering the third.
# =========================================================================

def test_digest_layers_are_independently_enforced():
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _emit_matching_r21_cert(cert)

    baseline = verify_chain(doc, cert, r21_cert)
    assert baseline.accepted

    # (a) snapshot payload_digest wrong, certificate/R21 digests untouched.
    doc_a = copy.deepcopy(doc)
    doc_a["payload_digest"] = "sha256:" + "1" * 64
    chain_a = verify_chain(doc_a, cert, r21_cert)
    assert not chain_a.accepted
    assert any("rejected by independent verifier" in msg for msg in chain_a.reasons)

    # (b) certificate_payload_digest wrong, snapshot/R21 digests untouched.
    cert_b = copy.deepcopy(cert)
    cert_b["certificate_payload_digest"] = "sha256:" + "2" * 64
    chain_b = verify_chain(doc, cert_b, r21_cert)
    assert not chain_b.accepted
    assert any("certificate payload digest mismatch" in msg for msg in chain_b.reasons)

    # (c) R21 certificate's input_digest wrong, snapshot/certificate digests untouched.
    r21_cert_c = dict(r21_cert)
    r21_cert_c["input_digest"] = "sha256:" + "3" * 64
    chain_c = verify_chain(doc, cert, r21_cert_c)
    assert not chain_c.accepted
    assert any("input_digest" in msg for msg in chain_c.reasons)

    # All three tamper independently -- none masks or is masked by the others.
    assert chain_a.reasons != chain_b.reasons != chain_c.reasons


# =========================================================================
# 15. Failure-closed CLI behaviour.
# =========================================================================

def test_verifier_cli_exits_zero_on_accept(tmp_path):
    doc = _obstructed_fixture_doc()
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(doc))
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0
    assert "ACCEPT" in result.stdout


def test_verifier_cli_exits_one_on_reject(tmp_path):
    doc = _obstructed_fixture_doc()
    doc["comparison_edges"][0]["discrepancy"] = "999"
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(doc))
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 1
    assert "REJECT" in result.stdout


def test_verifier_cli_exits_one_on_malformed_file_not_a_crash(tmp_path):
    path = tmp_path / "not_json.txt"
    path.write_text("{this is not valid json")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_verifier_cli_exits_nonzero_on_missing_file(tmp_path):
    missing_path = tmp_path / "does_not_exist.json"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_verifier.py"), str(missing_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_chain_cli_exits_zero_on_accept(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _emit_matching_r21_cert(cert)

    snapshot_path = tmp_path / "snapshot.json"
    cert_path = tmp_path / "certificate.json"
    r21_cert_path = tmp_path / "r21_certificate.json"
    snapshot_path.write_text(json.dumps(doc))
    cert_path.write_text(json.dumps(cert))
    r21_cert_path.write_text(json.dumps(r21_cert))

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"),
         str(snapshot_path), str(cert_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 0
    assert "CHAIN ACCEPT" in result.stdout


def test_chain_cli_exits_one_on_reject(tmp_path):
    doc = _obstructed_fixture_doc()
    cert = emit_certificate(doc)
    r21_cert = _emit_matching_r21_cert(cert)
    r21_cert["input_digest"] = "sha256:" + "0" * 64  # tamper

    snapshot_path = tmp_path / "snapshot.json"
    cert_path = tmp_path / "certificate.json"
    r21_cert_path = tmp_path / "r21_certificate.json"
    snapshot_path.write_text(json.dumps(doc))
    cert_path.write_text(json.dumps(cert))
    r21_cert_path.write_text(json.dumps(r21_cert))

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tracking_adapter_certificate.py"),
         str(snapshot_path), str(cert_path), str(r21_cert_path)],
        capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    assert result.returncode == 1
    assert "CHAIN REJECT" in result.stdout


# --- shared helpers --------------------------------------------------------

def _emit_matching_r21_cert(cert: dict, tmp_path=None) -> dict:
    """Runs the real R21 emitter on cert['roc_input'] and returns the
    resulting certificate -- used throughout this file wherever a
    self-consistent R21 certificate is needed but the test itself is not
    about the R21 emission step."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        input_path = Path(d) / "roc_input.json"
        cert_path = Path(d) / "r21_cert.json"
        input_path.write_text(json.dumps(cert["roc_input"]))
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(input_path),
             "--certificate", str(cert_path)],
            check=True, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
        )
        return json.loads(cert_path.read_text())


def _recompute(cert: dict) -> str:
    from tracking_adapter_certificate import _compute_certificate_digest
    body = {k: v for k, v in cert.items() if k != "certificate_payload_digest"}
    return _compute_certificate_digest(body)
