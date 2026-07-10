# Status: Refinement Witness Composition

**Status: proved for two and three sequential steps; proved for N0/E0
and for a full branchwise/aggregate A4 classification under two-branch
disjoint parallel composition.** (N0), (A4), and (E0) composability are
theorems for binary sequential composition
(`rocq/RefinementWitnessComposition.v`,
`rocq/RefinementWitnessVerdictComposition.v`) and for three-step
sequential composition (`rocq/RefinementWitnessSequentialComposition.v`),
`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`. Released as
`v0.11-refinement-witness-composition`. The ~175,000-case adversarial
search (Phase 2b) turned out to be evidence for something that was, in
fact, provable — see "Phase 2c: the proof attempt" below for what each
proof actually needed, which is less than the search's own framing
suggested; "Phase 4a: sequential composition" extends this to three
steps with the same discipline. Disjoint *parallel* composition (a
genuinely different construction — direct sum, not function composition)
was probed first (Phase 4b) and found to split: `N0_parallel_disjoint`
and `E0_parallel_disjoint` are proved
(`rocq/RefinementWitnessParallelComposition.v`, Phase 4c), `coqchk`-clean;
the naive scalar `A4_parallel_disjoint` is **false**, demonstrated by
probe and then, in Phase 4d, by a machine-checked Rocq witness too — and
Phase 4d proves the corrected replacement classification in full:
`A4_parallel_disjoint_branchwise` (unconditional), `A4_parallel_disjoint_
nonzero_sum` (the scalar test, exactly under an explicit non-cancellation
hypothesis), and the fact that branchwise success alone does not imply
the aggregate. *Coupled* parallel composition (branches sharing
structure, not fully independent) was posed as a well-definedness
question first (Phase 5a), probed with a conservative compatibility gate
(Phase 5b), and that gate itself is now proved
(`rocq/CoupledParallelCompatibility.v`, Phase 5c, `coqchk`-clean):
agreement is necessary and sufficient for a glued composite to exist at
all. Coupled-parallel *well-definedness* is now formalised; coupled-
parallel *preservation* remains open. Phase 5d then answered the one
preservation-adjacent question that was left deliberately deferred:
shared-seam compatibility does **not** force non-cancellation — a
compatible, branchwise-A4-preserved, aggregate-A4-cancelling case was
found and verified (`refinement_witness_coupled_a4_cancellation_probe.
py`), so the disjoint case's branchwise/aggregate split survives fully
into the compatible-coupled case, at least for one witness family. Phase
5e turns that finding into a machine-checked `Example`
(`compatible_glue_can_cancel_aggregate_A4`,
`rocq/CoupledParallelCompatibility.v`, `coqchk`-clean), and proves the
general single-counting correction between a glued aggregate and the
naive disjoint-style sum (`glued_aggregate_vs_naive_sum`, by `ring`). No
merge rule and no general (N0)/(A4)/(E0) preservation claim exists yet
for the coupled case. Arbitrary finite sequential chains,
three-or-more-branch parallel composition, and any conflict-resolution
or preservation theorem for coupled parallel composition remain open —
see "What is still not known."

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

## Phase 4a: sequential (three-step) composition

`rocq/RefinementWitnessSequentialComposition.v` extends the binary
result to three composed steps, $P \to Q \to R \to S$. Each proof is a
direct restatement of its binary predecessor's technique, applied once
more, not a new argument — and each condition keeps its own distinct
dependency profile, sharper than "safe chains compose":

```text
N0_composes_three : needs ALL THREE steps' own N0 -- pure iterated
                     function-composition rewriting.
A4_composes_three : needs ONLY the LAST step's own A4, applied to the
                     fully-pushed-forward residue -- steps 1 and 2's own
                     A4 are not hypotheses at all, exactly as step 1's
                     A4 was not needed in the binary case.
E0_composes_three : needs ALL THREE steps' own E0 (and none of their
                     N0) -- InSpan_transport applied twice, chaining
                     step1's coverage through step2's through step3's.
```

This confirms the predicted pattern exactly: N0 and E0 both require
*every* component step's own obligation (though for different
mechanical reasons — N0 by direct substitution, E0 by span-transport
chaining), while A4 requires only the *final* step's, regardless of
chain length. `coqchk`-clean, no `Admitted`/`Axiom`/`sorry`; full
13-file Rocq chain and the Python suite verified green before this was
recorded.

