#!/usr/bin/env python3
"""
refinement_witnesses.py

Explicit refined-complex constructions for the four refinement witnesses of
the paper's "Admissible refinement persistence" section (subdivide U1,
subdivide U2, subdivide all regions, insert bridge). Each witness declares
its refined vertices, refined (oriented) edges, which coarse edge each
refined edge lies over (if any), and a declared refined cycle z'.

This replaces the earlier scaffolding in
archive/deprecated_universal_refinement_scaffold/ (refinement_classifier.py
and ocaml/refinement_theorem.ml), which checked a different, stronger
four-condition scheme (cochain-map naturality, chain-map naturality, pairing
adjointness, H1 surjectivity) and stored the paper's claimed pairing values
as literal constants with no supporting construction. That scheme is not
what the paper's Theorem (thm:witness-persistence / thm:universal-persistence)
states. The theorem only requires conditions (A1)-(A4); see
refinement_checker.py.

All coordinates match examples/four_cycle.json exactly:
    vertices: U1, U2, U3, U4
    edges:    e12 (U1->U2), e23 (U2->U3), e34 (U3->U4), e14 (U1->U4)
    residue r = (1, 1, 1, -2)
    cycle z  = (-1, -1, -1, 1)
"""

from dataclasses import dataclass, field
from fractions import Fraction
from typing import List, Optional


@dataclass(frozen=True)
class Edge:
    name: str
    src: str
    tgt: str
    # Name of the coarse edge this refined edge lies over under the
    # refinement map rho^*, or None if this edge is genuinely new
    # (an internal split edge or an inserted bridge).
    over: Optional[str] = None
    over_sign: Fraction = Fraction(1)


@dataclass
class CoarseComplex:
    vertices: List[str]
    edges: List[Edge]
    residue: List[Fraction]
    cycle: List[Fraction]


@dataclass
class Witness:
    name: str
    description: str
    vertices: List[str]
    edges: List[Edge]
    # Declared refined cycle z', aligned index-for-index with `edges`.
    declared_z_prime: List[Fraction]
    # Vertex-level pullback rho_0^* : C^0(coarse) -> C^0(refined), given as
    # the coarse parent of each refined vertex ("which coarse vertex does
    # this refined vertex lie over"). Every refined vertex must map to
    # exactly one coarse vertex -- this is a genuine quotient/subdivision
    # map, not an arbitrary correspondence. Used only to check cochain-map
    # naturality (delta'^0 rho_0^* = rho_1^* delta^0); it plays no role in
    # (A1)-(A4) themselves.
    vertex_over: dict = field(default_factory=dict)
    # The value the paper's table claims for this witness, kept only for
    # comparison -- it is not assumed or reproduced by construction.
    legacy_claimed_pairing: Optional[Fraction] = None


def _F(*xs) -> List[Fraction]:
    return [Fraction(x) for x in xs]


COARSE = CoarseComplex(
    vertices=["U1", "U2", "U3", "U4"],
    edges=[
        Edge("e12", "U1", "U2"),
        Edge("e23", "U2", "U3"),
        Edge("e34", "U3", "U4"),
        Edge("e14", "U1", "U4"),
    ],
    residue=_F(1, 1, 1, -2),
    cycle=_F(-1, -1, -1, 1),
)


# ---------------------------------------------------------------------------
# Witness 1: subdivide U1 into U1a (incoming half) / U1b (outgoing half).
#
# Walk (all edges oriented along the same directed traversal, so the
# declared cycle is simply all +1's):
#   U1b --e12'--> U2 --e23--> U3 --e34--> U4 --e14r--> U1a --s1--> U1b
# e14r runs opposite to the coarse edge e14 (U1->U4), hence over_sign=-1.
# ---------------------------------------------------------------------------
SUBDIVIDE_U1 = Witness(
    name="subdivide_U1",
    description="Split U1 into U1a (incoming half) and U1b (outgoing half), "
                 "joined by an internal edge s1.",
    vertices=["U1a", "U1b", "U2", "U3", "U4"],
    edges=[
        Edge("e12p", "U1b", "U2", over="e12", over_sign=Fraction(1)),
        Edge("e23", "U2", "U3", over="e23", over_sign=Fraction(1)),
        Edge("e34", "U3", "U4", over="e34", over_sign=Fraction(1)),
        Edge("e14r", "U4", "U1a", over="e14", over_sign=Fraction(-1)),
        Edge("s1", "U1a", "U1b", over=None),
    ],
    declared_z_prime=_F(1, 1, 1, 1, 1),
    vertex_over={"U1a": "U1", "U1b": "U1", "U2": "U2", "U3": "U3", "U4": "U4"},
    legacy_claimed_pairing=Fraction(-7, 2),
)


