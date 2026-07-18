# Certified Append-Only Restrictive Evidence Evolution (R28 scope)

**Status (2026-07-16): design only. Nothing in this document is
committed as a repository proof, and no `rocq/*.v` file should be
created or modified from it until an explicit go-ahead names which
theorem below (or a scoped variant) to build.** This document exists to
answer, before any streaming/incremental-certificate code is written,
what the smallest true one-step transition calculus is that the applied
"evidence arrives over time" scenario actually needs, and to separate
that from the larger, genuinely harder, non-monotone update calculus
that "evidence changes over time" would require instead.

**Revision (2026-07-16, same day): reviewed before anything was built,
per this repository's own discipline, and five gaps were found and
fixed in place** -- the append constructor was left as an unspecified
block-matrix notation rather than an actual typed Rocq definition (§2),
evidence identifiers were not required to be unique (§2), §6's hypothesis
hid its repair witness inside an existential rather than naming it (§6),
§10 conflated an order-theoretic fact with a separate decidability
obligation (§10), and §12 stated the three audit notions as parallel
without saying which is a proved consequence versus recorded metadata
(§12). All five are addressed below; none required changing which
theorems this document scopes, only how precisely they are stated.

**Second revision (2026-07-16, same day): the §2 fix above was itself
found to be insufficient** -- uniqueness of `ev_id` alone does not give
positional alignment between an evidence history and `D`/`r` -- and was
replaced with `EvidenceState` (§2), making `D`/`r` derived projections of
the evidence history so alignment holds by construction. An untracked
Rocq feasibility spike (§13) then checked the six raw append-arithmetic
facts every theorem in §3-§10 depends on against R24's actual
definitions; all six compile and `coqchk`-check clean, with no
adjustment needed to any theorem signature above.

The governing question:

> When a certified rational presentation `(D, r)` is extended by exactly
> one new, immutable evidence constraint, what certificate information
> from the old state can be reused to decide and certify the new state,
> and can any newly arising obstruction be proved to depend essentially
> on the new constraint?

## 0. What already exists, checked directly, not assumed

R21 (`rocq/ExactRationalRepairOrSeparator.v`) computes a single
repair-or-separator certificate for a fixed `(D, r)`; it has no notion of
`(D, r)` changing over time at all. R24
(`rocq/InvertiblePresentation.v`, `rocq/CertificateTransport.v`) proves
transport of a certificate when the *same-dimensional* system is
re-expressed under an invertible change of basis on both spaces -- a
different kind of change from what this document needs, since here `D`
grows a row and no change of basis is involved. Nothing in this
repository currently has a notion of a presentation being extended by an
additional constraint, of an evidence history, or of a certificate being
partially reused rather than recomputed from scratch.

R28 builds directly on R24's `qcvec`/`MatrixQc` infrastructure
(`dot_qc`, `mat_vec_qc`, `transpose_qc`), not R21's `list Q`
representation, for the same reason R24 chose it over R21's: `Qc`'s
Leibniz equality avoids `list Q`'s `Qeq`/setoid friction, and nothing
below needs R21's elimination procedure directly, only the notions of
repairability and separation it computes witnesses for. R28 does not
depend on R22 or R24's own theorems either -- it introduces a genuinely
new operation (row append) that neither file has any notion of -- though
§11 flags where a later document might compose R28 with R24 (evidence
arriving *and* a presentation change happening together), explicitly not
attempted here.

## 1. Scope, stated precisely

The imprecise phrase "adding evidence" is not adopted. The one-step
transition this document scopes is exactly:

> **Append-only restrictive evidence extension**: given `(D, r)` and one
> new row `e = (a, b)` (an evidence label `id`, a coefficient row vector
> `a`, and a target scalar `b`), form
>
> ```text
> D' = [D; a]      r' = [r; b]
> ```
>
> by appending `a` as a new row of `D` and `b` as a new entry of `r`.
> Nothing about `D` or `r`'s existing rows changes.

