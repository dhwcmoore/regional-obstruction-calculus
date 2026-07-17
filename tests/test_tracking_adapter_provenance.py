"""
Core provenance/independence tests for step 10D of the tracking-adapter
implementation order -- fast, hand-built ancestry graphs, no Stone Soup
needed. Covers the structural (SNAPSHOT REJECT) and admissibility
(PROVENANCE REFUSE/ACCEPT) checks directly, complementing tests/
test_stonesoup_provenance.py's end-to-end, Stone-Soup-driven coverage of
the same governing distinction.

Reuses the obstructed/coherent fixture builders from test_tracking_
adapter_certificate.py for the underlying (D, r) evidence, attaching a
hand-built `provenance` (ancestry graph) and `independence_policy` on
top -- exactly the layering tracking_adapter_stonesoup_provenance.py
also uses.
"""

import copy

import pytest

from tests.test_tracking_adapter_certificate import _obstructed_fixture_doc
from tracking_adapter_certificate import CertificateError, emit_certificate
from tracking_adapter_format import parse_snapshot_doc
from tracking_adapter_provenance import check_independence, compute_closure
from tracking_adapter_verifier import (
    compute_ancestry_closure,
    compute_payload_digest,
    verify_snapshot_doc,
)


def _node(node_id, node_type, parent_ids, source="src-x", digest=None, feeder=None):
    return {
        "node_id": node_id,
        "node_type": node_type,
        "parent_ids": list(parent_ids),
        "originating_source_id": source,
        "source_record_digest": digest if digest is not None else node_id,
        "transformation_or_feeder_id": feeder,
    }


def _policy(independent_comparisons, shared_prohibited=True, correlated_reuse=None):
    return {
        "policy_version": "test-policy/v1",
        "independent_comparisons": list(independent_comparisons),
        "shared_ancestry_prohibited": shared_prohibited,
        "declared_correlated_reuse": list(correlated_reuse or []),
    }


def _two_track_doc(ancestry_graph, policy):
    """A minimal two-track, one-edge snapshot -- provenance tests don't
    need the full four-cycle, only one declared comparison."""
    doc = {
        "schema_version": "tracking-adapter/v1",
        "scenario_id": "provenance-unit-001",
        "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
        "state_space": {"dimension": 1},
        "quantisation_policy": {"position_decimal_places": 6, "transform_decimal_places": 6, "rounding_mode": "half_even"},
        "correction_policy": {"kind": "additive-per-track"},
        "sources": [
            {"source_id": "src-1", "sensor_modality": "radar", "platform_id": "platform-1",
             "source_data_digest": "sha256:" + "a" * 64, "source_timestamp_utc": "2026-01-01T00:00:00Z",
             "coordinate_frame": "frame-A", "measurement_model_id": "model-1"},
            {"source_id": "src-2", "sensor_modality": "radar", "platform_id": "platform-2",
             "source_data_digest": "sha256:" + "b" * 64, "source_timestamp_utc": "2026-01-01T00:00:00Z",
             "coordinate_frame": "frame-A", "measurement_model_id": "model-1"},
        ],
        "detections": [
            {"detection_id": "det-1", "source_id": "src-1", "timestamp_utc": "2026-01-01T00:00:00Z",
             "state_values": ["100"], "coordinate_frame": "frame-A", "transformation_history": [],
             "source_record_digest": "sha256:" + "c" * 64},
            {"detection_id": "det-2", "source_id": "src-2", "timestamp_utc": "2026-01-01T00:00:00Z",
             "state_values": ["100"], "coordinate_frame": "frame-A", "transformation_history": [],
             "source_record_digest": "sha256:" + "d" * 64},
        ],
        "tracks": [
            {"track_id": "trk-1", "tracker_id": "tracker-1", "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
             "state_values": ["100"], "state_space": "scalar", "contributing_detection_ids": ["det-1"],
             "ancestry": [], "transformation_record": "identity", "track_digest": "sha256:" + "e" * 64},
            {"track_id": "trk-2", "tracker_id": "tracker-2", "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
             "state_values": ["100"], "state_space": "scalar", "contributing_detection_ids": ["det-2"],
             "ancestry": [], "transformation_record": "identity", "track_digest": "sha256:" + "f" * 64},
        ],
        "transformations": [
            {"transformation_id": "xf-1", "edge_id": "e12", "track_id": "trk-1", "kind": "additive_offset", "offset": "0"},
            {"transformation_id": "xf-2", "edge_id": "e12", "track_id": "trk-2", "kind": "additive_offset", "offset": "0"},
        ],
        "comparison_edges": [
            {"edge_id": "e12", "source_track_id": "trk-1", "target_track_id": "trk-2",
             "orientation": "source_to_target", "comparison_space_id": "cmp-1",
             "transformation_id": "family-1", "discrepancy": "0", "coreference_provenance": "test-declared"},
        ],
        "provenance": ancestry_graph,
        "derived_problem": {"D": [], "r": []},
        "payload_digest": "PLACEHOLDER",
        "independence_policy": policy,
    }
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def _disjoint_graph():
    return [
        _node("source_record:1", "source_record", []),
        _node("source_record:2", "source_record", []),
        _node("detection:det-1", "detection", ["source_record:1"]),
        _node("detection:det-2", "detection", ["source_record:2"]),
        _node("track:trk-1", "local_track", ["detection:det-1"]),
        _node("track:trk-2", "local_track", ["detection:det-2"]),
        _node("comparison:e12", "declared_comparison", ["track:trk-1", "track:trk-2"]),
    ]


