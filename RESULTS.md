# Results

What has been learned, organised by result. See [STATUS.md](STATUS.md) for the proved/computed/diagnostic distinction each result sits at, and [PROJECT_MAP.md](PROJECT_MAP.md) for file locations.

## R1. Four-cycle obstruction

```text
Residue: (1, 1, 1, -2)
Cycle:   (-1, -1, -1, 1)
Pairing: -5
Verdict: nontrivial H^1 obstruction
```

`residue_classifier.py` on `examples/four_cycle.json`; `-5 != 0` means the residue is not a coboundary. Formalised concretely in `rocq/FourCycleObstruction.v`, and used as the abstract instance of `rocq/AssociatorResidueRepair.v`'s repair-impossibility theorem.

## R2. Associator-generated residue

The same residue `(1, 1, 1, -2)` is generated from explicit associator-field data (`finite_algebra.py`, `regional_composition.py`, `associator_residue.py`) — one seam's defect is computed two independent ways (literal expansion and the closed-form four-term formula) and cross-checked on every call, not declared as an input.

## R3. Repair obstruction

The residue is closed but not globally repairable: no boundary correction assignment produces it as a coboundary. Computed by `repair_solver.py`; proved abstractly by `rocq/AssociatorResidueRepair.v` (repair would force the residue into `im(delta^0)`, contradicting a nonzero cycle pairing).

## R4. Refinement persistence

The A1-A4 witnesses (`refinement_checker.py`) preserve the obstruction in the refined complex for all four refinement witnesses (three subdivisions, one bridge insertion). The **descent-safe** result — (N0) cochain-map naturality, letting non-exactness descend back to the coarse complex — is narrower: it holds for the three subdivision witnesses and fails for the bridge witness, which changes `H_1` rather than subdividing. (E0) exactness reflection, checked independently, holds for all four witnesses including the bridge — it is (N0), not H1-surjectivity, that blocks the bridge witness specifically. Proved abstractly for A1-A4 (`rocq/AdmissibleRefinementPersistence.v`), (N0) (`rocq/CochainNaturalityDescent.v`), and (E0) (`rocq/ExactnessReflection.v`).

## R5. First-order certificate checking

Classifier verdicts (from R1/R2) can be emitted as proof-carrying certificates (`certificate_emitter.py`) and independently checked (`first_order_certificate_checker.py`), so trust does not have to rest on the generating Python program itself. Both certificate forms' soundness is proved in `rocq/FirstOrderClassifierCertificate.v`.

## R6. Independent generator: too free

The first associator generator's parameter-to-residue map is full rank: every residue in `C^1(N;Q)`, obstructed or not, is realisable, because its four seams share no data. Cannot distinguish a structurally-forced obstruction from an arbitrary choice of residue. (`realisability_diagnostic.py`, negative result.)

## R7. Coupled adjacent-overlap collapse

A genuinely coupled generator (one shared point universe, no private per-seam data), sharing only the adjacent-overlap correction slots and fixing the outer slots to zero, drops rank (3, not 4) but its entire image is exactly `im(delta^0)` — every producible residue is already repairable. Gradients, not curvature: with outer slots pinned to zero, each residue reduces to a discrete gradient of the shared data, a coboundary by construction. Identifies the outer correction slots as load-bearing. (`coupled_realisability_diagnostic.py`, negative but structural result.)

## R8. Two more negative linear/rational attempts, and one non-linear positive witness

- **Boolean proper-crossing** (`boolean_crossing_diagnostic.py`): a deterministic, parameter-free rule (correction slots derived from region containment/crossing, not shared scalars) produces a genuine non-degenerate residue outside `im(delta^0)`, verified through six gates against the real code on one specific non-degenerate cover. Positive, but non-linear — no rank or quotient to compute, so it does not answer the linear coupling question.
- **Ordered inclusion-exclusion** (`lattice_ie_diagnostic.py`): `mu` indexed globally by lattice-derived support pairs. The associator formula cancels exactly the genuinely-shared adjacent-pair terms, leaving only composite terms that never coincide across theta-triples in this cover — full rank, disguised independence. A parameter can be globally indexed and still fail to impose structural dependence if the formula cancels exactly the shared coordinates.

