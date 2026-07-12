# The Contribution Judgement: What a Verified Contribution Certificate Must Establish

**Status (2026-07-12): Phases 3A, 3B, and 3C are all complete.** Phase
3B (`rocq/AssociatorContributionCertificate.v`) — see that file's
header for its two honest scoping decisions (the registered
orientation is a *stipulated* convention checked against
`FourCycleObstruction.v`'s `r`, not derived from `delta0`'s formula;
`associatorContribution` formalises `closed_form_delta`'s arithmetic,
not `associator_defect`'s full expansion). Phase 3C —
`ocaml/associator_contribution_checker.ml` (this repository) and
`veribound-fce`'s `src/associator_contribution_verifier.py` (commit
`f672f1e`) independently implement and agree on a fourteen-case parity
corpus; real verified contribution certificates now back
`veribound-fce`'s primary four-cycle integration path, with
`src/pairwise_to_global_assembly.py` unmodified (confirmed by an empty
`git diff`). See `STATUS.md` §1 for the theorem-by-theorem summary.
Phase 4 (operational integration into `fce_check.py` and the
certificate envelope) remains unstarted. This document exists to
answer one question, asked before any `VerifiedContributionCertificate`
type or verifier was written:

> What must a witness establish, and what data must it bind, for a
> rational scalar to count as the contribution of a particular
> registered interface, rather than merely a number attached to that
> interface?

Phase 2.5 proved the middle of three levels this whole bridge keeps
deliberately separate:

```text
pairwise admissibility  !=  provenance-preserving assembly  !=  semantic correctness of contributions
```

It establishes that a completed assembly represents every required
interface exactly once, preserves order, invents nothing, and binds
admissibility and contribution evidence to the same registered
interface instance. It does **not** establish that the scalar attached
to an interface is mathematically the correct associator contribution
— that is this document's subject.

**A confirmation, not a new finding**: the correction Phase 2.5 made to
`AssemblyUnresolved`'s scope (it is a claim about the classification
*reached* under the algorithm's precedence for each required
interface, not a claim that no `Incompatible` certificate exists
anywhere in the raw input) is exactly the right theorem for the
implemented semantics, and needs no further change here.

## 1. The governing judgement

```text
ValidContribution(Gamma, i, x, c, w)
```

read: *under registered context `Gamma`, interface `i`, and committed
input `x`, witness `w` establishes that the interface contribution is
exactly `c`.*

The rest of this document is about what `Gamma` and `x` actually have
to be — not about field names. Field names are derived at the end
(§6), from the answer, not guessed first.

## 2. Is the contribution genuinely local? Checked against the real code, not assumed

