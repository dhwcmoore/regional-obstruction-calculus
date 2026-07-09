# Status

What is proved, what is computed, what is diagnostic, and what is not claimed. See [PROJECT_MAP.md](PROJECT_MAP.md) for file locations and [RESULTS.md](RESULTS.md) for the results themselves.

## 1. Verified or proof-supported (Rocq, no `Admitted`/`Axiom`/`sorry`)

- Abstract admissible-refinement persistence (`rocq/AdmissibleRefinementPersistence.v`).
- Abstract associator repair-impossibility theorem, and its concrete four-cycle instantiation over the paper's own `r`, `z`, `delta0` (`rocq/AssociatorResidueRepair.v`, `rocq/FourCycleObstruction.v`).
- (N0) cochain-map naturality / descent-safe subdivision persistence (`rocq/CochainNaturalityDescent.v`).
- Common-subdivision certificate agreement, built on the descent theorem (`rocq/CommonSubdivisionAgreement.v`).
- (E0) exactness reflection (`rocq/ExactnessReflection.v`).
- Soundness of the two proof-carrying certificate forms (`rocq/FirstOrderClassifierCertificate.v`).
- Repeated triple-support incidence condition and Candidate 3b's induced-map theorems (`rocq/RepeatedTripleSupportCandidate3b.v`): the `RepeatedTripleSupport` record, the partial-support impossibility lemma, genuinely-shared-column theorem, and exhibited repairable/non-repairable residue witnesses — checked with `coqchk`.
- Candidate 3b's distinct-support classification, the other half of the same result (`rocq/CandidateThreeBDistinctSupportClassification.v`): under pairwise-distinct triple support (abstracted over any type with decidable equality, no `Point`/finiteness assumption, only the support values need be distinct), no two seams can ever reference the same carrier coordinate, and the induced map is full rank — plus a concrete instantiation confirming this specialises correctly to the cover `candidate_discipline_diagnostic.py` actually uses. Together with the row above, this makes the full Candidate 3b classification (distinct support ⟹ cover-inert; repeated support ⟹ genuinely partial nontrivial quotient) machine-checked at the same level, not diagnostic-only in either direction.
- Refinement witness composition, all three conditions, two and three steps (`rocq/RefinementWitnessComposition.v`, `rocq/RefinementWitnessVerdictComposition.v`, `rocq/RefinementWitnessSequentialComposition.v`): if composed refinement witnesses each satisfy (N0)/(A4)/(E0), their composite does too — `N0_composes`/`N0_composes_three` (associativity of function composition, needs *every* step's own N0), `A4_composes`/`A4_composes_three` (near-definitional: the composite pairing test is literally the *last* step's own pairing test, needs no hypothesis about earlier steps), and `E0_composes`/`E0_composes_three` (a short span-transport argument through linearity, needing *every* step's own (E0), not any step's (N0)). Minimal finite-dimensional vector-space/span infrastructure built from scratch for the E0 proofs. Together, `verdict_safe` composability follows by conjunction. Released as `v0.11-refinement-witness-composition`.
- Disjoint *parallel* refinement witness composition, N0 and E0 only, two branches (`rocq/RefinementWitnessParallelComposition.v`): `N0_parallel_disjoint` and `E0_parallel_disjoint`, built from a genuine direct-sum (product-type) construction rather than function composition — a different construction from every row above, reusing the same `VSpace`/`InSpan`/`IsLinear` infrastructure for E0 plus a new direct-sum constructor and a span-monotonicity lemma. Deliberately does **not** include an A4 theorem — see §2 for why the natural statement is false, not merely unproved.

Verified with `make check-rocq`. Requires a Rocq/`coqc` toolchain; not assumed available in every environment.

## 2. Exact computational results (Python, exact rational, tested)