## R9. Candidate 3b classification: distinct support is cover-inert, repeated support is selective

**Candidate 3b** (`mu_UV=mu_VW=0`, outer slots `rho_{X,T}`/`rho_{Z,T}` keyed by region and triple support `T=X∩Y∩Z`) is cover-inert on the standard distinct-support cover (`candidate_discipline_diagnostic.py`: 8 parameters, all `private_residual`, full rank 4 — not because the rule is too free, but because the cover never lets two triple overlaps coincide). This negative direction is now machine-checked in general, not just on that one concrete cover: `rocq/CandidateThreeBDistinctSupportClassification.v` proves that whenever the four triple supports are pairwise distinct — abstracted over any type with decidable equality, no `Point` model or finiteness assumption required, only the four support *values* need differ — no two seams can ever reference the same carrier coordinate, and the induced map achieves every standard basis direction (hence full rank 4). A concrete instantiation confirms this specialises correctly to the actual cover the diagnostic uses.

Proved structurally (both computationally and, later, in Rocq) that in a four-theta-cycle, any two triples sharing a support point are forced to share it across **all four** — so the only repeated-support cover consistent with every triple overlap remaining a genuine singleton has all four supports equal to one global point. On such a cover (`repeated_triple_support_diagnostic.py`):

```text
n_params = 4
sharing = {zero_column: 0, private_residual: 0, genuinely_shared: 4}
rank(B) = 2
dim(im(B) ∩ im δ⁰) = 1
dim(quotient) = 1
verdict = genuinely_partial_nontrivial_quotient
```

**This is the first positive linear/rational diagnostic witness in the chain** — neither full-rank surjectivity (R6, R8) nor total coboundary collapse (R7). Invariant under enriching the cover up to `|Ui|=12` (six independent trials, `richness_invariance_check()`): the result depends only on theta-role incidence and the shared support point, never on what else a region contains.

Machine-checked in `rocq/RepeatedTripleSupportCandidate3b.v`: the `RepeatedTripleSupport` incidence record, the partial-support impossibility lemma, the genuinely-shared-columns theorem, and explicit repairable (`g1`) and non-repairable (`g2`) residue witnesses — `coqchk`-clean, no `Admitted`/`Axiom`/`sorry`.

**Together, the two Rocq files give a full classification, both directions machine-checked at the same level:**

```text
Candidate 3b is structurally selective only when triple support is
genuinely forced to repeat (all four supports collapse to one point).
Distinct support degenerates into independent seam-local freedom,
regardless of which specific cover realises the distinctness.
```

**What this does not show**: it is one rule (Candidate 3b), not a general theorem about linear couplings generally; it does not replace R8's non-linear Boolean witness, which is a different mechanism entirely; it does not claim Candidate 3b is the final, unique, or most natural coupling discipline — only that its behavior on these two support regimes is now fully characterised, not merely observed on isolated covers. See `docs/diagnostics/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md` for the diagnostic-level account.

## R10. Refinement-witness composition

A separate question from R1-R9: given two refinement witnesses $P \to
Q$ and $Q \to R$, each individually admissible, descent-safe (N0), and
exactness-reflecting (E0), does the composite $P \to R$ inherit those
properties? Not addressed by the original refinement-persistence result
(item 10/R4) at all — that concerns a single witness, not composing two.

Tested first: 26 composed witnesses from genuine graph refinements
(subdividing a vertex, inserting a bridge), then ~175,000 from an
adversarial search dropping all graph structure — small arbitrary
rational coboundary maps and edge-level pullbacks, constrained only by
the actual hypotheses. Zero (A4)/(E0) counterexamples in either search.
A real methodological mistake was caught and corrected along the way:
an early, unfiltered version of the adversarial search reported
thousands of spurious composite (E0) "failures" that turned out to be
individual-step failures inherited by the composite, not composition
failures.

That evidence was then turned into three Rocq theorems
(`rocq/RefinementWitnessComposition.v`, `rocq/
RefinementWitnessVerdictComposition.v`), each needing less than the
search's own framing suggested:

