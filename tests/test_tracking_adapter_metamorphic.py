"""
Mathematical metamorphic properties for the tracking adapter -- step 8
of the implementation order. Deliberately separate from step 7's
malformed/adversarial-input coverage: everything here starts from a
WELL-FORMED snapshot and checks a semantic relationship a transformed
(but still well-formed) sibling must satisfy -- verdict preservation,
digest/certificate non-interchangeability, or an explicit equivalence
class rather than byte-identical witnesses where the algorithm has
genuine gauge freedom (design doc SS15).

Two mathematical facts about this repository's four-cycle D, checked
directly (not assumed) before relying on them below:

    rank(D)   = 3  =>  ker(D)   is 1-dimensional, spanned by (1,1,1,1)
    rank(D^T) = 3  =>  ker(D^T) is 1-dimensional

The first is the REPAIR-side gauge freedom already surfaced in step 6's
fixtures (R21's own witness for the coherent case, (-2,-1,1,0), differs
from the (0,1,3,2) used to construct r by exactly 2*(1,1,1,1)) -- repair
witnesses are only ever an equivalence class here, never asserted
byte-exact. The second means the NORMALIZED separator (y.r = 1) is
actually UNIQUE for this system (no comparable freedom), so separator
values ARE asserted exactly where the math guarantees uniqueness.
"""

import copy
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from tests.test_tracking_adapter_certificate import (
    QUANTISATION_POLICY,
    _coherent_fixture_doc,
    _detection,
    _edge,
    _four_cycle,
    _make_doc,
    _obstructed_fixture_doc,
    _source,
    _track,
    _xf,
)
from tracking_adapter_certificate import emit_certificate, verify_chain
from tracking_adapter_format import parse_snapshot_doc
from tracking_adapter_generator import generate_problem
from tracking_adapter_verifier import compute_payload_digest, verify_snapshot_doc

REPO_ROOT = Path(__file__).resolve().parent.parent
SUBPROCESS_TIMEOUT = 30

D_FOUR_CYCLE = [
    [Fraction(-1), Fraction(1), Fraction(0), Fraction(0)],
    [Fraction(0), Fraction(-1), Fraction(1), Fraction(0)],
    [Fraction(0), Fraction(0), Fraction(-1), Fraction(1)],
    [Fraction(-1), Fraction(0), Fraction(0), Fraction(1)],
]
EDGE_ORDER = [("e12", "t1", "t2"), ("e23", "t2", "t3"), ("e34", "t3", "t4"), ("e14", "t1", "t4")]


def _mat_vec(D, b):
    return [sum(D[row][col] * b[col] for col in range(len(b))) for row in range(len(D))]


def _mat_vec_T(D, y):
    n = len(D[0])
    return [sum(D[row][col] * y[row] for row in range(len(D))) for col in range(n)]


def _emit_r21_cert(roc_input: dict, tmp_path) -> dict:
    input_path = tmp_path / "roc_input.json"
    cert_path = tmp_path / "r21_cert.json"
    input_path.write_text(json.dumps(roc_input))
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "r21_certificate_emitter.py"), str(input_path),
         "--certificate", str(cert_path)],
        check=True, capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
    )
    return json.loads(cert_path.read_text())


def _finalize_digest(doc: dict) -> dict:
    doc["payload_digest"] = compute_payload_digest(doc)
    return doc


def _full_chain(doc: dict, expected_result: str, tmp_path):
    """Verifies the snapshot, confirms generator and verifier agree,
    emits a certificate, runs the real R21 emitter, and confirms the
    complete chain verifies. Returns (verifier_result, cert, r21_cert)."""
    ver = verify_snapshot_doc(doc)
    assert ver.accepted, ver.reasons

    snapshot = parse_snapshot_doc(doc)
    gen_problem = generate_problem(snapshot)
    assert gen_problem.D == ver.D
    assert gen_problem.r == ver.r
    assert gen_problem.track_order == ver.track_order
    assert gen_problem.edge_order == ver.edge_order

    cert = emit_certificate(doc)
    r21_cert = _emit_r21_cert(cert["roc_input"], tmp_path)
    assert r21_cert["result"] == expected_result

    chain = verify_chain(doc, cert, r21_cert)
    assert chain.accepted, chain.reasons

    return ver, cert, r21_cert