def _shared_direct_detection_graph():
    """Both tracks share the SAME detection as a direct parent."""
    return [
        _node("source_record:1", "source_record", []),
        _node("detection:shared", "detection", ["source_record:1"]),
        _node("track:trk-1", "local_track", ["detection:shared"]),
        _node("track:trk-2", "local_track", ["detection:shared"]),
        _node("comparison:e12", "declared_comparison", ["track:trk-1", "track:trk-2"]),
    ]


def _shared_remote_ancestor_graph():
    """Different paths (one via an extra feeder node) reach the same
    source_record."""
    return [
        _node("source_record:shared", "source_record", []),
        _node("detection:det-1", "detection", ["source_record:shared"]),
        _node("feeder:secondary", "track_feeder", ["source_record:shared"], feeder="secondary"),
        _node("detection:det-2", "detection", ["source_record:shared"]),
        _node("track:trk-1", "local_track", ["detection:det-1", "feeder:secondary"]),
        _node("track:trk-2", "local_track", ["detection:det-2"]),
        _node("comparison:e12", "declared_comparison", ["track:trk-1", "track:trk-2"]),
    ]


# --- 1. Disjoint ancestry accepted ----------------------------------------

def test_disjoint_ancestry_accepted():
    doc = _two_track_doc(_disjoint_graph(), _policy(["e12"]))
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons
    prov = check_independence(ver)
    assert prov.accepted
    assert prov.claimed_independent_edges == ["e12"]


# --- 2. Shared direct detection rejected -----------------------------------

def test_shared_direct_detection_rejected_under_independence_claim():
    doc = _two_track_doc(_shared_direct_detection_graph(), _policy(["e12"]))
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons
    prov = check_independence(ver)
    assert not prov.accepted
    assert prov.reason == "UNDECLARED_SHARED_ANCESTRY"


# --- 3-4. Shared remote ancestor / different paths to the same record ----

def test_shared_remote_ancestor_via_different_paths_rejected():
    doc = _two_track_doc(_shared_remote_ancestor_graph(), _policy(["e12"]))
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons
    prov = check_independence(ver)
    assert not prov.accepted
    assert prov.reason == "UNDECLARED_SHARED_ANCESTRY"
    assert "source_record:shared" in prov.message


# --- 5. Same originating source, genuinely distinct records --------------