```text
N0_composes:  needs both steps' own N0 -- pure associativity of
              function composition.
A4_composes:  needs only step 2's own A4, applied to the residue step 2
              actually receives -- near-definitional, once the composite
              is defined as function composition. Step 1's A4 is not a
              hypothesis; neither is N0.
E0_composes:  needs both steps' own E0, chained through linearity of the
              pushforward maps (minimal span/linear-map infrastructure
              built from scratch for this proof) -- does NOT need
              either step's N0, contrary to an earlier hand derivation
              that reached for it unnecessarily.
```

**The headline fact**: the three conditions compose with three
*different* dependency profiles, not uniformly — "the composite is
verdict-safe" is the conjunction of three separately-justified facts,
not one fact. This is also the precise, now-proved mechanism behind the
caught mistake above:

```text
A composite failure is not automatically a compositional failure; it
may be inherited warrant debt from a defective component step.
```

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`. See
`docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md` for the full
search-then-proof account and `paper/finite_obstruction_calculus_for_
regional_warrant.tex` §5 (Theorems 5.1-5.3) for the formal statements.

**Extended to three steps** (`rocq/RefinementWitnessSequentialComposition.v`,
$P \to Q \to R \to S$): the same dependency profile, applied once more,
not a new argument. `N0_composes_three` and `E0_composes_three` need
*all three* steps' own condition; `A4_composes_three` needs *only the
last* step's own (A4), regardless of chain length. `coqchk`-clean.

**What this does not show**: that a different formalisation of "the
composite witness" (not reusing the same declared cycle at the
composite level) behaves the same way; that chains of four or more
steps behave the same way (expected, by the shape of the three-step
proofs, but not checked); or anything about the
sequential/parallel/restriction/failure composition axes proposed (not
proved) in `veribound-fce`'s `docs/design/CERTIFICATE_COMPOSITION_SPEC.md`.

**Disjoint parallel composition — a genuinely different construction,
a genuinely different result.** All of the above concerns *sequential*
composition, $P \to Q \to R$: the composite is built by function
composition. Disjoint parallel composition combines two *independent*
witnesses side by side — a direct sum, not a composition — per
`veribound-fce`'s `docs/design/PARALLEL_WITNESS_COMPOSITION_SPEC.md`.

Probed first (`refinement_witness_parallel_disjoint_probe.py`, 32
cases, all 16 ordered pairs from `ALL_WITNESSES` with and without a
sign-negated declared cycle): N0 and E0 always equal AND(branch A,
branch B); A4 does not — 16/32 cases mismatch. The mechanism, worked
out by hand and then checked: under a direct sum, the combined
coboundary/pullback structure is block-diagonal, so N0 (matrix
equality) and E0 (subspace containment) reduce cleanly to "holds in
block A and holds in block B." A4 is different in kind — the combined
declared cycle's pairing is the *sum* of the two branches' own
pairings, not an AND, and two nonzero numbers can sum to zero.
Demonstrated concretely: `SUBDIVIDE_U1` paired against a sign-negated
copy of itself gives branch pairings $+5$/$-5$, both individually
satisfying each branch's own (A4), and a combined pairing of exactly
$0$, failing the composite's (A4).

That probe result was then turned into two Rocq theorems
(`rocq/RefinementWitnessParallelComposition.v`), built from a genuine
direct-sum (product-type) construction rather than function
composition, reusing the E0 proof's `VSpace`/`InSpan`/`IsLinear`
infrastructure plus a new direct-sum constructor and a
span-monotonicity lemma:

```text
N0_parallel_disjoint:  pure case analysis on the product type, no
                        vector-space structure needed.
E0_parallel_disjoint:  each branch's own E0 transports through a linear
                        embedding into the combined space; a
                        monotonicity lemma glues the two branch results
                        together.
```

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`. **No bare A4 theorem is
stated** — that name (`A4_parallel_disjoint`) belongs to a false claim.

