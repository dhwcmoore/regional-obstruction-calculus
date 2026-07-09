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
- `refinement_witness_composition_probe.py` — (A4)/(E0)-composability: probed, not proved. See `docs/design/REFINEMENT_WITNESS_COMPOSITION_STATUS.md`.

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

## 7. Paper

- `paper/associator_fields_ACS_revised.tex` — the associator-fields manuscript. See `paper/README.md` for how it relates to the current repository state.
