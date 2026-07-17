#!/usr/bin/env python3
"""
tracking_adapter_provenance.py

Step 10D of the tracking-adapter implementation order
(docs/design/TRACKING_EVIDENCE_TO_RATIONAL_ADAPTER_SPEC.md SS18-19,
inspired by Stone Soup's own data-incest architecture discussion --
see that project's own documentation on track-to-track fusion feedback
loops; this module does NOT claim to prove Stone Soup's statistical
fusion output overconfident, only to check structural evidence
admissibility, a separate and much narrower claim, see below).

GOVERNING DISTINCTION -- every function below depends on keeping this
precise, per this step's own instructions:

    R21 (steps 3-9) asks whether accepted pairwise declarations can be
    repaired coherently -- a MATHEMATICAL question about (D, r).

    This module asks whether those declarations are ADMISSIBLE as
    independent evidence in the first place -- an EVIDENTIARY question
    about the ancestry graph, checked BEFORE (D, r) is ever computed,
    and answered independently of whether (D, r) turns out repairable
    or obstructed. R21 is never used to "detect data incest": two
    tracks with duplicated ancestry can produce a perfectly repairable,
    numerically consistent (D, r) while their independence claim remains
    unsupported -- numerical coherence does not establish evidential
    independence, and this module's REFUSAL is not a repairability
    verdict, it is a decision that (D, r) should not even be computed
    from these declarations under the declared policy.

THREE OUTCOMES, corresponding to three different failure classes:

    SNAPSHOT REJECT   -- malformed ancestry (dangling parent, cycle,
                         duplicate node_id, ...). Purely structural.
                         Handled by tracking_adapter_format.py /
                         tracking_adapter_verifier.py, NOT this module --
                         a malformed graph is rejected regardless of what
                         any independence policy says.
    PROVENANCE REFUSE -- a WELL-FORMED snapshot whose independence claim
                         is not supported by its own ancestry graph.
                         This module's own job. Neither the adapter
                         certificate emitter nor R21 is ever invoked for
                         a refused snapshot (tracking_adapter_
                         certificate.emit_certificate calls this module
                         before building anything).
    PROVENANCE ACCEPT -- either no independence claim is being made at
                         all (no ancestry graph, or no independence_
                         policy declared), or every claimed-independent
                         comparison's ancestry is genuinely disjoint (or
                         its shared ancestry was explicitly declared as
                         permitted correlated reuse, in which case it is
                         accepted STRUCTURALLY but never relabelled
                         independent).

WHAT THIS DOES NOT CLAIM: that a PROVENANCE ACCEPT snapshot's tracks are
statistically independent in the sense a fusion algorithm's own
covariance assumptions require, that Stone Soup's fusion output for any
scenario is overconfident, or that this structural check is a
substitute for a proper information-theoretic or statistical
independence analysis. It checks one thing: whether the DECLARED
evidence-ancestry graph supports the DECLARED independence claim.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from tracking_adapter_format import AncestryNode
from tracking_adapter_verifier import VerificationResult


class ProvenanceError(ValueError):
    """Raised by callers (e.g. tracking_adapter_certificate.
    emit_certificate) that choose to treat a PROVENANCE REFUSE as an
    exception rather than inspect a ProvenanceResult directly."""


@dataclass
class ProvenanceResult:
    accepted: bool = True
    reason: Optional[str] = None
    message: Optional[str] = None
    claimed_independent_edges: List[str] = field(default_factory=list)
    correlated_reuse_edges: List[str] = field(default_factory=list)

    def refuse(self, reason: str, message: str) -> None:
        self.accepted = False
        self.reason = reason
        self.message = message


def compute_closure(nodes: List[AncestryNode], node_id: str) -> frozenset:
    """Transitive closure over `parent_ids`: every `source_record` node
    reachable from `node_id`, arbitrarily far back. Recursive here --
    an INDEPENDENT implementation from `tracking_adapter_verifier.
    compute_ancestry_closure` (an iterative work-list there), sharing no
    code beyond the `AncestryNode` type itself. `tests/test_stonesoup_
    provenance.py` checks both agree on every fixture, which would be a
    meaningless test if the two were actually the same code path."""
    by_id = {n.node_id: n for n in nodes}

    def walk(nid: str, visiting: frozenset) -> frozenset:
        if nid in visiting:
            # A cycle here should already have been caught by
            # tracking_adapter_format.py/tracking_adapter_verifier.py's
            # own structural checks before this function is ever called
            # -- this is a defensive stop, not the primary enforcement.
            return frozenset()
        node = by_id[nid]
        closure = frozenset({nid}) if node.node_type == "source_record" else frozenset()
        for parent_id in node.parent_ids:
            closure = closure | walk(parent_id, visiting | {nid})
        return closure

    return walk(node_id, frozenset())


def check_independence(verified: VerificationResult) -> ProvenanceResult:
    """Checks whether the snapshot's `independence_policy`, if any, is
    actually supported by its ancestry graph. Takes the RESULT of an
    already-successful `verify_snapshot_doc` call (never re-derives
    structural well-formedness itself -- that is the verifier's job,
    already done, per this module's own governing distinction)."""
    result = ProvenanceResult()
    policy = verified.independence_policy
    nodes = verified.ancestry_nodes or []

    if policy is None or not nodes:
        return result  # no independence claim is being made -- nothing to check

    comparison_nodes = {n.node_id: n for n in nodes if n.node_type == "declared_comparison"}

    for edge_id in policy["independent_comparisons"]:
        comparison_node_id = f"comparison:{edge_id}"
        comparison_node = comparison_nodes.get(comparison_node_id)
        if comparison_node is None:
            result.refuse(
                "MISSING_COMPARISON_NODE",
                f"independence_policy claims edge {edge_id!r} independent, but no declared_comparison "
                f"ancestry node {comparison_node_id!r} exists in the graph",
            )
            return result
        if len(comparison_node.parent_ids) != 2:
            result.refuse(
                "MALFORMED_COMPARISON_NODE",
                f"declared_comparison node {comparison_node_id!r} must have exactly 2 parents, "
                f"got {len(comparison_node.parent_ids)}",
            )
            return result

        side_a, side_b = comparison_node.parent_ids
        closure_a = compute_closure(nodes, side_a)
        closure_b = compute_closure(nodes, side_b)
        shared = closure_a & closure_b

        if shared and policy["shared_ancestry_prohibited"]:
            if edge_id in policy["declared_correlated_reuse"]:
                # Explicitly declared correlated reuse: accepted
                # STRUCTURALLY, but this edge is deliberately NOT added
                # to claimed_independent_edges below -- accepting it
                # must never be read as relabelling it independent.
                result.correlated_reuse_edges.append(edge_id)
                continue
            result.refuse(
                "UNDECLARED_SHARED_ANCESTRY",
                f"comparison {edge_id!r} claims independent evidence, but both sides share "
                f"ancestry via source_record(s) {sorted(shared)}, and this reuse was not "
                f"declared in independence_policy.declared_correlated_reuse",
            )
            return result

        result.claimed_independent_edges.append(edge_id)

    return result