This is a *restriction* of the solution set: `Sol(D', r') ⊆ Sol(D, r)`,
because every old equation must still hold and one new equation is
added. That containment is the entire source of every monotonicity
result in this document (§4, §7, §10) -- it does not hold, and none of
those results hold, for any update that modifies or removes an existing
row.

**Explicitly out of scope for R28**, because each breaks the restriction
property and requires a genuinely different, non-monotone transition
calculus:

- replacing an earlier row's target value `r_i`;
- correcting an earlier row's coefficients `D_i`;
- adding a new correction variable or column (changes `n`, not just
  `m`);
- retracting or removing an earlier row;
- merging or re-identifying two earlier rows.

Any of these can make an obstructed system repairable, or a repairable
system obstructed, in a direction §4's monotonicity theorem does not
cover. They are a separate, later milestone if pursued at all, and this
document takes no position on their eventual proof structure.

## 2. The formal object: an evidence-labelled presentation state

R24 fixes `MatrixQc m n := Vector.t (qcvec n) m` (`InvertiblePresentation.v`
line 71) -- a matrix is a length-`m` vector of rows, each an `n`-vector.
Appending one row is therefore not free-form block-matrix notation but a
single, dimensionally exact stdlib operation, `Vector.shiftin : A ->
Vector.t A n -> Vector.t A (S n)` (appends at the end, typed so the
result is provably length `S n`, not merely "an enlarged matrix" left
to the reader):

```coq
Definition row_append {n : nat} {m : nat} (D : MatrixQc m n) (a : qcvec n)
  : MatrixQc (S m) n := Vector.shiftin a D.

Definition vec_append {m : nat} (r : qcvec m) (b : Qc) : qcvec (S m) :=
  Vector.shiftin b r.
```

This is stated as an actual candidate definition, not deferred to "an
explicit constructor is a prerequisite" -- it is exactly the constructor
this document's own theorems (§3-§7) are stated against, and every
identity in §7 depends on this specific choice (row appended at index
`m`, i.e. last, matching `vec_last` in §6). If a tracked development
later picks a different convention (e.g. `Vector.cons`, prepending at
index `0`), every signature below needs re-deriving against that
convention -- nothing here is convention-independent.

**A separate `E`/`D`/`r` triple with a bolted-on alignment invariant was
the wrong shape, caught before writing any theorem against it.** The
first draft of this section defined `State := (D, r)` alone and treated
the evidence history `E` as an add-on for §12's audit purposes, related
to `D`/`r` only by an informal "the entry at position `i` labels row `i`"
expectation -- nothing enforced that `E` had length `m`, that appending
kept `E`, `D`, and `r` in lockstep, or that `E`'s labelling was even
well-typed against `D`'s row count. The fix is not an added invariant to
maintain, but a change of primary object: make `E` itself the state, and
derive `D` and `r` *from* `E`, so alignment is true by construction, not
by a side-condition that could be forgotten:

```coq
Record Evidence (n : nat) := mkEvidence { ev_id : ID; ev_a : qcvec n; ev_b : Qc }.
Definition EvidenceState (m n : nat) := Vector.t (Evidence n) m.

Definition state_D {m n : nat} (E : EvidenceState m n) : MatrixQc m n :=
  Vector.map (@ev_a n) E.
Definition state_r {m n : nat} (E : EvidenceState m n) : qcvec m :=
  Vector.map (@ev_b n) E.

Definition append {m n : nat} (E : EvidenceState m n) (e : Evidence n)
  : EvidenceState (S m) n := Vector.shiftin e E.
```

