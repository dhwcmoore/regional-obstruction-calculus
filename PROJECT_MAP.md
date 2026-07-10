# Project Map

Where to start, by layer. See [STATUS.md](STATUS.md) for what each layer actually establishes, and [RESULTS.md](RESULTS.md) for the results themselves.

## 1. Core exact rational layer

- `rational_linear_algebra.py` — shared exact-rational solver (`mat_vec`, `mat_mat`, `dot`, `solve_over_Q`, `nullspace_over_Q`, `in_span_over_Q`, ...), used by every layer below.
- `residue_classifier.py` — the base obstruction classifier.
- `examples/four_cycle.json` — the central four-region witness data.
- `rocq/AdmissibleRefinementPersistence.v` — Rocq proof of the abstract A1-A4 persistence theorem.

## 2. Associator-generation layer

- `finite_algebra.py` — structure-constant `Q`-algebra and literal associator.
- `regional_composition.py` — square-zero Venn model, boundary-corrected product, associator defect.
- `associator_residue.py` — compiles a seam residue from associator-field data.
- `repair_solver.py` — obstruction-language wrapper around `rational_linear_algebra`.
- `run_associator_obstruction.py` — CLI entry point.
- `certificate_emitter.py` — JSON certificate for the associator-generated pipeline.
- `examples/four_cycle_associator.json` — local product/correction data for the four seams.
- `rocq/AssociatorResidueRepair.v` — abstract associator repair-impossibility theorem.
- `rocq/FourCycleObstruction.v` — the paper's own `r`, `z`, and pairing checked inside Rocq.

## 3. Refinement layer

