#!/usr/bin/env python3
"""
regional_composition.py

A concrete finite instance of the paper's supported-regional-algebra
machinery (Section 3, "Boundary corrections and associator fields"),
specialised to the square-zero Venn model of Example ex:venn: regions are
subsets of a finite point universe P, the ordinary algebra is A0(S) = k^S
with pointwise multiplication and extension by zero, and the boundary
module is a second copy B(S) = k^S*eps with the same pointwise action, so

    A(S) = A0(S) (x) B(S) = k^S[eps]/(eps^2).

Because extension by zero embeds A0(R) into A0(S) as "zero outside R", an
element of A(S) can be represented directly as a pair of dictionaries over
the *global* universe P (primary part, boundary part) without maintaining
separate per-region vector spaces: "supported on R" simply means "zero
outside R". This is the same model the paper uses in ex:venn; it is not a
simplification of the general theory, it is the theory's own worked
example, implemented directly rather than asserted.

The boundary-corrected product and the associator defect are computed by
literal expansion of Definitions "Raw overlap product", "Boundary-corrected
product", and "Associator defect" -- not by the closed-form four-term
shortcut of Proposition prop:four-term. That closed form is instead
*checked* against this direct computation (see
tests/test_regional_composition.py and closed_form_delta below), the same
way refinement_checker.py cross-checks its cycle-pairing certificate
against an independent exact solver.
"""

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, FrozenSet, Tuple

Region = FrozenSet[int]


@dataclass(frozen=True)
class DualNumber:
    """
    An element of k^P[eps]/(eps^2), represented as two point->coefficient
    maps over the shared universe P. Points absent from a dict have
    coefficient 0. This is exactly A0(P) (+) B(P) of Definition
    "Square-zero regional extension", with A0(P) = k^P pointwise algebra.
    """

    primary: Tuple[Tuple[int, Fraction], ...]
    boundary: Tuple[Tuple[int, Fraction], ...]

    @staticmethod
    def indicator(region: Region) -> "DualNumber":
        """The element 1_region, i.e. pi(x) = indicator of `region`, zero boundary."""
        return DualNumber(
            primary=tuple((p, Fraction(1)) for p in sorted(region)),
            boundary=(),
        )

    def as_dicts(self) -> Tuple[Dict[int, Fraction], Dict[int, Fraction]]:
        return dict(self.primary), dict(self.boundary)

    def support(self) -> Region:
        p, b = self.as_dicts()
        return frozenset(pt for pt, v in {**p, **b}.items() if p.get(pt, 0) != 0 or b.get(pt, 0) != 0)


def _pointwise_product(x: Dict[int, Fraction], y: Dict[int, Fraction]) -> Dict[int, Fraction]:
    out: Dict[int, Fraction] = {}
    for pt in set(x) & set(y):
        v = x[pt] * y[pt]
        if v != 0:
            out[pt] = v
    return out


def _pointwise_sum(*terms: Dict[int, Fraction]) -> Dict[int, Fraction]:
    out: Dict[int, Fraction] = {}
    for term in terms:
        for pt, v in term.items():
            out[pt] = out.get(pt, Fraction(0)) + v
    return {pt: v for pt, v in out.items() if v != 0}


def dual_multiply(a: DualNumber, b: DualNumber) -> DualNumber:
    """
    The full square-zero multiplication of Definition "Square-zero
    regional extension": (x, xi)(y, eta) = (xy, x.eta + xi.y). This is the
    multiplication used inside A(S) for the raw overlap product, applied
    to whatever a and b currently are -- including, for an *inner* corrected
    product fed into an *outer* one, a nonzero boundary component.
    """
    ax, axi = a.as_dicts()
    bx, beta = b.as_dicts()
    primary = _pointwise_product(ax, bx)
    boundary = _pointwise_sum(_pointwise_product(ax, beta), _pointwise_product(axi, bx))
    return DualNumber(
        primary=tuple(sorted(primary.items())),
        boundary=tuple(sorted(boundary.items())),
    )


def restrict(x: DualNumber, region: Region) -> DualNumber:
    p, b = x.as_dicts()
    return DualNumber(
        primary=tuple(sorted((pt, v) for pt, v in p.items() if pt in region)),
        boundary=tuple(sorted((pt, v) for pt, v in b.items() if pt in region)),
    )


def dual_add(a: DualNumber, b: DualNumber) -> DualNumber:
    ap, ab = a.as_dicts()
    bp, bb = b.as_dicts()
    return DualNumber(
        primary=tuple(sorted(_pointwise_sum(ap, bp).items())),
        boundary=tuple(sorted(_pointwise_sum(ab, bb).items())),
    )


