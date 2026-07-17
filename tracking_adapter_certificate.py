#!/usr/bin/env python3
"""
tracking_adapter_certificate.py

Step 5 of the tracking-adapter implementation order in
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md` SS16: binds
a verified `(D, r)` derivation into a portable `tracking-adapter-
certificate/v1` certificate, and provides `verify_chain`, which checks
the complete evidence chain --

    tracking snapshot -> verified (D, r) -> canonical roc-input/v1
        -> R21 certificate -> repair or obstruction

-- rejecting any mix-and-match substitution across the chain's stages.

EMISSION AUTHORITY: `emit_certificate` calls `tracking_adapter_
verifier.verify_snapshot_doc` itself and refuses to emit anything unless
that independent verifier accepted the snapshot. `tracking_adapter_
generator.py` may produce a proposed snapshot and a claimed `derived_
problem`, but it is never treated as the authority that certifies its
own derivation -- only the independent verifier's ACCEPT authorizes a
certificate.

WHAT THIS CERTIFICATE PROVES, stated precisely, and what it does not:

    PROVES: the independent adapter verifier reconstructed this exact
    rational problem (D, r) from this canonical snapshot, under this
    declared adapter policy, and every value used to build it is
    attributable to a specific field of that snapshot's evidence.

    DOES NOT PROVE: that the adapter policy is the only correct tracking
    semantics; that the quantised snapshot exactly equals physical
    reality; that `tracking_adapter_verifier.py` itself is formally
    verified (it is ordinary, reviewed Python, not a Rocq-checked
    artifact -- unlike R21's own certificate, which IS backed by a
    machine-checked proof); that the adapter policy matches any external
    (e.g. MIST) standard; or that Stone Soup (or any other evidence
    producer) generated the source evidence correctly. Those remain
    explicit, separately-trusted or externally-validated boundaries --
    see the design doc's own SS19 for the identical caveat about the
    design itself.
"""

import hashlib
import json
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, List

from r21_certificate_format import canonical_input_digest, strict_json_load, validate_closed_keys
from r21_certificate_checker import check_certificate
from tracking_adapter_canon import to_exact_rational_independent
from tracking_adapter_verifier import VerificationResult, verify_snapshot_doc

CERTIFICATE_SCHEMA = "tracking-adapter-certificate/v1"
ADAPTER_POLICY_VERSION = "tracking-adapter-policy/v1"  # names the additive_offset transformation family (design doc SS6)
CONVERSION_POLICY_VERSION = "tracking-adapter-canon/v1"  # names tracking_adapter_canon.py's rounding rules (design doc SS10)

MAX_ATTESTATIONS = 100_000  # resource limit, independent of soundness -- see r21_certificate_format.py's own rationale

CERTIFICATE_KEYS = frozenset({
    "schema_version", "adapter_schema_version", "adapter_policy_version",
    "snapshot_payload_digest", "quantisation_policy", "conversion_policy_version",
    "row_bindings", "column_bindings", "conversion_attestations",
    "D", "r", "roc_input", "r21_input_digest", "certificate_payload_digest",
})
ROW_BINDING_KEYS = frozenset({"row_index", "edge_id"})
COLUMN_BINDING_KEYS = frozenset({"col_index", "track_id"})
ATTESTATION_KEYS = frozenset({
    "attestation_id", "source_object", "source_field",
    "canonical_decimal", "decimal_places", "rounding_mode", "converted_rational",
})


class CertificateError(ValueError):
    """Raised when a certificate cannot be emitted -- e.g. because the
    independent verifier did not accept the snapshot. Distinct from
    plain ValueError so callers can tell "malformed snapshot" apart from
    "well-formed snapshot the verifier rejected"."""


# ---------------------------------------------------------------------
# Emission -- only ever from a snapshot the independent verifier accepted.
# ---------------------------------------------------------------------

def _source_kind_and_collection(source_object: str):
    kind, _, ident = source_object.partition(":")
    collection = {
        "track": "tracks",
        "transformation": "transformations",
        "comparison_edge": "comparison_edges",
    }.get(kind)
    if collection is None:
        raise CertificateError(f"unknown source_object kind: {source_object!r}")
    id_key = {"tracks": "track_id", "transformations": "transformation_id", "comparison_edges": "edge_id"}[collection]
    return collection, id_key, ident


