# Regional Obstruction Calculus

**Exact rational and machine-checked methods for detecting, transporting, and auditing local-to-global coherence failure in finite regional systems.**

Local validity does not guarantee global coherence. Pairwise-compatible regional declarations can still carry a non-removable global residue. This repository develops a finite obstruction calculus for distinguishing:

* a residue that is repairable from one that is genuinely obstructed;
* an obstruction that merely appears in one presentation from one that survives an admissible refinement;
* preservation of repair equivalence from reflection of repair equivalence;
* verdict invariance from the stronger, still-open claim of full class-level presentation invariance;
* a lossy scalar conflict summary from a structured, evidence-bearing diagnostic;
* a verdict asserted by a program from a verdict backed by an independently checkable certificate.

The distinctive contribution is the separation of these obligations. "There is an obstruction" is not treated as one monolithic claim.

Everything computational is exact rational arithmetic using Python `Fraction`, with no floating-point reasoning in any active path. The active Rocq chain contains 25 modules and is checked with both `coqc` and `coqchk`, with no project-added `Admitted`, `Axiom`, `Parameter`, or `sorry`.

## Central mathematical architecture

For a coboundary map `delta^0 : C^0 -> C^1`, a residue `r` in `C^1` is repairable when `r` is in `im(delta^0)`.

The repository separates four increasingly strong questions.

### 1. Obstruction inside a fixed presentation

Is `r` a coboundary? A non-zero pairing with a cycle that annihilates all coboundaries certifies that it is not.

### 2. Persistence under a specified refinement

Given a refinement map `rho^*`, do the transferred residue and its cycle certificate satisfy the declared A1-A4 conditions? This proves non-exactness inside the refined complex.

### 2b. Descent and reflection

Two further conditions have different logical roles:

```text
(N0)  rho_1^*(delta^0 b) = delta'^0(rho_0^* b)
```

preserves repair witnesses in the forward direction, while

```text
(E0)  rho_1^*(r) in im(delta'^0)  ==>  r in im(delta^0)
```

reflects exactness back to the source.

For linear refinement maps, R18-R19 prove their quotient-level meanings:

* **N0 preserves coboundary equivalence**
* **E0 reflects coboundary equivalence**
* **N0 + E0 give faithful quotient descent**

### 2c. Common-subdivision verdict invariance

If two presentations transfer their distinguished residues to the same residue in a common subdivision, and both refinement legs satisfy N0 and E0, then:

```text
r_1 in im(delta_1^0)   <=>   r_2 in im(delta_2^0)
```

Equivalently, constructively:

```text
r_1 notin im(delta_1^0)   <=>   r_2 notin im(delta_2^0)
```

This is R17, the repository's first presentation-invariance theorem. It applies to the descent-safe, exactness-reflecting common-subdivision fragment, corresponding to the three verified subdivision witnesses.

R20 reaches the same verdict-equivalence conclusion through the independently developed quotient machinery, confirming that the direct and quotient-level formalisations agree.

### 3. Full presentation invariance

Not proved.

The repository does not claim:

* invariance under every admissible refinement;
* invariance under topology-changing refinements such as `insert_bridge`, which fails N0;
* an isomorphism between the full obstruction quotients of two presentations;
* functoriality of obstruction quotients over a category of presentations;
* equivalence between quotient reflection and cycle-space surjectivity;
* completeness of cycle certificates for every non-exact residue.

These are later mathematical questions, not consequences silently attributed to the existing results.

See [`docs/theory/THEOREM_CONCORDANCE.md`](docs/theory/THEOREM_CONCORDANCE.md) for a claim-by-claim map of theorem, checker, scope, and non-claim.

## Central example

The base witness is a four-region cyclic cover

```text
U1 - U2 - U3 - U4 - U1
```

with residue `r = (1, 1, 1, -2)` and cycle `z = (-1, -1, -1, 1)`. Their pairing is

```text
<z, r> = -5 != 0
```

Because `z` annihilates every coboundary, `r` is not in `im(delta^0)`. In the concrete four-cycle complex, the residue is also closed, so it represents a non-trivial `H^1` obstruction rather than a bookkeeping artefact.

The same residue is independently generated from explicit associator-field data rather than merely declared as input.

## Main results

See [`RESULTS.md`](RESULTS.md) for the complete R1-R21 account and [`STATUS.md`](STATUS.md) for the distinction between proved, computed, diagnostic, and unclaimed results.

### R1-R5: obstruction, repair, refinement, and certificates

* The four-cycle residue is classified as a non-trivial obstruction.
* The residue is generated from explicit associator data.
* No regional boundary correction repairs it.
* Its transferred obstruction persists under four checked refinement witnesses at the A1-A4 level.
* Classifier verdicts can be emitted as independently checkable proof-carrying certificates.

### R6-R9: realisability

The realisability line asks whether an associator generator structurally forces obstruction or merely allows an arbitrary residue to be chosen.

Several candidate generators are shown to be either too free or collapsed into coboundaries. Candidate 3b receives a complete two-sided classification:

* pairwise-distinct triple support gives independent seam-local freedom and full rank;
* repeated triple support forces a genuinely partial, non-trivial quotient.

