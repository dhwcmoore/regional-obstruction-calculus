# Realisability roadmap

## The question

A reviewer can ask: is the paper's displayed obstruction class
structurally forced by the associator calculus, or did the repository
simply choose a convenient residue vector? Put precisely:

> Which residues can actually arise from supported regional composition
> data — and does that realisable space intersect the obstruction classes
> non-trivially, or contain them entirely, or something in between?

Answering this turns the project from "here is a checked finite example"
into "here is the space of all first-order associator residues realisable
under a stated support discipline, and here is how that space relates to
the cohomological obstruction classes." That is a materially bigger
mathematical result than anything currently in this repository — see
item 14 below for exactly how far short of it the current state falls.

## What was checked first, and why

Before writing any realisability theorem or certificate format, the
current associator generator (`associator_residue.py`'s
`four_cycle_instances()`-style construction — item 7) was checked
computationally: what is the image of its parameter-to-residue map?

`realisability_diagnostic.py` builds the map

```text
A : Q^16 -> Q^4
```

(16 = four seams, each with its own independent
`mu_VW`/`mu_UvV_W`/`mu_U_VvW`/`mu_UV`; 4 = the seam residue coordinates
of the four-cycle nerve `N`), one column at a time, by actually running
the literal-expansion-verified `compute_seam_residue` path — not the
closed-form shortcut, and not a hand derivation — on each unit parameter
vector. `tests/test_realisability_diagnostic.py` locks in the result:

```text
rank(A) = 4        (full rank -- A is surjective onto all of C^1(N;Q))
dim ker(A) = 12
```

Checked directly, not just inferred from the rank: the paper's own
residue `(1,1,1,-2)`, the zero residue, and an arbitrary residue
`(3,-5,7,11)` with no relationship to anything else in this repository
are all realisable.

## Why this is a negative result, not a null result

**The current generator imposes no structural constraint at all.** Every
residue in `C^1(N;Q)` — obstructed or exact, paper witness or arbitrary —
is realisable by `four_cycle_instances()`. That is not a subtle finding;
it follows immediately once the construction is examined: each of the
four seams is built from its own fully independent `regional_composition.
VennTriple` instance (its own private seven-point universe `{1..7}`),
with no data shared between seams. Seam `e12` and seam `e23` share the
coarse vertex `U2` in the four-cycle nerve, but nothing in the generator
enforces any relationship between the correction constants assigned to
each — they are sixteen free parameters (four seams times four
constants), and the map from each seam's own four parameters to that
seam's single residue coordinate is already a surjective linear
functional (`Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV`) on its own.
Four independent surjections stacked together are surjective onto the
product space. This was always implicit in `associator_residue.py`'s own
docstring — "a free modelling choice of which pairwise reconciliation
carries the seam's residue... not a claim that the paper's displayed
residue was historically derived this way" — but had not been checked as
a precise linear-algebra fact until now.

**Consequence:** the current generator cannot answer the reviewer
question above. "Every residue is realisable" is a true statement about
it, but a one-paragraph triviality, not the structural classification a
realisability theorem should provide. Attempting to build a realisability
theorem, an analyser module, or a proof-carrying realisability certificate
format on top of the *current* generator would be building real
machinery around a vacuous claim.

## What a non-trivial realisability theorem needs

See `docs/COUPLED_GENERATOR_SPEC.md` for the architectural correction
this points to: the problem is not merely that the seams choose
independent data, but that no regional object exists yet whose identity
could be shared between them. That document settles the architectural
inversion (seams must restrict from one shared regional carrier, not
instantiate private local worlds) without choosing a sharing discipline.

A generator where seams that share regional data are actually constrained
by that sharing — so that not every combination of per-seam correction
data is achievable independently. Candidates, not yet decided or
designed:

- A single shared multiplication table (`finite_algebra.FiniteAlgebra`)
  applied consistently across the *whole* four-region cover, rather than
  four disconnected three-region `VennTriple` toy instances.
- A genuine consistency requirement at shared vertices — e.g. the
  boundary data two adjacent seams both reference at their common region
  must agree, rather than being drawn from unrelated local universes.
- Some other explicit coupling rule this repository has not yet
  specified.