def test_same_originating_source_but_distinct_records_accepted():
    """Two tracks whose detections both came from the SAME physical
    source (originating_source_id) but on two genuinely SEPARATE
    source_record nodes -- same sensor, two different readings. Same
    source alone must not trigger refusal, only an actually SHARED
    record does."""
    graph = [
        _node("source_record:reading-1", "source_record", [], source="src-1"),
        _node("source_record:reading-2", "source_record", [], source="src-1"),  # same source, different record
        _node("detection:det-1", "detection", ["source_record:reading-1"], source="src-1"),
        _node("detection:det-2", "detection", ["source_record:reading-2"], source="src-1"),
        _node("track:trk-1", "local_track", ["detection:det-1"], source="src-1"),
        _node("track:trk-2", "local_track", ["detection:det-2"], source="src-1"),
        _node("comparison:e12", "declared_comparison", ["track:trk-1", "track:trk-2"]),
    ]
    doc = _two_track_doc(graph, _policy(["e12"]))
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons
    prov = check_independence(ver)
    assert prov.accepted
    assert prov.claimed_independent_edges == ["e12"]


# --- 6. Explicitly declared correlated reuse distinguished from independence --

def test_declared_correlated_reuse_accepted_but_not_relabelled_independent():
    doc = _two_track_doc(_shared_remote_ancestor_graph(), _policy(["e12"], correlated_reuse=["e12"]))
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons
    prov = check_independence(ver)
    assert prov.accepted
    assert prov.correlated_reuse_edges == ["e12"]
    assert "e12" not in prov.claimed_independent_edges


# --- 7. Ancestry cycle rejected --------------------------------------------

def test_ancestry_cycle_rejected():
    graph = [
        _node("a", "source_record", ["b"]),
        _node("b", "detection", ["a"]),
    ]
    doc = _two_track_doc(graph, None)
    del doc["independence_policy"]
    doc["payload_digest"] = compute_payload_digest(doc)
    ver = verify_snapshot_doc(doc)
    assert not ver.accepted
    assert any("cycle" in msg for msg in ver.reasons)


# --- 8. Dangling ancestry rejected -----------------------------------------

def test_dangling_ancestry_parent_rejected():
    graph = [_node("track:trk-1", "local_track", ["detection:does-not-exist"])]
    doc = _two_track_doc(graph, None)
    del doc["independence_policy"]
    doc["payload_digest"] = compute_payload_digest(doc)
    ver = verify_snapshot_doc(doc)
    assert not ver.accepted
    assert any("unknown parent_id" in msg for msg in ver.reasons)


# --- 9. Duplicate provenance-node ID rejected ------------------------------

def test_duplicate_ancestry_node_id_rejected():
    graph = [
        _node("dup", "source_record", []),
        _node("dup", "detection", []),
    ]
    doc = _two_track_doc(graph, None)
    del doc["independence_policy"]
    doc["payload_digest"] = compute_payload_digest(doc)
    ver = verify_snapshot_doc(doc)
    assert not ver.accepted
    assert any("duplicate ancestry node_id" in msg for msg in ver.reasons)


# --- 10. Incomplete ancestry rejected ---------------------------------------

def test_incomplete_ancestry_missing_intermediate_node_rejected():
    """A declared_comparison references a track node that was never
    declared in the graph at all -- an incomplete ancestry declaration,
    caught as a dangling reference."""
    graph = [
        _node("track:trk-1", "local_track", []),
        _node("comparison:e12", "declared_comparison", ["track:trk-1", "track:trk-2"]),
    ]
    doc = _two_track_doc(graph, _policy(["e12"]))
    ver = verify_snapshot_doc(doc)
    assert not ver.accepted
    assert any("unknown parent_id" in msg for msg in ver.reasons)


# --- 11. Path-order changes do not affect closure --------------------------

def test_path_order_does_not_affect_closure():
    graph = _shared_remote_ancestor_graph()
    reordered = list(reversed(graph))
    from tracking_adapter_format import parse_ancestry_node

    nodes_a = [parse_ancestry_node(n) for n in graph]
    nodes_b = [parse_ancestry_node(n) for n in reordered]
    assert compute_closure(nodes_a, "track:trk-1") == compute_closure(nodes_b, "track:trk-1")


# --- 12. Node relabelling preserves the result -----------------------------