Both directions are machine-checked in Rocq.

### R10: refinement-witness composition

Sequential composition preserves N0, A4, and E0, but the three conditions have different dependency profiles.

Disjoint parallel composition preserves N0 and E0 componentwise. A4 does not behave as a Boolean conjunction because branch pairings can cancel in the aggregate. The repository proves both the branchwise preservation theorem and the exact non-cancellation condition required by the scalar aggregate.

For coupled parallel composition, the repository first proves a compatibility gate: agreeing shared-interface declarations admit a glue; conflicting declarations admit none. No conflict-resolution rule is introduced.

### R11-R14: no neutral scalar fusion

R11 proves that no single value can fully honour two disagreeing declarations unless the value domain is trivial.

R12 proves that a non-lossy diagnostic must preserve enough information to recover the ordered pair. For a finite value set of size `n`, this requires a codomain with at least `n^2` distinguishable values.

R13 gives a bounded four-way classification of honest conflict diagnostics:

1. refusal;
2. lossy scalar summary;
3. non-lossy structured diagnostic;
4. unresolved.

R14 turns that classification into a typed diagnostic calculus with explicit introduction, elimination, and evidence-refinement rules. Its central safety theorem states that, under genuine conflict, only a structured diagnostic can be both left-sound and right-sound.

### R15-R16: evidence-bearing diagnostic certificates

R15 connects the typed diagnostic calculus to the pairwise gluing theory. Compatibility requires an actual glue witness. Refusal requires an actual local-conflict witness. No bare "no composite" assertion is accepted as decisive evidence.

R16 gives the global analogue. A decisive global result carries either:

* a concrete repair witness; or
* a cycle obstruction witness with non-zero pairing.

The no-repair conclusion is derived from the evidence, never stored as an unaudited assertion.

### R17: common-subdivision verdict invariance

For two presentations with a shared transferred residue and refinement legs satisfying N0 and E0:

```text
[r_1] = 0   <=>   [r_2] = 0
```

This is verdict-level presentation invariance for the verified `verdict_safe` fragment. It is not full presentation invariance.

### R18-R19: quotient descent and reflection

For linear refinement maps, define coboundary equivalence by

```text
r ~ s   <=>   r - s in im(delta^0)
```

The machine-checked results show:

* N0 preserves `~`;
* E0 is equivalent to reflection of `~`;
* N0 and E0 together give faithful quotient descent.

The proof deliberately uses no quotient type, setoid machinery, cycle-space duality, adjunction, typeclass framework, or general presentation record.

### R20: quotient verdict closure

R20 rederives R17's verdict-equivalence conclusion through R18-R19's quotient machinery. This confirms that the direct and quotient-level proof routes agree.

It does not prove an isomorphism between the full quotient spaces. It compares the distinguished residues carried by the existing common-subdivision theorem.

### R21: exact rational repair-or-separator

A different kind of result from R17-R20: not another presentation-invariance theorem, but a general, verified, executable decision procedure for rational linear feasibility. For any rational system `D b = r`, R21 decides constructively:

```text
(exists b, D b = r)
\/
(exists y, D^T y = 0  /\  dot y r == 1)
```

by running verified exact-rational Gauss-Jordan elimination and extracting whichever witness the final state supports. Both witnesses are checked evidence, proved against the original `D`, `r`, not just the row-reduced matrix elimination operates on -- the repair branch needed its own solution-set-equivalence argument, proved independently of the transformation-matrix invariant the separator branch uses. The two witnesses are proved mutually exclusive as a separate theorem, not inferred from the algorithm's own branching.

R21 recovers R1's own four-cycle witness exactly: the internal elimination finds the paper's canonical cycle `z = (-1,-1,-1,1)` with pairing `-5` before normalisation, and the public certificate is the normalised `-1/5 z = (1/5,1/5,1/5,-1/5)`.

R21's Rocq proof is not itself the deployed executable path. A separate `roc-solve` / `roc-verify` CLI pair (`r21_certificate_emitter.py` / `r21_certificate_checker.py`) implements a digest-bound `repair-or-separator/v1` certificate: the generator is an untrusted hand-written mirror of R21's algorithm (not a Rocq extraction), and the independent checker imports neither the generator nor the emitter, recomputing `Db = r` or `D^Ty = 0 /\ y.r = 1` directly and failing closed. See `docs/design/R21_CERTIFICATE_TCB.md` for exactly what this closes and what remains open (extraction, a second cross-language checker, and per-domain input adapters).

It proves no general efficiency or numerical-stability property, and computes no rank, determinant, or general matrix inverse.

### Applied provenance bridges

The unnumbered pairwise-to-global assembly and associator-contribution results connect the mathematical certificates to the applied `veribound-fce` architecture.

They establish representation, provenance, co-reference, outcome-separation, orientation, and sign-determinacy properties. They deliberately do not claim that every applied implementation component has been extracted from or verified by Rocq.

## Interpretation, not formalism

