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
