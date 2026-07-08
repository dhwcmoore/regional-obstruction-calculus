# Reproducibility

Command-level reproduction of every checked result in this repository.
See `docs/THEOREM_CONCORDANCE.md` for which result each command exercises
and exactly what it does and does not prove; this file is deliberately
just commands and expected output, no explanation.

All commands below were run from the repository root immediately before
this file was committed, and all exited `0`.

## Python, exact rational

```sh
python residue_classifier.py examples/four_cycle.json
python refinement_checker.py
python run_associator_obstruction.py examples/four_cycle_associator.json --json out.json
python first_order_certificate_checker.py out.json
pytest
```

`pytest` alone (no path) collects the full suite — 68 tests as of this
commit, across `tests/test_random_residue_regression.py`,
`tests/test_refinement_witnesses.py`, `tests/test_finite_algebra.py`,
`tests/test_regional_composition.py`, `tests/test_associator_residue.py`,
`tests/test_repair_solver.py`, `tests/test_associator_four_cycle.py`, and
`tests/test_first_order_certificates.py`.

## Rocq

Compile in this order (later files `Require` earlier ones):

```sh
cd rocq
coqc AdmissibleRefinementPersistence.v
coqc CochainNaturalityDescent.v
coqc CommonSubdivisionAgreement.v
coqc ExactnessReflection.v
coqc AssociatorResidueRepair.v
coqc FourCycleObstruction.v
coqc FirstOrderClassifierCertificate.v
```

All seven compile with no `Admitted`, `Axiom`, or `sorry` (grep the
`.v` files yourself to check; none of the theorem statements above
depend on you trusting this file's word for it).

## OCaml parity (optional, environment-dependent)

```sh
cd ocaml
ocamlfind ocamlopt -package zarith -linkpkg \
  refinement_witnesses.ml refinement_checker.ml -o refinement_checker
./refinement_checker
```

Mirrors `refinement_checker.py`'s (A1)-(A4) computation independently, in
OCaml's own exact rational type — not (N0)/(E0), which were added to the
Python side after this mirror was last updated; see README item 5.

## Expected truth table (`refinement_checker.py`)

```text
subdivide_U1      A1-A4 true, N0 true,  E0 true, verdict_safe true
subdivide_U2      A1-A4 true, N0 true,  E0 true, verdict_safe true
subdivide_all     A1-A4 true, N0 true,  E0 true, verdict_safe true
insert_bridge     A1-A4 true, N0 false, E0 true, verdict_safe false
```

`insert_bridge` is the load-bearing row: it is admissible (a genuine
A1-A4 persistence witness) and satisfies (E0) exactness reflection, but
fails (N0) cochain-map naturality — the witness that shows (N0) and (E0)
are independent conditions, not two views of the same fact. See
`docs/THEOREM_CONCORDANCE.md` and the paper's Remark 10.8.