Designing that generator is a mathematical modelling decision, not an
engineering task layered on existing code — it determines what
"supported regional composition data" means precisely enough to ask
whether a given residue is realisable under it.

## Diagnostic result: adjacent-overlap μ with zero outer slots

The first concrete test of `docs/COUPLED_GENERATOR_SPEC.md`'s
architecture, run against the four-region cycle with one shared point
universe (`coupled_realisability_diagnostic.py`, no seam instantiates a
private `VennTriple`), using the cyclic-successor seam-context selector

```text
theta(e12) = (U1,U2,U3)   theta(e23) = (U2,U3,U4)
theta(e34) = (U3,U4,U1)   theta(e41) = (U4,U1,U2)
```

and the specific sharing rule under test: for triple `theta(e)=(X,Y,Z)`,
`mu_UV` and `mu_VW` are read from shared parameters `mu_{X,Y}` and
`mu_{Y,Z}` (one parameter per adjacent overlap, reused wherever that
overlap appears), with the two *outer* correction slots (`mu_U_VvW`,
`mu_UvV_W`) fixed to zero — not shared, not free, simply unused.

This induces the matrix, from `mu = (mu12,mu23,mu34,mu41)` to
`r = (r12,r23,r34,r41)`:

```text
[-1  1  0  0]
[ 0 -1  1  0]
[ 0  0 -1  1]
[ 1  0  0 -1]
```

`rank(B) = 3` — a genuine rank drop from the independent generator's full
rank 4. But `image(B)` is exactly `im(delta^0)` of this same cyclic graph
(every basis column of `B` lies in `im(delta^0)`, and the ranks match, so
containment plus equal dimension gives equality — checked, not asserted,
by `tests/test_coupled_realisability_diagnostic.py`). The realisable
obstruction quotient

```text
im(B) / (im(B) ∩ im δ⁰)  =  im(δ⁰) / im(δ⁰)  =  0
```

is zero-dimensional. **The rank drop is real but cohomologically empty:
every residue this construction can produce is already repairable.**

**This is a cohomological collapse lemma, not a failed test.** The
result is not "coupling failed" — it is "this particular coupling makes
every generated residue repairable." The reason is structural, not
numerical: with the outer slots pinned to zero, each `r_e` reduces to
exactly `mu_next - mu_prev` around the cycle — the discrete gradient of
the `mu`'s read as a 0-cochain on the same graph. A discrete gradient is
a coboundary by construction, regardless of what algebra sits under it.

```text
Slogan: adjacency-only mu produces gradients, not curvature.
```

**Consequence for what's still open.** The outer correction slots
(`mu_U_VvW`, `mu_UvV_W`) are load-bearing, not cosmetic: with them
pinned to zero, the triple associator has no higher-order content left
to produce curvature. The dangerous choices for them are now visible on
both sides:

```text
Too strict: fix them to zero        => everything collapses to im(delta^0)  (shown above)
Too loose:  private per-seam freedom => likely restores full-rank surjectivity (untested)
Needed:     a shared, non-zero, non-private regional rule for the outer slots
```

The sharpened open question, still deliberately unanswered here:

```text
What is the weakest non-private, non-zero rule for outer correction data
that can produce a residue not lying in im(delta^0)?
```

See `docs/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md` for one data point
toward this: a *deterministic*, non-linear rule (no free parameters —
correction slots derived from region-lattice containment relations, not
shared scalars) that does produce a residue outside `im(delta^0)`, for
one specific non-degenerate four-region cover. That result does not
answer the question above, which is about a *linear* coupled generator
(a genuine parameter space with a rank/quotient to compute) — it is
evidence that curvature is achievable at all under some sharing rule,
not progress on the linear picture this section's open question needs.

A first attempt at a linear rule did try to answer it directly: see
`docs/LATTICE_IE_DIAGNOSTIC.md` for the ordered inclusion-exclusion
discipline, indexed globally by lattice-derived support pairs rather than
by seam. It failed — but informatively, and it sharpens the open question
rather than just restating it. The associator formula cancels exactly the
terms that were genuinely shared (the adjacent-pair parameters), leaving
only composite (meet-based) terms that happen never to coincide across
different θ-triples in this cover — so the rule was globally indexed at
the parameter level but seam-independent in effect, and the induced map
is full rank. The sharpened open question:

```text
Can a linear/rational outer-slot rule be designed so that the
coordinates surviving the associator's cancellation are themselves
shared across more than one seam context -- avoiding both private-seam
surjectivity and zero-slot coboundary collapse?
```

The lesson driving that sharpening: a parameter can be globally indexed
and still fail to impose structural dependence, if the associator formula
cancels exactly those globally shared coordinates. Sharing parameters
that cancel out of the final formula does not count.

## Diagnostic result: repeated triple-support linear coupling (Candidate 3b)

A direct attempt at the sharpened open question above: **Candidate 3b**,
`mu_UV = mu_VW = 0`, `mu_U_VvW = rho_{X,T}`, `mu_UvV_W = rho_{Z,T}`, where
`T = X ∩ Y ∩ Z` is the theta-triple's own support and `rho_{A,T}` is a
carrier coordinate keyed by (region, triple-support).

Run first on the standard cover (`coupled_realisability_diagnostic.
REGIONS`, four distinct triple-overlap points), the rule is **cover-inert**:
every `rho_{A,T}` coordinate is `private_residual` (8 parameters, 0
shared, full rank 4) — not because the rule is too free, but because this
cover never lets two theta-triples' overlaps coincide, so no two
`rho_{A,T}` keys can ever be equal (`candidate_discipline_diagnostic.py`).

That raised a structural question, answered by direct construction, not
assumed: in a four-theta-cycle, can a cover give two triples one shared
overlap point and the other two triples a *different* shared point?
**No.** Any two of the four theta-triples' region-sets already union to
all four regions (each triple omits exactly one region; two distinct
triples omit two different ones), so a point shared by any two triples'
overlaps is forced into all four regions, hence into **all four** triple
overlaps. The only repeated-triple-support cover consistent with every
overlap remaining a genuine singleton is: all four triple supports equal
to one shared global point.

On such a cover (`repeated_triple_support_diagnostic.CANONICAL_REGIONS`
— one global point, one private point per region, one point per pairwise
overlap so every pair properly crosses), all four `rho_{Ui,T}`
coordinates come back `genuinely_shared`:

```text
n_params = 4
sharing = {zero_column: 0, private_residual: 0, genuinely_shared: 4}
rank(B) = 2
dim(im(B) ∩ im δ⁰) = 1
dim(quotient) = 1
verdict = genuinely_partial_nontrivial_quotient
```

**This is the first linear/rational positive result in the whole
diagnostic chain** — neither full-rank surjectivity (items 14, 17) nor
total coboundary collapse (item 15). Structurally, `r_e12 = -r_e34` and
`r_e23 = -r_e14`, each an ordered restriction difference between the
opposite pair of theta-triples the shared point forces together.
`richness_invariance_check()` confirms every number above is unchanged
across six independently-enriched covers up to `|Ui|=12`: the result
depends only on theta-role incidence and the shared support point, never
on what else a region contains, so there is no richer witness to search
for in the sense of changing the verdict.

**What this does not show:** it is one rule on one cover family, not a
general theorem; it depends on repeated triple support and does not apply
to the standard distinct-support cover; it does not replace item 16's
non-linear existence witness, which has no rank/quotient to compute at
all. See `docs/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md` for the full
five-point account and verification discipline.

## Status

14. **Realisability diagnostic** (Python, exact; negative result) —
    `realisability_diagnostic.py` + `tests/test_realisability_diagnostic.py`.
    Checked: the current associator generator's parameter-to-residue map
    is full rank (every residue realisable), so realisability is trivial
    for it.
15. **Coupled realisability diagnostic: cohomological collapse** (Python,
    exact; negative result) — `coupled_realisability_diagnostic.py` +
    `tests/test_coupled_realisability_diagnostic.py`. Checked: the first
    concrete coupled construction (shared adjacent-overlap μ, outer
    correction slots fixed to zero) does drop rank (3, not 4) but its
    image is exactly `im(delta^0)` — the realisable obstruction quotient
    is zero-dimensional. Not started: a shared, non-zero, non-private
    rule for the outer correction slots — the load-bearing open question
    this result identifies. No realisability theorem, analyser module, or
    proof-carrying certificate is attempted until a construction produces
    a non-trivial obstruction quotient.