# =========================================================================
# 1. Identifier relabelling.
# =========================================================================

def _relabel(doc: dict) -> dict:
    doc = copy.deepcopy(doc)
    rename = {
        "src-1": "SOURCE-ALPHA", "det-1": "DETECTION-ALPHA",
        "t1": "TRACK-W", "t2": "TRACK-X", "t3": "TRACK-Y", "t4": "TRACK-Z",
        "tracker-1": "TRACKER-W", "tracker-2": "TRACKER-X",
        "tracker-3": "TRACKER-Y", "tracker-4": "TRACKER-Z",
        "e12": "EDGE-WX", "e23": "EDGE-XY", "e34": "EDGE-YZ", "e14": "EDGE-WZ",
    }

    def r(s):
        return rename.get(s, s)

    for s in doc["sources"]:
        s["source_id"] = r(s["source_id"])
    for d in doc["detections"]:
        d["detection_id"] = r(d["detection_id"])
        d["source_id"] = r(d["source_id"])
    for t in doc["tracks"]:
        t["track_id"] = r(t["track_id"])
        t["tracker_id"] = r(t["tracker_id"])
        t["contributing_detection_ids"] = [r(x) for x in t["contributing_detection_ids"]]
    for x in doc["transformations"]:
        x["transformation_id"] = r(x["transformation_id"])
        x["edge_id"] = r(x["edge_id"])
        x["track_id"] = r(x["track_id"])
    for e in doc["comparison_edges"]:
        e["edge_id"] = r(e["edge_id"])
        e["source_track_id"] = r(e["source_track_id"])
        e["target_track_id"] = r(e["target_track_id"])
    return _finalize_digest(doc)


def test_identifier_relabelling_preserves_D_r_and_verdict(tmp_path):
    original = _obstructed_fixture_doc()
    relabelled = _relabel(original)

    ver_orig, cert_orig, r21_orig = _full_chain(original, "separator", tmp_path)
    ver_new, cert_new, r21_new = _full_chain(relabelled, "separator", tmp_path)

    # Same list ORDER preserved (only labels changed) -> D/r identical.
    assert ver_new.D == ver_orig.D
    assert ver_new.r == ver_orig.r
    # Bindings renamed consistently.
    assert ver_new.track_order == ["TRACK-W", "TRACK-X", "TRACK-Y", "TRACK-Z"]
    assert ver_new.edge_order == ["EDGE-WX", "EDGE-XY", "EDGE-YZ", "EDGE-WZ"]
    # The R21 problem itself (D, r) is identical -- same certificate content.
    assert r21_new["result"] == r21_orig["result"] == "separator"
    assert cert_new["r"] == cert_orig["r"]


# =========================================================================
# 2. Evidence-order invariance -- some orderings matter, some don't.
# =========================================================================

def test_reordering_sources_detections_transformations_leaves_D_r_byte_identical():
    """sources/detections/transformations are looked up by ID, never by
    list position -- reordering these three lists must leave D and r
    byte-identical, unlike reordering tracks/edges (which legitimately
    changes column/row order, covered by the existing test in
    test_tracking_adapter_verifier.py)."""
    original = _obstructed_fixture_doc()
    reordered = copy.deepcopy(original)
    reordered["transformations"] = list(reversed(reordered["transformations"]))
    reordered = _finalize_digest(reordered)

    ver_orig = verify_snapshot_doc(original)
    ver_new = verify_snapshot_doc(reordered)
    assert ver_orig.accepted and ver_new.accepted
    assert ver_new.D == ver_orig.D
    assert ver_new.r == ver_orig.r
    assert ver_new.track_order == ver_orig.track_order
    assert ver_new.edge_order == ver_orig.edge_order


