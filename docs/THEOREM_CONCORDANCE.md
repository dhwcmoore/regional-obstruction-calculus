# Theorem concordance

A one-page map from result name to file, checker, and scope. For
reviewers who want to know, for any claim in the paper or README, exactly
which file proves it and exactly what it does and does not establish —
without reading the surrounding prose first.

This table is a pointer, not a substitute for the README (which explains
*why* each result is scoped the way it is) or the paper (which states the
results in full mathematical prose). When in doubt, the Rocq file is
authoritative for what is proved; the "does not prove" column exists
because every one of these results has been mistaken, in earlier drafts
of this project or its archived scaffold, for something stronger than it
is.

| Paper / repo result | File | Checker | What it proves | What it does not prove |
|---|---|---|---|---|
| Base obstruction classifier (`prop:nonremovable`, `thm:classifier-soundness`) | — (hand proof in paper only; no Rocq file) | `residue_classifier.py` | `r=(1,1,1,-2)` is a cocycle and not a coboundary, by exact Gauss-Jordan elimination and independently by cycle pairing | Does not certify that the classifier's algorithm is correct for arbitrary input; regression-tested (1000-case property test), not formally verified |
| A1-A4 admissible-refinement persistence (Theorem 9.1/9.2) | `rocq/AdmissibleRefinementPersistence.v` | `refinement_checker.py` (A1-A4 fields) | The transferred residue `rho^*r` is non-exact *inside the refined complex*, given (A1)-(A4) | Nothing about the residue `r` itself in the *coarse* complex; no descent, no comparison between presentations |
| Descent-safe subdivision persistence (Theorem 9.4) | `rocq/CochainNaturalityDescent.v` | `refinement_checker.py`'s `N0`/`descent_safe` fields | Refined non-exactness descends to coarse non-exactness, given (N0) cochain-map naturality, in addition to (A1)-(A4) | Only for a single refinement map; fails (and is not claimed) for `insert_bridge`, which satisfies (A1)-(A4) but not (N0) |
| Common-subdivision certificate agreement (Theorem 10.3) | `rocq/CommonSubdivisionAgreement.v` | abstract theorem (no Python instantiation; witness data would come from `refinement_checker.py`) | Two coarse presentations sharing a descent-safe common subdivision, whose transferred residues agree and carry a shared non-zero cycle-pairing certificate, are both non-exact | Not the exactness side (see next row); not full verdict equivalence; not topology-changing refinements |
| Exactness reflection agreement (Theorem 10.6/10.7) | `rocq/ExactnessReflection.v` | `refinement_checker.py`'s `E0`/`verdict_safe` fields | Two coarse presentations sharing a common subdivision satisfying (E0) exactness reflection, whose transferred residues agree and are exact, are both exact | Not the obstruction-present side (previous row); does not combine with it into one iff theorem; (E0) holding does not imply (N0) holds (see `insert_bridge`) |
| Associator repair-impossibility (abstract) | `rocq/AssociatorResidueRepair.v` | — (abstract; instantiated concretely by the next row) | A non-zero cycle pairing on an associator-generated residue, modulo a declared equivalence relation the pairing respects, rules out repair | Does not mechanise `finite_algebra.py`/`regional_composition.py`; `AssocData`/`BoundaryCorrection` are left abstract |
| Four-cycle obstruction, concrete (`r=(1,1,1,-2)`, `z=(-1,-1,-1,1)`) | `rocq/FourCycleObstruction.v` | `associator_residue.py` + `repair_solver.py` | The concrete pairing `<z,r>=-5` is computed and shown non-zero *inside Rocq*, with `delta0` matching the JSON matrix row-for-row; non-repairability follows | Does not prove the Python associator compiler generated this `r`; that cross-check is `tests/test_associator_four_cycle.py`, not this file |
| Proof-carrying first-order classifier | `rocq/FirstOrderClassifierCertificate.v` | `first_order_certificate_checker.py` | Accepted exact-witness and obstruction-witness certificate forms imply the corresponding verdict is sound | Does not verify the Python classifier itself (`associator_residue.py` etc.); a certificate accompanying a verdict is what's trusted, not the program that produced it |

## Reading the table

- **"Checker" column**: where the *Python* side independently exercises the same claim in exact rational arithmetic. "Abstract theorem" means no Python instantiation exists yet — the Rocq file proves the inference pattern only.
- **No row here proves full presentation invariance.** That is deliberate; see the README's scope blockquote (levels 1, 2, 2b, 2c, 3) and the paper's Remark 10.8 ("Result ladder, and what remains open") for the exact boundary of what is and is not claimed.
- If a row's "does not prove" column looks incomplete relative to the corresponding file's own header comment, the file's header comment is authoritative — this table is deliberately terser and can drift; check `git log` on the file if the two disagree.

See also `REPRODUCIBILITY.md` for the commands that exercise every row in this table.
