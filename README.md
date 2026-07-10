# Regional Obstruction Calculus

Exact rational diagnostics for local-to-global coherence failure in finite regional systems.

This repository contains executable and proof-oriented artefacts for detecting when locally valid regional data fails to glue into a globally coherent object. It separates **detection**, **repair**, **refinement persistence**, and **realisability** as distinct, individually-checked questions, rather than treating "there is an obstruction" as one monolithic claim.

This repository grew out of the associator-fields paper and the `admissible-refinement-persistence` development. It is now the working repository for the broader regional obstruction calculus; see [Relation to the associator-fields paper](#relation-to-the-associator-fields-paper) below.

## What this repository does

Local compatibility does not guarantee global coherence. A finite regional system can satisfy local and pairwise boundary conditions while still carrying a non-removable global residue. This repository provides exact rational tools for:

- classifying whether a residue on a finite cover is a coherence obstruction or repairable;
- generating that residue from literal associator-field data instead of declaring it;
- checking whether an obstruction persists under refinement of the cover;
- emitting and independently checking proof-carrying certificates for classifier verdicts;
- diagnosing whether a given generator's associator residues are structurally forced or merely constructible (realisability).

Everything computational is exact-rational (Python `Fraction`, no floating point). Where a result is also formalised in Rocq, the proof scripts contain no `Admitted`, `Axiom`, or `sorry`.

## Interpretation, not formalism

The proved and computed content throughout this repository is entirely
at the level of finite cochains, δ⁰/δ¹, cocycles, and coboundaries -- a
Čech-style obstruction calculus, not a higher category. It is useful to
read the surviving classes as failures of *higher coherence*: local
validity (object-level data on a single region) and pairwise
compatibility (seam-level agreement across an overlap) can both hold
while the data still fail to assemble into a globally warranted
structure. That reading motivates why the obstruction calculus matters;
it is not a formal claim proved anywhere in this repository. The
refinement-persistence results (item 10 onward) can likewise be read as
a finite, cochain-level form of coherence under change of presentation --
an obstruction that survives admissible refinement was not an artefact
of how the system happened to be described. See RESULTS.md and STATUS.md
for exactly what is proved versus interpreted.

## Central example

A four-region cyclic cover `U1-U2-U3-U4-U1`, coboundary map `delta^0`, and a residue `r = (1, 1, 1, -2)` on the induced 1-cochains. Pairing `r` against the cycle `z = (-1, -1, -1, 1)` gives `<z, r> = -5 != 0`, so `r` is not a coboundary: a genuine `H^1` obstruction, not a bookkeeping artefact. See [RESULTS.md](RESULTS.md) R1-R2 for how this residue is both declared and independently generated from associator data.

## Main results

See [RESULTS.md](RESULTS.md) for the full account. Headline items:

- **R1-R5**: the four-cycle obstruction is classified, generated from associator data, shown not repairable, shown to persist under refinement, and independently certificate-checked -- all in exact rational arithmetic, with Rocq proofs for the repair-impossibility and refinement-persistence claims.
- **R6-R9**: a ladder of realisability diagnostics for what data a coupled associator generator must share to produce structurally-forced (rather than merely constructible) obstructions, ending in **R9**, the first positive linear/rational witness: a repeated-triple-support coupling with `rank(B)=2`, `dim(im(B) ∩ im δ⁰)=1`, `dim(quotient)=1` -- neither too free nor collapsed -- also formalised as a machine-checked Rocq theorem (`rocq/RepeatedTripleSupportCandidate3b.v`).
- **R10**: refinement-witness composition is theorem-grade for all three governing conditions, both for sequential composition (two and three steps: `N0_composes`, `A4_composes`, `E0_composes`, `rocq/RefinementWitnessComposition.v`, `rocq/RefinementWitnessVerdictComposition.v`, `rocq/RefinementWitnessSequentialComposition.v`) and for disjoint *parallel* composition (`N0_parallel_disjoint`, `E0_parallel_disjoint`, and a full branchwise/aggregate A4 classification -- `A4_parallel_disjoint_branchwise`, `A4_parallel_disjoint_nonzero_sum`, and a machine-checked witness that branchwise success does not imply aggregate success -- `rocq/RefinementWitnessParallelComposition.v`) -- reached only after searches/probes (~175,000 cases sequentially, 32 cases in parallel) that also found a genuine negative result: the naive scalar A4 does **not** compose under disjoint parallel composition, a demonstrated fact (in Rocq, not only Python), resolved by classification rather than left as an open question. Released as `v0.12-disjoint-parallel-classification`. A first step into *coupled* parallel composition (branches sharing a seam, not fully independent) asks a prior question instead of preservation -- is the glued composite even well-defined -- and answers it with a conservative compatibility gate, both probed (`refinement_witness_coupled_parallel_probe.py`) and proved (`rocq/CoupledParallelCompatibility.v`, `coqchk`-clean): agreement is necessary and sufficient for a glue to exist, agreeing declarations glue cleanly, conflicting ones are diagnosed and refused, never silently merged. Coupled-parallel well-definedness is now formalised; coupled-parallel preservation remains open -- except for one settled preservation-adjacent question, both probed (`refinement_witness_coupled_a4_cancellation_probe.py`) and proved (`rocq/CoupledParallelCompatibility.v`'s `CompatibleAggregateCancellation` section, `coqchk`-clean): shared-seam agreement does **not** force the aggregate (A4) to compose either -- a verified, compatible, branchwise-preserved, aggregate-cancelled case exists. Still no conflict-resolution rule anywhere in this project.
- **R11**: the conflict-resolution trilemma -- a separate mathematical question from R10, about equality and resolver functions in the abstract, not about refinement witnesses at all. Proves no *lossy* (same-type) resolver can honour both disagreeing branches at once unless the whole value type is trivial (`rocq/ConflictResolutionTrilemma.v`, `coqchk`-clean), and classifies seven candidate resolver shapes (`left_wins`, `right_wins`, `average`, `sum`, `erase`, `refuse`, `external_authority`) by what each sacrifices (`conflict_resolution_trilemma_probe.py`). Also proves a *structured* (non-lossy) resolver preserving both declarations always exists -- the impossibility is about collapsing to one value of the same type, not about preserving information as such -- while showing structure does not exempt a structured object's own scalar summary field from the same impossibility. No resolver is proposed, recommended, or implemented.
- **R12**: the non-lossy lower bound -- given R11's structured resolver exists, how much structure does non-lossy resolution actually require? Proves any encoding recoverable via fixed projections must be injective on `V x V` (`rocq/ConflictResolutionLowerBound.v`, `coqchk`-clean), so for finite `V` with `|V|=n`, a non-lossy codomain needs at least `n^2` elements -- a cardinality restatement of R11's impossibility, checked computationally for `n=1..6` (`conflict_resolution_lower_bound_probe.py`). Characterises the abstract shape a faithful conflict record must have, not a concrete schema.
- **R13**: bounded conflict-diagnostic completeness -- combines R11 and R12 into a closed, four-constructor classification (`rocq/ConflictDiagnosticCompleteness.v`, `coqchk`-clean) of what a diagnostic about a conflicting shared interface can honestly be: refusal (`RefuseDiagnostic`), a lossy scalar summary (`ScalarDiagnostic`, always lossy once the declarations disagree -- R11, imported directly), a non-lossy structured diagnostic (`StructuredDiagnostic`, non-lossy exactly under R12's projection condition, imported directly), or an explicitly unresolved case (`UnresolvedDiagnostic`). Classification is proved total and exclusive, and the four classes are pairwise distinct. **Bounded** is the key word: this is completeness for the narrow fragment defined in `docs/design/CONFLICT_DIAGNOSTIC_COMPLETENESS.md`, not for all possible diagnostic systems -- it does not choose a resolver, and does not contradict R11's own §10 disclaimer that its seven named resolver *shapes* are not exhaustive (R13 classifies structural *shapes* of diagnostic, a coarser, different question). Checked computationally in `conflict_diagnostic_completeness_probe.py`: every named strategy lands in exactly one of the four classes.
- **R14**: a typed diagnostic calculus for the R11-R13 fragment (`rocq/TypedDiagnosticCalculus.v`, `coqchk`-clean) -- turns R13's static classification into explicit introduction/elimination/reduction rules. `SoundL`/`SoundR` (left/right-soundness) let `structured_intro`/`-left-elim`/`-right-elim` restate R12 and `scalar_conflict_loss` restate R11 as an elimination-*inadmissibility* fact; `refuse_no_composite_left`/`-right` and `unresolved_no_claim_left`/`-right` show neither `RefuseDiagnostic` nor `UnresolvedDiagnostic` has any sound elimination, for two deliberately distinct reasons. The unifying theorem, `elimination_soundness`: under a genuine conflict, only a `StructuredDiagnostic` can be both left- and right-sound -- the formal cash-out of `docs/theory/NO_NEUTRAL_SCALAR_FUSION.md`'s headline sentence. A one-constructor reduction relation, `RefinesByEvidence`, formalises refining an `Unresolved` diagnostic once evidence arrives, with two safety theorems (`preservation_under_reduction`, `no_silent_soundness_gain` -- the latter showing that refining `Unresolved` into a `ScalarDiagnostic` under conflict is still fully subject to `scalar_conflict_loss`: passing through `Unresolved` buys nothing). Deliberately does **not** derive `REFUSE-NO-COMPOSITE` from `CoupledParallelCompatibility.v`'s glue theorems -- a related but distinct object, not a definitional identity.
- **R15**: the pairwise diagnostic certificate (`rocq/PairwiseDiagnosticCertificate.v`, `coqchk`-clean) -- the first bridge between R14 and `CoupledParallelCompatibility.v`'s two-branch, one-seam gluing theory, neither source file modified. `DecisivePairwiseEvidence` carries either a positive glue witness (`CompatibleEvidence`) or a positive `LocalConflict` witness (`IncompatibleEvidence`) -- no constructor for a bare "no acceptable composite" claim. Evidence erases into `ConflictDiagnostic Declaration (Declaration * Declaration)`, the payload being the declaration *pair* rather than the glue itself (a glue does not determine its two source declarations uniquely -- see the file's own header note). `pairwise_diagnostic_certificate_sound` combines representation soundness (R14) and semantic soundness (`CoupledParallelCompatibility.v`) case by case, with the no-glue conclusion under conflict *derived* from `interface_disagreement_blocks_glue` rather than stored as primitive evidence. `refusal_requires_local_conflict` is the certificate-level safety property: `RefuseDiagnostic` is never emitted, in this bridge, without a checked `LocalConflict` witness. Deliberately narrow: no deciding algorithm for `Compatible dA dB` is claimed, and no exhaustiveness theorem is attempted.
- **R16**: the global coherence certificate (`rocq/GlobalCoherenceCertificate.v`, `coqchk`-clean) -- a global-coherence analogue of R15, packaging `AssociatorResidueRepair.v`'s already-abstract `nonzero_pairing_blocks_repair_mod_ceq` (source file not modified) rather than deriving new cohomology. `DecisiveGlobalEvidence` carries either a positive repair witness (`RepairEvidence`, `b` with `ceq (delta0 b) r`) or a positive obstruction witness (`ObstructionEvidence`, a cycle `z` with nonzero pairing against `r`) -- no constructor for a bare "not repairable" claim. Deliberately does **not** reuse `ConflictDiagnostic`/`SoundL`/`SoundR` -- the global problem has one residue, not two declarations, and forcing it into R14's pairwise vocabulary would overload `RefuseDiagnostic` with two genuinely different obstruction theories. Deliberately does **not** claim `H^1` nontriviality -- every obstruction fact is named non-repairable, never nontrivial cohomology class, since `delta1 r = 0` is never assumed. `global_coherence_certificate_sound` combines both cases plus `GlobalUnresolvedResult`, with the no-repair conclusion *derived*, never stored; `repair_and_obstruction_evidence_are_disjoint` is the consistency property earned. Scoped to the abstract Layer-1 interface exactly as it already exists, neither the concrete four-cycle alone nor a new general cover theory.

## Repository map

See [PROJECT_MAP.md](PROJECT_MAP.md) for the full file-by-file map. Top level:

```
README.md            this file
PROJECT_MAP.md        where to start, by layer
STATUS.md             what is proved / computed / diagnostic / not claimed
RESULTS.md            the results, R1-R16
REPRODUCIBILITY.md    exact commands to reproduce every check
CHANGELOG.md
LICENSE
Makefile
requirements.txt
examples/             JSON witness data
tests/                pytest suite (181 tests)
rocq/                 Rocq proof scripts (no Admitted/Axiom/sorry)
ocaml/                OCaml parity mirror of the refinement checker
docs/                 theory, diagnostics, design, and archive notes
paper/                the associator-fields manuscript (see paper/README.md)
```

## Quick start

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make check-python
```

Expect `181 passed`. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the full command sequence, including the optional Rocq and OCaml checks.

## Verification status

| Layer | Artefact | Status |
|---|---|---|
| Exact rational classifier | `residue_classifier.py` | executable, tested |
| Associator-generated residue | `associator_residue.py`, `run_associator_obstruction.py` | executable, tested |
| Repair obstruction | `repair_solver.py` | executable, tested |
| Refinement witnesses | `refinement_checker.py` | executable, tested |
| First-order certificates | `certificate_emitter.py`, `first_order_certificate_checker.py` | executable, tested |
| Rocq abstract proofs | `rocq/*.v` | proof scripts, toolchain-dependent, no `Admitted`/`Axiom`/`sorry` |
| Realisability diagnostics (negative) | `realisability_diagnostic.py`, `coupled_realisability_diagnostic.py`, `lattice_ie_diagnostic.py`, `candidate_discipline_diagnostic.py` | executable, tested, negative/cover-inert results |
| Boolean proper-crossing witness | `boolean_crossing_diagnostic.py` | executable, tested, non-linear diagnostic witness |
| Repeated triple support | `repeated_triple_support_diagnostic.py`, `rocq/RepeatedTripleSupportCandidate3b.v` | executable + machine-checked, positive diagnostic witness |
| Full presentation invariance | none | not claimed |
| Full end-to-end verified implementation | none | not claimed |

## What is proved, what is computed, what is diagnostic

Three distinct kinds of evidence appear in this repository, and they are not interchangeable:

- **Proved** (Rocq, no `Admitted`/`Axiom`/`sorry`): abstract theorems and, where stated, their concrete instantiation over the paper's own numbers. See `rocq/*.v` and [STATUS.md](STATUS.md) §1.
- **Computed** (Python, exact rational): executable checks with a pytest regression suite. See [STATUS.md](STATUS.md) §2.
- **Diagnostic** (Python, exact rational, but not a theorem): witnesses and negative results in the realisability line -- they establish that a specific candidate rule does or does not do something on a specific construction, not a general theorem about all such rules. See [STATUS.md](STATUS.md) §3.

[STATUS.md](STATUS.md) §4 states explicitly what is **not** claimed.

## Relation to the associator-fields paper

This repository originated as the companion code to *Associator Fields and Local-to-Global Failure in Finite Compositional Structures* (`paper/associator_fields_ACS_revised.tex`). The repository has since grown beyond that paper -- in particular, the realisability diagnostics (R6-R9), the Candidate 3b classification, and refinement-witness composition (R10) are post-paper developments. A second manuscript, *A Finite Cohomological Obstruction Calculus for Regional Warrant* (`paper/finite_obstruction_calculus_for_regional_warrant.tex`), packages that later work into its own theorem ladder, with the Candidate 3b classification (§4) and refinement-witness composition (§5) as its actual new content. See `paper/README.md` for how the two manuscripts and the repository now relate.

The prior repository, `admissible-refinement-persistence`, is retained as historical/paper-companion material; this repository is the current, active one.

## Citation / contact

Duston Moore -- Independent Researcher. See [CITATION.cff](CITATION.cff) if present, or the repository metadata on GitHub.
