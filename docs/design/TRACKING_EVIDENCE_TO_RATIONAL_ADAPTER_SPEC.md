# Tracking Evidence to Rational Adapter: Exact Semantics (first Meridian domain adapter)

**Status (2026-07-16): design, now reviewed against the real R21
pipeline. No adapter code, no Stone Soup dependency, and no `rocq/*.v`
file should be written from this document until a go-ahead names which
section to implement first.** This document exists to answer, before a
single Stone Soup object is imported, what a tracking disagreement
*means* in this calculus's terms, which corrections are *permitted*, and
why solvability of `Db = r` represents *global repairability* of a set
of local-track comparisons -- not to reproduce an operational tracker.

**Review (2026-07-16, same day): a read-only audit plus bounded,
untracked spikes (§20) found and fixed one real sign error in §4/§7's
correction semantics** -- the originally-stated additive correction
`s_i' = s_i + b_i` does not actually resolve any comparison edge when
`Db = r`, confirmed by direct computation, not merely inspection; the
corrected subtractive form `t_i := s_i - b_i` does. Both fixtures (§13)
were reconstructed from genuine per-edge transformation data (not
literal residue insertion) and run through the real `roc-solve` and both
real independent R21 checkers, which all accepted. §20 records exactly
what was and was not exercised by this review.

The governing question:

> Under an explicit track-comparison and correction policy, what must be
> preserved from tracking evidence so that `Db = r` is equivalent to
> simultaneous repair of the declared pairwise discrepancies, and so
> that an R21 separator has a precise operational interpretation?

## 0. What already exists in this repository, checked directly, not assumed

This is not a fresh domain. R21 (`rocq/ExactRationalRepairOrSeparator.v`,
`r21_certificate_format.py`, `r21_certificate_checker.py`,
`r21_certificate_emitter.py`) already has a fixed, working input/output
interface this adapter must target exactly, not redesign:

- **`roc-input/v1`** (`r21_certificate_format.py`): `{"schema":
  "roc-input/v1", "D": [[<rational strings>, ...], ...], "r":
  [<rational strings>, ...]}` -- `D` is `m` rows by `n` columns,
  matching this document's own row/column convention below.
- **Rational strings are `a/b` or bare integers ONLY**
  (`_RATIONAL_RE = r"^-?[0-9]+(/[0-9]+)?$"`, `r21_certificate_format.py`
  line 95) -- **decimal notation is explicitly rejected** by R21's own
  parser. This is a real interface boundary this document must resolve,
  not paper over: §9 states exactly where the adapter's own
  decimal-string canonicalisation ends and where conversion to exact
  `a/b` strings must happen before anything is handed to R21.
- **`repair-or-separator/v1`** certificate schema: `{"schema": ...,
  "input_digest": "sha256:<hex>", "result": "repair"|"separator",
  "repair": [...] | "separator": [...]}`, bound to its `(D, r)` via
  `canonical_input_digest` (`r21_certificate_format.py` line 208). Any
  adapter certificate (§15) must chain to this digest, not invent a
  parallel one.
