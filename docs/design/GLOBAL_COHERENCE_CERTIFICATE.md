# A Proof-Carrying Global Coherence Certificate

**Status: design document, no Rocq proof yet.** This document specifies
a global-coherence analogue of R15
(`docs/design/CERTIFICATE_COMPOSITION_SPEC.md`'s `pairwise_
compatibility` bridge, `rocq/PairwiseDiagnosticCertificate.v`), scoped
narrowly to what `AssociatorResidueRepair.v`'s existing abstract
theorem already supports. It proves no new cohomology; it packages
existing theorems into evidence-carrying certificate constructors, the
same way R15 packaged `CoupledParallelCompatibility.v` rather than
re-deriving its gluing theory.

## 1. What is already proved, exactly as it stands

Two files, neither modified here, give this bridge everything it needs.

**`FourCycleObstruction.v`** defines a cycle *functionally*, not via a
separate boundary operator:

```coq
Definition cycle (w : vec4) : Prop :=
  forall b : vec4, pairing w (delta0 b) == 0.

Lemma coboundaries_pair_zero :
  forall (w : vec4) (b : vec4), cycle w -> pairing w (delta0 b) == 0.
Proof. intros w b Hcycle; apply Hcycle. Qed.
```

"`w` is a cycle" *means* "`w` pairs to zero against every coboundary."
There is no boundary operator, transpose construction, or adjoint law
anywhere in this definition, and none is needed: `coboundaries_pair_
zero` is a one-line unfolding of `cycle`'s own definition. This
settles, for this repository specifically, a question that would
otherwise need its own lemma in a more general treatment (one that
defined cycles via `ker` of an independently-introduced boundary map
and then had to relate that back to the pairing).

**`AssociatorResidueRepair.v`**'s Layer 1 is already exactly this
abstraction, generalised over arbitrary `C0`, `C1`, `Z1`:

```coq
Theorem nonzero_pairing_blocks_repair_mod_ceq :
  forall (C0 C1 Z1 : Type)
         (delta0 : C0 -> C1)
         (pairing : Z1 -> C1 -> Q)
         (cycle : Z1 -> Prop)
         (ceq : C1 -> C1 -> Prop)
         (ceq_equiv : Equivalence ceq)
         (pairing_respects_ceq :
            forall (z : Z1) (r r' : C1), ceq r r' -> pairing z r == pairing z r')
         (coboundaries_pair_zero :
            forall (z : Z1) (b : C0), cycle z -> pairing z (delta0 b) == 0)
         (r : C1) (z : Z1),
    cycle z -> ~ (pairing z r == 0) -> ~ (exists b : C0, ceq (delta0 b) r).
```

This is not associator-specific (that is Layer 2, built on top, not
used here). It makes no assumption about how many regions exist, what
`C0`/`C1` are concretely, or how `cycle` is decided — only that
`coboundaries_pair_zero` and `pairing_respects_ceq` hold for whatever
`delta0`/`pairing`/`cycle`/`ceq` a caller supplies. `FourCycleObstruction
.v` is a *concrete instance* of this abstraction (`C0 := C1 := vec4`,
`ceq := veq`), not its foundation.

## 2. Scope: the abstract Layer-1 interface, not a new cover theory

This bridge is parameterised exactly as `nonzero_pairing_blocks_repair_
mod_ceq` already is:

```text
C0 C1 Z1   : Type
delta0     : C0 -> C1
pairing    : Z1 -> C1 -> Q
cycle      : Z1 -> Prop
ceq        : C1 -> C1 -> Prop
ceq_equiv, pairing_respects_ceq, coboundaries_pair_zero
```

Deliberately neither extreme: not limited to the concrete four-cycle
(that would waste the abstraction already built), and not a new general
`n`-region cover, boundary operator, or sheaf framework (that would be
new mathematics, not packaging). Anyone instantiating this bridge for a
real cover supplies their own `delta0`/`pairing`/`cycle` and proves
`coboundaries_pair_zero` for it once — exactly the same shape of
per-domain obligation R15 left to `CoupledParallelCompatibility.v`'s own
`Key`/`Value` instantiation.

## 3. Why this does not reuse `ConflictDiagnostic`

R14's diagnostic vocabulary is intrinsically pairwise: two declarations,
`SoundL`/`SoundR` governing their separate recoverability,
`StructuredDiagnostic` preserving their provenance as a pair,
`RefuseDiagnostic` naming refusal of *their* local composition. R15
correctly instantiates that vocabulary because its subject really is
two declarations disagreeing (or agreeing) over one shared interface.

The global problem has a different logical shape entirely: one regional
residue `r`, one possible repair potential `b`, one possible obstruction
cycle `z` — no left and right declarations to recover, no role for
`SoundL`/`SoundR`, no scalar-loss question of R11's kind (a repair
potential is not a lossy summary of two disagreeing things; it is a
witness that one thing is removable). Forcing this into `ConflictDiagnostic
V C` would require inventing fake branch declarations merely to reuse
its constructors, and would overload `RefuseDiagnostic` with two
genuinely different meanings — local disagreement between two
declarations, and global non-repairability of one residue — which are
exactly the two obstruction theories `docs/design/
CERTIFICATE_COMPOSITION_SPEC.md` already keeps separate
(`pairwise_compatibility` vs. `global_coherence`). This bridge therefore
defines its own, independent evidence type.

## 4. The certificate type

```coq
Inductive DecisiveGlobalEvidence (r : C1) : Type :=
  | RepairEvidence :
      forall b : C0, ceq (delta0 b) r -> DecisiveGlobalEvidence r
  | ObstructionEvidence :
      forall z : Z1, cycle z -> ~ (pairing z r == 0) -> DecisiveGlobalEvidence r.

Inductive GlobalCoherenceResult (r : C1) : Type :=
  | GlobalDecided : DecisiveGlobalEvidence r -> GlobalCoherenceResult r
  | GlobalUnresolvedResult : GlobalCoherenceResult r.
```

Not the GADT-indexed form (`DecisiveGlobalEvidence r : GlobalCoherenceStatus
-> Type`, with a separate three-constructor status enum) originally
sketched during design. Deliberately simplified to a plain sum type,
matching `DecisivePairwiseEvidence`/`PairwiseResult`'s own successful
shape in R15 exactly: indexing by a status enum adds no soundness
content beyond what the two constructors already carry, and would force
dependent pattern-matching complexity into the central theorem's proof
for no semantic gain. `GlobalUnresolvedResult` plays exactly
`PairwiseResult`'s `Unresolved` role: it means only that no validated
repair or obstruction certificate is being presented, not that any
search was exhaustive, bounded, or correctly executed — that stronger
procedural claim needs a separate search semantics this file does not
define, exactly as R15 left `PairwiseResult`'s `Unresolved` case
underspecified in the same way.

The asymmetry is deliberate, matching R15's own: repairability carries
a positive repair witness; obstruction carries a positive cycle
witness; non-repairability is *derived* from the obstruction witness
(via `nonzero_pairing_blocks_repair_mod_ceq`), never stored as
primitive evidence. There is no constructor for a bare "residue is not
repairable" claim independent of an actual cycle witness.

## 5. Naming discipline: do not claim `H^1` nontriviality

`nonzero_pairing_blocks_repair_mod_ceq` proves `~ (exists b, ceq (delta0
b) r)` — `r` is not a coboundary. It does **not** require or establish
`delta1 r = 0` — that `r` is a cocycle. A genuine "`[r] != 0` in `H^1`"
claim (`H^1 := ker delta1 / im delta0`) is *strictly stronger*: cocycle
*and* not-coboundary, not not-coboundary alone. Nothing in this bridge's
hypotheses supplies or checks the cocycle condition, so nothing here is
named `NontrivialH1Obstruction`, `H1Obstruction`, or similar. The
obstruction evidence constructor and any surrounding vocabulary must
say only what is actually proved: *non-repairable*, not *nontrivial
cohomology class*. A later, separate layer could add the cocycle
condition as an extra field and derive the stronger claim honestly, but
that is not attempted here.

## 6. Also not added: a fourth "already coherent" case

No `GloballyCoherent`/zero-residue constructor is added in this first
bridge. The Layer-1 interface supplies no distinguished zero element of
`C1` and no reason the central repair theorem needs one — adding one
here would enlarge the abstraction to support a classification
distinction (`r = 0` vs. `r != 0` but repairable) the proved machinery
does not currently need. A later verdict layer, once a zero/near-zero
distinction is actually wanted, can refine the repairable side without
touching this file.

## 7. The central theorem and supporting results

```text
global_coherence_certificate_sound :
    GlobalDecided (RepairEvidence b Hrepair)      -> ceq (delta0 b) r
    GlobalDecided (ObstructionEvidence z Hcyc Hnz) -> ~ exists b, ceq (delta0 b) r
    GlobalUnresolvedResult                          -> True
```

The obstruction branch's conclusion is *obtained* from `nonzero_
pairing_blocks_repair_mod_ceq` applied to the evidence's own `(z, Hcyc,
Hnz)`, never re-derived or stored separately. The `Unresolved` branch's
`True` is deliberately the weakest possible statement — it asserts
nothing about search completeness.

Supporting theorems, honestly scoped rather than padded to match a
target count: the design brainstorm that produced this document
proposed `repairable_requires_repair_witness` and `obstructed_requires_
cycle_witness` as two separate facts. Attempting both separately
produced two statements whose only content was a constructor's own
carried hypothesis restated verbatim — not worth two named theorems.
Merged into one honest fact instead:

```text
decisive_global_evidence_is_repair_or_obstruction :
    any DecisiveGlobalEvidence r testifies to EITHER a repair witness
    or an obstruction witness -- the two constructors are exhaustive
    for whatever evidence was actually constructed.

obstruction_certificate_blocks_every_repair :
    a checked obstruction witness (z, cycle z, nonzero pairing) entails
    no b satisfies the repair equation for r -- direct restatement of
    the central theorem's obstruction branch as a standalone fact.

unresolved_result_carries_no_decisive_evidence :
    GlobalUnresolvedResult is never equal to GlobalDecided _ -- an
    inversion fact, matching R15's certified_pairwise_never_scalar in
    spirit (a constructor-distinctness fact worth naming, not merely
    assuming).

repairable_and_obstructed_are_disjoint :
    no residue can simultaneously have a checked repair witness and a
    checked obstruction witness -- follows immediately from the
    obstruction theorem applied to the repair witness itself. The
    genuine consistency property this bridge earns.
```

## 8. What is not claimed

- **This does not prove `H^1` nontriviality anywhere** — see §5. Every
  obstruction fact proved here is "not a coboundary," never "nontrivial
  cohomology class."
- **This does not add a fourth, "already coherent" status** — see §6.
- **This does not reuse `ConflictDiagnostic`, `SoundL`, or `SoundR`** —
  see §3. Global coherence gets its own, independent type.
- **This does not claim decidability.** Whether `Compatible`-style
  membership (`exists b, ceq (delta0 b) r`) holds is not claimed
  decidable in general; `GlobalUnresolvedResult` is not evidence that a
  search was exhaustive.
- **This does not generalise `coboundaries_pair_zero` to an arbitrary
  cover.** That obligation is left to whoever instantiates this bridge
  for a concrete domain — either the existing four-cycle (cheap, already
  proved) or a new general cover (a new, but likely short, proof, not
  attempted here).
- **This does not add global-coherence certificates to `veribound-fce`,
  policy obstruction, or any executable pipeline change.** Those remain
  separate, unstarted layers, exactly as R15 left them.
- **This does not claim generation is easy while verification is hard,
  or the reverse, via complexity-theoretic language (NP-hardness,
  approximate/floating-point methods, timeouts).** The project's
  strength is exact rational verification; nothing here needs, or
  claims, more than that an untrusted generator may use any method
  while a trusted checker evaluates the certificate in exact arithmetic.

## 9. Expected Rocq target

`rocq/GlobalCoherenceCertificate.v`, importing `AssociatorResidueRepair.v`
directly (for `nonzero_pairing_blocks_repair_mod_ceq`) rather than
duplicating it. Not yet attempted; scoped in full above.
