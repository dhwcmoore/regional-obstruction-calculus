# Status: Refinement Witness Composition

**Status: mixed, and that is the actual result.** (N0)-composability is
now **proved** (`rocq/RefinementWitnessComposition.v`, `coqchk`-clean, no
`Admitted`/`Axiom`/`sorry`). (A4) and (E0) composability remain
**probed, not proved** — but the probe is now a genuinely adversarial
search over ~175,000 small arbitrary (not geometrically-natural) linear
witnesses, not two hand-picked examples, and it found zero
counterexamples after correcting a real methodological mistake made and
caught along the way (see "Phase 2b" below). No tag, no release
milestone; one real theorem plus two open, now well-stress-tested,
questions, not a composition theory yet.

## The question

Given two refinement witnesses, $C \to Q$ and $Q \to R$, each
individually satisfying (A1)-(A4)/(N0)/(E0), does the **composite** map
$C \to R$ -- built by matrix-multiplying the two individually-verified
pullback maps, not re-derived from scratch -- itself satisfy those same
conditions? This is explicitly not assumed anywhere else in this
project (see the "Open directions" section of
`paper/finite_obstruction_calculus_for_regional_warrant.tex`), and it is
**not** the same claim as `rocq/CommonSubdivisionAgreement.v`, which
compares two witnesses sharing a common target, not one witness composed
with another.

## What is now known

### N0-composability: proved, not just probable

Machine-checked in `rocq/RefinementWitnessComposition.v`: given three
complexes' worth of vertex/edge cochain types and coboundary maps, and
two witnesses' worth of pullbacks each satisfying (N0), the theorem
`N0_composes` proves the composite pullbacks satisfy (N0) too. The proof
needs no linear algebra or matrix type at all — (N0) is an equality of
two composed *functions*, and the composite case is the same equality
one level up, closed by two `rewrite`s using associativity of function
composition. This is strictly more general than the matrix-level
argument below (which is the special case where every type involved is
`Q^n` and every map is `mat_vec` applied to a matrix): the theorem holds
for *any* pullback/coboundary maps between *any* types, linear or not.

### The matrix-level version of the same argument

If both individual steps satisfy (N0) -- $\delta'^0 \rho_0^{*} =
\rho_1^{*} \delta^0$ -- the composite provably satisfies (N0) too,
**by associativity of matrix multiplication alone**:

```text
delta''^0 . (rho0_QR . rho0_CQ)
    = (delta''^0 . rho0_QR) . rho0_CQ         [associativity]
    = (rho_QR . delta'^0) . rho0_CQ            [N0 at step 2]
    = rho_QR . (delta'^0 . rho0_CQ)            [associativity]
    = rho_QR . (rho_CQ . delta^0)              [N0 at step 1]
    = (rho_QR . rho_CQ) . delta^0              [associativity]
```

This needs no empirical support -- it is a one-line algebraic identity.
`refinement_witness_composition_probe.verify_n0_composability_is_
associativity()` checks the underlying associativity identity itself
against 20 random rational matrix triples, as a sanity check of
`mat_mat`'s own correctness, not as evidence for the argument (which
needs none). Machine-checked, abstractly, in
`rocq/RefinementWitnessComposition.v` (see above).

**Caveat, stated precisely:** this shows N0 composes *when both steps
individually satisfy it*. It does not show the converse (that a
composite failing N0 always traces to an individual step failing N0),
though the one case tested where a step fails N0 (bridge insertion, see
below) did propagate to the composite failing N0 too.

### A4 and E0 composability: tested, not proved

Two concrete composed witnesses were run through the real
`coboundary_0`/`pullback_matrix`/`vertex_pullback_matrix`/
`nullspace_over_Q`/`in_span_over_Q` machinery (`refinement_witness_
composition_probe.py`):

**Scenario 1 -- two genuine subdivisions.** Step 1: `SUBDIVIDE_U1`
(already verified elsewhere). Step 2: a second subdivision splitting the
already-refined complex's own `U2` vertex, constructed the same way
`SUBDIVIDE_U2` splits `COARSE`'s `U2`. Result:

```text
step1: admissible=True   descent_safe=True   E0=True
step2: admissible=True   descent_safe=True
composite: admissible=True  N0=True  descent_safe=True  E0=True  verdict_safe=True
```

The composite is fully verdict-safe here.

**Scenario 2 -- subdivision composed with bridge insertion.** Step 2 is
a bridge inserted inside the already-refined complex, analogous to
`INSERT_BRIDGE`'s construction -- the one operation that already fails
(N0) at a single step. Result:

```text
step2_N0: False  (expected -- mirrors INSERT_BRIDGE's own failure)
composite: admissible=True  N0=False  descent_safe=False  E0=True  verdict_safe=False
N0 failure propagated from step 2 to the composite: True
```