**A4's full classification, proved, not left as an open design
question.** The natural statement ("both branches' own A4 implies the
composite's A4") is false, and the follow-up work settled which of the
two candidate replacements to prove, and proved both:

```text
A4_parallel_disjoint_branchwise:
    each branch's own A4 survives combination, reported separately --
    proved unconditionally, no extra hypothesis needed.
A4_parallel_disjoint_nonzero_sum:
    the aggregate (summed) pairing is nonzero exactly when an explicit
    non-cancellation hypothesis holds -- needs ONLY that hypothesis,
    neither branch's own A4.
A4_parallel_aggregate_can_fail_despite_branchwise (Example):
    a concrete, machine-checked witness (Q values +5/-5, the same
    numbers the probe found) that branchwise success does not imply
    aggregate success -- upgrading "the naive claim is false" from a
    Python-probe finding to a coqchk-verified fact.
```

Branchwise semantics was deliberately pursued first (not the scalar
`_nonzero_sum` patch): it is the more diagnostic replacement, since it
preserves the fact of each branch's own evidence rather than collapsing
it into one number that can silently cancel. `verdict_safe`, as already
defined elsewhere in this project, uses the *aggregate* (A4); no
`verdict_safe_parallel_disjoint` claim is made using that existing
definition, since the aggregate needs the explicit non-cancellation
hypothesis. A branchwise-flavored `verdict_safe` variant is not defined
anywhere either — an open question, not a proved or refuted one.

Not addressed at all: coupled parallel composition (branches sharing a
vertex, seam, declared cycle, or downstream target) — no preservation
candidate exists for it, probed or proved; three-or-more-branch disjoint
parallel composition.

**Coupled parallel composition — the first boundary, not preservation
(Phase 5b).** Released as `v0.12-disjoint-parallel-classification`
covered only Phases 4a-4d above; coupled parallel composition was
posed as a problem afterward (`docs/design/COUPLED_PARALLEL_
COMPOSITION_PROBLEM.md`, Phase 5a) and then probed
(`refinement_witness_coupled_parallel_probe.py`, Phase 5b) — deliberately
answering a prior question, not the preservation question:

> When two branches share one refined-level seam rather than being fully
> independent, is the glued composite witness even well-defined?

Both branches sit over the *same* coarse complex (unlike the disjoint
case, which duplicates it), with one designated shared edge and its two
endpoint vertices kept identical between branches instead of
independently renamed. A deliberately conservative compatibility gate —
no averaging, summing, or branch-preference merge rule — requires both
branches' own declarations for the shared seam (edge data, declared-cycle
value, and coarse parent) to agree *exactly* before any composite is
built at all.

Five cases, checked: two consistent-declaration cases (one a self-pairing,
one a genuine cross-witness agreement between `SUBDIVIDE_U1` and
`SUBDIVIDE_U2` sharing edge `e34`) glue cleanly and reduce to the
disjoint case's own preservation pattern (N0/E0 match AND, A4 branchwise
holds). Three conflicting-declaration cases — two deliberately
constructed (a flipped pullback sign; a mismatched declared-cycle
coefficient), one arising *organically* between `SUBDIVIDE_U1` and
`SUBDIVIDE_U2`'s own real declarations for an edge both happen to name
`e12p` but mean differently — correctly refuse a composite entirely,
reported as `interface_conflict`, never as an (N0)/(A4)/(E0) failure,
since no composite object exists for those conditions to be tested
against.

Not addressed by the probe itself: any conflict-resolution rule
(deliberately excluded); whether the consistent-case finding
generalises beyond 2 hand-picked cases; the other six coupling sources
named in the problem document's taxonomy (policy authority, downstream
fusion target, common restriction/downgrade, cross-branch pairing
constraint, shared vertex/region carrier without a shared edge, shared
declared cycle without a shared seam).

**The compatibility gate itself, formalised in Rocq (Phase 5c).**
`rocq/CoupledParallelCompatibility.v` proves the well-definedness
property underneath Phase 5b's `interface_conflict` refusal, deliberately
NOT any (N0)/(A4)/(E0) claim and NOT a merge rule. A branch's interface
declaration is modelled abstractly as `Key -> option Value` (no `Edge`/
`Witness` types, no decidable-equality hypothesis — the same abstraction
discipline as `CandidateThreeBDistinctSupportClassification.v`):

```text
interface_agreement_allows_glue:
    Compatible dA dB -> exists g, IsGlue dA dB g.
    (constructive: the glue is exhibited explicitly.)
interface_disagreement_blocks_glue / incompatible_has_no_glue:
    a disagreeing shared key means NO glue satisfies both branches'
    declarations at all -- near-definitional once "glue" is stated to
    mean "reproduces both branches' declared values at a shared key,"
    not a separately-imposed side condition.
shared_label_not_sufficient_for_agreement (Example):
    a concrete Key:=nat/Value:=Q witness (values 1 vs -1 at the same
    key) -- the Rocq-level counterpart of the probe's organic e12p
    finding, upgraded from illustrated to coqchk-verified.
```

