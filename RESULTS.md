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

## R9. Repeated triple-support positive witness (Candidate 3b)

**Candidate 3b** (`mu_UV=mu_VW=0`, outer slots `rho_{X,T}`/`rho_{Z,T}` keyed by region and triple support `T=X∩Y∩Z`) is cover-inert on the standard distinct-support cover (`candidate_discipline_diagnostic.py`: 8 parameters, all `private_residual`, full rank 4 — not because the rule is too free, but because the cover never lets two triple overlaps coincide).

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

**What this does not show**: it is one rule (Candidate 3b) on one cover family, not a general theorem about linear couplings; it does not apply to distinct-support covers; it does not replace R8's non-linear Boolean witness, which is a different mechanism entirely. See `docs/diagnostics/REPEATED_TRIPLE_SUPPORT_DIAGNOSTIC.md` for the full account.