Admissibility (A1-A4) and E0 both still held at the composite level even
though N0 failed -- consistent with (N0) and (E0) being logically
independent at the single-witness level too (see `refinement_
checker.py`'s own module docstring).

**A caught mistake, worth recording.** The first draft of scenario 2
hand-copied `INSERT_BRIDGE`'s `declared_z_prime` vector into the
composed complex. The real code correctly rejected it: (A3) failed,
because the composed complex's edge structure is not `COARSE`'s, so that
vector is not actually a cycle there. Fixed by deriving a genuine cycle
from the composed complex's own coboundary map
(`nullspace_over_Q(transpose(delta0))`) instead of assuming a
plausible-looking vector would still work. This is exactly the
discipline the rest of this project insists on, caught here rather than
silently producing a wrong "witness."

## The systematic search (phase 2)

`refinement_witness_a4_e0_counterexample_search.py` replaces "more
positive examples" with an actual search: two generic second-step
operations (subdividing an arbitrary vertex; inserting a bridge between
an arbitrary pair of vertices — the general form of what
`refinement_witnesses.py`'s four hand-built witnesses do for one
specific vertex/pair each), applied to the resulting complex of *every*
one of the four base witnesses (`SUBDIVIDE_U1`, `SUBDIVIDE_U2`,
`SUBDIVIDE_ALL`, `INSERT_BRIDGE`), with *every* basis cycle of the
resulting complex's own cycle space tried as the declared witness cycle
(a complex can have more than one independent cycle once bridges
accumulate — `nullspace_over_Q`, not one hand-picked vector).

Current result: **26 systematically-generated composed witnesses, 0 A4
counterexamples, 0 E0 counterexamples.** All 8 composite N0 failures
found trace to `INSERT_BRIDGE` as step 1 (whose own N0 already fails) —
`verify_n0_theorem_consistency()` checks this automatically against
`N0_composes`'s hypotheses (both steps must individually satisfy N0),
so the search's own data is consistent with, and gives an independent
empirical cross-check of, the proved Rocq theorem, not just the two
witnesses `N0_composes` was written to cover.

Twenty-six systematically generated cases surviving with no
counterexample is stronger evidence than two hand-picked ones, but it is
still evidence, not a proof. Nothing in this search's coverage rules out
a counterexample existing outside the two generic operations tried
(subdivision, bridge insertion) or beyond a two-step composition.

## Phase 2b: the adversarial boundary search

Phase 2's search, however systematic, only tried witnesses built from
genuine graph refinements (subdividing a vertex, inserting a bridge) —
well-behaved by construction. `refinement_witness_composition_boundary_
search.py` drops the graph structure entirely: small, otherwise-
arbitrary rational coboundary maps and edge-level pullbacks, constrained
only by the actual hypotheses (vertex-level pullbacks fixed to the
identity throughout — a real, stated scope limitation, not a hidden
one — so all freedom is in the coboundary maps and edge pullbacks, which
is where A4/E0 actually live).

Two searches:

```text
Exhaustive (n1=2, entries in {-1,0,1}):
    162,816 fully verdict-safe composite witnesses tested
    0 A4 counterexamples
    0 E0 counterexamples
    completed within time budget -- genuinely exhaustive over these bounds

Randomized (n1 in [1,4), entries in [-3,3], NOT exhaustive):
    12,921 fully verdict-safe composite witnesses tested
    0 A4 counterexamples
    0 E0 counterexamples
```

**A caught mistake, worth recording exactly like the others in this
project.** The first version of this search checked only (A3)/(A4)/(N0)
at each individual step, not (E0), before testing the composite. It
found over 24,000 apparent "E0 counterexamples." Every single one turned
out to be a case where an individual *step* already failed (E0) on its
own terms — the composite was inheriting a pre-existing failure, not
demonstrating anything about composition. Once each step was required to
be fully verdict-safe (A3+A4+N0+E0, not just admissible) before the
composite was even examined, **every one of those apparent
counterexamples disappeared.** This was checked, not assumed, before
being reported here — see `refinement_witness_composition_boundary_
search.py`'s module docstring for the same account in the code itself.

This is materially stronger evidence than phase 2: ~175,000 witnesses,
not 26, none tied to any geometric refinement structure, one genuine
methodological bug caught and fixed rather than silently producing a
false positive. Still not a proof, and still scoped: vertex-level
pullbacks were held at the identity throughout (see the module
docstring) — a genuinely unrestricted search would vary that too.

## What is not known

- **A4 composability has no algebraic argument**, unlike N0. Nothing
  guarantees the composite pairing is nonzero just because both
  individual steps' pairings were nonzero — the composite pairing is a
  different quantity (paired against the fully-composed pullback of the
  *original* coarse residue, not against either intermediate step's own
  residue). No counterexample has been found across ~175,000 adversarial
  cases (plus the 26 geometric ones); none has been proved impossible.
- **E0 composability likewise has no algebraic argument** — E0's own
  definition (a subspace-inclusion condition on cycle spaces, not a
  simple matrix identity) gives no obvious associativity argument the
  way N0 has. Same result: 0 counterexamples, not a proof.
- The adversarial search fixed vertex-level pullbacks to the identity.
  Nothing here rules out a counterexample that requires genuinely
  varying vertex-level structure (which the phase 2 geometric search did
  vary, without finding one either, but not adversarially).
- No general theorem for A4 or E0 is stated or attempted here. This
  document deliberately stops at "probed" — strongly probed, not proved.

## Reproducing this

```sh
python refinement_witness_composition_probe.py
python refinement_witness_a4_e0_counterexample_search.py
python refinement_witness_composition_boundary_search.py
coqc rocq/RefinementWitnessComposition.v
```

## Next steps

- Widen the adversarial search: vary vertex-level pullbacks too (not
  fixed to the identity), larger dimensions, three-step compositions
  rather than two.
- If A4/E0 continue to survive wider adversarial search, that would be
  evidence (not proof) worth escalating to an actual proof attempt --
  Phase 2b's ~175,000-case null result is a meaningfully stronger prior
  toward that than phase 2's 26 cases were, but still not a trigger for
  claiming a theorem on its own.
- ~~Write the N0-composability lemma into the Rocq chain~~ — done,
  `rocq/RefinementWitnessComposition.v`.
- ~~Reclassify A4/E0 as a counterexample search rather than a
  positive-example generator~~ — done,
  `refinement_witness_a4_e0_counterexample_search.py`, 26 cases, 0
  counterexamples.
- ~~Adversarial boundary search over small arbitrary (non-geometric)
  witness data~~ — done, `refinement_witness_composition_boundary_
  search.py`, ~175,000 cases, 0 counterexamples after correcting a
  caught methodological mistake.