`coqchk`-clean, full 14-file dependency closure, no `Admitted`/`Axiom`/
`sorry`. Deliberately does not connect back to the concrete `Edge`/
`Witness` types, does not address multiple simultaneously-shared keys
by example (though `Compatible`'s own definition already generalises to
that case), and does not attempt any preservation theorem or merge
rule — both remain open, the merge rule intentionally so until the
refusal semantics was theorem-grade.

**Compatible aggregate-A4 cancellation — found, not merely possible
(Phase 5d).** With the compatibility gate theorem-grade, the one
preservation-adjacent question left deliberately deferred was: does
shared-seam *agreement* force the aggregate (A4) to compose, the way it
forces (N0)/(E0) to (Phase 5b)? Answer: no.

The construction problem, worked out before any code: for a witness
whose refined complex has a 1-dimensional cycle space (every
`SUBDIVIDE_*` witness here, each a single loop), the declared cycle is
determined up to an overall scalar by any one coordinate, so agreement
at one shared coordinate pins the *entire* vector down — no room to vary
anything else. Cancellation needs independent variation away from the
shared seam while the seam stays fixed, which needs a cycle space of
dimension $\geq 2$. Checked, not assumed: of this project's four
canonical witnesses, only `INSERT_BRIDGE` has one (two parallel edges
between `U1` and `U2` give a "big loop" and a "small loop" as
independent cycle directions; the small loop is zero at `e23` but
nonzero, and residue-carrying, at `e12`).

`refinement_witness_coupled_a4_cancellation_probe.py` computes, for
each (witness, edge) pair, the subspace of cycle vectors vanishing at
that edge exactly (`nullspace_over_Q`, not hand-picked), then *exactly
solves* for the scalar multiple that zeroes the glued composite's
aggregate pairing, verified against the real `check()` machinery. A
real mid-probe correction was caught along the way: the first solve
assumed the glued pairing sums like the disjoint case (`pairing_A +
pairing_B`), but in the glued complex the shared edge appears **once**,
not twice — the naive formula double-counts it whenever it carries
nonzero residue, silently correct only for the one shared edge (`b12`)
that happens to carry none. Fixed by deriving the correct formula
accounting for single-counting.

Result: **5 of 5** candidate cases produced a compatible
(`interface_consistent`), branchwise-A4-preserved, aggregate-A4-
cancelled composite, each independently solved and independently
verified against `check()`:

```text
insert_bridge, e12: branch pairings -5/4,  combined pairing 0, A4=False
insert_bridge, e23: branch pairings -5/4,  combined pairing 0, A4=False
insert_bridge, e34: branch pairings -5/4,  combined pairing 0, A4=False
insert_bridge, e14: branch pairings -5/3,  combined pairing 0, A4=False
insert_bridge, b12: branch pairings -5/5,  combined pairing 0, A4=False
```

Every found case also shows `N0=False` on the combined witness — flagged
explicitly as **inherited, not new**: `INSERT_BRIDGE` already fails its
own (N0) individually (documented in `refinement_witnesses.py`'s own
comment), confirmed directly against `refinement_checker.check_witness`
before being reported, the same "composite failure is not automatically
a compositional failure" distinction this project has drawn since
Phase 2b.

**What this settles**: shared-seam compatibility does not force
non-cancellation — the disjoint case's branchwise/aggregate A4 split
survives fully into the compatible-coupled case, for this witness
family. Not a general theorem: evidence on the one witness with enough
cycle-space freedom to test, not a statement about how common
cancellation is across some wider class of witnesses this project has
not built. Still no conflict-resolution rule, and none proposed.

**The cancellation phenomenon, formalised in Rocq (Phase 5e).**
`rocq/CoupledParallelCompatibility.v` gained a second section,
`CompatibleAggregateCancellation`, proving the general mechanism as an
abstract fact and the probe's specific finding as a concrete `Example`
-- not a general existence theorem, matching the same "candidate/example
before theorem" discipline the disjoint case's own
`A4_parallel_aggregate_can_fail_despite_branchwise` used.