- `refinement_witnesses.py` — explicit refined complexes, pullback maps, declared cycles.
- `refinement_checker.py` — checks (A1)-(A4), (N0) cochain naturality, (E0) exactness reflection, `descent_safe`, `verdict_safe`.
- `ocaml/refinement_witnesses.ml`, `ocaml/refinement_checker.ml` — self-contained OCaml mirror (local exact-rational `Q.t`).
- `rocq/CochainNaturalityDescent.v` — Rocq proof of the (N0)-descent theorem.
- `rocq/CommonSubdivisionAgreement.v` — two-map common-subdivision certificate agreement.
- `rocq/ExactnessReflection.v` — Rocq proof of the (E0)-reflection theorem.
- `rocq/RefinementWitnessComposition.v` — (N0)-composability, proved abstractly: `N0_composes`.
- `rocq/RefinementWitnessVerdictComposition.v` — (A4)/(E0)-composability, proved abstractly: `A4_composes`, `E0_composes`, with minimal span/linear-map infrastructure built from scratch.
- `rocq/RefinementWitnessSequentialComposition.v` — three-step composition: `N0_composes_three`, `A4_composes_three`, `E0_composes_three`. Arbitrary finite chains not attempted.
- `refinement_witness_composition_probe.py`, `refinement_witness_a4_e0_counterexample_search.py`, `refinement_witness_composition_boundary_search.py` — the ~175,000-case computational search that preceded and corroborates the proofs above. See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`.
- `refinement_witness_parallel_disjoint_probe.py` — Phase 4b probe: does disjoint-parallel (direct-sum) composition of two refinement witnesses preserve (N0)/(A4)/(E0) componentwise? N0 and E0 always match AND across 32 cases; A4 does not (16/32 mismatches, via sign-cancellation of the combined pairing). See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`, Phase 4b.
- `rocq/RefinementWitnessParallelComposition.v` — Phase 4c/4d: proves `N0_parallel_disjoint` and `E0_parallel_disjoint` (Phase 4c) built via a genuine direct-sum (product-type) construction, not function composition; and a full A4 classification (Phase 4d) — `A4_parallel_disjoint_branchwise` (unconditional), `A4_parallel_disjoint_nonzero_sum` (the scalar test, exactly under an explicit non-cancellation hypothesis), `A4_parallel_disjoint_branchwise_and_nonzero_sum` (bundling corollary), and a machine-checked witness (`A4_parallel_aggregate_can_fail_despite_branchwise`) that branchwise success does not imply aggregate success. Deliberately does *not* state a bare `A4_parallel_disjoint` — that name belongs to the false naive claim. Released as `v0.12-disjoint-parallel-classification`.
- `docs/design/COUPLED_PARALLEL_COMPOSITION_PROBLEM.md` — problem framing only, no theorem/probe/code: picks shared seam / shared declared cycle as the first concrete coupled-parallel-composition case, ahead of policy authority, downstream fusion targets, and cross-branch pairing constraints. Explains why coupled parallel composition needs an identification/gluing construction, not a variant of disjoint parallel's direct sum.
- `refinement_witness_coupled_parallel_probe.py` — Phase 5b probe: a conservative compatibility gate for shared-seam coupled parallel composition (no merge rule). Consistent shared-seam declarations glue cleanly and reduce to disjoint-style preservation (N0/E0 match AND, A4 branchwise holds); conflicting declarations refuse a composite entirely (`interface_conflict`), including a case where the conflict arises organically between two of this project's own canonical witnesses, not only from a deliberately constructed one. See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`, Phase 5b.
- `rocq/CoupledParallelCompatibility.v` — Phase 5c/5e: formalises the compatibility gate itself, abstractly (`Key -> option Value`, no `Edge`/`Witness` types, no decidable-equality hypothesis) — `interface_agreement_allows_glue`, `interface_disagreement_blocks_glue`, `incompatible_has_no_glue`, and a concrete `Example` (`shared_label_not_sufficient_for_agreement`) upgrading the probe's organic naming-collision finding to `coqchk`-verified (Phase 5c). A second section, `CompatibleAggregateCancellation` (Phase 5e), proves the single-counting correction between a glued aggregate and the naive disjoint-style sum (`glued_aggregate_vs_naive_sum`) and a concrete `Example` (`compatible_glue_can_cancel_aggregate_A4`), grounded in the Phase 5d probe's own computed numbers, that branchwise A4 can hold on both branches while the glued aggregate is exactly zero. Deliberately no merge rule. See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`, Phases 5c and 5e.
- `refinement_witness_coupled_a4_cancellation_probe.py` — Phase 5d: does shared-seam compatibility force non-cancellation of the aggregate (A4)? No — 5 verified cases (all using `INSERT_BRIDGE`, the only canonical witness with a $\geq2$-dimensional cycle space) show a compatible glue with branchwise A4 preserved on both branches yet aggregate pairing exactly zero. See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`, Phase 5d.
- `docs/design/CONFLICT_RESOLUTION_TRILEMMA.md` — a separate mathematical question from the Phase 5 line above: once two branches disagree (`interface_conflict`), what must any conflict-resolution rule sacrifice? Six named resolver desiderata (agreement, left/right fidelity, symmetry, idempotence, refusal), with idempotence shown (and checked) to be a special case of agreement, not independent. No resolver is proposed or endorsed.
- `conflict_resolution_trilemma_probe.py` — checks the design doc's §4 classification table computationally over `Q`: `left_wins`/`right_wins`/`average`/`sum`/`erase`, against all five checkable desiderata. Confirms no named resolver has both fidelities, and that `sum` sacrifices agreement/idempotence too, not only the fidelities.
- `rocq/ConflictResolutionTrilemma.v` — the core impossibility, proved abstractly for any type `V`: `no_single_value_matches_both_declarations` (the minimal fact — disagreement means no single value can match both declarations); `full_fidelity_forces_trivial_domain` and its contrapositive `no_resolver_has_both_fidelities_on_nontrivial_domain` (no resolver can have both full fidelities unless `V` is trivial). Plus a lossy-vs-structured section: `pair_resolver_preserves_both_claims` (existence: a structured, non-lossy resolver preserving both declarations always exists) and `structure_does_not_exempt_the_resolved_field` (structure does not exempt a structured object's own scalar summary field from the same impossibility). `coqchk`-clean.
- `rocq/ConflictResolutionLowerBound.v` — R12: how much structure a non-lossy encoding actually requires. `nonlossy_encoding_injective` (any non-lossy encoding `V -> V -> C` must be injective on `V * V`) and `structured_pair_is_nonlossy` (pairing into `V * V` achieves this bound exactly). `coqchk`-clean.
- `conflict_resolution_lower_bound_probe.py` — checks the finite corollary computationally: for `|V| = n`, `|V x V| = n^2 > n` whenever `n > 1`, so no codomain-confined-to-`V` resolver can be non-lossy. Confirms `left_wins`/`right_wins`'s image size is exactly `n` (best possible for a codomain-confined resolver) and `erase`'s is exactly `1` (worst) — both strictly short of `n^2`.
- `docs/design/CONFLICT_DIAGNOSTIC_COMPLETENESS.md` — R13: combines R11 and R12 into a bounded, closed classification of what a diagnostic about a conflicting shared interface can honestly be — refusal, lossy scalar summary, non-lossy structured diagnostic, or unresolved. Defines the fragment tightly before any proof; its §7 "What is not claimed" states explicitly this is not a claim about all possible diagnostic systems, only the narrow four-constructor fragment defined here.
- `rocq/ConflictDiagnosticCompleteness.v` — imports `ConflictResolutionTrilemma.v` and `ConflictResolutionLowerBound.v` rather than duplicating them. Packages R11/R12 in the fragment's own vocabulary (`scalar_summary_not_fully_faithful_on_conflict`, `structured_diagnostic_nonlossy`, `nonlossy_diagnostic_injective`, `pair_diagnostic_is_nonlossy`, `pair_encoding_injective`), then defines the closed `ConflictDiagnostic V C` inductive (`RefuseDiagnostic`/`ScalarDiagnostic`/`StructuredDiagnostic`/`UnresolvedDiagnostic`) and proves classification is total and exclusive (`conflict_diagnostic_classification_total`, `..._exclusive`), the four `DiagnosticClass` names are pairwise distinct, and the constructors themselves are pairwise distinct (`no_diagnostic_is_both_refuse_and_scalar` and its two siblings). Headline sentence: `no_hidden_neutral_scalar_case`. `coqchk`-clean.
- `conflict_diagnostic_completeness_probe.py` — classifies the same named strategies (`left_wins`/`right_wins`/`average`/`sum`/`erase`/`refuse`/`pair`/`unresolved`) into the fragment's four buckets, confirms every strategy tested lands in exactly one, and reconfirms `left_wins`/`right_wins`/`erase`'s lossiness via the R12 pigeonhole argument while deliberately excluding `average`/`sum` from that specific check (their outputs are not confined to `V`).
- `docs/theory/NO_NEUTRAL_SCALAR_FUSION.md` — a standalone synthesis note (no new theorem) pulling R11-R13 into one narrative: interface conflict, why scalar resolution is tempting, R11's impossibility, R12's lower bound, R13's bounded completeness, and the applied consequence (a scalar summary is an audit claim about a resolver's own behaviour, not a neutral compression of the disagreement). Read this before the three design docs if you want the shape of the whole argument first.
- `docs/design/TYPED_DIAGNOSTIC_CALCULUS.md` — design doc, no Rocq proof yet: turns R11-R13 into explicit introduction/elimination/reduction rules over `ConflictDiagnostic V C` (`STRUCTURED-INTRO`/`-LEFT-ELIM`/`-RIGHT-ELIM`, `SCALAR-CONFLICT-LOSS`, `REFUSE-NO-COMPOSITE`, `UNRESOLVED-NO-CLAIM`, `UNRESOLVED-REFINE-BY-EVIDENCE`). Explicitly separates what restates R11-R13 from what is genuinely new (§9): the reduction relation and its safety properties are the only new structure; everything else is existing theorems read as inference rules. Rocq target `rocq/TypedDiagnosticCalculus.v` is scoped in §11 but not yet attempted.