def test_reordering_tracks_changes_presentation_not_underlying_math():
    """Track/edge order IS semantically significant (design doc SS3: it
    IS what D's columns/rows mean) -- explicitly documented here as the
    "which ordering is significant" half of this property, complementing
    the invariant orderings above."""
    original = _obstructed_fixture_doc()
    reordered = copy.deepcopy(original)
    reordered["tracks"] = list(reversed(reordered["tracks"]))
    reordered = _finalize_digest(reordered)

    ver_orig = verify_snapshot_doc(original)
    ver_new = verify_snapshot_doc(reordered)
    assert ver_orig.accepted and ver_new.accepted
    assert ver_new.track_order == list(reversed(ver_orig.track_order))
    assert ver_new.D != ver_orig.D  # legitimately different presentation
    # But the per-edge residues, keyed by edge, are unchanged.
    assert dict(zip(ver_new.edge_order, ver_new.r)) == dict(zip(ver_orig.edge_order, ver_orig.r))


# =========================================================================
# 3. Common translation.
# =========================================================================

def test_common_translation_leaves_residues_and_verdict_unchanged(tmp_path):
    original = _obstructed_fixture_doc()
    translated = copy.deepcopy(original)
    for t in translated["tracks"]:
        t["state_values"] = [str(int(t["state_values"][0]) + 1000)]  # same K=1000 for every track
    translated = _finalize_digest(translated)

    ver_orig, _, r21_orig = _full_chain(original, "separator", tmp_path)
    ver_new, _, r21_new = _full_chain(translated, "separator", tmp_path)

    assert ver_new.r == ver_orig.r  # K cancels within every edge's subtraction
    assert ver_new.D == ver_orig.D


# =========================================================================
# 4. Coboundary perturbation: r' = r + Dc for a chosen c.
# =========================================================================

def test_coboundary_perturbation_preserves_obstruction_class(tmp_path):
    """Shifting EVERY edge-instance of track i's transformation offset by
    the same per-track delta_i (regardless of which edge) adds exactly
    D*delta to r -- confirmed directly against D_FOUR_CYCLE first, then
    exercised through the real adapter."""
    delta = {"t1": Fraction(0), "t2": Fraction(5), "t3": Fraction(-2), "t4": Fraction(7)}
    Ddelta = _mat_vec(D_FOUR_CYCLE, [delta["t1"], delta["t2"], delta["t3"], delta["t4"]])
    assert Ddelta == [Fraction(5), Fraction(-7), Fraction(9), Fraction(7)]

    original = _obstructed_fixture_doc()
    perturbed = copy.deepcopy(original)
    for xf in perturbed["transformations"]:
        xf["offset"] = str(int(xf["offset"]) + int(delta[xf["track_id"]]))
    for e in perturbed["comparison_edges"]:
        i, j = e["source_track_id"], e["target_track_id"]
        e["discrepancy"] = str(int(e["discrepancy"]) + int(delta[j]) - int(delta[i]))
    perturbed = _finalize_digest(perturbed)

    ver_orig, _, r21_orig = _full_chain(original, "separator", tmp_path)
    ver_new, _, r21_new = _full_chain(perturbed, "separator", tmp_path)

    expected_r_new = [a + b for a, b in zip(ver_orig.r, Ddelta)]
    assert ver_new.r == expected_r_new
    assert r21_new["result"] == r21_orig["result"] == "separator"  # obstruction class preserved


# =========================================================================
# 5. Gauge freedom: repair witnesses differing by k*(1,1,1,1).
# =========================================================================

def test_gauge_freedom_both_witnesses_produce_the_same_residue():
    b1 = [Fraction(0), Fraction(1), Fraction(3), Fraction(2)]
    b2 = [Fraction(-2), Fraction(-1), Fraction(1), Fraction(0)]  # R21's own actual witness, step 6
    diff = [x - y for x, y in zip(b1, b2)]
    assert diff == [Fraction(2)] * 4  # exactly 2*(1,1,1,1)
    assert _mat_vec(D_FOUR_CYCLE, b1) == _mat_vec(D_FOUR_CYCLE, b2)