- **The repository's own four-cycle example already fixes the
  orientation convention this document's comparison graph must match**
  (`examples/four_cycle.json`, `rocq/FourCycleObstruction.v`,
  `rocq/R21CycleQuotientBridge.v`'s `FourCycleExample`,
  `rocq/R24CertificateTransportExamples.v`'s `D4`/`r4`/`y4`): four
  objects `U1..U4`, four edges in row order `(e12, e23, e34, e14)`, each
  oriented edge `i -> j` contributing row `(..., -1 at column i, ...,
  +1 at column j, ...)` (i.e. `(Db)_{ij} = b_j - b_i`), matching

  ```text
  D = [[-1,  1,  0,  0],
       [ 0, -1,  1,  0],
       [ 0,  0, -1,  1],
       [-1,  0,  0,  1]]
  ```

  with the canonical obstructed residue `r = (1, 1, 1, -2)`. R21/R24
  represent the separator as `y4 = (1/5, 1/5, 1/5, -1/5)` (`dot_qc y4 r4
  = 1`, the *normalized* pairing R21's own certificate schema expects);
  the paper's own presentation (`FourCycleObstruction.v`) instead uses
  the un-normalized cycle `z = (-1, -1, -1, 1)` with `<z, r> = -5`. Both
  are valid separators for the same obstruction (`y4 = -(1/5) * z`); §7
  and §12 use `y4`'s normalized form, since that is what R21's certificate
  schema (`result: "separator"`, pairing exactly `1`) actually requires.
- **No existing file in this repository defines a tracking domain
  object, a comparison-edge concept, or a snapshot/provenance schema.**
  Everything in §2-§11 below is new content this document scopes for
  the first time; §0 exists only to fix what this new content must be
  consistent with, not to claim any of it already exists.

## 1. Freeze the scope of the first adapter

The first adapter analyses compatibility among several local tracks
asserted to describe **one physical target at one common evaluation
time**. Deliberately excluded from the first version, each because it
adds a dimension of complexity orthogonal to the semantic question this
document exists to settle:

- more than one target hypothesis;
- more than four local trackers/observation sources;
- more than one fixed timestamp;
- more than a two-dimensional position state (velocity comes after
  position works, per below);
- inexact (non-terminating or floating-point) values;
- nondeterministic coordinate transformations;
- clutter, missed detections, classification uncertainty, probabilistic
  association, Kalman-filter internals;
- any live Stone Soup dependency (§16, §17);
- a track set that changes within one snapshot.

State type for the first version:

```text
x_i = (p_x_i, p_y_i)   -- position reported by tracker i,
                          transformed into a declared common frame
```

Velocity is a later extension; covariance is recorded as provenance
(§8) but does not yet enter any equation.

## 2. Domain objects

The adapter needs these explicit objects before it constructs any
matrix -- code that builds `D`/`r` directly from ad hoc dictionaries,
skipping this layer, is exactly the failure mode §0's "no existing
tracking domain object" gap would otherwise let happen silently.

### 2.1 Source

Identifies the originating sensor or replay stream: `source_id`, sensor
modality, platform identity, source-data digest, source timestamp,
declared coordinate frame, measurement-model identity.

### 2.2 Detection

An observation produced directly from a source: `detection_id`,
`source_id`, timestamp, state values as canonical decimal strings (§9),
coordinate-frame identity, transformation history, optional covariance,
source-record digest.

### 2.3 Local track

A tracker's state estimate derived from one or more detections:
`track_id`, `tracker_id`, evaluation timestamp, state values,
state-space definition, contributing detection IDs, ancestry record,
transformation record, local-track digest.

### 2.4 Declared comparison edge

Asserts that two local tracks are being compared under the hypothesis
that they describe the same physical target: `edge_id`, source track,
target track, orientation, comparison-space identity, transformation
used, calculated discrepancy, **provenance for the co-reference
hypothesis itself**. This last field is not optional bookkeeping: the
mere existence of two tracks never justifies comparing them, and an
edge without a recorded co-reference claim is not a valid input to §5.

### 2.5 Adapter snapshot

Freezes all evidence used for one decision: schema version, scenario
ID, fixed evaluation time, all sources, detections, local tracks,
comparison edges, transformations, ancestry, quantisation policy,
adapter policy, canonical evidence digest. **The snapshot -- not any
Stone Soup object -- is the authoritative adapter input**, exactly as
`roc-input/v1` (not any Python solver's internal state) is R21's
authoritative input.

## 3. The comparison graph

The first fixture uses four trackers in the cycle `T1-T2-T3-T4-T1`,
oriented edges `e12, e23, e34, e14` (`i -> j` orientation fixed and
documented, matching §0's existing convention exactly, column order
`(T1,T2,T3,T4)`):

```text
D = [[-1,  1,  0,  0],
     [ 0, -1,  1,  0],
     [ 0,  0, -1,  1],
     [-1,  0,  0,  1]]
```

Columns are permitted corrections to the four local tracks; rows are
the effect of those corrections on the four pairwise discrepancies.
This interpretation is stated here, in the design document -- not left
implicit in adapter code, which is exactly the gap that made §0's
citations necessary in the first place.

## 4. Correction variables

**This section originally stated the corrected value as `s_i' = s_i +
b_i` (additive). §20 records that this is sign-inconsistent with §7's
theorem and was caught only by computing a concrete example, not by
inspection -- the corrected formula is below, kept in this numbered
section (not silently fixed) precisely because the wrong version was
load-bearing prose, not a typo isolated to one line.**

For tracker `i` reporting scalar value `s_i`, introduce a correction
variable `b_i`, understood as *the estimated registration bias present
in track `i`'s value*. The corrected (bias-removed) value is:

```text
t_i := s_i - b_i
```

For oriented comparison `i -> j`, resolving the edge means the two
tracks' corrected values agree, `t_i = t_j`, i.e. `s_i - b_i = s_j -
b_i`... equivalently `b_j - b_i = s_j - s_i`. Collecting all edges'
right-hand sides gives exactly `r` (§5) on one side and `Db` on the
other -- this is why `Db = r`, not `Db = -r`, is the correct resolution
condition given §5's `r_ij := s_j - s_i` and the fixed graph orientation
already established in §0/§3; see §20 for the numeric check that
confirmed it.

**`b_i`'s meaning is fixed, for the first adapter, to exactly one
thing**: *an admissible additive registration correction to local track
`i` in the declared common comparison space.* It explicitly does NOT
mean: changing the physical target; retraining the detector; changing a
classification; altering covariance; deleting an observation; selecting
a different association; overriding a sensor value without provenance.
Those may become later correction classes (a later document's problem,
not this one's) -- conflating them with `b_i` now would make the
semantic theorem in §6 true of a different, unstated correction policy.

## 5. The residue construction problem -- the central design question

For oriented edge `i -> j`, the observed discrepancy is `r_{ij} = s_j -
s_i` (or its sign-reversed counterpart, fixed to match §0's convention).
**If every `r_{ij}` is computed directly from one globally available
collection of scalar states `s_1, ..., s_4`, then `r` is automatically a
coboundary, `r = Ds`, and no fixture built this way could ever be
genuinely obstructed** -- it would only rediscover that ordinary
coordinate differences telescope to zero around a cycle. This is not a
minor implementation detail; it is the reason a naive adapter
("difference the four already-known positions") cannot produce the
obstructed fixture §12 needs, and any adapter design that does not
address it has not yet defined real semantics.

The residue must therefore be capable of carrying **context-dependent
information not reducible to one global assignment**. Candidate
sources: pair-specific transformations; inconsistent frame
registrations; different temporal projections; pairwise association
claims produced in different contexts; local fusion outputs with
overlapping provenance; edge-specific corrections; incompatible
state-space mappings.

## 6. The chosen construction: pair-specific coordinate transformation

**Recommended first construction.** Each tracker has local state `x_i`;
each comparison edge has its OWN declared transformation into a
comparison space, `F_ij^(i)` and `F_ij^(j)` (not one shared global
frame map per tracker):

```text
r_ij = F_ij^(j) x_j  -  F_ij^(i) x_i
```

If the `F`s are all induced by one coherent family of global frame maps,
the cycle residue is repairable. If the per-edge transformations are
each *locally plausible* (individually defensible frame registrations)
but *globally inconsistent* (no single per-tracker correction reconciles
all four simultaneously), the residue may be obstructed. This gives the
obstruction a defensible tracking meaning:

> The pairwise track comparisons cannot all be reconciled by assigning
> one admissible correction to each local track.

-- rather than an arbitrary manufactured vector with no domain content.

## 7. The semantic theorem (now checked by hand against concrete numbers, not yet a Rocq theorem)

> Given a fixed comparison graph, canonical local-track states,
> certified pairwise transformations, and the bias-removal correction
> variables of §4 (`t_i := s_i - b_i`), `Db = r` holds exactly when
> there exists a collection of permitted local corrections that
> simultaneously resolves every declared pairwise discrepancy (`t_i =
> t_j` for every edge `i -> j`).

Two directions, both needed -- the backward direction is not a
formality: without it, `Db = r` might describe *one sufficient* repair
mechanism without describing *every* repair the domain policy actually
permits, silently narrowing what "repairable" means relative to what
the tracking domain intends. Both are now short, direct derivations from
§4/§5's fixed definitions (not assumed):

- **Forward**: given `Db = r`, i.e. `b_j - b_i = s_j - s_i` for every
  edge, rearranging gives `s_i - b_i = s_j - b_j`, i.e. `t_i = t_j` --
  every edge resolves.
- **Backward**: given `t_i = t_j` (i.e. `s_i - b_i = s_j - b_j`) for
  every edge, rearranging gives `b_j - b_i = s_j - s_i = r_ij` for every
  edge, i.e. `Db = r`.

§20 confirms both directions numerically on the repairable fixture (§13.1):
applying `t_i := s_i - b_i` with the fixture's own `b = (0,1,3,2)`
resolves all four edges to the identical corrected value; the additive
form `s_i + b_i` this section originally stated does **not** resolve
any edge, confirming the fix was necessary, not cosmetic. This is stated
here as the target semantic claim for the adapter specification to
defend precisely (with the domain-object definitions of §2 and the
corrected policy of §4 as its exact hypotheses) -- it is not a Rocq
theorem yet, and nothing in this document should be read as claiming a
machine-checked proof exists.

## 8. The separator's tracking meaning

If R21 returns `y` with `D^T y = 0` and `y . r = 1` (R21's own
normalized certificate form, §0), its adapter-facing translation is
fixed to:

- `y` is a weighted cycle of declared track comparisons;
- `D^T y = 0` means every permitted per-track correction cancels around
  that weighted cycle;
- `y . r <> 0` means the observed pairwise discrepancies do not cancel;
- therefore no collection of permitted local corrections resolves all
  comparisons simultaneously.

Plain-language rendering required in any adapter report: "The
certificate identifies a closed chain of track comparisons whose
accumulated discrepancy survives every permitted correction to the
individual tracks." §13.2's obstructed fixture gives the concrete
instantiation of this rendering, using the repository's own `y4`.

## 9. Provenance obligations

For each residue row: comparison-edge ID, two track IDs, two source
identities, transformation identity and parameters, comparison-space
identity, timestamp policy, quantised input values, exact rational
values, formula used, resulting residue component. For each matrix
column: correction-variable identity, affected track, correction-space
identity, units, permitted operational meaning. For each matrix entry,
the adapter must be able to answer: *why does this correction variable
affect this comparison equation by this coefficient?* If that cannot be
reconstructed independently of the code that produced it, the matrix is
not yet proof-carrying, no matter what R21 says about it.

## 10. Canonical number conversion -- and the exact rational-string boundary

The snapshot layer (§2, §11) uses canonical, human-auditable
**decimal** strings: no floating point, a single declared rounding rule,
a fixed decimal-place count per field family, no exponent notation,
normalized zero, no `NaN`/infinity, explicit units:

```json
{
  "quantisation_policy": {
    "position_decimal_places": 6,
    "transform_decimal_places": 9,
    "rounding_mode": "half_even",
    "number_format": "plain_decimal_no_exponent"
  }
}
```

**This is NOT the format R21 accepts** (§0: R21's `_RATIONAL_RE` rejects
decimal notation outright). The adapter's derived-problem construction
(§11) must therefore perform an explicit, auditable conversion step --
each canonical decimal string parsed to an exact `Fraction`, then
rendered as R21's own `a/b`/integer string form -- before any `D`/`r`
entry is handed to `roc-input/v1`. This conversion step is itself part
of what the adapter certificate (§15) must attest to, since a rounding
or parsing bug here is exactly the kind of defect that would corrupt
`D`/`r` before R21 ever sees a malformed problem, not a bug R21's own
checker could ever catch (it only ever sees the post-conversion
rationals). The exact claim is restricted accordingly:

> The certificate proves repairability or obstruction of the canonical
> rationalised evidence snapshot under the declared adapter policy. It
> does not prove that an unquantised physical system is obstructed.

## 11. The canonical snapshot schema

```json
{
  "schema_version": "tracking-adapter/v1",
  "scenario_id": "four-track-obstructed-001",
  "evaluation_timestamp_utc": "2026-01-01T00:00:00Z",
  "state_space": {},
  "quantisation_policy": {},
  "correction_policy": {},
  "sources": [],
  "detections": [],
  "tracks": [],
  "transformations": [],
  "comparison_edges": [],
  "provenance": [],
  "derived_problem": { "D": [], "r": [] },
  "payload_digest": ""
}
```

`derived_problem` may be present for convenience but is **not trusted**
-- the independent verifier (§12) must recompute both `D` and `r` from
the evidence fields, never read them off this field, exactly as R21's
own checker recomputes `Db`/`D^Ty` rather than trusting a supplied
verdict.

## 12. The independent adapter verifier

The single most important component in this milestone -- it must NOT
import the same helper functions the adapter generator uses, or a
shared bug could pass both sides silently, defeating the entire point of
an independent check (the same discipline `r21_certificate_checker.py`
already follows relative to `r21_certificate_emitter.py`, per §0). It
must: reject duplicate JSON keys; reject unknown fields; validate schema
version; validate all identifiers and reject dangling references;
validate timestamp consistency, state dimensions, units, decimal normal
forms, transformation dimensions, edge orientation, provenance
completeness; reconstruct every comparison and every matrix coefficient
independently; reconstruct `D` and `r`; compare against any supplied
`derived_problem` and reject on any disagreement; recompute the
canonical digest and reject on mismatch; emit the verified `roc-input/v1`
payload for R21.

## 13. Fixtures

### 13.1 Repairable

Four distinct tracker identities, four comparison edges, complete
provenance, a *coherent* transformation family, `r in im(D)`, an
explicit repair witness `b`, acceptance by the adapter verifier,
acceptance of the resulting R21 repair certificate by both existing R21
checkers (Python and OCaml, §0). Construction order matters: **choose
`b` first** (e.g. `b = (0, 1, 3, 2)`), compute `r = Db`, THEN express
that `r` through coherent per-edge transformations and track evidence --
the fixture must not simply store the pre-computed residue, or it would
not exercise §6's actual construction at all.

```text
ADAPTER ACCEPT
R21 REPAIR
Db = r
PYTHON VERIFIER ACCEPT
OCAML VERIFIER ACCEPT
```

**§20 records that everything except `ADAPTER ACCEPT` above has now
actually been run, not merely predicted**: `b = (0,1,3,2)` was chosen
first, `r` was independently derived from coherent per-edge transformed
values (not copied from `Db`), and the resulting `(D, r)` was fed to the
REAL `roc-solve`/`roc-verify`/`roc-verify-ocaml` and accepted by all
three. `ADAPTER ACCEPT` itself remains untested, since §12's independent
verifier does not exist yet -- there is no adapter to accept or reject
anything against; only the mathematical layer beneath it was spiked.

### 13.2 Obstructed

Locally valid but globally inconsistent pairwise transformations,
reproducing a nonzero cycle accumulation. **Use the repository's own
canonical instance directly rather than an arbitrary new one**: `r =
(1, 1, 1, -2)` (§0), with every component derived from explicit track
evidence and pair-specific transformation records, not copied in as a
literal. Expected:

```text
ADAPTER ACCEPT
R21 SEPARATOR
D^T y = 0
y.r = 1
PYTHON VERIFIER ACCEPT
OCAML VERIFIER ACCEPT
```

translated back to edge identities using R21's own normalized `y4 =
(1/5, 1/5, 1/5, -1/5)` (§0, §8), e.g.:

```text
Weighted comparison cycle:
  +1/5  e12: tracker-1 -> tracker-2
  +1/5  e23: tracker-2 -> tracker-3
  +1/5  e34: tracker-3 -> tracker-4
  -1/5  e14: tracker-1 -> tracker-4

Every permitted per-track correction cancels on this cycle.
The observed transformed-track discrepancies accumulate to 1.
No permitted collection of local corrections resolves all four
declarations.
```

**§20 confirms this fixture end to end, using genuine edge-specific
(incoherent) per-track offsets, not a copied literal**: track 2's
per-edge transformed value differs between `e12` and `e23`, track 3's
between `e23` and `e34`, track 4's between `e34` and `e14` -- and the
resulting `r`, computed purely from those eight independent offset
values plus a shared raw base, reproduces `(1, 1, 1, -2)` bit-exactly.
`roc-solve` on this `(D, r)` really does emit `y = (1/5, 1/5, 1/5,
-1/5)` (not merely the documented value, read directly from the
certificate this run produced), `y . r = 1` exactly, and both real
independent checkers accept. As in §13.1, `ADAPTER ACCEPT` remains
untested pending §12's implementation.

## 14. Negative fixtures

At minimum: missing track; duplicated track ID; missing source
ancestry; inconsistent timestamp; dimension mismatch; undeclared
coordinate frame; invalid transformation; unknown correction variable;
edge with reversed orientation but unchanged residue; tampered state
value, transformation, residue, matrix, or ancestry; incorrect digest;
duplicate JSON key; unknown schema field; noncanonical decimal; `NaN`
or infinity; excessively large input. Necessary because the adapter
receives untrusted evidence, exactly as R21's own certificate checker
must reject malformed or tampered certificates rather than assume
well-formedness.

## 15. Metamorphic tests

Relationships that must always hold, not just fixed examples:

- **Relabelling invariance**: renaming sources/trackers/edges does not
  change the verdict.
- **Orientation consistency**: reversing an edge and negating its
  residue preserves the problem.
- **Common translation**: adding the same translation to every track in
  the same frame does not create an obstruction.
- **Coherent frame change**: one certified invertible coordinate
  transformation preserves the verdict -- this is the adapter's direct
  connection point to R24 (`rocq/CertificateTransport.v`,
  `repairable_iff_transport_repairable`), not a new invariant needing
  its own proof from scratch.
- **Repair perturbation**: `r' = r + Dc` does not change the
  obstruction class.
- **Evidence-order invariance**: reordering canonical evidence records
  does not change the reconstructed problem, though canonical
  serialised order must rebuild deterministically.
- **Tamper sensitivity**: changing a semantically relevant input changes
  the digest and either changes the reconstructed problem or causes
  rejection.

## 16. The adapter certificate and the two-certificate chain

R21's certificate proves the final linear verdict; a separate adapter
certificate proves how `(D, r)` was obtained from evidence, binding:
snapshot digest, adapter-policy version, graph identity, row-to-edge
map, column-to-correction map, reconstructed `D`, reconstructed `r`,
R21 input digest (§0's `canonical_input_digest`, not a new hash scheme).

**The decimal-to-`a/b` conversion (§10) must be bound into this
certificate explicitly, per residue/matrix component, not left as an
untracked adapter-internal step**: for every value that passed through
§10's conversion, the certificate must record all three of (a) the
canonical decimal string as originally recorded in the snapshot, (b)
the quantisation-policy version that governed its rounding, and (c) the
resulting `a/b` string actually placed into `roc-input/v1` -- binding
`canonical decimal -> exact rational value -> canonical a/b string`
end to end, not just the final number. Critically, **the independent
adapter verifier (§12) must REDO this conversion from the recorded
decimal string and policy version, and reject on any mismatch with the
certificate's claimed `a/b` value -- it must never simply trust the
supplied conversion result**, for the same reason R21's own checker
recomputes `Db`/`D^Ty` rather than trusting a claimed verdict (§0, §12).
§20 records that this conversion was spiked and cross-checked against
an independently-written rounding path, but the CERTIFICATE-BINDING
requirement above (recording decimal + policy + result together, and
having the verifier redo it) is new content from this review, not
previously stated in §9/§10's first draft.

```text
tracking evidence --[adapter certificate]--> (D, r) --[R21 certificate]--> repair or obstruction
```

This chain is necessary because R21 alone has no way to attest that its
`(D, r)` correctly represents the tracking evidence -- exactly as R24's
certificate says nothing about whether a presentation change was itself
a faithful zoom/rescale of a real sensor, only that the linear transport
is correct once such a change is asserted (`CERTIFICATE_TRANSPORT_SPEC.md`
§4).

## 17. Milestone completion criteria

Complete only when: the meaning of `D`, `r`, `b`, `y` is documented in
tracking language (§3-§4, §8); each matrix row is derived from a
declared comparison edge and each column from one explicitly permitted
correction (§3-§4); §7's semantic argument is stated precisely (forward
and backward); the adapter verifier (§12) independently reconstructs `D`
and `r`; one repairable and one obstructed fixture (§13) pass end to
end; both existing R21 verifiers accept both certificate kinds;
tampering with evidence, transformations, provenance, `D`, `r`, or
digests is rejected (§14); no uncontrolled time, RNG, or floating-point
rendering enters any fixture; the exact claim is restricted to the
canonical quantised snapshot (§10); and the design clearly marks what
remains a provisional reference policy rather than a Meridian-validated
MIST policy.

## 18. What happens immediately afterward -- Stone Soup stays outside this milestone

The first implementation must use plain canonical fixtures resembling
tracking evidence, NOT a live Stone Soup dependency -- importing it now
would mean simultaneously debugging Stone Soup's own objects, stochastic
models, coordinate transformations, snapshot serialisation, exact
rational conversion, `(D, r)` construction, and R21 integration all at
once, with no way to isolate which layer a failure belongs to. Only
once §12's verifier and §13's two fixtures pass does Stone Soup become
an evidence *producer* for this already-fixed interface: pin a Stone
Soup version; reproduce a seeded linear-architecture example; map its
sources/detections/tracks into §11's canonical snapshot; freeze the
output; run §12's verifier; run R21; verify the certificate; port a
track-to-track fusion example; add a data-incest provenance case;
present the result to Meridian as a functioning reference integration.
None of that is scoped further here.

## 20. Feasibility review results (2026-07-16)

A read-only audit plus bounded, untracked spikes (a single Python script
in a session scratchpad, never added to this repository, no `roc-input`
fixture files committed) checked this document against the REAL R21
pipeline before anything above was trusted -- not merely re-read against
static files as the first draft's §0 did.

1. **Reference audit**: every citation in §0 (`roc-input/v1`,
   `repair-or-separator/v1`, the `_RATIONAL_RE` decimal rejection, the
   four-cycle `D`/`r=(1,1,1,-2)`/`y4` convention) was confirmed not just
   by reading the source files but by actually invoking
   `r21_certificate_emitter.py`, `r21_certificate_checker.py`, and
   `roc-verify-ocaml` as real subprocesses on real input. Both existing R21
   checkers ran from their real compiled/interpreted form, not a
   re-implementation.
2. **Decimal -> exact rational -> `a/b` conversion (§10)**, tested
   independently on cases requiring actual rounding (two exact
   half-way ties under `half_even`, e.g. `10.0000015` at 6 decimal
   places), cross-checked against a SECOND, independently-written
   rounding path (`Decimal`-context rounding vs. plain-`Fraction`
   round-half-to-even) that shares no code with the first. All cases
   agreed exactly.
3. **Repairable fixture (§13.1)**: `b = (0,1,3,2)` chosen first; `r =
   (1,2,-1,2)` derived from a genuinely COHERENT per-track
   transformation family (same offset for a track regardless of which
   edge references it) and confirmed to equal `Db` exactly, not
   asserted. Fed through the real `roc-solve`; result `repair`; accepted
   by both real independent checkers.
4. **Obstructed fixture (§13.2)**: `r = (1,1,1,-2)` derived from a
   genuinely INCOHERENT, edge-specific transformation family (each
   track's offset differs depending on which edge references it) and
   confirmed to reproduce the repository's own canonical value
   bit-exactly, not copied in as a literal. Fed through the real
   `roc-solve`; result `separator`; the certificate's own emitted `y`
   was read back (not assumed) and matched `(1/5,1/5,1/5,-1/5)` exactly,
   with `y . r = 1`; accepted by both real independent checkers.
5. **`roc-input/v1` acceptance**: both fixtures' independently
   reconstructed `D`/`r` were written directly in `roc-input/v1` form
   and consumed unmodified by the real emitter/checker -- no schema
   friction.
6. **The critical finding**: §4's original correction formula, `s_i' =
   s_i + b_i` (additive), is sign-inconsistent with §7's theorem as
   originally stated. Verified by direct computation on the repairable
   fixture: applying the additive formula with the fixture's own
   `Db = r`-satisfying `b` does **not** make any of the four edges'
   corrected values agree (all four came out unequal); the corrected
   subtractive formula, `t_i := s_i - b_i`, makes all four edges agree
   on the identical corrected value (`100`) exactly when `Db = r` holds.
   §4 and §7 above are the corrected versions; this is not a cosmetic
   fix -- the original formula, if implemented as originally stated,
   would have produced a plausible-looking adapter whose "resolves the
   discrepancy" narrative was backwards relative to its own linear
   algebra. Caught only by computing concrete numbers, exactly the
   failure mode block/prose notation conceals, matching this
   repository's own recurring lesson from R28's review
   (`APPEND_ONLY_EVIDENCE_EVOLUTION_SPEC.md` §13).
7. **Certificate-binding for the decimal conversion (§16)**: not
   previously stated precisely in the first draft; now requires the
   adapter certificate to record canonical decimal, quantisation-policy
   version, and converted `a/b` string together per value, with the
   independent verifier redoing the conversion rather than trusting the
   supplied result.

**What was NOT tested, and remains open for the implementation phase**:
§2's domain objects (`Source`/`Detection`/`LocalTrack`/`ComparisonEdge`/
`AdapterSnapshot`), §11's full snapshot schema, and §12's independent
verifier do not exist in any form yet -- the spike worked directly with
`D`/`r` and per-edge offset dictionaries, deliberately skipping the
domain-object layer to isolate the mathematical semantic question (§7)
and the R21 interface boundary (§10) first, per this repository's own
"spike the smallest true thing first" discipline. §14's negative
fixtures and §15's metamorphic tests were not exercised at all. None of
that is a defect in this review -- it was not this review's scope --
but it means "the design is validated" refers specifically to §4-§10 and
§13's two fixtures, not to §2/§11/§12/§14/§15 as implemented artifacts.

## 21. What this document does not claim

- That §7's semantic theorem, in either direction, has been proved --
  it is the target claim the adapter specification must defend, stated
  here to fix what "the adapter is correct" will mean, not a result. §20
  confirms both directions by hand on one concrete fixture, which is
  short of a general proof.
- That any Rocq file, Python adapter module, or independent verifier
  implementing §2-§16 has been written -- this document is design only,
  matching this repository's own precedent
  (`OBSTRUCTION_SIGNATURE_SPEC.md`, `APPEND_ONLY_EVIDENCE_EVOLUTION
  _SPEC.md` before either's implementation phase began).
- That §6's pair-specific-transformation construction is the only
  defensible source of context-dependent residue -- it is the
  recommended FIRST construction (§5's listed alternatives are not
  explored further here) because it is the smallest one that avoids §5's
  "residue automatically telescopes to zero" failure mode, not because
  the others are unsound.
- That this connects to any real Meridian tracking scenario, sensor,
  or fusion architecture -- §0's citations ground this document's
  mathematical conventions in the existing repository, not in any actual
  Meridian data.
- That velocity, more than four trackers, more than one timestamp, or
  any of §1's excluded complexity classes are scoped, planned, or even
  sketched beyond being named as explicitly deferred.
- That this is the next authorized phase for R28 or any other numbered
  result -- this is a parallel, applied-layer milestone, not a
  replacement for the R28 implementation order already recorded for this
  repository; starting either needs its own explicit go-ahead.