- Four-cycle residue classification (`residue_classifier.py`).
- Associator-generated residue, reproducing the same residue from literal associator-field data (`associator_residue.py`, `run_associator_obstruction.py`).
- Repair solver / obstruction language (`repair_solver.py`).
- Refinement witness checks: (A1)-(A4), (N0), (E0), `descent_safe`, `verdict_safe` (`refinement_checker.py`).
- Refinement witness composition search scripts (`refinement_witness_composition_probe.py`, `refinement_witness_a4_e0_counterexample_search.py`, `refinement_witness_composition_boundary_search.py`): computational evidence — ~175,000 cases, 0 counterexamples — that predates and independently corroborates the composition theorems now proved in §1.
- Disjoint parallel composition probe (`refinement_witness_parallel_disjoint_probe.py`, Phase 4b): over 32 cases of two certificate-disjoint refinement witnesses combined by direct sum, (N0) and (E0) always equal AND(branch A, branch B); (A4) does not — 16/32 cases mismatch, always because the combined pairing (a *sum* of the two branches' own pairings, not an AND) cancels to exactly 0 even though both branches individually satisfy their own (A4). This probe result is what motivated the shape of the N0/E0 proofs and the deliberate absence of an A4 proof in §1's `RefinementWitnessParallelComposition.v` row — not yet reflected in any `verdict_safe`-style composite claim, for the same reason.
- First-order proof-carrying certificate emission and independent checking (`certificate_emitter.py`, `first_order_certificate_checker.py`).
- 1000-case random-residue regression (`tests/test_random_residue_regression.py`).
- Coupled realisability diagnostics: independent generator, shared adjacent-overlap coupling, ordered inclusion-exclusion, Candidate 3b on both distinct- and repeated-support covers.

Verified with `make check-python` — 140 tests, all passing. This is the default reproducibility path; see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## 3. Diagnostic witnesses, not general theorems

These establish that one specific candidate rule does or does not do something on one specific construction — not a theorem about every rule in its class:

- **Independent generator** (`realisability_diagnostic.py`): too free — surjective onto all of `C^1(N;Q)`.
- **Shared adjacent-overlap coupling** (`coupled_realisability_diagnostic.py`): rank drops but the image collapses entirely into `im(delta^0)` — cohomological collapse.
- **Boolean proper-crossing diagnostic** (`boolean_crossing_diagnostic.py`): a deterministic, parameter-free rule that produces a non-degenerate residue outside `im(delta^0)` on one specific cover. Non-linear — no rank or quotient to compute.
- **Ordered inclusion-exclusion** (`lattice_ie_diagnostic.py`): globally-indexed but the associator formula cancels exactly the shared terms — full rank, disguised independence.
- **Candidate 3b, distinct-support cover** (`candidate_discipline_diagnostic.py`, `rocq/CandidateThreeBDistinctSupportClassification.v`): cover-inert — the cover never lets two triple overlaps coincide, so nothing can be shared. Now machine-checked (§1) as a general fact about any pairwise-distinct-support assignment, not just the one concrete cover the diagnostic ran.
- **Candidate 3b, repeated-support cover** (`repeated_triple_support_diagnostic.py`, `rocq/RepeatedTripleSupportCandidate3b.v`): the first positive linear/rational witness — `rank(B)=2`, neither full rank nor coboundary collapse. Also machine-checked in Rocq, which upgrades the *incidence condition and the induced-map facts* to proved status (§1) while the underlying claim — that this is a structurally meaningful or unique coupling discipline — remains diagnostic.

## 4. Not claimed

This repository does not claim:

- full presentation invariance (comparing two different coarse presentations of the same regional situation and concluding their obstruction verdicts agree, in general);
- a fully verified end-to-end implementation (the Rocq proofs are abstract or instantiated on the paper's own concrete numbers; they do not mechanise `finite_algebra.py` or `regional_composition.py` themselves — see each `rocq/*.v` file's header comment for its exact scope);
- that every associator residue is structurally meaningful — the independent generator (§3) is a counterexample to that on its own;
- that every coupled generator produces a nontrivial obstruction quotient — most tried so far do not (§3);
- that Candidate 3b is the final, unique, or general coupling principle — it is one rule, verified on one family of covers.
- that disjoint parallel composition preserves (A4) in general — the Phase 4b probe (§2) exhibits a concrete case where two certificate-disjoint witnesses each individually satisfy (A4) but their direct-sum composite does not.