def test_node_relabelling_preserves_the_admissibility_result():
    # Deliberately does NOT rename "comparison:e12" itself -- that node's
    # own id is a structurally DERIVED convention (f"comparison:{edge_id}",
    # per tracking_adapter_provenance.check_independence's own lookup),
    # not a free label; only the evidence-chain nodes it points to are
    # relabelled here.
    rename = {
        "source_record:shared": "SR-X", "detection:det-1": "DET-1", "detection:det-2": "DET-2",
        "feeder:secondary": "FEEDER-X", "track:trk-1": "TRACK-1", "track:trk-2": "TRACK-2",
    }

    def relabel(graph):
        out = []
        for n in graph:
            n2 = dict(n)
            n2["node_id"] = rename.get(n["node_id"], n["node_id"])
            n2["parent_ids"] = [rename.get(p, p) for p in n["parent_ids"]]
            out.append(n2)
        return out

    original = _two_track_doc(_shared_remote_ancestor_graph(), _policy(["e12"]))
    relabelled = _two_track_doc(relabel(_shared_remote_ancestor_graph()), _policy(["e12"]))

    ver_orig = verify_snapshot_doc(original)
    ver_new = verify_snapshot_doc(relabelled)
    assert ver_orig.accepted and ver_new.accepted

    prov_orig = check_independence(ver_orig)
    prov_new = check_independence(ver_new)
    assert prov_orig.accepted == prov_new.accepted == False
    assert prov_orig.reason == prov_new.reason == "UNDECLARED_SHARED_ANCESTRY"


# --- 13. Ancestry tamper changes the digest --------------------------------

def test_ancestry_tamper_changes_the_payload_digest():
    doc = _two_track_doc(_disjoint_graph(), _policy(["e12"]))
    original_digest = doc["payload_digest"]

    tampered = copy.deepcopy(doc)
    tampered["provenance"][0]["parent_ids"] = ["some-new-unrelated-parent-that-does-not-exist"]
    # payload_digest NOT recomputed -- simulates tampering under an old digest.
    ver = verify_snapshot_doc(tampered)
    assert not ver.accepted
    # Either the dangling reference is caught, or (if we had recomputed
    # the digest to match) it would be a digest mismatch instead --
    # confirm the ORIGINAL digest no longer matches the tampered content.
    assert compute_payload_digest({**tampered, "payload_digest": "x"}) != original_digest


# --- 14. Generator and independent verifier calculate the same closure ---

def test_provenance_and_verifier_closure_implementations_agree():
    from tracking_adapter_format import parse_ancestry_node

    graph = _shared_remote_ancestor_graph()
    nodes = [parse_ancestry_node(n) for n in graph]

    for target in ("track:trk-1", "track:trk-2", "detection:det-1", "feeder:secondary"):
        closure_provenance = compute_closure(nodes, target)
        closure_verifier = compute_ancestry_closure(nodes, target)
        assert closure_provenance == closure_verifier


# --- 15. Refusal proves neither the certificate emitter nor R21 is invoked --

def test_refusal_prevents_certificate_emission(monkeypatch):
    import subprocess

    def _spy_run(*args, **kwargs):
        raise AssertionError("subprocess.run (e.g. the R21 emitter) must never be invoked on a PROVENANCE REFUSE")

    monkeypatch.setattr(subprocess, "run", _spy_run)

    doc = _two_track_doc(_shared_direct_detection_graph(), _policy(["e12"]))
    with pytest.raises(CertificateError, match="PROVENANCE REFUSE"):
        emit_certificate(doc)


# --- 16. Identical (D, r) can receive different admissibility outcomes ---

def test_identical_D_r_different_admissibility_outcomes():
    accepted_doc = _two_track_doc(_disjoint_graph(), _policy(["e12"]))
    refused_doc = _two_track_doc(_shared_direct_detection_graph(), _policy(["e12"]))

    ver_accepted = verify_snapshot_doc(accepted_doc)
    ver_refused = verify_snapshot_doc(refused_doc)
    assert ver_accepted.accepted and ver_refused.accepted
    assert ver_accepted.D == ver_refused.D
    assert ver_accepted.r == ver_refused.r

    prov_accepted = check_independence(ver_accepted)
    prov_refused = check_independence(ver_refused)
    assert prov_accepted.accepted is True
    assert prov_refused.accepted is False
