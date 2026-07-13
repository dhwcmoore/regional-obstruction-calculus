# Changelog

Tags refer to milestones in the admissible-refinement-persistence work
(the paper's "Admissible refinement persistence" section) and, from R17
onward, in the presentation-invariance and quotient-semantics work built
on top of it. Scope discipline kept throughout: A1-A4 alone proves
persistence for a single refinement, not arbitrary refinement invariance;
R17-R20 later prove verdict-level invariance for the descent-safe,
reflecting common-subdivision fragment specifically, not full
presentation invariance through arbitrary or topology-changing
refinement. See the "Presentation fidelity and quotient semantics"
checkpoint below and `docs/theory/THEOREM_CONCORDANCE.md` for the exact
current boundary.

## Unreleased

### Presentation fidelity and quotient semantics

- Added R17, `rocq/CommonSubdivisionVerdictInvariance.v`: the first
  combined verdict-invariance theorem for two presentations related
  through a common subdivision whose refinement legs are both
  descent-safe (N0) and exactness-reflecting (E0). Proves both the
  exactness-side equivalence and its fully constructive obstruction-side
  contraposition. Introduces no new primitive preservation mechanism;
  its contribution is the first formal assembly of the existing N0/E0
  results.
- Added
  `docs/design/PRESENTATION_INVARIANCE_SPEC.md`, which established before
  implementation that most of the proposed presentation-invariance
  ladder already existed in separate form and identified the combined
  verdict equivalence as the precise missing theorem.
- Added R18-R19, `rocq/QuotientDescentReflection.v`: introduces the small
  `CoboundaryQuotientLaws` extension without strengthening the existing
  `VSpace` record; proves coboundary equivalence is an equivalence
  relation under the stated hypotheses; proves N0 preserves
  coboundary equivalence; proves E0 is equivalent to reflection of
  coboundary equivalence; and packages N0 plus E0 as faithful quotient
  descent for linear refinement maps.
- Added
  `docs/design/QUOTIENT_DESCENT_AND_REFLECTION_SPEC.md`, based on a
  compiling scratch prototype against the repository's actual algebraic
  infrastructure. The prototype identified both the extra quotient laws
  missing from `VSpace` and the independent linearity hypothesis required
  for quotient descent.
- Added R20, `rocq/QuotientVerdictClosure.v`: rederives R17's
  distinguished-residue verdict equivalence through the R18-R19 quotient
  machinery, confirming that the direct and quotient-level
  formalisations agree.
- The active formal chain now contains 25 Rocq modules. `make check-all`
  runs Python, Rocq compilation, complete `coqchk` trust checking, the
  OCaml refinement checker, assembly parity, and contribution parity.
- Scope remains deliberately limited. No full quotient-space
  isomorphism, arbitrary presentation invariance, topology-changing
  invariance, cycle-space/quotient duality theorem, or general
  functoriality result is claimed.

- Generalised `rocq/AssociatorResidueRepair.v` from Leibniz equality on
  `C1` to an explicit, caller-supplied equivalence relation `ceq`
  (`nonzero_pairing_blocks_repair_mod_ceq`,
  `nontrivial_associator_residue_not_repairable_mod_ceq`), with the
  hypothesis that `pairing` respects `ceq`. This closes, at the abstract
  level, the same gap `FourCycleObstruction.v` first worked around
  file-locally: Leibniz equality is too strict once `C1` is instantiated
  concretely (e.g. as `Q`-valued vectors, where `1#1` and `2#2` are
  `Qeq`-equal but not Leibniz-equal), so a theorem proved only for
  Leibniz `delta0 b = r` does not, in general, rule out a "repair" via a
  differently-represented but rational-equal coboundary. The original
  Leibniz-based theorems (`nonzero_pairing_blocks_repair`,
  `nontrivial_associator_residue_not_repairable`) are kept, now as
  one-line corollaries obtained by instantiating `ceq := eq`, for callers
  with no finer structure on `C1` than Leibniz equality. Updated
  `rocq/FourCycleObstruction.v` so `four_cycle_not_repairable` is obtained
  by *direct application* of the new `..._mod_ceq` theorem with
  `ceq := veq` (the file's pre-existing componentwise-`Qeq` relation),
  rather than a hand-written, file-local proof; `pairing_congr` is now
  literally the `pairing_respects_ceq` witness the abstract theorem
  requires. `four_cycle_not_repairable_leibniz` is kept as a secondary,
  strictly weaker corollary. No `Admitted`/`Axiom`/`sorry`.
- Added `rocq/FourCycleObstruction.v`: instantiates
  `AssociatorResidueRepair.v`'s abstract Layer-1 theorem concretely, over
  `Q`, with the paper's own numbers -- `r = (1,1,1,-2)`, `z = (-1,-1,-1,1)`,
  and `delta0` matching `examples/four_cycle.json`'s `coboundary_0` matrix
  row-for-row. Proves `<z,r> == -5`, `<z,r> <> 0`, and
  `four_cycle_not_repairable`, all inside Rocq. Caught and documented a
  real subtlety along the way: the 4-tuple-of-`Q` type's meaningful
  equality is componentwise `Qeq` (`veq`), not Leibniz `=` -- two
  representations of the same rational are `veq`-equal but not
  Leibniz-equal, so a non-repairability theorem stated only for Leibniz
  equality would not, in general, rule out a "repair" via a
  differently-represented coboundary. `four_cycle_not_repairable` is
  stated and proved with `veq`, matching the paper; a second, strictly
  weaker `four_cycle_not_repairable_leibniz` corollary is also proved, by
  unmodified direct application of `AssociatorResidueRepair.v`'s theorem,
  to confirm that file needs no repackaging (it is already
  `forall`-quantified, not built from top-level `Parameter`s) to be
  reused. Does not instantiate the associator-layer theorem (`AssocData`
  left abstract) -- that still requires a concrete `AssocData` matching
  `regional_composition.py`, deferred as before. No
  `Admitted`/`Axiom`/`sorry`.
- Added `rocq/AssociatorResidueRepair.v`: an abstract Rocq proof of the
  repair-impossibility inference the associator-generation layer below
  exemplifies computationally (associator defect -> seam residue -> repair
  equation -> obstruction to global correction). Two theorems:
  `nonzero_pairing_blocks_repair` (pure cohomology, same content as
  `AdmissibleRefinementPersistence.v`'s cycle-pairing lemma, restated with
  `delta0`/`pairing`/`cycle` naming to match `repair_solver.py`) and
  `nontrivial_associator_residue_not_repairable` (the associator layer,
  with `AssocData`/`BoundaryCorrection` left abstract and proved by direct
  application of the first theorem). No `Admitted`/`Axiom`/`sorry`. Does
  not mechanise `finite_algebra.py`/`regional_composition.py`/the Venn
  model, and does not import or build on
  `AdmissibleRefinementPersistence.v` -- the two files are deliberately
  kept separate (refinement of presentation vs. repair of an
  associator-generated residue).
- Added an associator-generation layer beneath the existing classifier:
  `finite_algebra.py` (structure-constant Q-algebra with a literal, not
  shortcut, associator computation), `regional_composition.py` (the
  square-zero Venn model of Example ex:venn, boundary-corrected products,
  and associator defects computed by direct expansion of the paper's
  definitions and cross-checked against the closed-form four-term formula
  of Proposition prop:four-term), `associator_residue.py` (compiles the
  four coarse seam values of the Section-7 witness from four independent
  associator instances instead of declaring them), `repair_solver.py`
  (obstruction-language wrapper reusing `rational_linear_algebra`),
  `certificate_emitter.py`, and `run_associator_obstruction.py`. New
  example `examples/four_cycle_associator.json` and five new test files.
  The resulting residue is checked to equal both
  `refinement_witnesses.COARSE.residue` and the residue in the pre-existing
  `examples/four_cycle.json`, and to produce an identical verdict when run
  through the unmodified `residue_classifier.classify`. This does not
  change the historical record: the paper's displayed residue was
  originally posited directly (see below), and none of items 1-6 are
  modified by this addition.

- **Fixed a real exactness bug**: `residue_classifier.py` computed its
  coboundary-solvability check with `numpy.linalg.lstsq` on a `float` cast
  of the exact rational data, then rounded back to `Fraction` via
  `limit_denominator` — not exact rational linear algebra, despite the
  "exact rational classifier" framing. Replaced with the same exact
  Gauss-Jordan elimination `refinement_checker.py` already used. Both now
  import a shared `rational_linear_algebra.py` (`mat_vec`, `row_vec_mat`,
  `dot`, `is_zero`, `solve_over_Q`) instead of each having its own copy.
  `numpy` is no longer a dependency of any active code path.
- Added `tests/test_random_residue_regression.py`: the 1000-case
  property-based regression test the paper claimed but the repository
  didn't contain — bounded random rational residues on the four-cycle,
  checking `δ⁰b = r` solvable `<=>` `⟨z,r⟩ = 0`, plus 250+250 forced
  exact/obstruction control cases and a direct check of the paper's
  displayed residue. Fixed seed for reproducibility.
- Moved the old, superseded universal-refinement scaffold (four-condition
  scheme with adjointness and H₁-surjectivity, three placeholder checks,
  hardcoded legacy pairing values, non-compiling Rocq skeleton, and four
  now-inactive design docs) into
  `archive/deprecated_universal_refinement_scaffold/`, with its own README
  explaining what's there and why. Nothing in the current checked result
  depends on it.
- Updated the paper: renamed the theorem from "Universal admissible-
  refinement persistence" to "A1-A4 admissible-refinement persistence"
  (the old name risked being misread as unrestricted refinement
  invariance, which is explicitly not claimed); simplified the refinement
  witness table to computed-pairing-and-verdict only, moving the legacy
  `(-7/2, -4, -5/4, -5)` values into the correction note where they were
  already explained rather than displaying them as a table column;
  corrected the "1000 passed cases" claim to match the now-real test;
  added reproducibility commands for the random-residue test and the Rocq
  proof; clarified that the Rocq proof is of the abstract theorem, not a
  verified kernel for the concrete classifier.
- Added `Makefile` (`check-python`, `check-random`, `check-rocq`,
  `check-ocaml`, `clean`), `requirements.txt` (just `pytest`), `.gitignore`,
  and a GitHub Actions workflow (`.github/workflows/python.yml`) running
  the Python checks on push/PR. Rocq and OCaml CI workflows intentionally
  not added yet — not claiming CI for those until a workflow actually
  passes on GitHub's runners, not just locally.

## v0.6-rocq-a1-a4-persistence

- Added `rocq/AdmissibleRefinementPersistence.v`: an abstract Rocq proof of
  the paper's admissible-refinement persistence theorem, conditions
  (A1)-(A4) only. No adjointness, no H₁-surjectivity, no presentation
  invariance, no `Admitted`/`Axiom`/`sorry`. Compiles clean with `coqc`.
- Does not build on and does not touch `rocq/UniversalRefinement.v`, which
  remains deprecated (targets the old, superseded four-condition scheme and
  contains `sorry`).

## v0.5-admissible-refinement-parity

- Added `refinement_witnesses.py`: explicit refined-complex constructions
  for the four refinement witnesses (subdivide `U1`, subdivide `U2`,
  subdivide all regions, insert bridge) — vertices, oriented edges,
  pullback data (`over`/`over_sign`), and a declared refined cycle `z'` for
  each, replacing hardcoded table values with an actual construction.
- Added `refinement_checker.py`: checks conditions (A1)-(A4) exactly as
  stated in the paper's theorem (not the old, stronger four-condition
  scheme involving adjointness and H₁-surjectivity), and computes
  `⟨z', ρ*r⟩` by construction. Reports an independent exact-Gaussian-
  elimination solver cross-check alongside the cycle-pairing certificate.
- Added `tests/test_refinement_witnesses.py`: 17 regression tests locking
  down the computed values and the solver/pairing agreement.
- Added `ocaml/refinement_witnesses.ml` + `ocaml/refinement_checker.ml`: an
  independent OCaml mirror of the above, using `zarith`'s exact `Q.t`.
  Computes the identical pairings; the values appear as literals only in
  the parity self-check against Python.
- **Corrected the paper's refinement witness table.** The previous table
  claimed pairings `(-7/2, -4, -5/4, -5)` that were never produced by any
  refined complex, pullback map, or declared cycle — they were literal
  constants in `ocaml/refinement_theorem.ml`. The corrected, independently
  computed values (Python and OCaml agree) are `(5, 5, 5, -5)`; only the
  bridge witness matches the old claim. Added prose explaining why the
  three subdivision witnesses agree (internal split edges have `over =
  None`, so they don't contribute to the pairing) and why the bridge sign
  differs (declared cycle orientation, not a mathematical inconsistency).
  Old values retained in the table only as a labelled "legacy claim" column.
- Marked `refinement_classifier.py`, `ocaml/refinement_algebra.ml`,
  `ocaml/refinement_theorem.ml`, `ocaml/refinement_types.ml`, and
  `ocaml/refinement_verification.ml` as deprecated (header comments only,
  not deleted): they check a different, stronger four-condition scheme
  than the paper's actual theorem, with three of four checks hardcoded as
  placeholders, and (for the OCaml files) depend on `Core`/`Batteries`,
  neither of which had `ocamlfind` dev files available when checked.

## Initial import

- `d7de826`: associator-fields paper (`paper/associator_fields_ACS_revised.tex`
  / `.pdf`) and its accompanying code: `residue_classifier.py` (working,
  exact-rational four-region obstruction witness), plus the
  refinement-persistence scaffolding later found to be non-functional and
  superseded above.