## 4. Certificate layer

- `certificate_emitter.py` (shared with layer 2) — proof-carrying certificate schema.
- `first_order_certificate_checker.py` — independent certificate checker.
- `rocq/FirstOrderClassifierCertificate.v` — Rocq proof of the two certificate forms' soundness.

## 5. Realisability diagnostics

The diagnostic ladder — see `docs/diagnostics/REALISABILITY_ROADMAP.md` for the narrative and [RESULTS.md](RESULTS.md) R6-R9 for the numbers.

- `realisability_diagnostic.py` — independent generator: too free (negative).
- `coupled_realisability_diagnostic.py` — shared adjacent-overlap coupling: cohomological collapse (negative).
- `boolean_crossing_diagnostic.py` — deterministic proper-crossing rule: positive non-linear existence witness.
- `lattice_ie_diagnostic.py` — ordered inclusion-exclusion: too free by disguised independence (negative).
- `carrier_matrix_infrastructure.py` — reusable carrier/restriction/delta matrix pipeline and sharing validator, used by the two diagnostics below.
- `candidate_discipline_diagnostic.py` — Candidate 3b on the standard (distinct-support) cover: cover-inert.
- `repeated_triple_support_diagnostic.py` — Candidate 3b on a repeated-triple-support cover: **first positive linear/rational witness**.
- `rocq/RepeatedTripleSupportCandidate3b.v` — the same result, machine-checked: `RepeatedTripleSupport` incidence condition, partial-support impossibility, Candidate 3b's induced map, shared-column and repairable/non-repairable-residue theorems.
- `rocq/CandidateThreeBDistinctSupportClassification.v` — the negative-direction half of the classification: under pairwise-distinct triple support (abstracted over any type with decidable equality, not tied to a specific cover), no two seams can ever reference the same carrier coordinate, and the induced map is full rank — machine-checked, plus a concrete instantiation matching the actual distinct-support cover.

## 6. Rocq proof artefacts

All compile clean with no `Admitted`/`Axiom`/`sorry` (`make check-rocq`):

- `rocq/AdmissibleRefinementPersistence.v`
- `rocq/AssociatorResidueRepair.v`
- `rocq/FourCycleObstruction.v`
- `rocq/CochainNaturalityDescent.v`
- `rocq/CommonSubdivisionAgreement.v`
- `rocq/ExactnessReflection.v`
- `rocq/FirstOrderClassifierCertificate.v`
- `rocq/RepeatedTripleSupportCandidate3b.v`
- `rocq/CandidateThreeBDistinctSupportClassification.v`
- `rocq/RefinementWitnessComposition.v`
- `rocq/RefinementWitnessVerdictComposition.v`
- `rocq/RefinementWitnessSequentialComposition.v`

## 7. Paper

- `paper/associator_fields_ACS_revised.tex` — the associator-fields manuscript. See `paper/README.md` for how it relates to the current repository state.
- `paper/finite_obstruction_calculus_for_regional_warrant.tex` — the second manuscript: the realisability-line theorem ladder, including the Candidate 3b classification (§4) and refinement-witness composition (§5, Theorems 5.1-5.3: `N0_composes`, `A4_composes`, `E0_composes`). See `paper/README.md`.