The single-counting correction, proved rather than only argued in a
comment: once a shared seam is agreed, a branch's own pairing splits
into a piece unique to that branch plus the shared seam's own
contribution (the *same* value in both branches, by agreement):

```text
left_total  = left_unique  + shared
right_total = right_unique + shared
```

The glued composite's aggregate is *not* `left_total + right_total` --
the shared seam appears once in the glued complex, not twice -- so

```text
glued_aggregate = left_unique + right_unique + shared
                = left_total + right_total - shared      (glued_aggregate_vs_naive_sum, by `ring`)
```

`compatible_glue_can_cancel_aggregate_A4` (`Example`) instantiates this
with the probe's own computed numbers (`INSERT_BRIDGE`, shared edge
`e23`: shared contribution `-1`, branch A's off-seam contribution `-4`
giving `left_total = -5`, branch B's off-seam contribution `5` giving
`right_total = 4`) -- both totals nonzero, `glued_aggregate` exactly
zero, matching the probe's computed result exactly, now checked
independently of the Python machinery entirely.

`coqchk`-clean, full 14-file dependency closure, no `Admitted`/`Axiom`/
`sorry`. Still no conflict-resolution rule anywhere in this project.

## R11. The conflict-resolution trilemma

A genuinely separate mathematical question from R10's whole composition
line — not about refinement witnesses, coupled parallel composition, or
any structure elsewhere in this project, but about equality and total
resolver functions `V x V -> V` in the abstract. Motivated directly by
R10's shared-seam compatibility gate: once two branches disagree
(`interface_conflict`), any system that wants to *produce* a composite
value anyway, rather than refuse, needs a resolver. This result shows
such a resolver can never be neutral.

**The minimal core fact**, `docs/design/CONFLICT_RESOLUTION_TRILEMMA.md`
§3:

```text
x != y  ->  ~ (z = x /\ z = y)
```

If two declarations genuinely disagree, no single value equals both.
Combined with two named properties (Left fidelity: `resolve(x,y)=x`
always; Right fidelity: `resolve(x,y)=y` always), this forces: **no
resolver can have both fidelities, unless the whole value type collapses
to at most one element.** Proved in general, not just for the pair that
triggered a specific conflict — `rocq/ConflictResolutionTrilemma.v`:

```text
no_single_value_matches_both_declarations
full_fidelity_forces_trivial_domain
no_resolver_has_both_fidelities_on_nontrivial_domain   (the operationally
    meaningful contrapositive: given any two distinct values -- true of
    every real interface-value type this project uses -- no resolver
    can have both fidelities)
```

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`.

**Six named desiderata** (agreement, left fidelity, right fidelity,
symmetry, idempotence, refusal), with an honest observation checked
before building anything on top of it: *idempotence is exactly the
diagonal special case of agreement* (`resolve(x,x)=x`, where agreement's
hypothesis `x=y` is trivially satisfied) — not an independent property,
though kept as its own named column for clarity.

**Seven candidate resolver shapes classified**, computationally
(`conflict_resolution_trilemma_probe.py`, exact rationals) not merely
argued:

```text
resolver             agreement  idempotent  left_fid  right_fid  symmetric
left_wins             True       True        True      False      False
right_wins            True       True        False     True       False
average               True       True        False     False      True
sum                   False      False       False     False      True
erase                 False      False       False     False      True
refuse                (not a V x V -> V function on disagreement at all)
external_authority    (not a function of (x, y) alone -- category-level exclusion)
```

`sum` and `erase` are the sharper finding: they sacrifice *more* than
the two fidelities — `sum(x,x) = 2x`, which equals `x` only when `x=0`,
so `sum` fails agreement and idempotence too, not merely both
fidelities like `average` does. Confirmed computationally that agreement
and idempotence coincide for every resolver tested, exactly as the
diagonal-case observation predicts.

**What this does not do**: choose, recommend, or endorse a resolver.
`external_authority` is flagged as not even the same kind of object the
other six are (not a pure function of the two declared values alone —
the sacrifice is category-level, not property-level). No resolver is
implemented in either `regional-obstruction-calculus` or
`veribound-fce`.

**Lossy versus structured resolution.** The impossibility above is
specifically about resolvers whose *output* is the same type `V` as the
two declarations — a **lossy** resolver necessarily discards
information on disagreement, since §3's minimal fact rules out any
value of type `V` recovering both sides. Nothing forces the output to
stay in `V`, though: a **structured** resolver's codomain can be a
different type carrying both original declarations, recoverable by
projection. Proved, not merely asserted, in
`rocq/ConflictResolutionTrilemma.v`:

```text
pair_resolver_preserves_both_claims :
    forall x y : V, fst (pair_resolver x y) = x /\ snd (pair_resolver x y) = y.
    (pair_resolver x y := (x, y) -- both projections recover the original
    values exactly, for every pair, including disagreeing ones.)