**Scope, stated precisely**: this proves exactly three steps, not an
arbitrary finite chain. A general $n$-step theorem needs dependent
list/vector machinery (each step's codomain type must match the next
step's domain type) not built anywhere in this project; whether the
"apply the lemma once per additional step" pattern continues to hold for
$n > 3$ is expected, by the shape of the three proofs, but not checked.

## Phase 4b: disjoint parallel composition (probe)

A genuinely different question from Phases 2-4a, all of which concern
one witness followed by another (function composition). **Disjoint
parallel composition** combines two independent witnesses side by side
-- a direct-sum / disjoint-union construction, per
`veribound-fce`'s `docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC.md`,
which defines "certificate-disjoint" as sharing no vertex, edge, seam,
declared cycle, or downstream target.

`refinement_witness_parallel_disjoint_probe.py` makes this concrete: two
witnesses over completely independent vertex/edge name universes (one
renamed with a prefix), combined by literal list concatenation of the
coarse complex, refined complex, coarse residue, and declared cycle --
then run through the real machinery (`coboundary_0`, `pullback_matrix`,
`vertex_pullback_matrix`, `nullspace_over_Q`, `in_span_over_Q`), not a
hand-derived block-matrix argument trusted on its own. Following the
order used for every prior phase of this line -- probe before proof --
no Rocq file existed for this at the time the probe was written; see
Phase 4c below for what was proved once the probe's findings were used
to correct the theorem statement.

**Result, checked over 32 cases (all 16 ordered pairs from
`ALL_WITNESSES`, with and without the second branch's declared cycle
negated):**

```text
N0 always equals AND(branch A's own N0, branch B's own N0): 32/32.
E0 always equals AND(branch A's own E0, branch B's own E0): 32/32.
A4 equals AND(branch A's own A4, branch B's own A4) in 16/32 cases --
    and DIFFERS in the other 16, always exactly the cases where the two
    branches' pairings have opposite sign, always producing a combined
    pairing of exactly 0.
```

**Why N0 and E0 are safe and A4 is not, worked out by hand and then
checked, not the other way round.** Under a direct-sum construction, the
combined coboundary/pullback matrices are block-diagonal: no cross-block
entries exist at all, so (N0) (a matrix *equality*) and (E0) (a subspace
*containment*, itself decomposing into block-diagonal cycle spaces)
reduce to "holds in the A block and holds in the B block" with no way
for the two blocks to interact -- a genuine, safe "AND". (A4) is
different in kind, not degree: the combined declared cycle is the
concatenation of both branches' own cycles, so the combined pairing is
literally the *sum* of the two branches' own pairings. A sum of two
nonzero numbers can be zero. This was demonstrated, not merely argued:
taking `SUBDIVIDE_U1` twice, with the second copy's declared cycle
negated, gives branch pairings $+5$ and $-5$ -- both individually
nonzero, satisfying each branch's own (A4) -- and a combined pairing of
exactly $0$, failing the composite's (A4), while (N0) and (E0) remain
fully intact on both branches and the composite throughout.

**What this means for the eventual theorem, and for
`PARALLEL_WITNESS_COMPOSITION_SPEC.md`'s candidate names.** This is not
evidence that "certificate-disjoint" is the wrong definition -- every
condition it was designed to rule out (shared vertices, seams, cycles)
plays no role in the cancellation above; the two branches really are
disjoint by that definition, and (A4) still fails to compose. The
lesson is narrower and sharper: `N0_parallel_disjoint` and
`E0_parallel_disjoint` are reasonable theorem targets essentially as
originally named. `A4_parallel_disjoint`, if attempted, cannot be stated
as "both branches' own (A4) implies the composite's (A4)" -- that
statement is false, demonstrated above, not merely unproved. Any real
`A4_parallel_disjoint` theorem needs an additional hypothesis ruling out
sign cancellation (e.g. that the two branches' pairings are of the
*same* sign, or some other condition on their combination) -- exactly
the kind of "additional hypothesis" question this whole composition line
has been built to surface precisely rather than paper over.

**Reproducing this**:

```sh
python refinement_witness_parallel_disjoint_probe.py
pytest tests/test_refinement_witness_parallel_disjoint_probe.py
```

**Not done in this phase**: any Rocq attempt (per the established
order, probe first -- see Phase 4c for what followed); coupled parallel
composition (no preservation candidate exists for it at all --
`PARALLEL_WITNESS_COMPOSITION_SPEC.md` §4); parallel-then-merge (a
separate operation, per that document's §5).

## Phase 4c: N0/E0 proved in Rocq; A4 deliberately not attempted

Per the probe's finding, `rocq/RefinementWitnessParallelComposition.v`
proves exactly `N0_parallel_disjoint` and `E0_parallel_disjoint` --
the two conditions the probe supported -- and deliberately does **not**
state or attempt an `A4_parallel_disjoint` theorem, since the probe
showed the natural statement of that theorem ("both branches' own A4
implies the composite's A4") is false, not merely unproved.

**Construction.** Unlike every sequential-composition proof in this
project (`RefinementWitnessComposition.v`,
`RefinementWitnessVerdictComposition.v`,
`RefinementWitnessSequentialComposition.v`), which build composite maps
by literal function *composition*, disjoint parallel composition is
built from a genuine direct sum. At the cochain-space level (as opposed
to the vertex/edge index-set level the Python probe operates on), a
function on a disjoint union of index sets is exactly a *pair* of
functions, one per branch -- so the combined coboundary/pullback maps
act on Rocq product types (`C0 * D0 -> C1 * D1`, etc.) componentwise,
mirroring the probe's block-diagonal matrices exactly.

**N0_parallel_disjoint**: pure case analysis on the product type,
needing no vector-space structure at all -- the same flavor of proof as
the original two-step `N0_composes` (`RefinementWitnessComposition.v`),
just a pairing instead of a further composition.

**E0_parallel_disjoint**: reuses the `VSpace`/`InSpan`/`IsLinear`
infrastructure originally built for `RefinementWitnessVerdictComposition
.v` (redeclared locally in the new file rather than imported, matching
this project's existing pattern of small self-contained Rocq files), plus
a new `VSpace_prod` direct-sum constructor and `embed_left`/`embed_right`
linear embeddings. The combined cycle-space basis is the concatenation of
each branch's own basis, embedded into the product space with a zero in
the other component -- matching the actual mathematical fact that the
kernel of a block-diagonal map is the direct sum of the two branches'
kernels. Each branch's own (E0) transports through its own embedding
(shown linear) into the combined space; a new monotonicity lemma
(`InSpan_incl`, span is monotone under basis inclusion) glues the two
branch-level results into the combined statement, since -- unlike the
sequential case -- this proof needed *inclusion* into a larger basis
rather than *transport* through a single composed map.

Both `coqc`-clean and `coqchk`-clean (zero axioms across the full
13-file dependency closure). No `Admitted`/`Axiom`/`sorry`.

**A4 is not attempted, and this is a deliberate scope decision, not an
oversight.** The probe demonstrated a genuine counterexample to naive
componentwise A4 preservation, so no such theorem can be proved as
stated. `veribound-fce`'s `docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC
.md` §7 now names two non-interchangeable candidate replacements
(`A4_parallel_disjoint_nonzero_sum`, an aggregate statement with an
explicit non-cancellation hypothesis; `A4_parallel_disjoint_branchwise`,
a semantically different composite obligation reporting per-branch
witness presence instead of one summed test) -- deciding between them is
a design question, not yet settled, and is a precondition for any future
A4 proof attempt in this repository.

**Scope, stated precisely**: this proves disjoint parallel composition
of exactly two branches, for N0 and E0 only. Not proved (at the time
Phase 4c landed): three-or-more branch parallel composition (would need
the same kind of dependent-list generalisation flagged as open for
sequential composition); coupled parallel composition (no candidate
exists, see Phase 4b); any A4 statement for parallel composition (see
Phase 4d below); interaction between parallel and sequential composition
(e.g. two sequential chains combined in parallel) -- not modeled
anywhere in this project.

## Phase 4d: branchwise A4 semantics — design, then proof

Phase 4c deliberately left A4 unaddressed rather than proving a false
statement. This phase settles a semantics for A4 under disjoint parallel
composition and proves the parts of it that are actually true, following
the same discipline as every other phase: design first (a short spec, no
proof), then formalise.

### Branchwise A4 semantics (design)

The naive statement treated the composite's (A4) as one scalar test: dot
the combined declared cycle against the combined pushed residue, check
nonzero. That single number is an *aggregate* — literally the sum of the
two branches' own pairings, since the combined vectors are
concatenations. Aggregation is exactly what allows cancellation, and
cancellation is exactly what the probe found.

The alternative is not to fix the aggregate but to change what is being
asked. **Branchwise A4** reports each branch's own pairing test
separately, instead of collapsing them into one number first:

```text
A4_branchwise(WA (+) WB) :=
    left_pairing  <> 0    -- branch A's own pairing, unchanged by combination
    right_pairing <> 0    -- branch B's own pairing, unchanged by combination
```

with the aggregate retained alongside it as a third, explicitly
*derived* fact, not the primary report:

```text
aggregate_pairing := left_pairing + right_pairing
aggregate_pairing <> 0   -- may fail even when both branchwise tests hold
```

This gives a three-valued diagnostic outcome instead of one boolean:

```text
branchwise_preserved   -- both left_pairing <> 0 and right_pairing <> 0
aggregate_preserved    -- branchwise_preserved AND aggregate_pairing <> 0
aggregate_cancelled    -- branchwise_preserved AND aggregate_pairing == 0
```

`aggregate_cancelled` is the case the probe exhibited concretely
(`SUBDIVIDE_U1` against a sign-negated copy of itself): a real,
nameable outcome, not an error state — the evidence from both branches
is intact, but the scalar summary that used to encode "is there a
nonzero pairing" has genuinely lost information by summing. Branchwise
semantics keeps that information; aggregate semantics discards it.

**Why branchwise first, not the scalar patch.** `A4_parallel_disjoint_
nonzero_sum` (aggregate pairing plus an explicit non-cancellation
hypothesis) is a valid theorem but a thin one — it says the old scalar
test works *if* it happens not to cancel, without saying anything new.
Branchwise semantics is the sharper diagnostic: it says the individual
evidence always survives combination, and separately names cancellation
as its own classified outcome rather than an unexplained aggregate
failure. This mirrors a preference already established elsewhere in this
project (e.g. Candidate 3b's classification keeping "cover-inert" and
"genuinely shared" as two named outcomes rather than one collapsed
verdict) — a structured report over a single collapsed boolean, when the
underlying mathematics genuinely has more than one case.

### Proved in Rocq

`rocq/RefinementWitnessParallelComposition.v`, Part 4, proves all of the
following, `coqchk`-clean, no `Admitted`/`Axiom`/`sorry`:

```text
A4_parallel_disjoint_branchwise :
    each branch's own (A4) survives combination, reported separately.
    Near-definitional once stated this way -- the honest content is the
    DESIGN DECISION to report two obligations instead of one, not proof
    difficulty.

A4_parallel_disjoint_nonzero_sum :
    the aggregate (summed) pairing is nonzero exactly when the explicit
    non-cancellation hypothesis holds. Needs ONLY that hypothesis --
    neither branch's own (A4) is used in this proof at all, a fact
    stated plainly in the file rather than glossed over.

A4_parallel_disjoint_branchwise_and_nonzero_sum :
    a corollary bundling the two theorems above. Recorded because the
    classification ladder names it explicitly, not because combining
    them adds mathematical content beyond what each already proves
    separately -- branchwise success and the non-cancellation hypothesis
    are logically independent facts about the same two branches, not two
    halves of one argument.

A4_parallel_aggregate_can_fail_despite_branchwise (Example) :
    a concrete, machine-checked witness (Q values 5 and -5) that
    branchwise success does NOT imply aggregate success. This upgrades
    "the naive aggregate A4_parallel_disjoint statement is false" from a
    Python-probe finding to a coqchk-verified fact -- the same numbers
    the probe found (SUBDIVIDE_U1 against its own sign-negated copy),
    now checked independently of the Python machinery entirely.
```

**What this settles, precisely.** The full two-branch A4 classification
is now closed: branchwise preservation always holds when each branch's
own (A4) holds (unconditionally); aggregate preservation holds exactly
under an explicit non-cancellation hypothesis (no other condition
needed); and aggregate preservation can genuinely fail even when
branchwise preservation holds (proved by witness, not left as an
open possibility). Nothing here weakens Phase 4c's N0/E0 results or
revives a "verdict_safe_parallel_disjoint" claim — `verdict_safe` in
this project's existing vocabulary means the single aggregate (A4), and
that condition is still not unconditionally guaranteed by the two
branches' own admissibility.

**Not attempted**: connecting branchwise/aggregate A4 to a concrete
matrix-shaped instantiation (mirroring how `CandidateThreeBDistinct
SupportClassification.v` was both proved abstractly and instantiated
concretely) — the abstract statement is intended to cover the matrix
case (a dot product is the relevant `pairing_*` function) but this
correspondence is not separately checked in Rocq here; three-or-more
branch parallel composition; coupled parallel composition, still with no
preservation candidate at all.

**A real gap found and fixed during this checkpoint.** `make check-rocq`
had never actually compiled four already-proved files —
`rocq/CochainNaturalityDescent.v`, `rocq/CommonSubdivisionAgreement.v`,
`rocq/ExactnessReflection.v`, `rocq/FirstOrderClassifierCertificate.v`
— even though `STATUS.md` §1 has listed them as verified since well
before this composition line began, and `REPRODUCIBILITY.md` correctly
documented the gap ("not yet wired into the `check-rocq` Makefile
target") rather than hiding it. They were never broken; they just needed
`coqc` invoked on them explicitly, which the make target never did.
Confirmed all 13 `.v` files compile and `coqchk` together with zero
axioms across the full closure, then fixed the `Makefile`'s `check-rocq`
target to compile all 13 in dependency order and updated
`REPRODUCIBILITY.md` to match. This is the same category of gap the
Phase 3b traceability checkpoint (see `RESULTS.md`/`README.md`/
`PROJECT_MAP.md` history) found and fixed for the *documentation*
surface; this one was in the *verification tooling* surface instead —
worth checking for again at the next release-style checkpoint.

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
- Three-step composition is now checked (Phase 4a, above) and needs
  exactly repeated application, with the same per-condition dependency
  profile. Whether this continues to hold for four-or-more-step (or
  arbitrary finite) chains has *not* been checked — expected, by the
  shape of the proofs, but not proved.
- No general theorem for refinement-witness composition beyond (N0),
  (A4), (E0) is attempted — full `verdict_safe` composability follows
  immediately by conjunction of the three, but nothing about
  presentation invariance or the broader open questions in the paper's
  "What is not claimed" section is affected by this result.
- **Disjoint parallel `verdict_safe` composability, in this project's
  existing sense of that word (the single aggregate `verdict_safe`
  including the scalar A4 test), still does not hold unconditionally**,
  even though N0 and E0 do compose (Phase 4c) and even though the full
  branchwise/aggregate A4 classification is now proved (Phase 4d) —
  because `verdict_safe` as defined elsewhere in this project means the
  *aggregate* (A4), and `A4_parallel_disjoint_nonzero_sum` needs an
  explicit non-cancellation hypothesis that is not implied by either
  branch's own admissibility. A *branchwise* `verdict_safe`-style
  statement (using `A4_parallel_disjoint_branchwise` in place of the
  scalar test) is not stated anywhere either — it would require deciding
  whether `verdict_safe`'s existing definition should be extended or a
  new parallel-specific notion introduced, which has not been decided.
- Coupled parallel composition (branches sharing a vertex, seam,
  declared cycle, or downstream target) has no preservation candidate at
  all, probed or proved — `PARALLEL_WITNESS_COMPOSITION_SPEC.md` §4
  names it a possible *source* of obstruction, not something to assume
  safe. `docs/design/COUPLED_PARALLEL_COMPOSITION_PROBLEM.md` now poses a
  first concrete question (shared seam / shared declared cycle) but
  contains no probe or proof yet.
- Three-or-more-branch disjoint parallel composition (Phase 4c/4d prove
  exactly two branches) has not been attempted.
- Whether `A4_parallel_disjoint_branchwise`'s report structure is the
  right shape to expose in an eventual applied diagnostic (three
  outcomes: `branchwise_preserved` / `aggregate_preserved` /
  `aggregate_cancelled`, per Phase 4d's design subsection) or whether a
  different structured report is more useful once real transformation
  diagnostics are built in `veribound-fce` — not decided, no
  implementation exists yet in either repository.
- ~~Whether shared-seam compatibility and aggregate-A4 cancellation can
  co-occur.~~ **Resolved, Phase 5d: yes, they can.** See Phase 5d below —
  it does not follow from the single-cycle-space witnesses Phase 5b used
  (their cycle space is too rigid), but a witness with a higher-dimensional
  cycle space (`INSERT_BRIDGE`) exhibits it directly, checked against the
  real machinery, not merely argued.

## Phase 5b: shared-seam coupled parallel probe

Per `docs/design/COUPLED_PARALLEL_COMPOSITION_PROBLEM.md`'s framing
(Phase 5a): the first question about coupled parallel composition is not
whether it preserves (N0)/(A4)/(E0) — it is **whether the glued
composite witness is even well-defined**. This phase probes exactly that
boundary, and only that boundary; no preservation claim is attempted for
this phase's own sake, and none should be inferred beyond what §"What
this settles" below states.

`refinement_witness_coupled_parallel_probe.py` builds a genuinely
different construction from the disjoint case (`refinement_witness_
parallel_disjoint_probe.py`): both branches sit over the **same** coarse
complex (`COARSE`, unprefixed and used once — not duplicated), and only
their refined complexes are otherwise independently renamed, *except*
for one designated shared seam (one refined edge name and its two
endpoint vertices), which is deliberately kept identical between
branches rather than renamed. This matches "two refinements of the same
regional situation, agreeing to share exactly one seam," a different
premise from disjoint composition's "two completely independent regional
situations placed side by side."

**The compatibility gate, deliberately conservative, exactly as
directed**: no merge rule (averaging, summing, branch-preference) is
attempted. A shared seam is well-defined only if both branches' own
declarations for it agree *exactly* — the edge's structural data
(`src`, `tgt`, `over`, `over_sign`), the declared-cycle (`z'`) value
assigned to it, and the coarse parent (`vertex_over`) for each endpoint.
If they agree, the combined witness is built and checked with the same
real machinery every prior probe in this project uses. If they do not,
**no combined witness is built at all** — the case is reported as
`interface_conflict`, not as an (N0)/(A4)/(E0) failure, since there is
no composite object for those conditions to be tested against. This
distinction (composite *undefined* vs. composite *defined but failing*)
is kept explicit throughout the script and its report.

**Five cases, checked, not merely argued:**

```text
Case 1 (SUBDIVIDE_U1 self-paired, sharing 'e23', no perturbation):
    interface_consistent -> disjoint_like_preserved
    (both branches' own declaration for the shared seam is identical by
    construction -- the simplest possible consistent case)

Case 2 (SUBDIVIDE_U1 + SUBDIVIDE_U2, sharing 'e34', no perturbation):
    interface_consistent -> disjoint_like_preserved
    (an ORGANIC agreement between two genuinely different witnesses --
    both independently declare the identical Edge('e34','U3','U4',
    over='e34',sign=1) -- not a self-pairing artifact)

Case 3 (SUBDIVIDE_U1 + SUBDIVIDE_U2, sharing edge-NAME 'e12p'):
    interface_conflict
    (an ORGANIC conflict: both witnesses happen to name an edge 'e12p',
    but branch A's runs U1b->U2 and branch B's runs U1->U2a -- same
    name, genuinely different edges, arising from the two witnesses'
    own real declarations, not a constructed adversarial case)

Case 4 (SUBDIVIDE_U1 self-paired, sharing 'e23', over_sign perturbed):
    interface_conflict
    (deliberately constructed: same name/src/tgt/over, sign flipped)

Case 5 (SUBDIVIDE_U1 self-paired, sharing 'e23', z' entry perturbed):
    interface_conflict
    (deliberately constructed: edge data agrees, cycle coefficient does
    not)
```

A sixth, unplanned but real finding surfaced while writing the test
suite: `SUBDIVIDE_U1` and `INSERT_BRIDGE` (two of this project's own
four canonical witnesses) organically disagree on `e23`'s `z'` value
(`+1` vs. `-1`) — another naturally-arising conflict, not constructed,
now locked in as `tests/test_refinement_witness_coupled_parallel_probe.
py::test_organic_conflict_between_subdivide_u1_and_insert_bridge`.

**What this settles, precisely.** When two branches' shared-seam
declarations agree exactly, gluing introduces no new obstruction: the
combined witness reduces to the *same* preservation pattern already
proved for disjoint composition (N0/E0 match AND, A4 branchwise holds)
— consistent with, but not the same claim as, `docs/design/
COUPLED_PARALLEL_COMPOSITION_PROBLEM.md` §5's "consistent gluing
degenerates to disjoint-style preservation" conjecture; this is
evidence for that conjecture on 2 cases, not a proof of it in general.
When declarations disagree, **no composite witness exists to test at
all** — a category distinct from local failure, inherited failure, or
composite failure in this project's existing vocabulary
(`TRANSFORMATION_CERTIFICATE_VOCABULARY.md`), and worth keeping
distinct in any future diagnostic status scheme.

**Reproducing this**:

```sh
python refinement_witness_coupled_parallel_probe.py
pytest tests/test_refinement_witness_coupled_parallel_probe.py
```

**Not done in this phase**: any merge/resolution rule for conflicting
shared-seam data (averaging, branch-preference, or otherwise) —
deliberately excluded per the design doc's explicit instruction; a Rocq
formalisation of the *consistent-case preservation pattern* itself (see
Phase 5c for the compatibility gate, which *was* formalised); any
systematic sweep beyond the five cases above (kept narrow, per
instruction, rather than testing all pairs of all witnesses against all
shared-edge choices); shared declared-cycle coupling *without* a shared
seam (this probe's construction ties the two together at one edge; a
cycle shared across otherwise-disjoint seams is a different, untested
construction); any of the other six coupling sources named in
`docs/design/COUPLED_PARALLEL_COMPOSITION_PROBLEM.md` §2 (policy
authority, downstream fusion target, common restriction/downgrade,
cross-branch pairing constraint, shared vertex/region carrier without a
shared edge).

## Phase 5c: shared-seam compatibility gate, formalised in Rocq

Per the explicit instruction not to formalise a merge rule yet: this
phase proves the *gate itself*, not full coupled parallel composition
and not any (N0)/(A4)/(E0) behaviour of a glued composite. The result is
the safety property underneath Phase 5b's `interface_conflict` refusal:
an incompatible interface does not merely make a bad composite — no
composite satisfying both branches' declarations exists **at all**, so
testing (N0)/(A4)/(E0) against one would be a category error, not a
finding.

`rocq/CoupledParallelCompatibility.v` models a branch's interface
declaration abstractly as a partial function `Key -> option Value`
(deliberately not tied to `Edge`/refinement-witness types — the same
"no `Point`/finiteness assumption" abstraction discipline as
`CandidateThreeBDistinctSupportClassification.v`, and general enough to
cover any future coupling source from the Phase 5a taxonomy, not just
shared seams). No decidable-equality hypothesis on the key type is
needed — none of the proofs below ever compare two keys for equality,
only pattern-match on each branch's own declaration at a given key.

```text
Compatible dA dB :=
    forall k, (dA and dB both declare k) -> (their declared values agree)

IsGlue dA dB g :=
    g reproduces dA's own declaration wherever only dA declares a key,
    reproduces dB's own declaration wherever only dB declares a key, and
    reproduces BOTH branches' declared values at any key both declare
    (possible only when those values coincide).
```

```text
interface_agreement_allows_glue :
    Compatible dA dB -> exists g, IsGlue dA dB g.
    (constructive -- exhibits the glue explicitly: prefer dA's
    declaration where it exists, fall back to dB's otherwise; this is
    NOT a branch-preference merge rule in the sense the design doc warns
    against, since it is only ever invoked once Compatible already
    guarantees the two branches agree wherever both declare a key --
    "prefer A" and "prefer B" give the identical result there.)

interface_disagreement_blocks_glue :
    dA k = Some vA -> dB k = Some vB -> vA <> vB ->
    forall g, ~ IsGlue dA dB g.
    (near-definitional once IsGlue is stated this way: any candidate g
    would have to satisfy g k = Some vA AND g k = Some vB
    simultaneously, which is impossible when vA <> vB -- the refusal
    rule is a direct consequence of what "glue" is required to mean,
    not a separately-imposed side condition.)

incompatible_has_no_glue :
    a corollary restating the above in exactly the shape Phase 5b's
    probe needs: an incompatible pair of declarations has NO glue at
    all, not merely an unproved one.
```

**`shared_label_not_sufficient_for_agreement`**, a concrete `Example`
(not a general theorem, per the instruction that this one "may be
represented as an example"): instantiates `Key := nat`, `Value := Q`
with two declarations that both declare the *same* key but with
different values (`1` vs. `-1`, deliberately matching the shape of the
probe's own Case 5 z'-value conflict) — the Rocq-level counterpart of
the probe's *organic* `e12p` finding. This upgrades "a shared label is
not sufficient for agreement" from something the probe merely
illustrated to something `coqchk`-verified. A second example,
`shared_label_not_sufficient_for_agreement_no_glue`, applies
`incompatible_has_no_glue` directly to the same witness, confirming no
glue exists for it at all.

**A real Coq debugging note, worth remembering.** The first proof
attempt used `repeat split` immediately after `unfold`, expecting it to
split the top-level triple conjunction into exactly three unintroduced
`forall`-goals and stop there. In this Coq version, `split` is smart
enough to auto-`intro` leading binders before attempting to split an
inner conjunction — so `repeat split` silently drilled all the way
through `IsGlue`'s third conjunct's `forall k vA vB, ... -> ... /\ ...`,
introducing `k`/`vA`/`vB`/hypotheses *and* splitting the final `/\`,
producing four goals where three were expected, and later bullets'
explicit `intros k ...` then failed (`k is already used`) because those
names were already in context. Fixed by replacing `repeat split` with
an explicit `split; [| split]`, splitting only the outer two-level
conjunction and leaving each of the three resulting goals as a full,
unintroduced `forall` for the bullet's own `intros` to handle. A second,
related mistake: `apply (Hcompat k); split; [exists vA | exists vB];
assumption` assumed `split` would only affect the first of the several
goals `apply` produces — but `t1; t2` applies `t2` to *every* goal `t1`
produces, and `split` failing outright on one of the non-conjunction
goals (`dA k = Some vA`) aborted the whole chain with a confusing
"unable to unify" error. Fixed by restructuring as an explicit bulleted
sub-proof, one bullet per goal `apply` produces, rather than chaining
tactics across an unknown number of goals with `;`.

`coqc`-clean and `coqchk`-clean (zero axioms across the full 14-file
dependency closure). No `Admitted`/`Axiom`/`sorry`.

**Scope, stated precisely.** This proves the compatibility gate is
correct — agreement is necessary and sufficient for a glue to exist —
for an abstract single-shared-key interface model. It does **not**
prove anything about (N0)/(A4)/(E0) behaviour of a glued composite (that
remains Phase 5b's Python-probe-only finding, on 2 cases); does not
address multiple simultaneously-shared keys (the abstract `Compatible`
definition already covers this — "every shared key agrees" — but no
probe or instantiation exercises more than one shared key at a time);
and does not propose or formalise any conflict-resolution rule, per the
explicit instruction to leave that until the refusal semantics was
theorem-grade, which it now is.

**Not done**: any Rocq connection back to the concrete `Edge`/`Witness`
types in `refinement_witnesses.py` (the abstraction is intended to cover
that case — an edge's structural data plus its declared-cycle value is
one instance of `Value` — but this correspondence is not separately
checked in Rocq, the same kind of gap already open for
`A4_composes`/`E0_composes`'s own matrix instantiation); any preservation
theorem for the consistent case; any progress on the aggregate-A4
cancellation question, which the user explicitly deferred until after
this phase.

## Phase 5d: compatible aggregate-A4 cancellation — found, not merely possible

Phase 5b's probe never observed a compatible shared seam whose aggregate
(A4) still cancelled, and flagged this explicitly as open rather than
claiming compatibility rules cancellation out. This phase settles it:
**it can, and does, for a witness this project already uses.**

**The construction problem, worked out before any code.** Naive
sign-negation (the disjoint case's mechanism) does not obviously carry
over: for a witness whose refined complex has a 1-dimensional cycle
space — every `SUBDIVIDE_*` witness in this project, each a single loop
— the declared cycle is determined up to an overall scalar by any one of
its own coordinates. Fixing agreement at one shared coordinate therefore
pins down the *entire* vector, leaving no freedom to vary anything else.
Cancellation needs independent variation **away from** the shared seam
while the seam itself stays fixed — which needs a cycle space of
dimension $\geq 2$, so that some cycle direction is exactly zero at the
shared edge (never touches it) while still nonzero, and residue-
carrying, elsewhere.

**Checked, not assumed**: of this project's four canonical witnesses,
computing each one's actual cycle space dimension
(`nullspace_over_Q` on the refined coboundary's transpose) shows only
`INSERT_BRIDGE` has dimension $2$ (the other three are exactly $1$).
`INSERT_BRIDGE`'s refined complex has two parallel edges (`e12` and
`b12`) between `U1` and `U2`, giving a "big loop" (around all four
coarse edges) and a "small loop" (between the two parallel edges) as
independent cycle directions. The small loop has a **zero** coefficient
at `e23` (never touches it) but a **nonzero** coefficient at `e12`
(which carries nonzero pulled-back residue) — exactly the needed shape.
This narrows the search to one witness, honestly, not by choice.

**Method**: for each (witness, edge) pair, compute the subspace of cycle
vectors vanishing at that edge (`off_seam_directions`, itself a
`nullspace_over_Q` call on the single linear constraint "coefficient at
this edge is zero" — not hand-picked from the raw basis), then *exactly
solve* (not scan) for the scalar multiple of an off-seam direction that
zeroes the glued composite's aggregate pairing, and verify the result
against the real `build_coupled_shared_seam`/`check()` machinery, not
trusted from the algebra alone.

**A real mid-probe correction, caught before results were reported.**
The first solve assumed the glued complex's combined pairing equals
`pairing_A + pairing_B`, exactly as in the *disjoint* case. It does not:
in the glued complex the shared edge appears **once**, not twice, so
that naive sum double-counts the shared edge's own contribution whenever
it carries nonzero residue. This was caught by comparing the first
(wrong) solve's predicted `lambda` against the real `check()` output on
the combined complex, which disagreed for every shared edge except `b12`
(where the shared edge's residue contribution happens to be exactly
zero, since `b12` lies over no coarse edge — coincidentally making the
naive formula correct there and nowhere else). Fixed by deriving and
using the correct formula, `combined_pairing(lambda) = 2*pairing_own -
shared_contrib + lambda*correction`, accounting for the single-counted
shared edge explicitly.

**Result: 5 of 5 candidate (witness, edge) pairs with off-seam freedom
produced a compatible, branchwise-preserved, aggregate-cancelling
case**, each independently solved and independently verified:

```text
insert_bridge, shared_edge=e12: branch pairings -5/4,  combined pairing 0
insert_bridge, shared_edge=e23: branch pairings -5/4,  combined pairing 0
insert_bridge, shared_edge=e34: branch pairings -5/4,  combined pairing 0
insert_bridge, shared_edge=e14: branch pairings -5/3,  combined pairing 0
insert_bridge, shared_edge=b12: branch pairings -5/5,  combined pairing 0
```

Every case: `glued_status = interface_consistent` (a genuine, checked
compatible glue, not a constructed edge case bypassing the gate),
`branch_a["A4"] = branch_b["A4"] = True`, `combined["A4"] = False`,
`combined["pairing"] = 0`.

**A side observation, worth stating precisely so it is not misread as a
new finding.** Every found case shows `combined["N0"] = False`. This is
**inherited, not caused by gluing**: `INSERT_BRIDGE` — the only witness
this search could use at all — already fails its own (N0) individually
(documented in `refinement_witnesses.py`'s own comment: "naturality
fails at `b12`'s row"), confirmed directly against `refinement_checker.
check_witness(INSERT_BRIDGE)` before writing this down. The combined
(N0) failure is exactly the "a composite failure is not automatically a
compositional failure; it may be inherited warrant debt from a defective
component step" lesson this project has carried since Phase 2b, now
recurring in a new construction.

**What this settles, precisely.** Shared-seam compatibility does **not**
force non-cancellation: the disjoint-parallel case's branchwise/aggregate
A4 split survives fully into the compatible-coupled case, for this
witness family. This is evidence on one witness (the only one with
enough cycle-space freedom to test), not a general theorem — the
possibility is demonstrated, not the frequency or inevitability of it
across some wider class of witnesses this project has not built.

**Reproducing this**:

```sh
python refinement_witness_coupled_a4_cancellation_probe.py
pytest tests/test_refinement_witness_coupled_a4_cancellation_probe.py
```

**Not done in this phase**: any conflict-resolution rule (still
deliberately excluded — resolving this open question was never a
precondition for one, and remains the user's call, not a default); a
Rocq formalisation of the cancellation phenomenon (see Phase 5e, which
*was* done next); testing witnesses beyond this project's existing four
(a witness family with more/richer higher-dimensional cycle spaces might
show cancellation is *common*, not just possible — untested); any claim
about whether `A4_parallel_disjoint_branchwise`'s diagnostic report
structure (§Phase 4d) needs revision in light of this — it does not need
revision to remain correct (branchwise preservation is exactly what this
phase confirms still holds), but whether the *aggregate_cancelled*
outcome should be expected routinely rather than treated as a rare edge
case is an open framing question, not decided.

## Phase 5e: compatible aggregate-A4 cancellation, formalised in Rocq

Per the explicit instruction not to move to a conflict-resolution rule
yet, and instead to turn Phase 5d's probe finding into a verified
example: `rocq/CoupledParallelCompatibility.v` gained a second section,
`CompatibleAggregateCancellation`, proving exactly the fact the probe
discovered — not a general theorem, an `Example`, matching the same
"candidate/example before theorem" discipline used for the disjoint
case's own `A4_parallel_aggregate_can_fail_despite_branchwise`.

**The single-counting correction, made a proved fact rather than a
comment.** A branch's own (A4) pairing, once a shared seam is agreed,
splits into a piece contributed by data unique to that branch and a
piece contributed by the shared seam itself (the *same* value in both
branches, by agreement):

```text
left_total  = left_unique  + shared
right_total = right_unique + shared
```

The glued composite's **aggregate** pairing is *not* `left_total +
right_total`: in the glued complex the shared seam appears **once**, not
twice (unlike disjoint parallel composition, where nothing is shared and
the naive sum is exactly right), so

```text
glued_aggregate = left_unique + right_unique + shared
                = left_total + right_total - shared
```

— proved as `glued_aggregate_vs_naive_sum`, a one-line `ring` fact once
stated this way, but the exact correction the Python probe caught and
fixed mid-search (Phase 5d): a first solve that assumed
`glued_aggregate = left_total + right_total` was silently correct only
when `shared = 0`, and wrong everywhere else.

**`compatible_glue_can_cancel_aggregate_A4`** (`Example`): grounded in
the probe's own computed numbers (`INSERT_BRIDGE`, shared edge `e23`),
not invented — the shared seam's own contribution is `-1` (its declared-
cycle coefficient there, times the pulled-back residue, both `-1` and
`1` respectively), branch A's off-seam contribution is `-4` (giving
`left_total = -5`, matching the probe's `branch_a` pairing exactly),
branch B's off-seam contribution is `5` (giving `right_total = 4`,
matching the probe's `branch_b` pairing exactly). Both totals nonzero
(branchwise (A4) holds on both, exactly as computed); `glued_aggregate`
exactly zero. The same fact the probe found computationally is now
checked independently of the Python machinery entirely.

`coqc`-clean and `coqchk`-clean (zero axioms, full 14-file dependency
closure). No `Admitted`/`Axiom`/`sorry`. Still no conflict-resolution
rule anywhere in this file, or this project.

**Scope, stated precisely.** This proves that the specific numbers the
probe found genuinely satisfy the claimed inequalities/equality — it
does not generalise the *existence* of a cancelling case to an abstract
statement over arbitrary `shared`/`left_unique`/`right_unique` (that
would be trivial to prove — the existence of *some* zero of a linear
function is not the interesting content here; the interesting content
was finding a concrete instance grounded in real refinement-witness data
that the probe's earlier, buggy version got wrong before correction).
`glued_aggregate_vs_naive_sum` *is* the general, abstract fact (proved
for all `shared`/`left_unique`/`right_unique`, by `ring`) — the
cancellation `Example` deliberately stays concrete.

**Reproducing this**:

```sh
coqc rocq/CoupledParallelCompatibility.v
```

## Reproducing this

```sh
python refinement_witness_composition_probe.py
python refinement_witness_a4_e0_counterexample_search.py
python refinement_witness_composition_boundary_search.py
coqc rocq/RefinementWitnessComposition.v
coqc rocq/RefinementWitnessVerdictComposition.v
coqc rocq/RefinementWitnessSequentialComposition.v
coqc rocq/RefinementWitnessParallelComposition.v
python refinement_witness_parallel_disjoint_probe.py
pytest tests/test_refinement_witness_parallel_disjoint_probe.py
python refinement_witness_coupled_parallel_probe.py
pytest tests/test_refinement_witness_coupled_parallel_probe.py
coqc rocq/CoupledParallelCompatibility.v
python refinement_witness_coupled_a4_cancellation_probe.py
pytest tests/test_refinement_witness_coupled_a4_cancellation_probe.py
```

## Next steps

- Arbitrary finite chains (four-or-more steps): would need dependent
  list/vector machinery this project has not built; the three-step
  pattern is expected to continue but is not proved to.
- Coupled parallel composition, beyond the shared-seam compatibility gate
  (Phase 5b/5c) and the cancellation finding, now Rocq-verified
  (Phase 5d/5e): still no preservation candidate of any kind, probed or
  proved. Concretely open: (a) a conflict-resolution rule — this project
  has deliberately not chosen one (averaging, branch-preference, or
  otherwise), and picking one is itself a design decision, not yet made,
  gated on the compatibility semantics now being theorem-grade; (b)
  whether the "consistent gluing degenerates to disjoint-style
  preservation" finding (2 cases, Phase 5b) generalises, or is a
  small-sample artifact — Phase 5d/5e confirm it is at least not
  *unconditional* (compatible cancellation is real, and now
  `coqchk`-verified), but say nothing about how *common* it is across a
  wider witness family this project has not built; (c) connecting
  `CoupledParallelCompatibility.v`'s abstract `Key`/`Value` model back to
  the concrete `Edge`/`Witness` types in `refinement_witnesses.py` — not
  attempted; (d) shared declared-cycle coupling *without* a shared seam,
  and the other six coupling sources named in `docs/design/COUPLED_
  PARALLEL_COMPOSITION_PROBLEM.md` §2 — none attempted.
- Three-or-more-branch disjoint parallel composition: would need the
  same kind of generalisation as the sequential four-or-more-step case,
  not attempted.
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
- ~~Three-step composition~~ — done, `rocq/
  RefinementWitnessSequentialComposition.v`, `N0_composes_three`,
  `A4_composes_three`, `E0_composes_three`, `coqchk`-clean.
- ~~Probe disjoint parallel composition~~ — done, Phase 4b,
  `refinement_witness_parallel_disjoint_probe.py`, 32 cases; found the
  N0/E0-vs-A4 split.
- ~~Prove the parts of disjoint parallel composition the probe
  supports~~ — done, Phase 4c, `rocq/
  RefinementWitnessParallelComposition.v`, `N0_parallel_disjoint` and
  `E0_parallel_disjoint`, `coqchk`-clean. A4 deliberately not attempted
  — see above.
- ~~Settle and prove a branchwise A4 semantics for disjoint parallel
  composition~~ — done, Phase 4d, `rocq/
  RefinementWitnessParallelComposition.v` Part 4:
  `A4_parallel_disjoint_branchwise`, `A4_parallel_disjoint_nonzero_sum`,
  `A4_parallel_disjoint_branchwise_and_nonzero_sum`, and a
  machine-checked witness (`A4_parallel_aggregate_can_fail_despite_
  branchwise`) that branchwise success does not imply aggregate success.
  `coqchk`-clean.
- ~~Release checkpoint for the disjoint parallel classification~~ —
  done, tagged `v0.12-disjoint-parallel-classification`. Also found and
  fixed a real gap: `make check-rocq` had never compiled four
  already-proved files (`CochainNaturalityDescent.v`,
  `CommonSubdivisionAgreement.v`, `ExactnessReflection.v`,
  `FirstOrderClassifierCertificate.v`), documented but deferred in
  `REPRODUCIBILITY.md`; now wired in, full 13-file chain `coqchk`-clean.
- ~~Pose the coupled parallel composition problem~~ — done, Phase 5a,
  `docs/design/COUPLED_PARALLEL_COMPOSITION_PROBLEM.md`: picks shared
  seam / shared declared cycle as the first case, over policy authority,
  downstream fusion targets, and cross-branch pairing constraints
  (named, deferred). No probe or proof yet — that is the next step, not
  taken here.
- ~~Probe the shared-seam compatibility boundary~~ — done, Phase 5b,
  `refinement_witness_coupled_parallel_probe.py`, 5 hand-picked cases (2
  consistent, 3 conflicting, one conflict arising organically from two
  of this project's own canonical witnesses' own declarations). Found:
  consistent declarations glue cleanly and reduce to disjoint-style
  preservation; conflicting declarations correctly refuse a composite
  entirely (`interface_conflict`, not an (N0)/(A4)/(E0) failure). No
  merge/resolution rule attempted — deliberately excluded, per
  instruction.
- ~~Formalise the shared-seam compatibility gate~~ — done, Phase 5c,
  `rocq/CoupledParallelCompatibility.v`: `interface_agreement_allows_
  glue`, `interface_disagreement_blocks_glue`,
  `incompatible_has_no_glue`, and a concrete `Example`
  (`shared_label_not_sufficient_for_agreement`) upgrading the probe's
  organic `e12p` finding to `coqchk`-verified. Abstract `Key -> option
  Value` model, no decidable-equality hypothesis needed. `coqchk`-clean,
  full 14-file chain. Deliberately no merge rule, no (N0)/(A4)/(E0)
  claim for a glued composite.
- ~~Search for compatible aggregate-A4 cancellation~~ — done, Phase 5d,
  `refinement_witness_coupled_a4_cancellation_probe.py`: found and
  verified 5 cases (all using `INSERT_BRIDGE`, the only canonical
  witness with a $\geq 2$-dimensional cycle space, hence the only one
  offering the needed off-seam freedom) where a compatible shared-seam
  glue has branchwise A4 preserved on both branches yet the aggregate
  pairing is exactly zero — shared-seam compatibility does not force
  non-cancellation. Caught and corrected a real mid-probe error (naively
  assuming the glued pairing sums like the disjoint case, which
  double-counts the shared edge). Still no merge rule.
- ~~Formalise the cancellation phenomenon in Rocq~~ — done, Phase 5e,
  `rocq/CoupledParallelCompatibility.v`'s `CompatibleAggregateCancellation`
  section: `glued_aggregate_vs_naive_sum` (the general single-counting
  correction, by `ring`) and `compatible_glue_can_cancel_aggregate_A4`
  (an `Example`, grounded in the probe's own computed numbers, not
  invented). `coqchk`-clean, full 14-file chain. Still no merge rule.