# ---------------------------------------------------------------------------
# Witness 2: subdivide U2 into U2a (incoming half) / U2b (outgoing half).
#   U1 --e12'--> U2a --s2--> U2b --e23'--> U3 --e34--> U4 --e14r--> U1
# ---------------------------------------------------------------------------
SUBDIVIDE_U2 = Witness(
    name="subdivide_U2",
    description="Split U2 into U2a (incoming half) and U2b (outgoing half), "
                 "joined by an internal edge s2.",
    vertices=["U1", "U2a", "U2b", "U3", "U4"],
    edges=[
        Edge("e12p", "U1", "U2a", over="e12", over_sign=Fraction(1)),
        Edge("s2", "U2a", "U2b", over=None),
        Edge("e23p", "U2b", "U3", over="e23", over_sign=Fraction(1)),
        Edge("e34", "U3", "U4", over="e34", over_sign=Fraction(1)),
        Edge("e14r", "U4", "U1", over="e14", over_sign=Fraction(-1)),
    ],
    declared_z_prime=_F(1, 1, 1, 1, 1),
    vertex_over={"U1": "U1", "U2a": "U2", "U2b": "U2", "U3": "U3", "U4": "U4"},
    legacy_claimed_pairing=Fraction(-4),
)


# ---------------------------------------------------------------------------
# Witness 3: subdivide all four regions the same way.
#   U1b->U2a->U2b->U3a->U3b->U4a->U4b->U1a->U1b
# ---------------------------------------------------------------------------
SUBDIVIDE_ALL = Witness(
    name="subdivide_all",
    description="Split all four vertices into incoming/outgoing halves, "
                 "each joined by an internal edge.",
    vertices=["U1a", "U1b", "U2a", "U2b", "U3a", "U3b", "U4a", "U4b"],
    edges=[
        Edge("e12p", "U1b", "U2a", over="e12", over_sign=Fraction(1)),
        Edge("s2", "U2a", "U2b", over=None),
        Edge("e23p", "U2b", "U3a", over="e23", over_sign=Fraction(1)),
        Edge("s3", "U3a", "U3b", over=None),
        Edge("e34p", "U3b", "U4a", over="e34", over_sign=Fraction(1)),
        Edge("s4", "U4a", "U4b", over=None),
        Edge("e14r", "U4b", "U1a", over="e14", over_sign=Fraction(-1)),
        Edge("s1", "U1a", "U1b", over=None),
    ],
    declared_z_prime=_F(1, 1, 1, 1, 1, 1, 1, 1),
    vertex_over={
        "U1a": "U1", "U1b": "U1",
        "U2a": "U2", "U2b": "U2",
        "U3a": "U3", "U3b": "U3",
        "U4a": "U4", "U4b": "U4",
    },
    legacy_claimed_pairing=Fraction(-5, 4),
)


# ---------------------------------------------------------------------------
# Witness 4: insert a bridge edge directly between U1 and U2, with no new
# vertex. The bridge is a genuinely new 1-cell (over=None): it does not lie
# over any coarse edge, so it is a duplicate of e12's endpoints but not its
# data. The original four coarse edges are unchanged and pull back to
# themselves via the identity.
# ---------------------------------------------------------------------------
INSERT_BRIDGE = Witness(
    name="insert_bridge",
    description="Add a new edge b12 directly between U1 and U2, alongside "
                 "the unchanged original four-cycle.",
    vertices=["U1", "U2", "U3", "U4"],
    edges=[
        Edge("e12", "U1", "U2", over="e12", over_sign=Fraction(1)),
        Edge("e23", "U2", "U3", over="e23", over_sign=Fraction(1)),
        Edge("e34", "U3", "U4", over="e34", over_sign=Fraction(1)),
        Edge("e14", "U1", "U4", over="e14", over_sign=Fraction(1)),
        Edge("b12", "U1", "U2", over=None),
    ],
    declared_z_prime=_F(-1, -1, -1, 1, 0),
    # Identity: insert_bridge adds no new vertex, only a new edge b12
    # between the two existing vertices U1 and U2. This is exactly why
    # naturality fails at b12's row -- see refinement_checker.py.
    vertex_over={"U1": "U1", "U2": "U2", "U3": "U3", "U4": "U4"},
    legacy_claimed_pairing=Fraction(-5),
)


ALL_WITNESSES = [SUBDIVIDE_U1, SUBDIVIDE_U2, SUBDIVIDE_ALL, INSERT_BRIDGE]