structure_does_not_exempt_the_resolved_field :
    forall (resolved : V -> V -> V) (a b : V), a <> b ->
      ~ ((forall x y, resolved x y = x) /\ (forall x y, resolved x y = y)).
    (literally the same theorem as no_resolver_has_both_fidelities_
    on_nontrivial_domain, restated at a structured object's own scalar
    summary field to make explicit that structure does not exempt it.)
```

Existence, not a second impossibility: this shows the original
impossibility is about single-value (same-type) resolution
specifically, not about preserving information as such — but a
structured resolver that also exposes one scalar "resolved" summary
field (for a consumer that wants a single value) still owes that field
to the same trilemma as before. Preserving both claims and having one
faithful combined scalar are different goals; structure achieves only
the first. Checked computationally too
(`conflict_resolution_trilemma_probe.py`'s `pair_resolver`), `coqchk`
-clean, no `Admitted`/`Axiom`/`sorry`, full 16-file dependency closure.

## R12. The non-lossy lower bound

Given that structured (non-lossy) resolution is possible at all (R11's
`pair_resolver`), how much structure does it actually require? Not a
new question invented for its own sake — the natural next step once
existence was settled, and, like R11, a fact about functions and
equality in the abstract, not about refinement witnesses.

**Definition** (`docs/design/CONFLICT_RESOLUTION_TRILEMMA.md` §9): an
encoding `encode : V -> V -> C` is **non-lossy** when fixed projections
`left_read, right_read : C -> V` recover both original declarations,
for every pair. R11's `pair_resolver` is exactly the case `C := V * V`.

**The lower bound**, proved in `rocq/ConflictResolutionLowerBound.v`:

```text
nonlossy_encoding_injective :
    NonLossy(encode, left_read, right_read) ->
    encode(x1, y1) = encode(x2, y2) -> x1 = x2 /\ y1 = y2
```

A non-lossy encoding must assign a genuinely distinct `C`-value to every
distinct ordered pair of declarations, or its fixed projections could
not tell two different conflicts apart. Pairing into `V * V` is not
merely *one* way to be non-lossy — `structured_pair_is_nonlossy` shows
it achieves this bound exactly, with no wasted structure.

**The finite corollary**: for finite `V` with `|V| = n`, injectivity on
`V * V` forces the encoding's codomain to satisfy `|C| >= n^2`. In
particular, no encoding whose codomain is confined to `V` itself (size
`n`) can be non-lossy once `n > 1`, since `n^2 > n` — a
cardinality-flavoured restatement of R11's original equational
impossibility, not a new assumption. Checked computationally, not only
argued, in `conflict_resolution_lower_bound_probe.py`, `n = 1..6`:

```text
n    n^2   gap = n^2 - n
1    1     0
2    4     2
3    9     6
4    16    12
5    25    20
6    36    30
```

**A scope note, checked before writing it down**: this does *not* mean
every codomain-`V` resolver's actual output range is bounded by `n` in
general — `sum`'s outputs are not structurally confined to any finite
test subset of `Q`, so counting its image size would not demonstrate
the bound. The probe instead uses resolvers whose output is
structurally confined to `V` by construction: `left_wins`/`right_wins`
(image size exactly `n`, the best a codomain-confined resolver can do)
and `erase` (image size exactly `1`, the worst) — both confirmed strictly
short of `n^2` once `n > 1`.

**What this settles, and what it does not**: the *shape* a faithful,
non-lossy conflict record must have — an injective encoding of the
ordered pair, nothing looser — not what specific fields, names, or
format such a record should carry in a real diagnostic system. That
remains entirely undecided.

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`, full 16-file dependency
closure. No resolver, encoding format, or diagnostic schema is
proposed, recommended, or implemented in either
`regional-obstruction-calculus` or `veribound-fce`.

