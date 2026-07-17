#!/usr/bin/env python3
"""
tracking_adapter_generator.py

Step 3 of the tracking-adapter implementation order in
`docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md`: derives
`(D, r)` from an `AdapterSnapshot` (step 1) using the design doc's SS6
construction -- one declared per-endpoint transformation per edge, NOT
a single shared per-tracker frame map -- and SS10's decimal-to-exact-
rational conversion (step 2), producing a `roc-input/v1`-ready problem.

SCOPE (v1, matching the design doc SS1's own restriction): each track's
`state_values` must have length exactly 1 -- one scalar coordinate.
Multi-dimensional tracks (position, velocity, ...) need one independent
`(D, r)` system per coordinate, built by calling this module once per
coordinate; that composition is not implemented here.

Transformation family (v1, matching the design doc's own feasibility
spike, SS20): `kind == "additive_offset"` only, `F(x) = x + offset`.

Column order is the ORDER tracks appear in `snapshot.tracks` -- this is
NOT an incidental implementation detail, it is part of `D`'s meaning
(design doc SS3: "columns represent permitted corrections to the local
tracks") and must be documented wherever `D` is reported, not left to
be inferred from array position. Row order is the order comparison
edges appear in `snapshot.comparison_edges`, for the same reason.

This module performs ONE self-consistency check as it builds `r`: the
recomputed discrepancy for each edge (from raw track state + declared
transformations) is compared against that edge's own declared
`discrepancy` field, and a mismatch raises. This is NOT a substitute for
step 4's independent adapter verifier (which must be a SEPARATE module
sharing no reconstruction code with this one, per the design doc SS12)
-- it exists only so a generator built from obviously inconsistent
evidence fails immediately rather than silently emitting a `(D, r)`
nobody asked for.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Tuple

from tracking_adapter_canon import convert_and_verify
from tracking_adapter_format import AdapterSnapshot, ComparisonEdge, LocalTrack, Transformation


class GeneratorError(ValueError):
    """Raised for any evidence-level problem the generator finds while
    deriving (D, r) -- a distinct type from the plain ValueError step 1's
    schema parsing raises, so callers can distinguish "malformed
    snapshot" (tracking_adapter_format) from "well-formed snapshot, but
    the evidence itself does not derive a consistent problem"
    (this module)."""


def _decimal_places(policy: dict, key: str) -> int:
    if key not in policy:
        raise GeneratorError(f"quantisation_policy missing required key {key!r}")
    return policy[key]


def _rounding_mode(policy: dict) -> str:
    if "rounding_mode" not in policy:
        raise GeneratorError("quantisation_policy missing required key 'rounding_mode'")
    return policy["rounding_mode"]


def _scalar_state(track: LocalTrack) -> str:
    if len(track.state_values) != 1:
        raise GeneratorError(
            f"track {track.track_id!r} has {len(track.state_values)} state coordinate(s); "
            f"this generator (v1) only supports exactly 1 (multi-dimensional tracks need one "
            f"independent (D,r) system per coordinate, built by calling this module per-coordinate)"
        )
    return track.state_values[0]


def _find_transformation(transformations: List[Transformation], edge_id: str, track_id: str) -> Transformation:
    matches = [t for t in transformations if t.edge_id == edge_id and t.track_id == track_id]
    if len(matches) != 1:
        # tracking_adapter_format.parse_snapshot_doc already enforces
        # exactly one match at parse time; this is a defensive
        # re-check, not the primary enforcement point.
        raise GeneratorError(
            f"expected exactly 1 transformation for edge {edge_id!r} track {track_id!r}, found {len(matches)}"
        )
    return matches[0]


def _edge_endpoint_value(
    track: LocalTrack,
    transformation: Transformation,
    position_places: int,
    transform_places: int,
    rounding_mode: str,
) -> Fraction:
    """F(x) = x + offset, both x and offset independently converted from
    canonical decimal to exact rational via step 2's cross-checked
    converter, then added exactly."""
    x = Fraction(convert_and_verify(_scalar_state(track), position_places, rounding_mode))
    offset = Fraction(convert_and_verify(transformation.offset, transform_places, rounding_mode))
    return x + offset


@dataclass(frozen=True)
class GeneratedProblem:
    D: List[List[Fraction]]
    r: List[Fraction]
    track_order: List[str]   # track_id per column, in order
    edge_order: List[str]    # edge_id per row, in order


def generate_problem(snapshot: AdapterSnapshot) -> GeneratedProblem:
    position_places = _decimal_places(snapshot.quantisation_policy, "position_decimal_places")
    transform_places = _decimal_places(snapshot.quantisation_policy, "transform_decimal_places")
    rounding_mode = _rounding_mode(snapshot.quantisation_policy)

    track_order = [t.track_id for t in snapshot.tracks]
    col_index: Dict[str, int] = {tid: i for i, tid in enumerate(track_order)}
    track_by_id: Dict[str, LocalTrack] = {t.track_id: t for t in snapshot.tracks}

    n = len(track_order)
    D: List[List[Fraction]] = []
    r: List[Fraction] = []
    edge_order: List[str] = []

    for edge in snapshot.comparison_edges:
        edge_order.append(edge.edge_id)
        i_track = track_by_id[edge.source_track_id]
        j_track = track_by_id[edge.target_track_id]
        xf_i = _find_transformation(snapshot.transformations, edge.edge_id, edge.source_track_id)
        xf_j = _find_transformation(snapshot.transformations, edge.edge_id, edge.target_track_id)

        v_i = _edge_endpoint_value(i_track, xf_i, position_places, transform_places, rounding_mode)
        v_j = _edge_endpoint_value(j_track, xf_j, position_places, transform_places, rounding_mode)
        discrepancy_computed = v_j - v_i

        declared = Fraction(convert_and_verify(edge.discrepancy, position_places, rounding_mode))
        if discrepancy_computed != declared:
            raise GeneratorError(
                f"comparison_edge {edge.edge_id!r}: recomputed discrepancy {discrepancy_computed} "
                f"(from track state + declared transformations) does not match the edge's own "
                f"declared discrepancy {declared} -- evidence is internally inconsistent"
            )

        row = [Fraction(0)] * n
        row[col_index[edge.source_track_id]] = Fraction(-1)
        row[col_index[edge.target_track_id]] = Fraction(1)
        D.append(row)
        r.append(discrepancy_computed)

    return GeneratedProblem(D=D, r=r, track_order=track_order, edge_order=edge_order)


def to_roc_input(problem: GeneratedProblem) -> dict:
    """Renders a `GeneratedProblem` as a `roc-input/v1` document, using
    R21's own canonical rational-string form (`str(Fraction(...))`,
    exactly what `r21_certificate_format.parse_rational` requires)."""
    return {
        "schema": "roc-input/v1",
        "D": [[str(x) for x in row] for row in problem.D],
        "r": [str(x) for x in problem.r],
    }