@dataclass(frozen=True)
class SeamCorrectionData:
    """
    The seam correction datum lambda_{X,Y}(a,b) = mu_{X,Y} (ab)|_{X n Y} eps
    of Definition "Seam corrections and gauges in a square-zero extension",
    specialised to the Venn model: mu is a single rational constant per
    ordered pair of regions actually used below.
    """

    mu_VW: Fraction
    mu_UvV_W: Fraction
    mu_U_VvW: Fraction
    mu_UV: Fraction


def raw_overlap_product(a: DualNumber, b: DualNumber, U: Region, V: Region) -> DualNumber:
    """
    Definition "Raw overlap product": extend a, b to S = U v V (a no-op in
    this global representation), multiply in A(S), take the representative
    on U n V (restriction, since both factors already vanish outside their
    declared regions and pointwise product vanishes outside the
    intersection automatically).
    """
    return restrict(dual_multiply(a, b), U & V)


def boundary_correction(a: DualNumber, b: DualNumber, U: Region, V: Region, mu: Fraction) -> DualNumber:
    """
    beta_{U,V}(a, b) = mu * (pi(a) pi(b))|_{U n V} * eps, Definition
    "Seam corrections and gauges in a square-zero extension" -- depends
    only on the primary (pi) parts of a, b, and lands entirely in the
    boundary component, by construction support-refining onto U n V.
    """
    ax, _ = a.as_dicts()
    bx, _ = b.as_dicts()
    prod = _pointwise_product(ax, bx)
    restricted = {pt: v for pt, v in prod.items() if pt in (U & V)}
    boundary = {pt: mu * v for pt, v in restricted.items() if mu * v != 0}
    return DualNumber(primary=(), boundary=tuple(sorted(boundary.items())))


def corrected_product(a: DualNumber, b: DualNumber, U: Region, V: Region, mu: Fraction) -> DualNumber:
    """a *_{U,V} b of Definition 'Boundary-corrected product'."""
    return dual_add(raw_overlap_product(a, b, U, V), boundary_correction(a, b, U, V, mu))


@dataclass(frozen=True)
class VennTriple:
    """
    The three-region Venn configuration of Example ex:venn, reused as a
    self-contained "local instance": P = {1..7}, U/V/W chosen so all
    pairwise and triple overlaps, and the unions U v V and V v W, are
    non-empty, with triple overlap U n V n W = {7}.
    """

    U: Region = frozenset({1, 4, 5, 7})
    V: Region = frozenset({2, 4, 6, 7})
    W: Region = frozenset({3, 5, 6, 7})

    @property
    def triple_overlap(self) -> Region:
        return self.U & self.V & self.W


def associator_defect(triple: VennTriple, mu: SeamCorrectionData) -> DualNumber:
    """
    widetilde-alpha_{U,V,W}(1_U, 1_V, 1_W), computed by literal expansion
    of Definition "Associator defect":

        alpha = a *_{U, VvW} (b *_{V,W} c) - (a *_{U,V} b) *_{UvV, W} c

    using the *same* corrected_product for every seam, with the four seam
    constants (mu_VW, mu_{UvV,W}, mu_{U,VvW}, mu_UV) as independent inputs
    -- this is real local product/correction data, not a declared answer.
    Theorem thm:triple-localisation predicts the result is supported on
    U n V n W; that support claim is checked, not assumed, by
    tests/test_regional_composition.py.
    """
    U, V, W = triple.U, triple.V, triple.W
    a, b, c = DualNumber.indicator(U), DualNumber.indicator(V), DualNumber.indicator(W)

    inner_right = corrected_product(b, c, V, W, mu.mu_VW)
    right = corrected_product(a, inner_right, U, V | W, mu.mu_U_VvW)

    inner_left = corrected_product(a, b, U, V, mu.mu_UV)
    left = corrected_product(inner_left, c, U | V, W, mu.mu_UvV_W)

    ap, ab = right.as_dicts()
    lp, lb = left.as_dicts()
    primary = _pointwise_sum(ap, {pt: -v for pt, v in lp.items()})
    boundary = _pointwise_sum(ab, {pt: -v for pt, v in lb.items()})
    return DualNumber(primary=tuple(sorted(primary.items())), boundary=tuple(sorted(boundary.items())))


def closed_form_delta(mu: SeamCorrectionData) -> Fraction:
    """
    The four-term closed form of Proposition prop:four-term / the
    Section-4.3 worked instance:

        Delta_{U,V,W} = mu_{V,W} - mu_{UvV,W} + mu_{U,VvW} - mu_{U,V}

    Provided only as an independent cross-check of associator_defect
    above -- it is never used to *compute* the defect.
    """
    return mu.mu_VW - mu.mu_UvV_W + mu.mu_U_VvW - mu.mu_UV