Because `EvidenceState m n` is a `Vector.t (Evidence n) m`, it has
exactly `m` entries by its own type -- "`E` contains exactly `m`
entries" is not a proof obligation, it is what the type says. Row `i` of
`state_D E` and coordinate `i` of `state_r E` are `ev_a`/`ev_b` of `E`'s
own entry `i`, by definition of `Vector.map`, not by a coherence
condition (`D_i = ev_a(E_i)`, `r_i = ev_b(E_i)`) that could fail to
hold. And appending commutes with taking these projections *for free*,
via the stdlib's existing `map_shiftin` lemma (`map f (shiftin a v) =
shiftin (f a) (map f v)`, `VectorSpec.v` line 514 -- already proved,
reused directly, not re-derived):

```coq
Lemma state_D_append : forall (m n : nat) (E : EvidenceState m n) (e : Evidence n),
  state_D (append E e) = row_append (state_D E) (ev_a e).
Lemma state_r_append : forall (m n : nat) (E : EvidenceState m n) (e : Evidence n),
  state_r (append E e) = vec_append (state_r E) (ev_b e).
```

Both are one-line applications of `map_shiftin` (§13 below records that
the spike confirmed this). §3-§10's theorems are stated over `(D, r)`
directly (matching R24's own style, and because the mathematics does not
need `E` at all) but should be read as implicitly applied to `state_D
E`/`state_r E` for the actual `EvidenceState` whenever §12's audit claims
are in play.

**Evidence identifiers must still be unique across a history for §12's
`support` to mean what it claims -- this is now the only remaining
alignment-adjacent condition, and it is orthogonal to positional
alignment, not a substitute for it.** Position is handled by
`EvidenceState`'s type; `ev_id` is a separate external label attached to
each position, and nothing stops two positions from carrying the same
label. The needed hypothesis is `NoDup (map ev_id (Vector.to_list E))`
for any history whose audit claims (§12) are to be trusted -- stated
here as a standing requirement, not proved to hold automatically, and
not enforced by `append` itself (which accepts any `id`, duplicate or
not). `support` itself can be defined directly over `Fin.t m` positions
(`{ i : Fin.t m | y[@i] <> Q2Qc 0 }`) without reference to `ev_id` at
all, and only translated to `id`s, via `Vector.map ev_id`, at the point
where the uniqueness hypothesis is available -- keeping the
always-well-defined positional notion separate from the
label-uniqueness-dependent one.

`Repairable (D, r) := exists b, mat_vec_qc D b = r`. `Separates D r y :=
mat_vec_qc (transpose_qc D) y = zero_qc /\ dot_qc y r <> Q2Qc 0` (a
separator need not be normalized to pair to exactly `1`; §5's residual
identity is stated for the un-normalized pairing value directly, since
normalizing would obscure exactly the quantity §7 wants to expose).

## 3. Separator lifting -- proposed theorem, proof sketch included since it is short

```coq
Theorem separator_lifts :
  forall (m n : nat) (D : MatrixQc m n) (r : qcvec m) (a : qcvec n) (b : Qc)
         (y : qcvec m),
    Separates D r y ->
    Separates (row_append D a) (vec_append r b) (vec_append y (Q2Qc 0)).
```

Proof idea: appending a zero coefficient to `y` leaves `transpose_qc D`
annihilation untouched on the old rows and contributes `0 * a = 0` on
the new row, so `y^+ := (y, 0)` still annihilates `D'^T`; the pairing
`dot_qc y^+ r' = dot_qc y r + 0 * b = dot_qc y r`, unchanged, so
nonzero-ness is preserved exactly, not merely approximately. **This is
stronger than the monotonicity statement in §4** -- it is a constructive
certificate-transport operation, not just an existence claim: an
obstructed state's separator survives every subsequent append by
appending one more zero, with no solver re-run needed at any step (§9
makes this precise for finite sequences by induction).

## 4. Obstruction monotonicity

```coq
Theorem obstruction_monotone :
  forall (m n : nat) (D : MatrixQc m n) (r : qcvec m) (a : qcvec n) (b : Qc),
    ~ Repairable D r ->
    ~ Repairable (row_append D a) (vec_append r b).
```