## R13. Bounded conflict-diagnostic completeness

R11 showed a single value cannot preserve two disagreeing declarations.
R12 showed a non-lossy diagnostic must carry enough information to
recover the ordered pair. R13 combines both into a closed
classification, answering the question neither R11 nor R12 individually
asked: once two declarations disagree, what are the honest things a
diagnostic can even *be*?

**"Bounded" is load-bearing.** This is completeness for one small,
explicitly defined fragment (`docs/design/
CONFLICT_DIAGNOSTIC_COMPLETENESS.md`), not for all possible fusion,
policy, or coupled-composition systems. The fragment is formalised as a
closed, four-constructor Coq inductive type, `rocq/
ConflictDiagnosticCompleteness.v`:

```coq
Inductive ConflictDiagnostic (V C : Type) : Type :=
  | RefuseDiagnostic
  | ScalarDiagnostic (z : V)
  | StructuredDiagnostic (c : C)
  | UnresolvedDiagnostic.
```

matching, respectively: `interface_conflict` (no composite formed at
all), any named resolver strategy (`left_wins`/`right_wins`/`average`/
`sum`/`erase`), `NonLossyConflictDiagnostic`/R12's `encode`, and
`ReportSource.UNRESOLVED`. Classification into four `DiagnosticClass`
buckets (`no_composite`/`lossy_scalar`/`nonlossy_structured`/
`unresolved_case`) is proved total and exclusive
(`conflict_diagnostic_classification_total`,
`..._exclusive`), and the four classes — along with the underlying
`ConflictDiagnostic` constructors themselves — are proved pairwise
distinct.

**What makes this more than a restatement of Coq's own exhaustive
pattern matching**: `ScalarDiagnostic` is pinned to R11 — it is always
lossy once `x <> y`, imported directly rather than reproved
(`scalar_summary_not_fully_faithful_on_conflict`, and its headline
restatement `no_hidden_neutral_scalar_case`). `StructuredDiagnostic` is
pinned to R12 — non-lossy exactly when its fixed projections recover
both declarations (`structured_diagnostic_nonlossy`,
`nonlossy_diagnostic_injective`), with pairing achieving the bound
exactly (`pair_diagnostic_is_nonlossy`, `pair_encoding_injective`).
Every theorem in `rocq/ConflictDiagnosticCompleteness.v` either imports
R11/R12 directly or is a thin corollary of one of them — no new
mathematical machinery, only a vocabulary that closes the space of
honest diagnostics into four named, semantically pinned shapes.

**The disturbing sentence this licenses**: there is no fifth, neutral
scalar case. A system that claims to resolve a conflict with a single
scalar output is, within this fragment, either losing information
(`lossy_scalar`), refusing composition (`no_composite`), or hiding
additional structure it has not admitted to (in which case it is really
`nonlossy_structured` wearing a scalar-shaped label).

Checked computationally, not only stated, in
`conflict_diagnostic_completeness_probe.py`: every named strategy
(`refuse`/`left_wins`/`right_wins`/`average`/`sum`/`erase`/`pair`/
`unresolved`) lands in exactly one of the four classes, with
`left_wins`/`right_wins`/`erase` additionally confirmed lossy via the
R12 pigeonhole argument specialised at codomain `= V`. `average`/`sum`
are classified `lossy_scalar` by type alone, deliberately excluded from
the confinement check — the same caveat R12's own probe already
established, carried forward rather than silently dropped.

`coqchk`-clean, no `Admitted`/`Axiom`/`sorry`, full 17-file dependency
closure. No resolver is chosen; §7 of the design doc states in detail
what this does and does not claim — in particular, it does **not**
claim R11's seven named resolver shapes are exhaustive (the trilemma
doc's own §10 already disclaims that, at a different, finer level than
this result's four structural classes).

`docs/theory/NO_NEUTRAL_SCALAR_FUSION.md` synthesises R11-R13 into one
narrative note, with the headline sentence stated once, in full, rather
than assembled from three separate documents.