def _resolve_source_value(doc: dict, source_object: str, source_field: str) -> str:
    collection, id_key, ident = _source_kind_and_collection(source_object)
    for item in doc[collection]:
        if item[id_key] == ident:
            if source_field == "state_values[0]":
                return item["state_values"][0]
            if source_field not in item:
                raise CertificateError(f"unknown source_field {source_field!r} on {source_object!r}")
            return item[source_field]
    raise CertificateError(f"source_object {source_object!r} not found in snapshot")


def _build_attestations(doc: dict, result: VerificationResult) -> List[dict]:
    """One attestation per distinct (source_object, source_field) actually
    consumed while reconstructing (D, r): every track's state value,
    every transformation's offset, and every edge's declared
    discrepancy -- deduplicated (a track referenced by two edges gets
    ONE attestation, not two identical ones, since the provenance and
    value do not depend on which edge is asking)."""
    quantisation_policy = doc["quantisation_policy"]
    position_places = quantisation_policy["position_decimal_places"]
    transform_places = quantisation_policy["transform_decimal_places"]
    rounding_mode = quantisation_policy["rounding_mode"]

    attestations: Dict[str, dict] = {}

    for t in doc["tracks"]:
        key = f"track:{t['track_id']}.state_values[0]"
        if key in attestations:
            continue
        canonical_decimal = t["state_values"][0]
        converted = str(Fraction(to_exact_rational_independent(canonical_decimal, position_places, rounding_mode)))
        attestations[key] = {
            "attestation_id": key,
            "source_object": f"track:{t['track_id']}",
            "source_field": "state_values[0]",
            "canonical_decimal": canonical_decimal,
            "decimal_places": position_places,
            "rounding_mode": rounding_mode,
            "converted_rational": converted,
        }

    for xf in doc["transformations"]:
        key = f"transformation:{xf['transformation_id']}.offset"
        canonical_decimal = xf["offset"]
        converted = str(Fraction(to_exact_rational_independent(canonical_decimal, transform_places, rounding_mode)))
        attestations[key] = {
            "attestation_id": key,
            "source_object": f"transformation:{xf['transformation_id']}",
            "source_field": "offset",
            "canonical_decimal": canonical_decimal,
            "decimal_places": transform_places,
            "rounding_mode": rounding_mode,
            "converted_rational": converted,
        }

    for e in doc["comparison_edges"]:
        key = f"comparison_edge:{e['edge_id']}.discrepancy"
        canonical_decimal = e["discrepancy"]
        converted = str(Fraction(to_exact_rational_independent(canonical_decimal, position_places, rounding_mode)))
        attestations[key] = {
            "attestation_id": key,
            "source_object": f"comparison_edge:{e['edge_id']}",
            "source_field": "discrepancy",
            "canonical_decimal": canonical_decimal,
            "decimal_places": position_places,
            "rounding_mode": rounding_mode,
            "converted_rational": converted,
        }

    ordered = [attestations[k] for k in sorted(attestations)]
    if len(ordered) > MAX_ATTESTATIONS:
        raise CertificateError(f"{len(ordered)} attestations exceeds MAX_ATTESTATIONS={MAX_ATTESTATIONS}")
    return ordered


def _canonical_dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _compute_certificate_digest(certificate_without_own_digest: dict) -> str:
    canonical = _canonical_dump(certificate_without_own_digest)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def emit_certificate(doc: dict) -> dict:
    result = verify_snapshot_doc(doc)
    if not result.accepted:
        raise CertificateError(f"snapshot rejected by independent verifier: {result.reasons}")

    row_bindings = [{"row_index": i, "edge_id": eid} for i, eid in enumerate(result.edge_order)]
    column_bindings = [{"col_index": i, "track_id": tid} for i, tid in enumerate(result.track_order)]
    attestations = _build_attestations(doc, result)

    D_strings = [[str(x) for x in row] for row in result.D]
    r_strings = [str(x) for x in result.r]
    # Deliberately independent list objects from D_strings/r_strings below
    # (not the same references) -- roc_input and the certificate's own
    # top-level D/r are logically separate claims that happen to agree,
    # not one shared object, so tampering one in memory cannot silently
    # tamper the other (JSON serialisation would break any such aliasing
    # anyway; this just makes that true in-memory too).
    roc_input = {
        "schema": "roc-input/v1",
        "D": [list(row) for row in D_strings],
        "r": list(r_strings),
    }
    r21_input_digest = canonical_input_digest(result.D, result.r)

    certificate_body = {
        "schema_version": CERTIFICATE_SCHEMA,
        "adapter_schema_version": doc["schema_version"],
        "adapter_policy_version": ADAPTER_POLICY_VERSION,
        "snapshot_payload_digest": doc["payload_digest"],
        "quantisation_policy": doc["quantisation_policy"],
        "conversion_policy_version": CONVERSION_POLICY_VERSION,
        "row_bindings": row_bindings,
        "column_bindings": column_bindings,
        "conversion_attestations": attestations,
        "D": D_strings,
        "r": r_strings,
        "roc_input": roc_input,
        "r21_input_digest": r21_input_digest,
    }
    certificate_body["certificate_payload_digest"] = _compute_certificate_digest(certificate_body)
    return certificate_body