Before answering "what belongs in `Gamma`," it is necessary to check
what the *existing*, already-checked-twice computation
(`associator_residue.py`'s `compute_seam_residue`,
`regional_composition.py`'s `associator_defect`/`closed_form_delta`)
actually depends on — the same discipline that found the admissibility
vs. contribution split in Phase 1's own §1.

### 2a. No cross-seam data enters the computation

`four_cycle_instances()` builds **four entirely separate**
`SeamAssociatorInstance` objects, one per seam, and
`compute_seam_residue(instance)` is a pure function of that one
instance — its own `VennTriple` and its own `SeamCorrectionData`. No
other seam's data is read. `SeamAssociatorInstance`'s own docstring
states this explicitly: "`triple` defaults to the shared Venn shape of
Example ex:venn; distinct seams **may in principle use distinct
triples**, but all four witnesses below reuse the same shape with
different constants, exactly as multiple independent instances of one
construction." Reusing the same `VennTriple()` default across all four
seams in the existing fixture is a convenience, not a mathematical
requirement — nothing enforces or needs a shared regional carrier
across interfaces.

**Conclusion**: no "shared regional context spanning multiple
interfaces" belongs in `Gamma`. This rules out the heaviest reading of
the governing question at the top of this document — the contribution
function does not need the whole cover or cycle as an argument. The
assembler (already built, Phase 2) is exactly what supplies the
surrounding cycle structure; the per-interface contribution function
does not also need to know it.

### 2b. But the local instance already encodes an unchecked orientation-like choice

`associator_defect(triple, mu)` computes the *associator* of an
**ordered** triple `(U, V, W)`:

```text
alpha = a *_{U,VvW} (b *_{V,W} c)  -  (a *_{U,V} b) *_{UvV,W} c
```

— manifestly asymmetric in `U, V, W` (a specific left-nested vs.
right-nested product structure, not a symmetric function of an
unordered set). The four seam-correction constants
(`mu_VW`, `mu_U_VvW`, `mu_UV`, `mu_UvV_W`) attach to four *specific,
non-interchangeable* positions in that ordered expansion, and
`closed_form_delta` cross-checks the result against exactly the
alternating-sign four-term formula:

```text
Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV
```

`four_cycle_instances()`'s own docstring names the free choice this
creates directly: "Each instance sets exactly one of the four
seam-correction constants to the target value and the other three to
zero — **a free modelling choice of which pairwise reconciliation
carries the seam's residue**." Setting `mu_VW := target` and setting
`mu_UV := target` (with the other three zero in both cases) produce
`target` and `-target` respectively, from the closed form's own `+1`
and `-1` coefficients. This is a genuine sign/orientation-like choice,
and it is currently made *implicitly*, by which field of
`SeamCorrectionData` happens to be nonzero — `SeamAssociatorInstance`
has no explicit orientation field at all.

**Conclusion, the central finding of this document**: the contribution
*is* a pure function of one seam's own committed local input, in the
narrow sense that no other seam's data enters the computation — but
that local input's own internal structure already contains an
unchecked orientation-like degree of freedom, and nothing today
verifies that a given committed instance's implicit choice agrees with
any registered convention for that interface. Two independently
authored, individually well-formed `SeamAssociatorInstance` values for
"the same" nominal interface could legitimately compute to `c` and
`-c` respectively, and nothing in the current code — Python or the
Phase 2 assembler — would catch the disagreement, because `local_input
_digest` (Phase 2's field) only has to match *itself*, not commit to
which slot was used.

This answers the milestone question stated at the top of this
document precisely: contribution is determined by an interface's own
local committed state — **not** by a shared regional carrier spanning
several interfaces — but that local state must itself be checked
against a **registered, canonical orientation** for the assembly layer
to be sound, because the local state alone cannot distinguish a
correctly orientated contribution from its negation. This is a
narrower and more precise claim than "the latter" (a shared context) —
grounded in what the real code actually depends on, not a restatement
of the original hypothesis.

### 2c. Checking the other candidate dependencies named in the governing question

For completeness, the remaining candidates the question raised,
checked one at a time against the real code:

- **restriction maps** — internal to computing one seam's own defect
  (`restrict`, `raw_overlap_product`), not a dependency on anything
  outside that one seam's instance.
- **the ordered triple or composition path** — confirmed load-bearing,
  §2b above. Already captured by `VennTriple` + the specific nesting
  `associator_defect` performs; not an extra argument beyond what a
  `SeamAssociatorInstance`-shaped `x` already carries.
- **orientation or sign convention** — confirmed load-bearing, §2b.
  Not currently represented explicitly anywhere; this document's main
  proposal (§4) is to make it explicit.
- **generator data** — the `mu` constants themselves are exactly this;
  already part of the committed local instance.
- **the surrounding cover or cycle** — needed to interpret four
  contributions *together* as an obstruction (§2a); not needed to
  compute or verify any single one. Already the assembler's job, done.
- **the declaration state being compared** — this is R15's
  admissibility vocabulary (`Key -> option Value`), a genuinely
  separate concern from associator contribution computation (Phase 1's
  own §1a/§1c finding) — not applicable here at all.

## 3. What `Gamma` actually has to be

Given §2, `Gamma` does not need to be a large, separately-designed
"regional context" object. It reduces to exactly the Phase 2.5
registry entry for interface `i`, extended with the one piece of
information §2b shows is missing:

```text
Gamma(i) = RequiredInterface {
  interface_id      : InterfaceId          (* Phase 2.5, unchanged *)
  registered_digest  : Digest               (* Phase 2.5, unchanged *)
  registered_orientation : Orientation      (* NEW -- see section 4 *)
}
```

`x` (the committed input) is the seam's own local instance data — for
the associator-specific case, structurally a `SeamAssociatorInstance`
(an ordered triple plus its four correction constants), or a digest
that commits to exactly that structure (§5).

**This is a strengthening of `RequiredInterface`, not an incidental
schema edit** — recorded as such per this document's own governing
discipline (compare `PAIRWISE_TO_GLOBAL_PROVENANCE.md`'s own habit of
naming architecture decisions explicitly rather than folding them
into a field list unremarked).

## 4. Orientation: representation decision

Three options were on the table; §2b supplies a concrete, code-grounded
reason to choose among them, not merely a preference.

1. **Oriented interface identifiers** (the identity itself contains
   source/target). Rejected: this would require re-deriving `e12` vs.
   `e21`-style naming for every interface, duplicating information the
   registry already owns, and would not by itself stop a contribution
   certificate from silently using the wrong slot — the certificate's
   own local instance data still needs *some* explicit orientation
   marker to check against, so this option does not actually remove
   the need for §4's real content, it only relocates where the
   canonical value lives.
2. **Explicit orientation field on the certificate alone**, unchecked
   against anything external. Rejected: this is exactly the "two
   independently authored certificates silently disagree by a sign"
   failure mode §2b identified — an unchecked self-reported field adds
   no safety over today's implicit, unchecked choice.
3. **Canonical orientation from the registry, checked against the
   certificate's own declared/derived orientation.** Adopted. The
   registry (`RequiredInterface`) is already Phase 2.5's co-reference
   ground truth for `interface_id` and `digest` — extending it with
   `registered_orientation` and requiring the contribution verifier to
   check the committed instance's own orientation against it is the
   same mechanism Phase 2.5 already uses for digest co-reference,
   applied to the one additional fact §2b shows is needed.

`Orientation` for the associator-specific model is concretely: *which
of the four `SeamCorrectionData` slots is the target-bearing one* —
equivalently, given the closed-form's own coefficients, a value in
`{+1, -1}` naming whether the committed instance's nonzero slot
carries coefficient `+1` (`mu_VW` or `mu_U_VvW`) or `-1` (`mu_UvV_W` or
`mu_UV`) in `Delta = mu_VW - mu_UvV_W + mu_U_VvW - mu_UV`. The generic
layer (§5) only needs `Orientation` to be *some* type the registry and
the certificate both refer to and can be checked for equality — it
does not need to know this associator-specific meaning.

**Reorientation theorem, stated but not yet proved (deferred to Phase
3B, §7):**

```text
reverse(i, c) = (i^op, -c)
```

for whatever `i^op` (the registry's reversed-orientation counterpart of
`i`) turns out to mean once `Orientation` has a concrete type. Not
claimed here — `PAIRWISE_TO_GLOBAL_PROVENANCE.md` §7 already left this
exact theorem unproved for the same honest reason (no orientation
structure existed yet); this document supplies the structure, a later
one proves the theorem.

## 5. Generic envelope vs. model-specific validity

Two layers, per the user's own explicit instruction not to force the
associator mathematics into a supposedly generic certificate:

### Generic certificate envelope (assembler-facing, model-agnostic)

```text
VerifiedContributionCertificate
  interface_id
  registered_digest        (* checked against Gamma(i), as today *)
  committed_input_digest    (* NEW name for local_input_digest, see below *)
  contribution : Q
  witness : Witness          (* opaque at this layer *)
  verification_status
```

`veribound-fce`'s Phase 2 assembler (`src/pairwise_to_global_
assembly.py`) and `rocq/PairwiseToGlobalAssembly.v` (Phase 2.5) both
already operate at exactly this layer and need **no change** — they
consume a `VerifiedContributionCertificate`-shaped object and never
inspect `witness`. This is the whole point of keeping `Witness` opaque
in Phase 2.5: the generic assembler stays permanently decoupled from
any one mathematical source of contributions, associator or otherwise.

**Renaming note**: Phase 2's `local_input_digest` is renamed here to
`committed_input_digest` in the generic envelope's own vocabulary,
because §2b's finding changes what that digest has to commit to (§6) —
this is a documentation/intent clarification, not yet a code change;
Phase 3B decides whether the Python/Rocq field itself is renamed or
kept with a clarified docstring.

### Model-specific validity relation (associator-specific, Phase 3B)

```text
AssociatorContributionValid(Gamma, i, x, c, w)
```

For the first implementation, `x` is (or digests) a
`SeamAssociatorInstance`-shaped object — `(U, V, W)` and the four `mu`
constants — and the relation specifies exactly how `c` is derived from
that data via `associator_defect`, matching thm:triple-localisation's
already-verified support condition (the defect is supported on the
single-point triple overlap; `compute_seam_residue` already checks
this, raising if not). Scoped narrowly and concretely to this one
family, not a formalisation of the whole regional obstruction
calculus — matching every other bridge document in this project's
practice of proving the abstraction against one worked instance before
generalising (`GLOBAL_COHERENCE_CERTIFICATE_SPEC.md` §2 makes the same
scoping choice for the global bridge).

The associator-specific verifier is responsible for producing a
generic `VerifiedContributionCertificate`; the generic assembler is
never extended to know about `VennTriple`, `SeamCorrectionData`, or
`associator_defect` at all.

## 6. What `committed_input_digest` must commit to

Given §2b, a digest that commits only to an opaque label (as Phase 2's
fixture `local_input_digest` currently does — a caller-assigned linking
token, explicitly documented as "not a hash of shared raw data" in
`tests/four_cycle_assembly_fixtures.py`) is **adequate for Phase 2's
own co-reference purpose** (linking an admissibility certificate to a
contribution certificate for the same nominal interface) but
**insufficient as the final semantic binding** a sound contribution
certificate needs, because it does not commit to the one thing that
actually determines the sign: which correction-constant slot was used.

For the associator-specific model, `committed_input_digest` must
commit to the full local instance:

```text
(U, V, W, mu_VW, mu_UvV_W, mu_U_VvW, mu_UV)
```

— equivalently, a digest of the `SeamAssociatorInstance` itself. This
is not a new requirement invented for its own sake (this document's
own §4 warns against adding fields merely because they seem useful);
it is the minimum needed for `AssociatorContributionValid` to be
well-defined at all, since a digest that dropped, say, the triple's
identity could not distinguish two structurally different instances
that happen to produce the same numeric `c` by coincidence.

## 7. What the witness proves, and the trusted boundary

Per the user's own instruction: agreement between two independent
implementations is useful testing evidence, but it is not yet the
mathematical relation. The first Rocq contribution theorem (Phase 3B,
not this document) has the shape:

```text
verifyContribution(x, cert) = true  ->  AssociatorContributionValid(Gamma, i, x, cert.contribution, cert.witness)
```

with `AssociatorContributionValid` defined *independently* of
`verifyContribution` — the same generator/checker independence
discipline already load-bearing throughout this project (R15/R16's own
untrusted-builder/independent-verifier split; Phase 2's `pairwise_
certificate_verifier.py` never importing `build_certificate`). The
first concrete instance: prove `c_i = compute_seam_residue(x)`'s
already-Python-checked value equals a formally defined
`assocContribution(Gamma, i, x)` Gallina function, for the four
committed instances `four_cycle_instances()` already supplies — a
narrow, concrete target (§5), not a mechanisation of
`regional_composition.py` wholesale.

## 8. What this document settles vs. defers

**Settled here:**

- The contribution function's exact mathematical arguments (§2, §3):
  no shared regional context across interfaces; a per-interface
  committed local instance; an orientation check against the registry.
- Orientation representation: canonical registry orientation, checked
  against the certificate (§4), for the specific, code-grounded reason
  §2b gives — not merely because it seemed like the cleanest fit.
- What the digest commits to (§6): the full local instance, not an
  opaque label.
- The generic/model-specific split (§5) and the generic envelope's
  exact shape — unchanged from what the already-built assembler
  consumes.
- The verifier's trusted boundary and the first theorem's shape (§7).

**Deferred, explicitly not started by this document:**

- The actual Rocq `Orientation` type, `SeamAssociatorInstance`-shaped
  `x` type, `AssociatorContributionValid` relation, certificate type,
  decidable verifier, and soundness theorem — Phase 3B.
- The reorientation theorem (§4) — stated, not proved.
- An independently authored runtime parity checker for the new
  certificate, and replacing Phase 2's fixture contribution evidence
  with it in the integration path — Phase 3C, only after Phase 3B.
- Wiring pairwise verification -> contribution verification ->
  assembly -> global obstruction checking into `fce_check.py` or the
  certificate envelope — Phase 4, only after Phase 3C.
- Any change to `veribound-fce`'s actual `src/contribution_fixture.py`
  or `src/pairwise_to_global_assembly.py` — both remain exactly as
  Phase 2 left them; this document proposes a vocabulary clarification
  (`committed_input_digest`, §5) for Phase 3B to act on, not an
  immediate rename.

## 9. Open question — resolved in Phase 3B

`SeamAssociatorInstance` in the existing Python code has no explicit
orientation field — the choice is currently implicit in which `mu_*`
slot is nonzero, and `four_cycle_instances()` never states an explicit
"this is the canonical positive direction for `e12`" declaration
anywhere, because nothing has ever needed to check it before. This
document left open whether the registry's canonical orientation should
be chosen freshly or derived from `FourCycleObstruction.v`'s
`coboundary_0` matrix.

**Resolution (`rocq/AssociatorContributionCertificate.v`, header
Decision 1)**: neither, exactly — `delta0` (an abstract coboundary map
on four formal vertices, signs from graph incidence) and
`associator_defect` (a three-region Venn-algebra construction, no
vertices or incidence structure at all) are different mathematical
objects with no a priori structural connection, so there is no formula
to derive the slot choice *from*. The registered orientation is a
**stipulated** convention (a `Slot` value per registered interface),
chosen freely exactly as `four_cycle_instances()`'s own slot choice
already was — but then **checked**, not assumed: `registry_orientation
_agrees_with_delta0` proves the four contributions this stipulated
convention produces, assembled in `FourCycleObstruction.v`'s own
`SEAM_ORDER`, equal that file's own `r` constant exactly. This is the
sense in which "derived from `delta0`" ultimately cashes out — a
checked agreement with the existing global theory's own committed
values, not a structural derivation from its formula.
