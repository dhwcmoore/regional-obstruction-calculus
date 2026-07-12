# The Pairwise-to-Global Provenance Bridge

**Status: design document, no Rocq proof and no production code.**
Phase 1 architecture decisions recorded 2026-07-12 (§9) after the
finding in §1 changed the shape of the bridge; implementation has not
begun. This document exists to answer one question before anything is
implemented:

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

The governing constraint, now fixed as the central distinction this
whole document exists to preserve (§1 found it was not automatically
satisfied by anything that already exists; §9 records it as decided,
not merely proposed):

```text
pairwise admissibility evidence  !=  pairwise contribution evidence  !=  global coherence evidence
```

Concretely:

```text
Compatible(i)     does NOT imply     c_i = 0
Incompatible(i)   implies            assembly is not authorised
```

while the assembled residue `r = (c_i)` for `i` in the interface set
still requires a separate global test (unchanged R16) to determine
whether it is removable, obstructed, or unresolved. A locally accepted
interface may contribute a non-zero transition to the global loop. A
construction that cannot represent this could never represent the
central case this whole project studies: every local interface valid,
the total cycle still globally obstructed
(`FourCycleObstruction.v`'s own witness).

## 1. What already exists, and the gap this document exists to name

Before specifying `VerifiedPairwiseCertificate`, it is necessary to
check whether something already answers "what does one interface
contribute" — inventing a new mechanism when one already exists would
violate this project's own promotion-with-provenance discipline just
as much as inventing evidence would. Two things already exist, and
they are **not the same thing**, and neither one alone is what a
bridge-ready certificate needs to be.

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
today, cannot by itself populate a numeric contribution field. This is
now fixed as intentional, not a gap to be closed by extending R15
(§9, decision 1) — see §2 below.

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

**A single certificate combining admissibility and contribution does
not exist yet, in either half.** R15 proves admissibility with no
scalar; `associator_residue.py` computes a scalar with no certificate
type and no admissibility notion. Building the assembler on the
assumption that "verified pairwise certificate" already means
"admissible-and-quantified" would be inventing evidence — exactly what
§5's invariants below forbid the assembler itself from doing. The
right place to resolve this is here, explicitly, not silently inside
an implementation.

## 2. Decided architecture: three separate objects, not one

**This section records the decision made in response to §1's finding
(full reasoning in §9). Do not merge admissibility and contribution
into one certificate type. Do not add a numeric field to
`CompatibleEvidence`. That would recreate the exact collapse §1 exists
to prevent** — the same category error the R14 applied-pipeline audit
caught elsewhere in this project (collapsing a proved-impossibility
distinction onto a bare boolean; see
`[[veribound-fce-applied-layer]]`'s account of that audit).

```text
VerifiedInterfaceEvidence(interface) :=
    VerifiedPairwiseCertificate(interface)      -- R15-shaped, unchanged: Compatible / Incompatible / Unresolved
  x VerifiedContributionCertificate(interface)   -- new, separate: a checked scalar, or Unresolved
  + a co-reference condition linking the two (§5, §6)
```

`VerifiedPairwiseCertificate` is exactly R15's existing evidence type,
untouched. `VerifiedContributionCertificate` is a new object, deliberately
modest in its first form (decision 1, §9):

```text
VerifiedContributionCertificate
  interface_id
  local_input_digest
  contribution : Fraction
  witness
```

Its intended soundness statement, once formalised (later phase, not
this one — see §8): *for interface `i`, under declared local input
`x_i`, the certified contribution is `c_i`*. Nothing stronger. It does
not, and must not, say anything about admissibility.

The two evidences are linked only by a **co-reference condition** —
provenance consistency, not semantic derivability:

```text
admissibility.interface_id  = contribution.interface_id
admissibility.input_digest  = contribution.input_digest
```

**Wrong requirement, explicitly rejected**: prove that `CompatibleEvidence`
entails the certified scalar. Admissibility does not determine
contribution's value, in either direction.

**Right requirement**: check (or later prove) that both evidences
refer to the same local situation — the same interface, the same
underlying declarations or local input state. A future, genuinely
domain-specific theorem might connect the two more tightly for a
particular model (e.g. proving certain incompatible declarations
cannot have a meaningful contribution) — that would be an additional,
named theorem, not assumed generic architecture, and is out of scope
here.

## 3. Input objects

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
must reverse the sign of its contribution (§5, invariant 4).

### Verified pairwise certificate (admissibility only)

Exactly R15's own evidence type, unmodified — see §2. No numeric field.

```text
VerifiedPairwiseCertificate
  certificate_id
  interface_id
  input_digest
  admissibility : PairwiseResult   -- Decided(Compatible glue) | Decided(Incompatible conflict) | Unresolved
  verification_status
  certificate_digest
```

### Verified contribution certificate (new, modest first form)

```text
VerifiedContributionCertificate
  certificate_id
  interface_id
  input_digest
  contribution : ContributionResult   -- Decided(value: Fraction) | Unresolved
  witness
  verification_status
  certificate_digest
```

For the first integration case (§8), this certificate's verifier is a
**typed fixture stand-in** (decision 3, §9), not yet the eventual
Rocq-backed checker:

```text
FixtureVerifiedContribution
  interface_id
  input_digest
  contribution
  fixture_provenance
```

whose verifier validates a checked fixture manifest, or reproduces the
result through the existing two independent `associator_residue.py`
computations (literal expansion vs. closed-form). Its type and the
assembler's boundary already match the eventual proof-carrying
version's shape, so replacing the fixture verifier later does not
alter assembly semantics — only what backs `verification_status`.

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

## 4. The assembled object

```text
AssembledResidue
  ordered_interfaces
  contributions
  residue : List[Fraction]              -- same field name and shape
                                            global_coherence_certificate.py
                                            already uses
  admissibility_certificates
  contribution_certificates
  provenance_links
  assembly_status : AssemblyComplete | AssemblyUnresolved | AssemblyRefused
```

The global checker (unchanged R16 machinery) consumes only the
`residue` field of an `AssemblyComplete` result and produces a
separate global certificate or unresolved result — the assembler never
computes, interprets, or short-circuits that judgement itself.

### Residue construction

For each oriented interface `e`:

```text
residue[e] = contribution(evidence_for(e))
```

only if `evidence_for(e)` exists as a `VerifiedInterfaceEvidence` whose
`admissibility` is `Decided Compatible`, whose `contribution` is
`Decided(value)`, and whose co-reference condition (§2) holds. The
assembler must not:

- invent a missing coordinate;
- silently replace an unresolved or incompatible contribution with zero;
- infer evidence from file or argument order;
- accept two different certificates for the same interface without an
  explicit resolution rule (there is none in this first version —
  duplicates are `AssemblyRefused`, §5);
- proceed to a confident global verdict while any required evidence is
  unresolved.

### Provenance links

Every residue coordinate retains a path back to its source evidence —
both halves:

```text
ProvenanceEntry
  residue_coordinate
  interface_id
  admissibility_certificate_id
  admissibility_certificate_digest
  contribution_certificate_id
  contribution_certificate_digest
  source_declaration_ids
  orientation
  transformation_applied
```

Minimum invariant:

> Every coordinate in the assembled residue is justified by an
> identified `VerifiedInterfaceEvidence` (both admissibility and
> contribution halves), and every certificate used by the assembly
> appears in `provenance_links`.

Stronger invariant, deferred rather than assumed:

> Every non-zero residue contribution has exactly one declared
> evidential derivation, unless an explicit composition rule records
> multiple contributors.

**For this first specification, require exactly one
`VerifiedInterfaceEvidence` per interface. Multi-certificate
composition is out of scope**, matching this project's own repeated
practice of not building a general theory before a specific one is
proved (compare `docs/design/GLOBAL_COHERENCE_CERTIFICATE_SPEC.md`
§2's identical scoping choice for the global bridge itself).

## 5. Admissible states

Three terminal states, matching the diagnostic vocabulary already
established by R13/R14 (`docs/design/TYPED_DIAGNOSTIC_CALCULUS.md`)
and `veribound-fce/src/coherence.py`'s existing `UNRESOLVED_GLOBAL_EVIDENCE`
constant — with `Incompatible` and `Unresolved` kept as **distinct**
terminal outcomes rather than collapsed into one failure state, per
the sharpened fourth obligation below.

### `AssemblyComplete(residue, provenance)`

Every required interface has one `VerifiedInterfaceEvidence` whose
admissibility is `Decided Compatible`, whose contribution is
`Decided(value)`, whose endpoints and orientation agree with the
topology, and whose co-reference condition holds. The residue may then
be passed to `global_coherence_certificate.build_certificate`.

### `AssemblyUnresolved`

**Procedural absence, not contradiction.** Use when: an interface's
evidence is missing entirely; either the admissibility or the
contribution half is `Unresolved`; a required declaration cannot be
matched; the topology is incomplete. No `Incompatible` finding is
present anywhere in the required set. Maps to `hold_for_review` — the
same mapping `UNRESOLVED_GLOBAL_EVIDENCE` already has in
`veribound-fce/src/policy.py`, extended one layer earlier in the
pipeline, not given new vocabulary.

### `AssemblyRefused`

**Positively contradictory or positively disallowed evidence**, kept
separate from mere absence:

- any required interface's admissibility is `Decided Incompatible`
  (this blocks the *whole* assembly, not just that coordinate — §0's
  governing constraint, `Incompatible(i) => assembly is not authorised`);
- two certificates claim the same interface with different contributions;
- certificate endpoints disagree with the topology;
- a certificate digest does not match its contents;
- the same certificate is illicitly reused for distinct interfaces;
- orientation metadata is internally contradictory;
- a co-reference condition fails (admissibility and contribution
  evidence name different interfaces or input states).

`Incompatible` producing `AssemblyRefused` is a genuine, decisive
finding (R15's `IncompatibleEvidence` is not malformed input, it is a
checked local-conflict witness) — not the same category as the
structurally-malformed cases in that list. **This document deliberately
does not assign a policy-tier mapping for `AssemblyRefused`.** The
existing pairwise layer itself has no policy verdict for `Incompatible`
yet (`veribound-fce/fce_check.py`'s pairwise-interface branch is
explicitly out of scope for policy, per
`[[veribound-fce-applied-layer]]`'s Phase B boundary) — this document
does not extend policy vocabulary unprompted, matching `src/policy.py`'s
own explicit "only the three existing tiers, reused verbatim" discipline.

```text
unresolved = insufficient evidence, no contradiction
refused    = proved inconsistency, or a decisive Incompatible finding
obstructed = valid evidence establishes non-removability   (existing, R16, unchanged)
cleared    = valid evidence establishes repairability       (existing, R16, unchanged)
```

`AssemblyUnresolved`/`AssemblyRefused` are assembly-layer states,
upstream of and distinct from `obstructed`/`cleared`, which remain
exactly R16's own two decisive outcomes — this document adds no new
vocabulary at that layer.

## 6. Invariants

1. **No silent contribution creation.** If no verified contribution
   certificate supports interface `e`, the assembler cannot create `r(e)`.
2. **Provenance completeness.** Every assembled residue coordinate
   names both certificates (admissibility and contribution) and the
   declarations it was derived from.
3. **Endpoint and co-reference agreement.** Declaration identifiers
   inside each certificate must agree with the topology's endpoints
   for that interface, and the two certificates' `interface_id`/
   `input_digest` must agree with each other (§2's co-reference
   condition) — not merely each independently agreeing with the topology.
4. **Orientation covariance.** Reversing interface `e` transforms its
   contribution by the declared reversal operation (sign negation):
   `r(reverse(e)) = -r(e)`. The global classification must be invariant
   under a consistent reorientation of the whole presentation.
5. **Ordering invariance.** Reordering the input certificates must not
   alter the assembled object.
6. **Duplicate rejection.** Two certificates cannot silently populate
   the same interface — this is `AssemblyRefused`, not last-write-wins.
7. **Verification gating.** Only certificates whose `verification_status`
   reflects a genuinely independent recheck (in-process verifier result,
   or an envelope re-verified before assembly) may enter — a stored
   string reading `"verified"` is not itself evidence, the same
   discipline `veribound-fce/fce_check.py`'s own fail-closed rework
   already established for the existing pipeline.
8. **No silent confidence gain, and no conflation of refusal with
   unresolvedness.** An unresolved admissibility or contribution input
   cannot become a confident `AssemblyComplete`, and an `Incompatible`
   finding cannot be downgraded to merely `AssemblyUnresolved` — the
   two terminal failure states are not interchangeable (§5). This is
   the applied analogue of `TYPED_DIAGNOSTIC_CALCULUS.md`'s
   `no_silent_soundness_gain`, sharpened with the Refuse-vs-Unresolved
   distinction that calculus already keeps separate for R14's own
   `ConflictDiagnostic`.
9. **Global-envelope consistency.** The final output must agree across
   assembled residue, global certificate, coherence verdict, policy
   verdict, and provenance links — an envelope-aware verifier
   (extending `global_certificate_verifier.verify_envelope`, not
   replacing it) must reject any disagreement.

## 7. First theorem targets

Two theorems, deliberately kept separate — a provenance claim and a
co-reference claim — neither of which is "the assembler computes the
correct obstruction." That remains R16's unchanged job, downstream:

```text
pairwise admissibility soundness (R15, unchanged)
  + contribution certificate soundness (later phase, not this one)
  -> co-reference consistency        (this document, §7b)
  -> assembly representation/provenance soundness  (this document, §7a)
  -> existing global certificate soundness (R16, unchanged)
  -> policy derived from verified global result (existing, unchanged)
```

### 7a. Representation and provenance soundness

Four concrete obligations, matching exactly what the assembler must
and must not do (§4's residue-construction rules restated as proof
obligations):

1. **No invention.** Every output coordinate has an input contribution
   certificate.
2. **No mutation.** The output value equals the certified value.
3. **No omission.** Every required compatible interface appears
   exactly once.
4. **No unauthorised assembly.** `Incompatible` admissibility evidence
   for any required interface prevents `AssemblyComplete` outright
   (`AssemblyRefused`); `Unresolved` evidence (with no `Incompatible`
   present) also prevents `AssemblyComplete`, but produces the
   distinct `AssemblyUnresolved` state, not `AssemblyRefused` — the
   two are not the same terminal result (§5, §6 invariant 8).

Informally, the headline statement:

> Every coordinate in an assembled residue originates from exactly one
> verified contribution certificate attached to an admissible
> interface instance, and the assembler neither creates, changes,
> drops, nor silently defaults any contribution.

```text
forall e, AssembledResidue.residue(e) = Contribution(certificate_for(e))
```

This does **not** claim the global verdict is correct — R16 already
does that, unchanged, once handed a residue. It proves only that the
residue handed to R16 was not invented, mutated, or silently defaulted.

### 7b. Co-reference consistency

A separate, weaker theorem — provenance consistency, not semantic
derivability (§2):

> Every contribution included in an assembled residue is traceable to
> the same interface instance and declaration state whose admissibility
> evidence authorised its inclusion.

Explicitly **not** claimed, and never to be confused with 7b:

> Admissibility evidence validates the contribution value.

The contribution checker (§2, §3) establishes the contribution's
correctness independently; 7b only establishes that the two evidences
being combined actually describe the same local situation.

**Corollary (provenance preservation).** For every assembled
coordinate, there exists a verified source certificate pair recorded
in `provenance_links` that supports exactly that coordinate.

**Negative theorem (no unsupported coordinate).** The assembler cannot
produce a coordinate for an interface absent from the verified
evidence assignment.

**Reorientation theorem.** A consistent reversal of interface
orientation transforms the residue as invariant 4 requires and
preserves the global obstruction classification.

**Target file, later phase (not this one — see §8):**
`rocq/PairwiseToGlobalAssembly.v`, importing
`rocq/PairwiseDiagnosticCertificate.v` and
`rocq/GlobalCoherenceCertificate.v` directly, adding whatever
`VerifiedContributionCertificate` Rocq type a later phase settles on,
rather than duplicating either existing file's content.

## 8. Recommended Phase 2 boundary and roadmap beyond this document

**Phase 2, narrowly defined** (not yet authorized by this document
alone — implementation begins only once this update itself is
confirmed, matching this project's standing per-phase authorization
discipline throughout `[[veribound-fce-applied-layer]]` and
`[[associator-fields-frozen-kernel]]`):

> Implement a provenance-preserving assembler over independently
> verified admissibility evidence (real R15 certificates) and typed
> contribution evidence (fixture stand-ins, decision 3, §9), using the
> four-cycle as the first integration fixture, without yet claiming
> Rocq-level contribution soundness.

Phase 2's output is the `AssembledResidue` object (§4), in
`veribound-fce`, in Python — **not** a Rocq theorem, and not a bare
residue vector handed to the global builder without its provenance.
The complete architecture Phase 2 targets:

```text
declaration pairs
  |
  +---> pairwise admissibility certificates (R15, real, unchanged)
  |
  +---> pairwise contribution certificates (fixture stand-in, decision 3)
              |
              v
     provenance-preserving assembly  (Phase 2, this document's target)
              |
              v
        certified residue (AssembledResidue)
              |
              v
   global repairability or obstruction evidence  (R16, unchanged)
```

The assembler does not infer compatibility, calculate undocumented
contributions, interpret global coherence, or turn absence of evidence
into zero. It only joins independently warranted facts without losing
their origin.

Later phases, listed for context only — not queued, not authorized by
this document:

```text
Phase 2   pure Python assembler, fixture contribution evidence,
          four-cycle integration cases (obstructed / repairable /
          missing evidence / endpoint mismatch / duplicate interface /
          orientation reversal / tampered provenance)
Phase 3   VerifiedContributionCertificate as a real Rocq type +
          its own soundness theorem (decision 1, §9) -- only once
          Phase 2's integration semantics are demonstrated in Python
Phase 4   rocq/PairwiseToGlobalAssembly.v: representation/provenance
          soundness (7a) and co-reference consistency (7b), now against
          the real contribution certificate rather than a fixture
Phase 5   certificate envelope extension + verifier
Phase 6   unit / exhaustive / end-to-end regression tests beyond
          Phase 2's own integration cases
Phase 7   evaluator-kit demonstration, only after both upstream releases
```

## 9. Decisions recorded (2026-07-12)

Three questions were left open when this document was first drafted;
all three are now decided, in response to the user's own reasoning,
recorded here so the resolution is traceable rather than silently
folded into the sections above.

**1. Does contribution need its own Rocq certificate type?**
Yes, eventually — but not before Phase 2's integration semantics are
demonstrated in Python (§8). The first formal object should be modest:
establish only "for interface `i`, under declared local input `x_i`,
the certified contribution is `c_i`" (§2, §3) — not the entire
associator derivation or application semantics. Kept strictly separate
from `PairwiseDiagnosticCertificate`; no numeric field is added to
`CompatibleEvidence`.

**2. Is a formal consistency proof required between the two evidences?**
Not as a theorem saying admissibility determines contribution — it
does not, in either direction. What is required is the co-reference
condition (§2, §6 invariant 3, §7b): both certificates must concern
the same interface and the same underlying declarations or local input
state, checked (and later proved) via matching identifiers/digests.
Domain-specific semantic constraints connecting the two may exist
later as additional, explicitly named theorems — not assumed generic
architecture.

**3. Should the first integration case use real certificates or fixtures?**
Both, split by role: real R15 admissibility certificates for all four
declaration pairs, and typed fixture contribution certificates
(`FixtureVerifiedContribution`, §3) independently reproducing
`r = (1, 1, 1, -2)` via `associator_residue.py`'s existing
double-checked computation. Bare scalar fixtures alone would bypass
the provenance architecture under test; requiring the full Rocq
contribution certificate first would make the formal design depend on
an assembler that has never been exercised. The fixture type and the
assembler's boundary already match the eventual proof-carrying
version's shape, so replacing the fixture verifier later does not
alter assembly semantics.

## 10. What is not claimed

- **No production code yet.** No `assemble_global_evidence()`, no new
  Python dataclasses, no new Rocq file — this document specifies;
  Phase 2 (§8) is the next, separately-confirmed step.
- **No claim that admissibility determines or validates contribution**
  (§2, §7b) — the co-reference condition is provenance consistency,
  not semantic derivability.
- **No multi-certificate composition per interface** (§4) — exactly
  one `VerifiedInterfaceEvidence` per interface for this first version.
- **No policy-tier mapping for `AssemblyRefused`** (§5) — the existing
  pairwise layer itself has none for `Incompatible` yet; this document
  does not extend policy vocabulary unprompted.
- **No claim that this generalises beyond the four-cycle topology.**
  The four-cycle remains the first and, for this document, only
  concrete integration target.
- **No evaluator-kit, `veribound-fce` pipeline, or CI change.** Those
  are later phases in the broader plan this document is Phase 1 of.
- **No claim about raw sensor truth.** The chain begins with
  already-normalised source declarations, exactly as
  `veribound-fce/fce_check.py`'s own existing scope note already states
  for the pipeline stages it touches.