# ---------------------------------------------------------------------
# Chain verification.
# ---------------------------------------------------------------------

@dataclass
class ChainResult:
    accepted: bool = True
    reasons: List[str] = field(default_factory=list)

    def reject(self, msg: str) -> None:
        self.accepted = False
        self.reasons.append(msg)


def verify_chain(snapshot_doc: Any, certificate: Any, r21_certificate: Any) -> ChainResult:
    """Fail-closed, same discipline as `tracking_adapter_verifier.
    verify_snapshot_doc` and `r21_certificate_checker.check_certificate`:
    any unexpected exception is converted into a rejection."""
    result = ChainResult()
    try:
        _verify_chain(snapshot_doc, certificate, r21_certificate, result)
    except Exception as e:
        result.reject(f"unexpected error during chain verification: {e}")
    return result


def verify_chain_files(snapshot_path: str, certificate_path: str, r21_certificate_path: str) -> ChainResult:
    """File-based convenience wrapper: loads all three documents via
    `strict_json_load` (duplicate-JSON-key rejection at the file
    boundary) before delegating to `verify_chain`."""
    result = ChainResult()
    try:
        snapshot_doc = strict_json_load(snapshot_path)
        certificate = strict_json_load(certificate_path)
        r21_certificate = strict_json_load(r21_certificate_path)
    except Exception as e:
        result.reject(f"malformed chain input file: {e}")
        return result
    return verify_chain(snapshot_doc, certificate, r21_certificate)