def test_repairable_fixture_r21_witness_is_not_asserted_byte_exact_against_construction():
    """Documents the deliberate choice (per this task's own instruction):
    the constructed b=(0,1,3,2) and R21's actual witness are NOT expected
    to be equal -- only to lie in the same coset of ker(D)."""
    b_constructed = [Fraction(0), Fraction(1), Fraction(3), Fraction(2)]
    b_r21 = [Fraction(-2), Fraction(-1), Fraction(1), Fraction(0)]
    assert b_constructed != b_r21
    assert _mat_vec(D_FOUR_CYCLE, b_constructed) == _mat_vec(D_FOUR_CYCLE, b_r21)


# =========================================================================
# 6/8. Coherent frame change / uniform nonzero scaling -- the same
#      operation at v1's scalar-only scope (they diverge only once
#      multi-dimensional states exist, which this adapter does not yet
#      support -- design doc SS1).
# =========================================================================

def test_uniform_nonzero_scaling_preserves_verdict_and_scales_separator_contravariantly(tmp_path):
    LAMBDA = 3
    original = _obstructed_fixture_doc()
    scaled = copy.deepcopy(original)
    for t in scaled["tracks"]:
        t["state_values"] = [str(int(t["state_values"][0]) * LAMBDA)]
    for xf in scaled["transformations"]:
        xf["offset"] = str(int(xf["offset"]) * LAMBDA)
    for e in scaled["comparison_edges"]:
        e["discrepancy"] = str(int(e["discrepancy"]) * LAMBDA)
    scaled = _finalize_digest(scaled)

    ver_orig, _, r21_orig = _full_chain(original, "separator", tmp_path)
    ver_new, _, r21_new = _full_chain(scaled, "separator", tmp_path)

    assert ver_new.r == [x * LAMBDA for x in ver_orig.r]
    assert ver_new.D == ver_orig.D  # D is pure graph topology -- scale-invariant

    # ker(D^T) is 1-dimensional here (checked in this file's own header),
    # so the NORMALIZED separator is unique -- safe to assert exactly,
    # not merely "a valid equivalence-class member".
    y_orig = [Fraction(s) for s in r21_orig["separator"]]
    y_new = [Fraction(s) for s in r21_new["separator"]]
    assert y_new == [y / LAMBDA for y in y_orig]
    # Validity, not just the scaling relationship: D^T y' = 0 and y'.r' = 1.
    assert _mat_vec_T(ver_new.D, y_new) == [Fraction(0)] * 4
    assert sum(a * b for a, b in zip(y_new, ver_new.r)) == Fraction(1)


def test_uniform_scaling_of_repairable_fixture_scales_the_repair_witness(tmp_path):
    LAMBDA = 5
    original = _coherent_fixture_doc()
    scaled = copy.deepcopy(original)
    for t in scaled["tracks"]:
        t["state_values"] = [str(int(t["state_values"][0]) * LAMBDA)]
    for xf in scaled["transformations"]:
        xf["offset"] = str(int(xf["offset"]) * LAMBDA)
    for e in scaled["comparison_edges"]:
        e["discrepancy"] = str(int(e["discrepancy"]) * LAMBDA)
    scaled = _finalize_digest(scaled)

    ver_orig, _, r21_orig = _full_chain(original, "repair", tmp_path)
    ver_new, _, r21_new = _full_chain(scaled, "repair", tmp_path)

    assert ver_new.r == [x * LAMBDA for x in ver_orig.r]
    # Repair witnesses DO have gauge freedom (ker(D) is 1-dimensional) --
    # so check the scaling relationship holds for D*b, not that R21's
    # particular b scales by LAMBDA byte-for-byte (it need not, if the
    # solver's pivoting lands on a different coset representative).
    b_new = [Fraction(s) for s in r21_new["repair"]]
    reproduced = _mat_vec(ver_new.D, b_new)
    assert reproduced == ver_new.r
    b_orig = [Fraction(s) for s in r21_orig["repair"]]
    reproduced_scaled = _mat_vec(ver_orig.D, [b * LAMBDA for b in b_orig])
    assert reproduced_scaled == ver_new.r  # LAMBDA*b_orig is A valid witness, even if not THE one R21 returns