Follows immediately from §3 plus the repair-or-separator dichotomy R21
already establishes for any fixed presentation (an obstructed state has
a separator; a lifted separator obstructs the extended state). Stated
separately from §3 because it is the form most directly quotable as "an
already-obstructed stream stays obstructed," even though §3's
constructive version is what any implementation would actually use.

## 5. Conditional repair-witness reuse -- and the direction that does NOT hold

```coq
Theorem repair_reuse :
  forall (m n : nat) (D : MatrixQc m n) (r : qcvec m) (a : qcvec n) (b : Qc)
         (x : qcvec n),
    mat_vec_qc D x = r ->
    dot_qc a x = b ->
    mat_vec_qc (row_append D a) x = vec_append r b.
```

Cheap to check: only `dot_qc a x = b` needs testing against the new row,
not a full re-solve. **The converse is explicitly not a theorem and must
not be stated as one**: `dot_qc a x <> b` does not imply
`~ Repairable (row_append D a) (vec_append r b)`. A different old repair
`x'` (with `mat_vec_qc D x' = r` but `x' <> x`) may satisfy the new row
even when `x` does not, whenever the old system was underdetermined.
§6's converse only holds when *every* repair of `(D, r)` fails the new
row, not merely the one witness on hand -- which is exactly why a single
R21-style witness is insufficient for a complete converse (§8 makes this
precise).

## 6. Essential participation of the new row in a newly arising obstruction

```coq
Theorem new_row_essential :
  forall (m n : nat) (D : MatrixQc m n) (r : qcvec m) (a : qcvec n) (b : Qc)
         (x : qcvec n) (y_plus : qcvec (S m)),
    mat_vec_qc D x = r ->
    Separates (row_append D a) (vec_append r b) y_plus ->
    vec_last y_plus <> Q2Qc 0.
```

The hypothesis is stated with an explicit repair witness `x`, not the
opaque existential `Repairable D r` -- the proof needs to name `x`
directly, and this repository's own precedent (R24's `InvertibleMatrix`
takes explicit inverse witnesses rather than an opaque invertibility
predicate) is to prefer the constructive form wherever the existential
would otherwise just be destructed on the first line anyway.

Proof, as a direct computation rather than an appeal to an unnamed
dichotomy fact: write `y_plus = (y, alpha)` (via `Vector.shiftin`'s own
inverse view). Unfolding `Separates` on `row_append D a`, `mat_vec_qc
(transpose_qc D) y + alpha * a = zero_qc` (as `n`-vectors -- this
equation itself is a claim about `transpose_qc`'s interaction with
`Vector.shiftin` that should be checked as its own small lemma before
anything else in this document, since every proof below quietly depends
on it). Suppose `alpha = Q2Qc 0`: then `mat_vec_qc (transpose_qc D) y =
zero_qc`, and by R24's own `dot_qc_mat_vec_adjoint` (already proved,
reused directly rather than re-derived), `dot_qc y r = dot_qc y
(mat_vec_qc D x) = dot_qc (mat_vec_qc (transpose_qc D) y) x = dot_qc
zero_qc x = Q2Qc 0`. But `Separates`'s second conjunct requires `dot_qc
y_plus (vec_append r b) = dot_qc y r + alpha * b <> Q2Qc 0`, which with
`alpha = 0` reduces to `dot_qc y r <> Q2Qc 0` -- contradicting `dot_qc y
r = Q2Qc 0` just derived. So `alpha <> Q2Qc 0`. This is the audit-facing
theorem: it says the new evidence event does not merely happen
immediately before a conflict is detected, it appears with a nonzero
coefficient inside the mathematical object that certifies the conflict.

## 7. The residual identity

```coq
Theorem obstruction_residual :
  forall (m n : nat) (D : MatrixQc m n) (r : qcvec m) (a : qcvec n) (b : Qc)
         (x : qcvec n) (y : qcvec m) (alpha : Qc),
    mat_vec_qc D x = r ->
    mat_vec_qc (transpose_qc (row_append D a)) (vec_append y alpha) = zero_qc ->
    dot_qc (vec_append y alpha) (vec_append r b) = alpha * (b - dot_qc a x).