The proved and computed content is at the level of finite cochains, cocycles, coboundaries, exact rational linear algebra, and explicitly defined diagnostic judgements. It is a finite, Čech-style obstruction calculus, not a formal higher-category theory.

It is useful to interpret surviving obstruction classes as failures of higher coherence: local data and pairwise agreement can hold while no globally warranted object exists. That interpretation motivates the calculus but is not itself a theorem proved in this repository.

Likewise, the presentation results support a restricted reading of representation independence: within the descent-safe and reflecting fragment, the obstruction verdict is not an artefact of choosing either of two presentations. They do not establish unrestricted presentation independence.

## Evidence levels

Three kinds of evidence appear throughout the repository and are not interchangeable.

* **Proved:** Rocq theorems checked by `coqc` and independently by `coqchk`.
* **Computed:** exact-rational Python or OCaml calculations with regression tests.
* **Diagnostic:** exact computations that establish a witness, counterexample, or classification for a specified construction, but not a theorem about every construction of that kind.

[`STATUS.md`](STATUS.md) states which category each result belongs to and what is not claimed.

## Repository map

```text
README.md
    project overview and scope

RESULTS.md
    complete R1-R21 result account

STATUS.md
    proved, computed, diagnostic, and unclaimed results

PROJECT_MAP.md
    file-by-file entry points by mathematical layer

REPRODUCIBILITY.md
    exact commands, versions, and expected outputs

docs/theory/THEOREM_CONCORDANCE.md
    compact theorem-to-file-to-scope map

docs/design/
    design documents written before implementation

docs/theory/
    synthesis and interpretation notes

docs/diagnostics/
    realisability and computational diagnostic accounts

rocq/
    25 active machine-checked proof modules

examples/
    exact JSON witness data

tests/
    181-test Python regression suite

ocaml/
    independent refinement and parity checkers

paper/
    two manuscripts and their relationship to the current repository
```

## Quick start

### Python checks

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make check-python
```

Expected result:

```text
181 passed
```

### Complete verification

```sh
make check-all
```

This runs, in order:

```text
check-python
check-rocq
check-rocq-trust
check-ocaml
check-assembly-parity
check-contribution-parity
```

The active formal chain contains 26 Rocq modules. `check-rocq-trust` runs `coqchk` over the complete declared dependency closure.

### Pinned container

For a matching formal toolchain without local installation:

```sh
docker build -t regional-obstruction-calculus .
docker run --rm regional-obstruction-calculus
```

The pinned environment uses:

```text
Python       3.12
pytest       9.1.1
Coq/Rocq     8.18.0
OCaml        4.14.1
```

The container fails loudly if the installed `coqc` or `ocamlopt` versions do not match the declared versions.

See [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) for the complete command sequence and expected outputs.

## Verification status

| Layer                                     | Principal artefacts                                                           | Status                                                         |
| ----------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------- |
| Exact rational obstruction classification | `residue_classifier.py`, `repair_solver.py`                                   | executable and tested                                          |
| Associator-generated residue              | `associator_residue.py`, `run_associator_obstruction.py`                      | executable and tested                                          |
| Refinement checking                       | `refinement_checker.py`                                                       | executable and tested                                          |
| First-order certificates                  | `certificate_emitter.py`, `first_order_certificate_checker.py`                | executable and independently checked                           |
| Realisability diagnostics                 | R6-R9 Python diagnostics and Rocq witnesses                                   | computed, with the Candidate 3b classification machine-checked |
| Refinement composition                    | R10 Rocq modules and probes                                                   | sequential and disjoint-parallel results machine-checked       |
| Conflict and diagnostic calculus          | R11-R16 Rocq modules                                                          | machine-checked                                                |
| Verdict-level presentation invariance     | `rocq/CommonSubdivisionVerdictInvariance.v`                                   | machine-checked for the descent-safe, reflecting fragment      |
| Quotient preservation and reflection      | `rocq/QuotientDescentReflection.v`                                            | machine-checked for linear refinement maps                     |
| Quotient verdict closure                  | `rocq/QuotientVerdictClosure.v`                                               | machine-checked                                                |
| Applied provenance bridges                | `rocq/PairwiseToGlobalAssembly.v`, `rocq/AssociatorContributionCertificate.v` | machine-checked, with independent OCaml parity checks          |
| Full presentation invariance              | none                                                                          | not claimed                                                    |
| Full end-to-end verified implementation   | none                                                                          | not claimed                                                    |

## Papers

The repository originated as the companion code for:

*Associator Fields and Local-to-Global Failure in Finite Compositional Structures*

The later manuscript:

*A Finite Cohomological Obstruction Calculus for Regional Warrant*

packages the realisability classification and refinement-witness composition results.

The repository has now grown beyond both manuscripts. R11-R21, the typed diagnostic and certificate bridges, the common-subdivision verdict theorem, and the quotient-preservation/reflection theory should be treated as repository results unless and until they are incorporated into a revised manuscript.

See [`paper/README.md`](paper/README.md) for the manuscript-level map.

## Citation, licence, and contact

Citation metadata is provided in [`CITATION.cff`](CITATION.cff).

Licence: AGPL-3.0-or-later.

Duston Moore
Independent Researcher