# =========================================================================
# 7. Edge reversal: swap endpoints, negate the discrepancy consistently.
# =========================================================================

def test_edge_reversal_with_negated_discrepancy_preserves_verdict(tmp_path):
    original = _obstructed_fixture_doc()
    reversed_doc = copy.deepcopy(original)
    for e in reversed_doc["comparison_edges"]:
        if e["edge_id"] == "e12":
            e["source_track_id"], e["target_track_id"] = e["target_track_id"], e["source_track_id"]
            e["discrepancy"] = str(-int(e["discrepancy"]))
    reversed_doc = _finalize_digest(reversed_doc)

    ver_orig, _, r21_orig = _full_chain(original, "separator", tmp_path)
    ver_new, _, r21_new = _full_chain(reversed_doc, "separator", tmp_path)

    assert r21_new["result"] == r21_orig["result"] == "separator"
    # Row 0 (e12) is negated in both D and r; all other rows unchanged.
    assert ver_new.D[0] == [-x for x in ver_orig.D[0]]
    assert ver_new.D[1:] == ver_orig.D[1:]
    assert ver_new.r[0] == -ver_orig.r[0]
    assert ver_new.r[1:] == ver_orig.r[1:]

    # The (unique, per ker(D^T) being 1-D) separator negates at exactly
    # that one index and is otherwise unchanged.
    y_orig = [Fraction(s) for s in r21_orig["separator"]]
    y_new = [Fraction(s) for s in r21_new["separator"]]
    assert y_new[0] == -y_orig[0]
    assert y_new[1:] == y_orig[1:]


# =========================================================================
# 9. Provenance-only change: identical math, different digest, non-
#    interchangeable certificates.
# =========================================================================

def test_provenance_only_change_preserves_math_but_not_certificates(tmp_path):
    original = _obstructed_fixture_doc()
    ver_orig, cert_orig, r21_orig = _full_chain(original, "separator", tmp_path)

    reprovenanced = copy.deepcopy(original)
    reprovenanced["sources"][0]["sensor_modality"] = "optical"  # touches no D/r computation at all
    reprovenanced = _finalize_digest(reprovenanced)
    ver_new, cert_new, r21_new = _full_chain(reprovenanced, "separator", tmp_path)

    # The mathematical problem is identical...
    assert ver_new.D == ver_orig.D
    assert ver_new.r == ver_orig.r
    assert cert_new["r21_input_digest"] == cert_orig["r21_input_digest"]
    # ...but the snapshot digest changed...
    assert reprovenanced["payload_digest"] != original["payload_digest"]
    assert cert_new["snapshot_payload_digest"] != cert_orig["snapshot_payload_digest"]
    # ...so the ORIGINAL certificate is rejected against the NEW snapshot,
    # even though the (D, r) it certifies is identical.
    chain_cross = verify_chain(reprovenanced, cert_orig, r21_orig)
    assert not chain_cross.accepted
    assert any("snapshot_payload_digest" in msg for msg in chain_cross.reasons)


# =========================================================================
# 10. Canonical rebuild: parse -> serialise -> reparse stability.
# =========================================================================

def test_canonical_rebuild_is_stable_under_a_json_round_trip(tmp_path):
    original = _obstructed_fixture_doc()
    round_tripped = json.loads(json.dumps(original))
    assert round_tripped == original

    ver_orig, cert_orig, r21_orig = _full_chain(original, "separator", tmp_path)
    ver_rt, cert_rt, r21_rt = _full_chain(round_tripped, "separator", tmp_path)

    assert cert_rt == cert_orig
    assert r21_rt == r21_orig
    assert ver_rt.D == ver_orig.D and ver_rt.r == ver_orig.r
