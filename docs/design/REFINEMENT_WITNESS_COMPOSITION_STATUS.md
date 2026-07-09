# Status: Refinement Witness Composition

**Status: proved, all three.** (N0), (A4), and (E0) composability are
now all **theorems** (`rocq/RefinementWitnessComposition.v`,
`rocq/RefinementWitnessVerdictComposition.v`, `coqchk`-clean, no
`Admitted`/`Axiom`/`sorry`). The ~175,000-case adversarial search (Phase
2b) turned out to be evidence for something that was, in fact, provable
— see "Phase 2c: the proof attempt" below for what each proof actually
needed, which is less than the search's own framing suggested. No tag,
no release milestone; this is a small composition theory now, not a
diagnostic chain.

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

## Phase 2c: the proof attempt

`rocq/RefinementWitnessVerdictComposition.v` proves `A4_composes` and
`E0_composes`. Both succeed, and both need *less* than the adversarial
search's own framing suggested.

### A4_composes: near-definitional, not a coherence fact

The composite's pairing test, once the composite pullback is defined as
literal function composition (`composite_rho1 p := rho1_QR (rho1_PQ
p)`), is the *same expression* as step 2's own pairing test applied to
the already-once-pushed-forward residue — `unfold; exact`, no
computation beyond recognising two things are the same thing. The only
real hypothesis is step 2's own (A4), stated against `rho1_QR (rho1_PQ
r)` (the residue step 2 actually receives); **step 1's own (A4) is not
needed at all**, and neither is (N0). This precisely explains why the
adversarial search never found a counterexample: under the "reuse the
same witness cycle at the composite level" reading of composition (what
every search script here did), an A4 counterexample was never possible
in the first place.

### E0_composes: a real argument, needing less than first suspected

An earlier hand derivation (attempted before writing any Rocq) reached
for step 2's (N0) as well as its (E0), via a "pushforward of Z1(R) spans
exactly Z1(Q)" detour. The Rocq proof does not need that detour, or
(N0), at all: minimal finite-dimensional span/linear-map infrastructure
(`VSpace`, `InSpan`, `linear_maps_preserve_span`, `InSpan_transport`) is
enough to chain step 1's own (E0) — every coarse cycle is in the span of
the pushforward of `Z1(Q)` — through step 2's own (E0) — every `Z1(Q)`
element is itself in the span of the pushforward of `Z1(R)` — using only
linearity of the two pushforward maps. The composite coverage falls out
as `InSpan_transport` applied once. **Only step 1's (E0) and step 2's
(E0) are needed; neither step's (N0) is a hypothesis of `E0_composes`.**

### What this settles about the adversarial search's own question

Phase 2b asked whether A4/E0 are "pure preservation predicates" (nearly
formal, like N0) or "coherence predicates requiring extra
naturality/commutation hypotheses." The answer, now proved rather than
inferred from absence of counterexamples: **both are pure preservation
predicates** — A4 trivially so (definitional), E0 via a short but real
span argument — and *neither needs an extra hypothesis beyond what the
individual steps already assert about themselves*. No hidden coherence
condition was found because none was required. This is also the
mechanism behind the caught mistake in Phase 2b: a composite E0 failure
is not automatically a compositional failure — it may be inherited
warrant debt from a defective component step, exactly the sentence
recorded in the paper's remark after Theorem~5.3 (`thm:e0composes`), now
with its E0 analogue proved rather than just illustrated by one
corrected search bug.

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`, full 12-file Rocq chain
and the 136+-test Python suite verified green before this was recorded.

## Applied translation

`veribound-fce` (the applied layer built on this repository) has since
translated the obligation-dependency structure this section describes
into applied vocabulary — `docs/design/TRANSFORMATION_CERTIFICATE_
VOCABULARY.md` there: transformation witness, certificate obligation,
local/inherited/composite failure, preservation theorem, and five
diagnostic statuses (`preserved`/`inherited-failure`/`local-failure`/
`unresolved`/`out-of-scope`), grounded directly in `N0_composes`,
`A4_composes`, and `E0_composes`. Vocabulary/spec only there too — no
code in `veribound-fce` implements any of it yet.

## What is still not known

- **The scope of the *statement*, not the proof.** `A4_composes` and
  `E0_composes` are proved for arbitrary linear pullback maps between
  arbitrary (abstract, not dimension-bounded) vector spaces — strictly
  more general than anything the searches covered. What is *not* claimed
  is that this is the only possible formalisation of "composition" for
  refinement witnesses, or that every notion of "the composite witness"
  one might reasonably define coincides with the one used here (reuse
  the same declared cycle at the composite level; compose pullbacks by
  function composition). A different formalisation could in principle
  behave differently.
- Whether a three-step (or longer) composition needs anything beyond
  repeated application of these two-step theorems has not been checked.
- No general theorem for refinement-witness composition beyond (N0),
  (A4), (E0) is attempted — full `verdict_safe` composability follows
  immediately by conjunction of the three, but nothing about
  presentation invariance or the broader open questions in the paper's
  "What is not claimed" section is affected by this result.

## Reproducing this

```sh
python refinement_witness_composition_probe.py
python refinement_witness_a4_e0_counterexample_search.py
python refinement_witness_composition_boundary_search.py
coqc rocq/RefinementWitnessComposition.v
coqc rocq/RefinementWitnessVerdictComposition.v
```

## Next steps

- Three-step (or longer) composition: check whether repeated application
  of the two-step theorems is really all that is needed, or whether
  something new appears at three steps.
- A worked concrete instantiation of `A4_composes`/`E0_composes` against
  the actual matrix-shaped witnesses in `refinement_checker.py` (the way
  `CandidateThreeBDistinctSupportClassification.v` both proved
  abstractly and instantiated concretely) — not done here; the abstract
  theorems are stated to cover the matrix case as a special case (a
  matrix is a linear function of its argument) but that correspondence
  is not separately verified in Rocq the way `N0_composes`'s was.
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
- ~~Attempt the A4/E0 proof~~ — done, `rocq/
  RefinementWitnessVerdictComposition.v`, `A4_composes` and
  `E0_composes`, `coqchk`-clean.