def _verify_chain(snapshot_doc: Any, certificate: Any, r21_certificate: Any, result: ChainResult) -> None:
    # 1. Verify the snapshot (recomputes its own payload digest internally).
    snap_result = verify_snapshot_doc(snapshot_doc)
    if not snap_result.accepted:
        result.reject(f"snapshot rejected by independent verifier: {snap_result.reasons}")
        return

    if not isinstance(certificate, dict):
        result.reject(f"adapter certificate is not a JSON object: {certificate!r}")
        return
    extra = set(certificate.keys()) - CERTIFICATE_KEYS
    if extra:
        result.reject(f"adapter certificate has unrecognized field(s): {sorted(extra)}")
        return
    missing = CERTIFICATE_KEYS - set(certificate.keys())
    if missing:
        result.reject(f"adapter certificate missing required field(s): {sorted(missing)}")
        return
    if certificate.get("schema_version") != CERTIFICATE_SCHEMA:
        result.reject(f"unrecognized certificate schema_version: {certificate.get('schema_version')!r}")
        return

    body_without_digest = {k: v for k, v in certificate.items() if k != "certificate_payload_digest"}
    expected_cert_digest = _compute_certificate_digest(body_without_digest)
    if certificate.get("certificate_payload_digest") != expected_cert_digest:
        result.reject("adapter certificate payload digest mismatch -- certificate has been tampered with")
        return

    # Binds this certificate to THIS exact snapshot -- rejects "valid
    # adapter certificate paired with another snapshot".
    if certificate["snapshot_payload_digest"] != snapshot_doc.get("payload_digest"):
        result.reject("adapter certificate's snapshot_payload_digest does not match the supplied snapshot")
        return

    # 2. (D, r): trusted values come from the independent reconstruction
    # above, never from the certificate's own claims.
    D, r = snap_result.D, snap_result.r
    track_order, edge_order = snap_result.track_order, snap_result.edge_order

    # 3. Row/column bindings.
    try:
        row_bindings = certificate["row_bindings"]
        for b in row_bindings:
            validate_closed_keys(b, ROW_BINDING_KEYS, "row binding")
        col_bindings = certificate["column_bindings"]
        for b in col_bindings:
            validate_closed_keys(b, COLUMN_BINDING_KEYS, "column binding")
        claimed_edge_order = [b["edge_id"] for b in sorted(row_bindings, key=lambda b: b["row_index"])]
        claimed_track_order = [b["track_id"] for b in sorted(col_bindings, key=lambda b: b["col_index"])]
    except (KeyError, TypeError) as e:
        result.reject(f"malformed row/column bindings: {e}")
        return
    if claimed_edge_order != edge_order:
        result.reject("row_bindings do not match the independently reconstructed edge order")
        return
    if claimed_track_order != track_order:
        result.reject("column_bindings do not match the independently reconstructed track order")
        return

    # 4. Redo every decimal conversion independently, including attribution.
    attestations = certificate["conversion_attestations"]
    if len(attestations) > MAX_ATTESTATIONS:
        result.reject(f"{len(attestations)} attestations exceeds MAX_ATTESTATIONS={MAX_ATTESTATIONS}")
        return
    quantisation_policy = snapshot_doc["quantisation_policy"]
    for att in attestations:
        try:
            validate_closed_keys(att, ATTESTATION_KEYS, "conversion attestation")
            missing_att = ATTESTATION_KEYS - set(att.keys())
            if missing_att:
                result.reject(f"conversion attestation missing field(s): {sorted(missing_att)}")
                continue
            actual_decimal = _resolve_source_value(snapshot_doc, att["source_object"], att["source_field"])
        except (CertificateError, ValueError, TypeError, KeyError) as e:
            result.reject(f"malformed conversion attestation: {e}")
            continue
        if actual_decimal != att["canonical_decimal"]:
            result.reject(
                f"attestation for {att['source_object']}.{att['source_field']} claims canonical_decimal "
                f"{att['canonical_decimal']!r}, but the snapshot's actual value is {actual_decimal!r}"
            )
            continue
        expected_places = (
            quantisation_policy["transform_decimal_places"]
            if att["source_object"].startswith("transformation:")
            else quantisation_policy["position_decimal_places"]
        )
        if att["decimal_places"] != expected_places or att["rounding_mode"] != quantisation_policy["rounding_mode"]:
            result.reject(
                f"attestation for {att['source_object']}.{att['source_field']} uses a conversion policy "
                f"({att['decimal_places']}, {att['rounding_mode']!r}) inconsistent with the snapshot's own "
                f"quantisation_policy ({expected_places}, {quantisation_policy['rounding_mode']!r})"
            )
            continue
        try:
            recomputed = str(Fraction(to_exact_rational_independent(actual_decimal, att["decimal_places"], att["rounding_mode"])))
        except ValueError as e:
            result.reject(f"attestation for {att['source_object']}.{att['source_field']}: {e}")
            continue
        if recomputed != att["converted_rational"]:
            result.reject(
                f"attestation for {att['source_object']}.{att['source_field']}: claimed converted_rational "
                f"{att['converted_rational']!r} does not match recomputed {recomputed!r}"
            )
    if not result.accepted:
        return

    # 5. Rebuild roc-input/v1 from the TRUSTED (D, r), compare to the claim.
    rebuilt_D = [[str(x) for x in row] for row in D]
    rebuilt_r = [str(x) for x in r]
    if certificate["D"] != rebuilt_D:
        result.reject("certificate's D does not match the independently reconstructed D")
        return
    if certificate["r"] != rebuilt_r:
        result.reject("certificate's r does not match the independently reconstructed r")
        return
    rebuilt_roc_input = {"schema": "roc-input/v1", "D": rebuilt_D, "r": rebuilt_r}
    if certificate["roc_input"] != rebuilt_roc_input:
        result.reject("certificate's roc_input does not match the independently rebuilt roc-input/v1")
        return

    # 6-7. Recompute the R21 input digest; compare to the certificate's claim.
    expected_r21_digest = canonical_input_digest(D, r)
    if certificate["r21_input_digest"] != expected_r21_digest:
        result.reject("certificate's r21_input_digest does not match the recomputed digest")
        return

    # 8. The SEPARATE R21 certificate must be bound to the SAME digest --
    # rejects "valid R21 certificate paired with another adapter
    # certificate" and "R21 certificate substitution".
    if not isinstance(r21_certificate, dict) or r21_certificate.get("input_digest") != expected_r21_digest:
        result.reject(
            f"R21 certificate's input_digest ({r21_certificate.get('input_digest') if isinstance(r21_certificate, dict) else r21_certificate!r}) "
            f"does not match the recomputed R21 input digest ({expected_r21_digest!r})"
        )
        return

    # 9. Run R21's own independent checker.
    check_result = check_certificate(D, r, r21_certificate)
    if not check_result.accepted:
        result.reject(f"R21 certificate rejected by r21_certificate_checker: {check_result.reasons}")
        return

    # 10. Every stage agreed -- ACCEPT.