```

Proof idea: `(y, alpha)` annihilating `D'^T` unfolds to `mat_vec_qc
(transpose_qc D) y + alpha * a = 0` (as row-space elements), so `dot_qc
y r = dot_qc y (mat_vec_qc D x) = dot_qc (mat_vec_qc (transpose_qc D) y)
x = dot_qc (- alpha * a) x = - alpha * dot_qc a x`. Then `dot_qc (y,
alpha) (r, b) = dot_qc y r + alpha * b = alpha * b - alpha * dot_qc a x
= alpha * (b - dot_qc a x)`. The right-hand side is exactly the new
row's *prediction error* under the old repair `x`, scaled by the
obstruction certificate's own coefficient on that row -- this is the
quantity an audit trail should report instead of a bare `OBSTRUCTED`
verdict: "evidence `id` predicted `b`, the prior state's repair `x`
predicted `dot_qc a x`, and the discrepancy is exactly this certificate
value divided by `alpha`."

**This sign depended on §2's fixed append convention -- now checked, not
merely asserted.** The derivation above depended on the exact equation
`mat_vec_qc (transpose_qc (row_append D a)) (vec_append y alpha) =
mat_vec_qc (transpose_qc D) y + alpha * a` holding for
`row_append`/`vec_append` as defined via `Vector.shiftin` (§2). §13
records that an untracked spike proved exactly this equation
(`transpose_qc_row_append`), `coqchk`-clean, plus a concrete rational
example (`residual_sign_check`) confirming this sign directly by
`vm_compute`, independent of the general theorem. The sign and shape
stated here are therefore no longer merely read off block notation --
see §13 for what the spike needed to establish it (a genuine,
non-off-the-shelf three-vector induction lemma) and what stayed
untouched (this document's theorem statements needed no correction).

## 8. Why a single R21 repair witness is insufficient for a complete converse

§5 already shows one repair witness `x` cannot decide the converse case
(`dot_qc a x <> b`) alone. Making that direction decidable needs a
representation of the *whole* affine solution space, not one point in
it: a particular solution `x_0` together with a basis `K` for `ker D`
(every repair has the form `x_0 + K t`). The new row's behavior over the
whole solution space splits into exactly two cases:

- `dot_qc a (mat_vec_qc K _) <> 0` for some kernel direction (`a`
  varies over the old solution space): the new row is satisfiable by
  *some* old repair regardless of `b`'s exact value, by adjusting along
  that kernel direction; the extended state remains repairable, and an
  adjusted witness is constructible directly from `x_0`, `K`, and the
  one kernel direction that makes `a` vary (not a full re-solve).
- `dot_qc a (mat_vec_qc K _) = 0` for every kernel direction (`a` is
  constant over the old solution space, equal to `dot_qc a x_0`): the
  new row is either satisfied by every old repair (`b = dot_qc a x_0`,
  reuse `x_0`) or by none (`b <> dot_qc a x_0`, obstructed) -- and in
  the obstructed sub-case, because `a` lies in the row space of `D`
  exactly when it is constant over `ker D`, a separator can be
  constructed explicitly from the `lambda` with `mat_vec_qc
  (transpose_qc lambda) D = a` (standard finite-dimensional duality) as
  `(lambda, -1)`, without a full augmented-system solve.

This does not change any theorem statement above; it explains why an
executable incremental decision procedure needs strictly more cached
state than R21's certificate schema currently produces. That richer
object is named but **not designed** here -- see §11.

## 9. Finite append sequences by induction

For a history `E = [e_1; ...; e_k]` inducing states `S_0 -> S_1 -> ... ->
S_k` via repeated `append`, §3's lifting theorem and §4's monotonicity
theorem both extend to `S_0 -> S_j` for any `j` by ordinary induction on
the sequence (each step is a single application of the one-step
theorem); no new proof technique is needed beyond composing the one-step
results claimed above. This document does not spell out the induction
in full Rocq syntax -- flagged as a mechanical but unproved step, not a
mathematical gap.

## 10. Preserving a first-conflict certificate across an entire stream

This section is two separate claims, kept apart because they need
different amounts of proof:

**(a) At most one transition -- pure order theory, no decidability
needed.** For an append-only history `S_0 -> S_1 -> ... -> S_n`, there
is at most one index `j` where the state transitions from repairable to
obstructed: monotonicity (§4/§9) says the boolean sequence
`Repairable(S_0), ..., Repairable(S_n)` cannot go from false back to
true, so it has at most one true-to-false transition. This needs nothing
beyond §4/§9 -- it is a fact about any monotone-decreasing boolean
sequence, proved without inspecting `Repairable` itself at all.

**(b) A least obstructed index exists and is computable -- a separate
obligation, not free from (a).** Claiming a *specific* `j` can be found
-- the form an audit log needs ("the stream became inconsistent at event
`e_j`") -- additionally requires `Repairable` to be *decidable* at each
of the finitely many prefix states `S_0, ..., S_n`, so that a bounded
linear search over `{0, ..., n}` can locate the first `false`. This is
not automatic from (a)'s order fact alone; it is a finite-index
minimization over a decidable predicate. R21's own
`compute_repair_or_separator` already computes a concrete per-state
verdict (not merely proves decidability abstractly), so the ingredient
this needs likely already exists in the repository -- but chaining it
into a stated theorem ("there exists a least `j` such that ...,
computed by this specific procedure") is not done by this document and
should not be assumed free.

Once (b)'s `j` is in hand: §6 applies at exactly that transition, using
`S_{j-1}`'s repair witness and `S_j`'s separator -- the separator first
constructed at `S_j` has `e_j` participating with a nonzero coefficient.
By §3, that same separator (with the coefficients on all later events
set to zero) remains a valid separator for every `S_k`, `k >= j`,
without being recomputed. An audit log can therefore report,
permanently, "the stream became inconsistent at event `e_j`," using the
*original* separator constructed at that transition, even as later
events are appended and possibly acquire their own, different
separators that do not use `e_j` at all.

## 11. Verdict certificates vs. continuation certificates -- the real conceptual distinction

This document's central design decision is keeping these two objects
separate and not conflating them:

- **Verdict certificate**: exactly what R21 already produces and this
  repository already trusts -- a single repair witness `x` or separator
  `y` that externally verifies the current state's repairability
  verdict. §3-§7's theorems are stated in terms of this object and
  require nothing more.
- **Continuation certificate**: an internal object (sketched, not
  designed, in §8: `x_0` plus a kernel basis `K`, or equivalent
  elimination/factorisation data) that a streaming solver would cache
  *in addition to* the verdict certificate, purely to make the next
  append cheap to decide without a full re-solve. Its representation,
  its own correctness obligations, and whether it needs to be externally
  checkable at all (as opposed to trusted internal solver state that
  merely produces a verdict certificate at each step, which is then
  checked as R21 already checks one) are **explicitly deferred**. No
  representation is chosen, no theorem about it is claimed, and no code
  implementing it should be written from this document alone.

## 12. Audit-trail semantics, as a consequence of the certificate mathematics, not a separate vocabulary

Three notions must stay distinct, because §3 and §6 give genuinely
different answers for them on the same lifted separator:

- **State-history ancestry**: which prior state and which applied
  update produced the current state -- a bookkeeping fact about `E`
  itself, true of every event in the history regardless of any
  certificate.
- **Verification dependency**: which prior events were consulted while
  validating or constructing the current certificate -- e.g. lifting a
  separator through ten append steps "touches" all ten events
  procedurally even though nine of them contribute a zero coefficient.
- **Mathematical certificate support**: for a separator `y = (y_1, ...,
  y_m)` over history `E`, `support(y) := { id_i : y_i <> 0 }` -- the
  events the certificate's own nonzero coefficients single out. §3's
  lifted separator has the *same* support as the original, even though
  its history ancestry and verification dependency both grow with every
  append.

An audit record needs all three, kept labeled as such; collapsing them
into one "why did this happen" field would misreport, for example, a
long-lifted first-conflict separator (§10) as depending on every
intervening event, when its actual mathematical support never changes.

**Only mathematical support is a theorem-level consequence of anything
in this document.** §3 proves the lifted separator's support is
unchanged by later appends -- that is a proved fact, given the
uniqueness condition on `ev_id` (§2). State-history ancestry and
verification dependency are **not** proved, derived, or authenticated by
anything above -- they are operational bookkeeping this document assumes
some surrounding system records faithfully (e.g. an append-only log of
which `Evidence` values were actually applied in which order). If an
application needs those two notions to be tamper-evident or
cryptographically authenticated rather than merely recorded, that is a
separate mechanism this document says nothing about and does not
attempt to scope.

## 13. Feasibility spike results (untracked, 2026-07-16)

An untracked Rocq spike (`coqc -Q rocq "" R28Spike.v`, requiring
`RationalCanonicalVectors`/`InvertiblePresentation` unchanged, never
added to `rocq/` or the Makefile's module inventory, no R28 theorem
beyond raw append infrastructure attempted) checked every numbered item
below against R24's actual definitions, not the block-matrix notation
this document uses for readability. All six compile and `coqchk`-check
clean, with zero `Admitted`/`admit`/axioms:

1. `row_append`/`vec_append` as `Vector.shiftin`, exactly as §2 states.
2. Old entries survive `shiftin` under the old-index embedding
   (`Fin.L_R 1 k`) and the appended value is found at `Vector.last` --
   both are the stdlib's own `shiftin_nth`/`shiftin_last`, no new proof
   needed.
3. `dot_qc` decomposes over two appended vectors (`dot_qc (vec_append y
   alpha) (vec_append v c) = dot_qc y v + alpha * c`) -- needed one new
   helper (`map2` distributing over two simultaneous `shiftin`s, not in
   the stdlib as such) plus the stdlib's own `fold_right_shiftin`.
4. `mat_vec_qc` decomposes over `row_append` exactly as stated -- a
   direct instance of the stdlib's own `map_shiftin`, no new lemma
   needed.
5. The full vector-action form of the transpose/adjoint interaction
   §6-§7 need, `mat_vec_qc (transpose_qc (row_append D a)) (vec_append y
   alpha) = qcvec_add (mat_vec_qc (transpose_qc D) y) (qcvec_scale alpha
   a)`, now proved as `transpose_qc_row_append` -- **this was the one
   genuinely new piece of infrastructure**, needing four small lemmas
   none of which exist off-the-shelf: `map2_shiftin_shiftin` (two
   `shiftin`s under one `map2`), `map2_map2_fuse` (a three-vector
   simultaneous-induction fact relating `transpose_qc`'s own row-wise
   recursion to `shiftin` at the OUTER index -- this is the fact that
   makes `transpose_qc`, unlike `dot_qc`/`mat_vec_qc`, not just a
   direct stdlib application), and `map_map2_qc`/`map2_map_map_qc` (generic
   map/map2 fusion facts connecting the matrix-level identity to the
   `dot_qc`-level one §6/§7 are stated against). All four were provable
   by the same technique (`Vector.rect2`, simultaneous structural
   induction on two same-length vectors) once that technique was found
   -- none needed anything exotic beyond it.
6. A concrete rational example -- `D2` the 2x2 identity, `r2 = x2 =
   (2,3)`, appended row `a_row = (1,1)`, `b_bad = 6` (inconsistent, since
   `dot a_row x2 = 5`), `lambda2 := a_row` (since `D2` is its own
   transpose-inverse, `lambda^T D2 = a_row` is solved by `lambda2 =
   a_row` directly), `z2 := (lambda2, -1)`. Checked TWO things
   independently, not just the abstract theorem's instantiation, per
   this repository's own stated discipline against a single oracle:
   `z2_annihilates` (`z2` actually annihilates `transpose_qc
   (row_append D2 a_row)` by direct `vm_compute`) and
   `residual_sign_check` (the residual identity's sign, `dot_qc z2 r+ =
   alpha * (b - dot a x)` with `alpha = -1`, holds exactly as §7
   states, also by direct `vm_compute`, not by invoking
   `transpose_qc_row_append` itself).

**Dependent-vector friction actually encountered, for the next person
attempting this in a tracked file:** `induction u, v using Vector.rect2`
(the natural-looking tactic form) fails outright in this Coq version
(8.18.0) with "Cannot recognize the conclusion of an induction scheme"
-- the working form is `refine (Vector.rect2 (fun n u v => ...) _ _)`
with the goal left in fully-quantified form (not `intros`-ed on `u`/`v`
first) before the `refine`. Plain `apply` against stdlib lemmas whose
conclusion has a repeated argument in different positions (`map_shiftin`
applied where the goal has `dot_qc a x` on both a `f v` position and
literally as `a`) triggers higher-order-unification ambiguity and picks
the wrong instantiation silently until `Qed` reports a wrong-term error
several lines later; the fix was always to supply the lemma's arguments
explicitly (`exact (VectorSpec.map_shiftin (qcvec n) Qc (fun row =>
dot_qc row x) a m D)`) rather than trust `apply`'s unifier. Getting a
`cons`/`shiftin` index wrong by using the same length variable in two
positions that are actually different (`row_append`'s `cons` inside the
lifted-column construction is NOT the same index as the original
matrix's own row-transpose `cons`) produced an immediate, unambiguous
Coq type error, not a silent wrong proof -- exactly the failure mode
block-matrix notation in a design document cannot catch, which was the
point of running this spike before writing any tracked file.

**No adjustment to any theorem signature in §3-§10 is needed.** The
spike confirms the design note's mathematics and its append convention
(§2) are sound as stated; the only correction the spike itself drove was
internal to its own first attempt (the index mismatch above, caught and
fixed before `Qed`, never reaching this document). §2's `EvidenceState`
alignment fix and the `NoDup`/`ev_id` condition were unaffected by the
spike since they are about `Evidence`/history bookkeeping, not the raw
append arithmetic checked here.

## 14. What this document does not claim

- That any theorem in §3-§10 has been proved, prototyped, or even fully
  checked to typecheck as stated in Rocq -- every signature above is a
  proposed target, matching this repository's own precedent
  (`OBSTRUCTION_SIGNATURE_SPEC.md`, before its Modest-R23 target was
  attempted).
- That the continuation-certificate object sketched informally in §8/§11
  has a chosen representation, a stated theorem, or any planned Rocq
  file -- it is named as a necessary future concept, not designed.
- That retraction, replacement, correction, merging, or column-adding
  updates (§1) are scoped, planned, or even known to need the same proof
  techniques as the append-only case -- they are out of scope entirely,
  not a "part 2" of this document.
- That this composes with R24 (a presentation change happening
  concurrently with evidence arriving) -- not attempted here, flagged in
  §0 as a later question if it arises.
- That this connects to any real deployed evidence stream -- per this
  repository's own recurring caveat (`CERTIFICATE_TRANSPORT_SPEC.md` §7,
  `OBSTRUCTION_SIGNATURE_SPEC.md` §5), no real deployment scenario is
  decomposed or claimed to fit this scope here.
- That this is the next authorized phase. Starting any tracked Rocq
  implementation from this document -- including only §3's smallest
  theorem -- needs its own explicit go-ahead, per this repository's
  established discipline.