16. **Boolean proper-crossing diagnostic witness** (Python, exact;
    diagnostic witness, not a theorem) —
    `boolean_crossing_diagnostic.py` +
    `tests/test_boolean_crossing_diagnostic.py` +
    `docs/BOOLEAN_PROPER_CROSSING_DIAGNOSTIC.md`. A *deterministic*
    (parameter-free) outer-slot rule — genuine, verified through all six
    validation gates against the real code — that produces a
    non-degenerate residue outside `im(delta^0)`. Not a linear
    realisability result (no parameter space, so no rank/quotient); one
    existence data point for item 15's open question, not an answer to
    it. Superseded a degenerate witness (found first, excluded by the
    non-degeneracy gate) and an unverified hand-reasoned "witness" that
    failed outright when actually run through `compute_seam_residue` —
    both are documented, neither is the recorded result.
17. **Ordered inclusion-exclusion diagnostic: too free by disguised
    independence** (Python, exact; negative result) —
    `lattice_ie_diagnostic.py` + `tests/test_lattice_ie_diagnostic.py` +
    `docs/LATTICE_IE_DIAGNOSTIC.md`. A genuine attempt at a *linear*,
    globally-indexed (by lattice-derived support pairs, not seam label)
    outer-slot rule. Checked: the associator formula cancels exactly the
    genuinely-shared adjacent-pair terms, leaving only composite
    (meet-based) terms that never coincide across different θ-triples in
    this cover — full rank, a third distinct failure mode (neither
    private-seam freedom nor zero-slot collapse). Also corrects a
    misreading in passing: a nonzero quotient dimension is not evidence
    of selectivity when the map is already fully surjective — it is just
    `dim H^1(N;Q)`, a fixed fact about the graph. Not started: a linear
    rule whose surviving (non-cancelling) coordinates are themselves
    shared across more than one seam context — the sharpened open
    question this result identifies.
18. **Candidate 3b: repeated triple-support linear coupling** (Python,
    exact; Rocq, no `Admitted`/`Axiom`/`sorry`; **first positive
    linear/rational result**) —
    `candidate_discipline_diagnostic.py` (distinct-support cover,
    cover-inert) + `repeated_triple_support_diagnostic.py`
    (repeated-support cover, positive) +
    `rocq/RepeatedTripleSupportCandidate3b.v` +
    `tests/test_candidate_discipline_diagnostic.py` +
    `tests/test_repeated_triple_support_diagnostic.py` +
    `docs/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md`. Answers item 17's
    sharpened open question in the affirmative for one construction:
    `rank(B)=2`, `dim(im(B)∩im δ⁰)=1`, `dim(quotient)=1` — neither full
    rank nor coboundary collapse — on a cover where all four θ-triples
    share one repeated triple-support point (proved to be the only
    structurally achievable repeated-support pattern), invariant under
    enriching the cover. Formalised in Rocq as a finite incidence
    condition first (an abstract `RepeatedTripleSupport` record, the
    impossibility-of-partial-sharing lemma proved in general with no
    finiteness assumption) rather than a geometric theorem, with
    Candidate 3b's induced map as concrete finite rational linear algebra
    reusing `FourCycleObstruction.v`'s own `delta0`; `coqchk` confirms
    zero axioms across the dependency closure. A diagnostic witness, not
    a theorem; does not apply to distinct-support covers.

```sh
python realisability_diagnostic.py
pytest tests/test_realisability_diagnostic.py
python coupled_realisability_diagnostic.py
pytest tests/test_coupled_realisability_diagnostic.py
python boolean_crossing_diagnostic.py
pytest tests/test_boolean_crossing_diagnostic.py
python lattice_ie_diagnostic.py
pytest tests/test_lattice_ie_diagnostic.py
python candidate_discipline_diagnostic.py
pytest tests/test_candidate_discipline_diagnostic.py
python repeated_triple_support_diagnostic.py
pytest tests/test_repeated_triple_support_diagnostic.py
cd rocq && coqc AssociatorResidueRepair.v && coqc FourCycleObstruction.v && coqc RepeatedTripleSupportCandidate3b.v
```
