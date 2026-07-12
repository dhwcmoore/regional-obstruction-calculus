# The Pairwise-to-Global Provenance Bridge

**Status: design document, no Rocq proof and no production code.** This
document is Phase 1 of a longer plan; it exists to answer one question
before anything is implemented:

> What exact information must each verified pairwise interface
> contribute so that a global discrepancy object can be constructed
> without inventing evidence, losing source provenance, or confusing
> local admissibility with global coherence?

Sharper operational form:

> Given a finite family of independently verified pairwise
> certificates, an interface topology, and an orientation convention,
> when is there a canonical assembly into the global cochain consumed
> by the existing global certificate engine
> (`rocq/GlobalCoherenceCertificate.v`, R16), and what must happen when
> the evidence is incomplete, inconsistent, or structurally malformed?

The governing constraint, stated up front because §1 below shows it is
not automatically satisfied by anything that already exists:

```text
local interface admissibility  !=  zero local contribution  !=  global coherence
```

A locally accepted interface may contribute a non-zero transition to
the global loop. A construction that cannot represent this could never
represent the central case this whole project studies: every local
interface valid, the total cycle still globally obstructed
(`FourCycleObstruction.v`'s own witness).

## 1. What already exists, and the gap this document exists to name

Before specifying `VerifiedPairwiseCertificate`, it is necessary to
check whether something already answers "what does one interface
contribute" — inventing a new mechanism when one already exists would
violate this project's own promotion-with-provenance discipline just
as much as inventing evidence would. Two things already exist, and
they are **not the same thing**, and neither one alone is what a
`VerifiedPairwiseCertificate` needs to be.

### 1a. R15: admissibility of a declaration pair, no scalar anywhere

`rocq/PairwiseDiagnosticCertificate.v` (R15) and its applied mirror
`veribound-fce/src/pairwise_certificate.py` decide whether two
`Key -> option Value` declarations are compatible:

```coq
Inductive DecisivePairwiseEvidence (dA dB : Decl) : Type :=
  | CompatibleEvidence :
      forall g : Decl, IsGlue Key Value dA dB g -> DecisivePairwiseEvidence dA dB
  | IncompatibleEvidence :
      LocalConflict dA dB -> DecisivePairwiseEvidence dA dB.
```

`CompatibleEvidence`'s payload is a *glue declaration* `g`. `IncompatibleEvidence`'s
payload is a *conflicting key and two string values*. Neither
constructor carries, or could carry without a genuinely new field, an
exact-rational number. This is not an oversight: R15 was scoped
narrowly and deliberately to the question CoupledParallelCompatibility.v
answers (does a well-defined composite exist), never to "how much does
this interface displace the global cochain." The applied
`PairwiseCertificate` dataclass mirrors this exactly —
`CompatibleEvidence.glue: Declaration`, `IncompatibleEvidence.key/left_value/right_value`,
no numeric field anywhere in the schema.

**Consequence for this design**: R15-shaped evidence, as it exists
today, cannot by itself populate the `contribution` field an
operational-form sketch of this bridge would want. Compatibility says
a composite declaration exists; it says nothing about what that
composite is worth in `C^1`.

### 1b. `associator_residue.py`: a per-seam scalar, no admissibility anywhere

`associator_residue.py` (built on `regional_composition.py`'s
`associator_defect`) computes exactly one rational number per seam —
`compute_seam_residue(instance) -> Fraction`, cross-checked twice
(literal associator expansion vs. the closed-form four-term formula,
must agree exactly or the module raises). It reconstructs the paper's
own residue `r = (1, 1, 1, -2)` on `SEAM_ORDER = ("e12", "e23", "e34",
"e14")` — the exact same seam indexing `FourCycleObstruction.v` uses
for `C1`/`Z1`. Each `SeamAssociatorInstance` (a `VennTriple` plus
`SeamCorrectionData`) is genuinely local to one seam: nothing about
seam `e23`'s computed value depends on any other seam's data, matching
the way this whole construction is meant to be read as *four
independent* local computations later assembled into one vector
(the module's own docstring: "four *independent* finite associator
defects, one per coarse seam").

This is much closer to what "contribution" means operationally — but
it has **no decisive-evidence type at all**. There is no
`SeamContributionEvidence` inductive, no Rocq proof that
`compute_seam_residue`'s result is correct, and no notion of
"unresolved" (the Python code either produces a value or raises,
there is no third state). It is a trusted computation, not yet a
verified certificate in the sense R15/R16 use that word.

### 1c. The gap, stated plainly

**A `VerifiedPairwiseCertificate` in the sense this bridge needs does
not exist yet, in either half.** R15 proves admissibility with no
scalar; `associator_residue.py` computes a scalar with no certificate
type and no admissibility notion. Building the assembler on the
assumption that "verified pairwise certificate" already means
"admissible-and-quantified" would be inventing evidence — exactly what
§4's invariants below forbid the assembler itself from doing. The
right place to resolve this is here, explicitly, not silently inside
an implementation.

**Proposed resolution (design decision, not yet authorized — see §9):**
do not merge the two into one certificate type. Keep them as two
separately-verified facts about the same interface, composed, not
conflated — the same discipline `docs/design/CERTIFICATE_COMPOSITION_SPEC.md`
already applies to keep `pairwise_compatibility` and `global_coherence`
from collapsing into each other:

```text
VerifiedPairwiseCertificate(interface) :=
    AdmissibilityEvidence(interface)   -- R15-shaped: Compatible / Incompatible / Unresolved
  x ContributionEvidence(interface)    -- new: a checked scalar, or Unresolved
```

with one hard rule connecting them, cashing out the governing
constraint from the top of this document:

> `Incompatible` admissibility **blocks assembly outright**, regardless
> of whether a contribution value exists or what it would be. `Compatible`
> admissibility **does not determine** the contribution's value, and in
> particular does not license assuming it is zero.

This is why the two cannot be merged into a single boolean-flavoured
"ok/not-ok" field the way an earlier, since-corrected design in this
same project once nearly did (see
`[[veribound-fce-applied-layer]]`'s R14 audit finding, "the defect was
the representation itself, not a missing theorem" — the identical
category error, one level up, is available here again if `contribution`
is allowed to default to zero whenever `Compatible` holds).

**Whether `ContributionEvidence` needs its own Rocq certificate type
before Phase 2 begins, and whether it needs a formal consistency proof
against the admissibility side (e.g. that the same declared correction
data underlies both), is the largest open question this document
raises. It is not resolved here — see §9.**

## 2. Input objects

Four separate objects, matching the existing repository's own
vocabulary where it already has one.

### Source declaration

Reuses R15's existing `Declaration` (`Key -> option Value`) rather than
inventing a new normalised-input type — the assembler must not need to
understand raw sensor data, only already-normalised declarations, which
is exactly what `Declaration` already is on the applied side.

```text
SourceDeclaration
  source_id           -- e.g. "U1", matching FourCycleObstruction.v's C0 order
  declaration_id
  declaration : Key -> option Value
  schema_version
```

### Oriented interface

The topology already has a real precedent:
`veribound-fce/examples/coarse_to_fine_zoom_refinement_case.json`'s
`{"name": ..., "src": ..., "tgt": ...}` edge shape, and
`FourCycleObstruction.v`'s own `SEAM_ORDER = (e12, e23, e34, e14)`
seam naming. Reuse both rather than inventing a third naming scheme:

```text
OrientedInterface
  interface_id     -- e.g. "e12", matching SEAM_ORDER
  left_source       -- e.g. "U1"
  right_source      -- e.g. "U2"
  orientation       -- which direction is "+"
```

Orientation must be explicit and reversible: reversing an interface
must reverse the sign of its contribution (§6, invariant 4).

### Verified pairwise certificate

Per §1c, this is **two evidences, not one**:

```text
VerifiedPairwiseCertificate
  certificate_id
  interface_id
  admissibility : R15 PairwiseResult (Decided Compatible/Incompatible | Unresolved)
  contribution  : ContributionResult (Decided(value: Fraction) | Unresolved)
  verification_status
  certificate_digest
```

`contribution` must never be inferred from `admissibility`'s label
alone (§1c). A certificate may establish that a non-zero transition is
locally legitimate; `Compatible` is not evidence that the transition is
small, zero, or absent.

### Assembly topology

```text
AssemblyTopology
  vertices              -- source_ids, e.g. ("U1","U2","U3","U4")
  oriented_interfaces    -- e.g. the four SEAM_ORDER edges
  coboundary_0           -- reuse examples/four_cycle.json's own matrix
                            shape directly; this is not a new topology
                            encoding, it is the encoding the global
                            certificate builder already consumes
  topology_digest
```

Reusing `coboundary_0` as the topology's own serialisation (rather
than a fresh vertex/edge graph the assembler would need to re-derive a
coboundary matrix from) means the assembled residue's *shape* is
already exactly the shape `global_coherence_certificate.build_certificate`
expects — no new topology-to-matrix translation layer is needed for
the four-cycle case, and any topology beyond it inherits the same
requirement: it must already be expressible as a `coboundary_0` this
project's existing machinery understands.

## 3. The assembled object

```text
AssembledGlobalEvidence
  topology
  ordered_source_certificates
  residue : List[Fraction]      -- same field name and shape
                                    global_coherence_certificate.py
                                    already uses
  provenance_manifest
  assembly_status
```

### Residue construction

For each oriented interface `e`:

```text
residue[e] = contribution(certificate_for(e))
```

only if `certificate_for(e)` exists, its `admissibility` is `Decided
Compatible`, and its `contribution` is `Decided(value)`. The assembler
must not:

- invent a missing coordinate;
- silently replace an unresolved or incompatible contribution with zero;
- infer evidence from file or argument order;
- accept two different certificates for the same interface without an
  explicit resolution rule (there is none in this first version — see
  §5, `REFUSED_INCONSISTENT_ASSEMBLY`);
- proceed to a confident global verdict while any required evidence is
  unresolved.

### Provenance manifest

Every residue coordinate retains a path back to its source evidence:

```text
ProvenanceEntry
  residue_coordinate
  interface_id
  pairwise_certificate_id
  pairwise_certificate_digest
  source_declaration_ids
  orientation
  transformation_applied
```

Minimum invariant:

> Every coordinate in the assembled residue is justified by identified
> verified pairwise evidence, and every pairwise certificate used by
> the assembly appears in the provenance manifest.

Stronger invariant, deferred rather than assumed (see §5's requirement
that the first version accept exactly one certificate per interface):

> Every non-zero residue contribution has exactly one declared
> evidential derivation, unless an explicit composition rule records
> multiple contributors.

**For this first specification, require exactly one certificate per
interface. Multi-certificate composition (e.g. combining more than one
`SeamAssociatorInstance` per seam) is out of scope**, matching this
project's own repeated practice of not building a general theory before
a specific one is proved (compare `docs/design/GLOBAL_COHERENCE_CERTIFICATE_SPEC.md`
§2's identical scoping choice for the global bridge itself).

## 4. Admissible states

Three states, not a bare success/failure boolean, matching the
diagnostic vocabulary already established by R13/R14
(`docs/design/TYPED_DIAGNOSTIC_CALCULUS.md`) and mirrored in
`veribound-fce/src/coherence.py`'s existing `UNRESOLVED_GLOBAL_EVIDENCE`
constant and its `hold_for_review` policy mapping.

### `ASSEMBLED`

Every required interface has: one verified certificate, matching
endpoint declarations, matching interface identifiers, valid
orientation, and a `Decided` contribution of the expected type. The
residue may then be passed to `global_coherence_certificate.build_certificate`.

### `UNRESOLVED_ASSEMBLY_EVIDENCE`

Use when: an interface certificate is missing; a certificate's
admissibility or contribution is `Unresolved`; a required declaration
cannot be matched; a certificate is structurally incomplete; the
topology is incomplete. Maps to `hold_for_review` — the same mapping
`UNRESOLVED_GLOBAL_EVIDENCE` already has in `src/policy.py`, extended
one layer earlier in the pipeline, not given new vocabulary.

### `REFUSED_INCONSISTENT_ASSEMBLY`

A **separate** state from unresolved, for positively contradictory
evidence, not merely absent evidence:

- two certificates claim the same interface with different contributions;
- a certificate's admissibility is `Incompatible` (per §1c, this
  refuses the whole assembly, not just that coordinate);
- certificate endpoints disagree with the topology;
- a certificate digest does not match its contents;
- the same certificate is illicitly reused for distinct interfaces;
- orientation metadata is internally contradictory.

```text
unresolved = insufficient evidence
refused    = proved inconsistency
obstructed = valid evidence establishes non-removability   (existing, R16)
cleared    = valid evidence establishes repairability       (existing, R16)
```

`unresolved`/`refused` are assembly-layer states, upstream of and
distinct from `obstructed`/`cleared`, which remain exactly R16's own
two decisive outcomes — this document adds no new vocabulary at that
layer, matching the non-conflation discipline §1c already commits to.

## 5. Invariants

1. **No silent contribution creation.** If no verified pairwise
   certificate supports interface `e`, the assembler cannot create `r(e)`.
2. **Provenance completeness.** Every assembled residue coordinate
   names the certificate and declarations it was derived from.
3. **Endpoint agreement.** Declaration identifiers inside the
   certificate must agree with the topology's endpoints for that interface.
4. **Orientation covariance.** Reversing interface `e` transforms its
   contribution by the declared reversal operation (sign negation):
   `r(reverse(e)) = -r(e)`. The global classification must be invariant
   under a consistent reorientation of the whole presentation.
5. **Ordering invariance.** Reordering the input certificates must not
   alter the assembled object.
6. **Duplicate rejection.** Two certificates cannot silently populate
   the same interface — this is `REFUSED_INCONSISTENT_ASSEMBLY`, not
   last-write-wins.
7. **Verification gating.** Only certificates whose `verification_status`
   reflects a genuinely independent recheck (in-process verifier result,
   or an envelope re-verified before assembly) may enter — a stored
   string reading `"verified"` is not itself evidence, the same
   discipline `veribound-fce/fce_check.py`'s own fail-closed rework
   already established for the existing pipeline.
8. **No silent confidence gain.** An unresolved or refused pairwise
   input cannot become a confident global `cleared` or `obstructed`
   result. This is the applied analogue of
   `TYPED_DIAGNOSTIC_CALCULUS.md`'s `no_silent_soundness_gain`.
9. **Global-envelope consistency.** The final output must agree across
   assembled residue, global certificate, coherence verdict, policy
   verdict, and provenance manifest — an envelope-aware verifier
   (extending `global_certificate_verifier.verify_envelope`, not
   replacing it) must reject any disagreement.

## 6. First theorem target: representation soundness

A modest theorem, not the full end-to-end correctness claim, matching
this whole project's preference for a short modular proof chain over
one large theorem (see `GLOBAL_COHERENCE_CERTIFICATE_SPEC.md` §7 for
the same reasoning applied one layer down):

```text
pairwise certificate soundness (R15, plus a new contribution certificate)
  -> assembly representation soundness  (this document's target)
  -> existing global certificate soundness (R16, unchanged)
  -> policy derived from verified global result (existing, unchanged)
```

Informally:

> If every oriented interface in a declared topology is assigned
> exactly one verified pairwise certificate, and that certificate's
> endpoints and orientation agree with the topology, then the
> assembled residue agrees componentwise with the verified contributions.

```text
forall e, AssembledResidue(e) = Contribution(certificate_for(e))
```

This does not yet prove the global verdict is correct — R16 already
does that, unchanged, once handed a residue. It proves only that the
residue handed to R16 was not invented.

**Corollary (provenance preservation).** For every assembled
coordinate, there exists a verified source certificate recorded in the
manifest that supports exactly that coordinate.

**Negative theorem (no unsupported coordinate).** The assembler cannot
produce a coordinate for an interface absent from the verified
certificate assignment.

**Reorientation theorem.** A consistent reversal of interface
orientation transforms the residue as invariant 4 requires and
preserves the global obstruction classification — this is the theorem
that would need `AssociatorResidueRepair.v`'s abstract layer to already
be orientation-agnostic in the relevant sense; confirming that is part
of the proof, not assumed by it.

**Target file (not yet attempted):**
`rocq/PairwiseToGlobalAssembly.v`, importing
`rocq/PairwiseDiagnosticCertificate.v` and
`rocq/GlobalCoherenceCertificate.v` directly, adding whatever new
`ContributionEvidence` type §1c's resolution settles on, rather than
duplicating either existing file's content.

## 7. What is not claimed by this document

- **No production code.** No `assemble_global_evidence()`, no new
  Python dataclasses, no new Rocq file. This document only specifies.
- **No resolution of §1c's open question.** Whether `ContributionEvidence`
  gets its own Rocq certificate type, and whether it needs a formal
  consistency proof against the admissibility side, is not decided
  here — see §9.
- **No multi-certificate composition per interface** (§3) — exactly
  one certificate per interface for this first version.
- **No claim that this generalises beyond the four-cycle topology.**
  The four-cycle remains the first and, for this document, only
  concrete integration target (matching every other bridge document in
  this project's habit of proving the abstraction against one worked
  instance before generalising).
- **No evaluator-kit, `veribound-fce` pipeline, or CI change.** Those
  are later phases in the broader plan this document is Phase 1 of,
  and are not authorized by this document alone.
- **No claim about raw sensor truth.** The chain begins with
  already-normalised source declarations, exactly as
  `veribound-fce/fce_check.py`'s own existing scope note already states
  for the pipeline stages it touches.

## 8. Roadmap beyond this document (not authorized here)

For context only — later phases of the plan this document opens,
listed so the scope boundary above is legible, not as a queued task
list:

```text
Phase 2  minimal Rocq representation-soundness model and theorem
Phase 3  pure Python assembler in veribound-fce (no policy, no repair)
Phase 4  four-cycle integration cases (obstructed / repairable /
         missing evidence / endpoint mismatch / duplicate interface /
         orientation reversal / tampered provenance)
Phase 5  certificate envelope extension + verifier
Phase 6  unit / exhaustive / end-to-end regression tests
Phase 7  evaluator-kit demonstration, only after both upstream releases
```

None of these begin until this document's open questions (§9) are
resolved and Phase 2 is separately authorized, matching this project's
standing practice throughout `[[veribound-fce-applied-layer]]` and
`[[associator-fields-frozen-kernel]]`: each phase is its own decision
point, not implied by the previous one being written down.

## 9. Open questions requiring a decision before Phase 2

1. **Does `ContributionEvidence` get its own proof-carrying Rocq type**,
   parallel to how R15 gave `DecisivePairwiseEvidence` a type for
   admissibility — or does the bridge theorem take an already-correct
   `Fraction` as an opaque hypothesis (the way `AssociatorResidueRepair.v`
   already takes `pairing`/`cycle` as caller-supplied, proving nothing
   about how they were computed)? The second option is cheaper and
   matches this project's existing layering (Layer 1 abstract,
   `associator_residue.py` a trusted but unverified compiler feeding
   it) — but it means the bridge's soundness theorem would not, by
   itself, certify that a real `compute_seam_residue` output was
   correct, only that *if* it was correct, assembly preserved that.
2. **Is a consistency proof required between the admissibility glue and
   the contribution scalar** for the same interface (e.g. that both
   derive from the same declared correction/interface data), or are
   they permitted to remain two independently-supplied facts with no
   formal link between them in this first version? §1c's proposed
   resolution takes the weaker "independently supplied" position by
   default; this should be confirmed, not assumed.
3. **Does the four-cycle's actual seam data need to be re-expressed as
   `VerifiedPairwiseCertificate` objects for the first integration
   case (§8, Phase 4), or is a simpler fixture-level stand-in
   acceptable** for exercising the assembler's admissible-states logic
   before the real R15/`associator_residue.py` union is wired through?
