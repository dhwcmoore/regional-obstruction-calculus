# Exact Rational Separation: The Concrete Matrix Theorem Behind `SeparatesOutside`

**Status (2026-07-13): design only, nothing in this document is
committed as a repository proof.** Answers the question the corrected
`CYCLE_QUOTIENT_DUALITY_SPEC.md` deferred: having chosen Route C
(prove `SeparatesOutside` concretely for the finite rational spaces this
repository actually computes with, expose it through a thin Route A
interface, defer Route B), what is the smallest exact rational matrix
representation in Rocq that proves the normalised separation theorem,
and does it match the coordinate and orientation conventions
`rational_linear_algebra.py` already uses? The second half of that
question is answered precisely below, by tracing the actual code, not
by picking a convention and hoping it matches.

The governing question, unchanged from how it was first posed:

> What is the smallest exact rational matrix representation in Rocq
> that can prove `r notin im(D) iff exists y, y*D = 0 and y(r) = 1`,
> while matching the coordinate and orientation conventions already
> used by `rational_linear_algebra.py`?

**Refinement record**: §3's first version framed the remaining scope
question too coarsely, as "mirror all of `nullspace_over_Q`" versus
"prove existence non-executably." A sharper middle route exists —
extend `solve_over_Q`'s own elimination on an augmented `[D | r | I_m]`
matrix, so an inconsistent row's identity-block entries directly give
the separating certificate, with no need for a full nullspace *basis*
at all. §3 is rewritten around this route (now called Route C2) and
verified directly: implemented against the real `rational_linear_
algebra.py` functions and run on `FourCycleObstruction.v`'s own
concrete data, it extracts `y = (-1,-1,-1,1)`, `c = -5` — this
repository's own already-declared canonical cycle `z` and its own
recorded pairing, exactly, not merely some other valid witness. The
refined, narrower governing question this document now answers:

> Can the repository's exact Gauss-Jordan solver be refined into a
> proof-producing alternative procedure which, for every rational
> system `D b = r`, returns either a checked repair witness `b` or a
> checked normalised separator `y` satisfying `transpose(D) @ y = 0`
> and `dot(y, r) == 1`, without first formalising a complete nullspace
> basis algorithm? Yes — see §3.

## 0. The orientation convention, resolved by tracing the real code

Checked directly against `rational_linear_algebra.py` and
`refinement_checker.py`, not assumed:

- A coboundary or refinement matrix (`delta0`, `rho_star`) is `List[List[Fraction]]`, **rows indexed by the target space, columns by the source space** — an `M x N` matrix for a map `C^0 (dim N) -> C^1 (dim M)`. It acts on a **column** vector `b` (length `N`) via `mat_vec(matrix, b)`, left-multiplication: `result[i] = sum_j matrix[i][j] * b[j]`.
- A certificate/cycle `z` or `y` is a **plain vector** (`List[Fraction]`, length `M`, matching the target space's dimension) — never itself run through `transpose`. It pairs against a target-space vector `x` via `dot(z, x) = sum_i z[i] * x[i]`, i.e. as a covector/row vector under the inner product, without ever being reshaped into a `1 x M` matrix.
- **The annihilation condition** — "`z` annihilates every coboundary," i.e. `dot(z, mat_vec(D, b)) == 0` for all `b` — is *computed*, exactly, as membership in `nullspace_over_Q(transpose(D))`: the right-nullspace of the transposed matrix. This is not a documentation choice; it is what `refinement_checker.py`'s own E0 check literally does (`Z1_coarse = nullspace_over_Q(transpose(delta0_coarse))`), and it is the standard fact `dot(z, D @ b) = dot(transpose(D) @ z, b)` for all `b` iff `transpose(D) @ z = 0`.
- **The pushforward on cycles** (`rho_*`, informally "the transpose of `rho_star`" per `ExactnessReflection.v`'s own header) is computed as `mat_vec(transpose(rho_star), z)` — confirming that operation, too, is transpose-then-`mat_vec`, never a bespoke row-vector product.

**Resolved orientation, stated once, to be used everywhere below**: for
`D : M x N` (rows = target/`C1`, columns = source/`C0`), a certificate
`y` is a length-`M` plain vector, the annihilation condition is `D^T @
y = 0` (computed via `nullspace_over_Q(transpose(D))`), and evaluation
against a residue `r` (length `M`, in `C1`) is `dot(y, r)`. In the row-
vector notation the proposal used, `y*D = 0` (`y` a `1 x M` row, `D` an
`M x N` matrix, `y*D` a `1 x N` row) is the *same fact* as `D^T @ y = 0`
under this repository's actual column-vector convention — not a
different equation requiring a separate choice. Any Rocq statement,
and any future Python cross-check, should use `D^T @ y = 0` and `dot(y,
r)`, matching `nullspace_over_Q`/`dot` exactly, not a row-vector
formulation that would need its own, separately justified translation
layer.

## 1. The normalised theorem, and why it is the right target

The proposal's own correction is adopted directly: the existence
theorem should be stated in normalised form,

```text
r notin im(D)   iff   exists y, transpose(D) @ y = 0  and  dot(y, r) == 1
```

not merely `dot(y, r) <> 0`. Over `Q`, this is free once the
unnormalised form is available: given any `y0` with `transpose(D) @ y0
= 0` and `dot(y0, r) <> 0`, `y := vscale (1 / dot(y0, r)) y0` satisfies
`dot(y, r) == 1` (using `Q`'s field structure — every non-zero rational
has a multiplicative inverse) and `transpose(D) @ y = 0` is preserved by
scaling (linearity of `mat_vec`/`transpose` application in the second
argument, already available from this repository's existing `IsLinear`-
style reasoning). The normalised form is strictly more useful
downstream: a canonical certificate, a directly checkable witness (`==
1` is a sharper, more specific check than `<> 0`), and an exact match
for what an extraction-style corollary (D5) would want to hand a
caller.

## 2. The two-layer architecture

### Abstract interface (already named in `CYCLE_QUOTIENT_DUALITY_SPEC.md`)

```coq
Definition SeparatesOutside (S : VSpace) (B : carrier S -> Prop) : Prop :=
  forall x : carrier S,
    ~ B x ->
    exists phi : carrier S -> Q,
      IsLinearFunctional S phi /\ Annihilator S B phi /\ ~ (phi x == 0).
```

D1's hard direction, D2's mirror, and D4 should all be stated *only* in
terms of this interface, exactly as already decided — they should not
know, or need to know, that separation was proved by Gauss-Jordan
elimination on concrete matrices. This document does not revisit that
decision; it answers what discharges the interface.

### Concrete discharge, matching §0's conventions exactly

```coq
Definition RatVec (n : nat) : Type := list Q.   (* length-n, matching Python's List[Fraction] *)
Definition RatMatrix (m n : nat) : Type := list (RatVec n).   (* m rows, matching List[List[Fraction]] *)

(* mat_vec, transpose, dot: direct Rocq mirrors of rational_linear_algebra.py's
   same-named functions, operating on lists exactly as the Python does. *)

Theorem separation_for_finite_rational_image :
  forall (m n : nat) (D : RatMatrix m n) (r : RatVec m),
    ~ (exists b : RatVec n, VecEq (mat_vec D b) r) ->
    exists y : RatVec m,
      VecEq (mat_vec (transpose D) y) (zero_vec n) /\ dot y r == 1.
```

`VecEq` is componentwise `Qeq`, not Leibniz `=` — the same discipline
`AssociatorResidueRepair.v`'s `ceq` generalisation and
`CYCLE_QUOTIENT_DUALITY_SPEC.md`'s `IsLinearFunctional` both already
adopted, for the same reason: `Q`'s Leibniz equality is too strict for
this repository's own representation of rationals, confirmed concretely
in that document's own `QSpace` non-constructibility finding.

## 3. What proving this theorem actually requires — refined and narrowed

The first version of this section framed the choice as "mirror all of
`nullspace_over_Q`" versus "prove existence abstractly, non-
executably." That framing was too coarse. Certificate completeness
(D4) needs exactly one separating witness per non-repairable residue —
it does not need a full nullspace *basis*, and building one (pivot
selection across every column, free-column basis extraction for the
*entire* nullspace) is surplus machinery for this specific theorem,
even though `nullspace_over_Q` happens to compute one as part of how
`refinement_checker.py`'s E0 check works.

**The narrower, certificate-producing route**: `solve_over_Q` already
performs Gauss-Jordan elimination on the augmented matrix `[D | r]` and
detects inconsistency exactly when a row reduces to `[0 ... 0 | c]`
with `c <> 0`. Augmenting further, to `[D | r | I_m]`, and applying the
*same* row operations `solve_over_Q` already performs, means that when
an inconsistent row appears it has the form `[0 ... 0 | c | y]` — and
because every row of the reduced matrix is some linear combination of
the *original* rows (row operations are exactly: swap, scale, subtract
a multiple of another row), the `I_m`-block entries `y` of that specific
row record *which* linear combination produced it. That gives directly:
`y^T D = 0` (the combination annihilates every column of `D`, since the
`D`-block of that row is all zero) and `y^T r = c` (the same combination
applied to `r` gives the recorded inconsistency `c`). Rescaling by
`c^{-1}` gives the normalised certificate `dot(y, r) == 1` for free (§1).

**Checked, not merely reasoned about**: implemented this exact
augmented-elimination procedure directly against
`rational_linear_algebra.py`'s real `mat_vec`/`transpose`/`dot`, run
against three cases — a synthetic inconsistent `3x2` system, a
consistent `2x2` system (confirming the primal branch still works
unchanged), and, most tellingly, `FourCycleObstruction.v`'s own
concrete `delta0`/`r = (1,1,1,-2)` matrix (translated to the `RatMatrix`
representation for this check only — see §4's own note that this
translation is not free in Rocq). On the real four-cycle data, the
extracted, un-normalised certificate is `y = (-1,-1,-1,1)` with `c =
-5` — **exactly** the paper's own hand-declared cycle `z = (-1,-1,-1,1)`
and its own recorded pairing `-5`, not merely *some* valid separating
functional. The augmented-elimination procedure, run on the repository's
own central example, reproduces the repository's own canonical witness
exactly. That is strong, concrete evidence this is the right mechanism,
not just an elegant one on paper.

**The fork, restated more precisely than "mirror everything" versus
"prove nothing executable"**:

- **Route C1 — full nullspace verification.** Verify
  `nullspace_over_Q`'s complete algorithm: pivot selection, full row
  reduction, free-column basis extraction, and a proof the result
  spans the entire nullspace. Connects directly to the existing E0
  implementation, which genuinely needs a full cycle-space *basis* (to
  check span-coverage, not just non-emptiness) — valuable, but strictly
  more than certificate completeness by itself requires.
- **Route C2 — certificate-producing elimination.** Verify only the
  augmented procedure above: `solve_over_Q` extended to return either a
  repair witness `b` or a normalised separating certificate `y`, never
  a full basis. Closes the immediate gap D4 needs with substantially
  less infrastructure than C1, while still being a real, executable,
  third independent implementation of the same elimination mechanism
  this repository already has in Python (and, for a narrower purpose,
  OCaml).
- **Route C3 — pure existence.** Prove the alternative theorem (§3.1)
  by induction on dimension, with no executable decision procedure.
  Proves the mathematics; does not verify the computational mechanism,
  and leaves the gap between the abstract layer and the real Python
  computation exactly as open as before, one layer further down.

**Recommendation: Route C2.** It is exact, constructive, executable,
directly certificate-producing, derived from the same elimination
mechanism `solve_over_Q` already uses (not a parallel, independently-
motivated algorithm), narrower than a full verified nullspace library,
and — per the check above — already confirmed to reproduce this
repository's own canonical witness on its own central example. Route C1
remains valuable, but as a separate, later undertaking if the actual
goal becomes verifying E0's cycle-*coverage* computation (which
genuinely needs a basis) rather than certificate completeness alone.

### 3.1 The theorem C2 actually produces

The right theorem is not `separation_for_finite_rational_image` stated
as a bare implication from non-repairability. It is a constructive
alternative — repair witness or separating certificate, exactly one,
never neither:

```coq
Theorem rational_repair_or_separator :
  forall (m n : nat) (D : RatMatrix m n) (r : RatVec m),
    (exists b : RatVec n, VecEq (mat_vec D b) r)
    \/
    (exists y : RatVec m,
       VecEq (mat_vec (transpose D) y) (zero_vec n) /\ dot y r == 1).

Corollary separation_for_finite_rational_image :
  forall (m n : nat) (D : RatMatrix m n) (r : RatVec m),
    ~ (exists b : RatVec n, VecEq (mat_vec D b) r) ->
    exists y : RatVec m,
      VecEq (mat_vec (transpose D) y) (zero_vec n) /\ dot y r == 1.
```

The two branches are disjoint — if both a repair witness `b` and a
certificate `y` existed simultaneously, `1 = dot(y, r) = dot(y, mat_vec
D b) = dot(mat_vec (transpose D) y, b) = dot(zero_vec, b) = 0`, a
contradiction — so this is a genuine constructive exact alternative
(a Farkas'-lemma-shaped statement for this specific finite rational
setting), not merely an existence theorem with a separately-noted
non-overlap fact. `SeparatesOutside`'s own discharge (§2) is the
corollary; the alternative theorem is the stronger, more directly
useful object, and matches what the augmented elimination procedure
actually computes — the code produces one or the other, never merely
"exists," so the theorem it earns should say the same thing.

## 4. The smallest first step, if a first step is wanted before the general theorem

Consistent with this repository's own stated pattern (identify a
precise use case, find the minimal theorem, verify it concretely,
abstract only what is reused) — and consistent with
`FourCycleObstruction.v`'s own precedent, which instantiates
`AssociatorResidueRepair.v`'s abstract theorem concretely over the
paper's own numbers rather than reproving generality first — the
smallest possible discharge of `SeparatesOutside` is not the general `m
x n` theorem at all. It would be a concrete instance for one matrix.

**A representational mismatch to flag before assuming that instance is
free**: `FourCycleObstruction.v`'s actual concrete data is *not* a
`RatMatrix`/`RatVec` (§2's `list Q`-based representation, chosen to
mirror `rational_linear_algebra.py`'s own `List[List[Fraction]]`
directly). It is a bespoke, fixed-size record —

```coq
Record vec4 := mkvec4 { v0 : Q; v1 : Q; v2 : Q; v3 : Q }.
Definition delta0 (b : vec4) : vec4 :=
  mkvec4 (v1 b - v0 b) (v2 b - v1 b) (v3 b - v2 b) (v3 b - v0 b).
Definition r : vec4 := mkvec4 1 1 1 (-2).
Definition z : vec4 := mkvec4 (-1) (-1) (-1) 1.
```

— with `delta0` a hand-written function on named fields, not a matrix
applied via `mat_vec`. Checked directly, not assumed: instantiating
`separation_for_finite_rational_image` (§2) against this file's own
`r`/`delta0` is therefore not a free specialisation of the general
theorem to `n = 4`; it would need either (a) a translation lemma between
`vec4` and a length-4 `RatVec`, proved once and reusable, or (b) a
second, independent proof of the same normalised-separation fact stated
directly in `vec4`'s own terms, mirroring `FourCycleObstruction.v`'s own
existing style rather than reusing §2's list-based machinery. Neither is
large, but neither is nothing, and the choice affects whether this
document's `RatMatrix` representation (§2) or `FourCycleObstruction.v`'s
own `vec4` representation ends up as the one future files actually
build on.

Whichever representation is used, the target is the same normalised
fact, and §3's own check already computed the actual witness rather
than leaving it as "computable in principle": running the augmented-
elimination procedure on this file's own `delta0`/`r` (translated to
`RatMatrix` for that check only) extracts `y = (-1,-1,-1,1)`,
`c = -5` — this file's own `z` and its own recorded pairing, exactly,
not merely some other valid separator. In `vec4` terms the normalised
certificate is `pairing y_hat r == 1` for `y_hat := vscale (-1/5) z`,
using `z`'s own already-proved `cycle z` and `pairing z r == -5` facts
(`FourCycleObstruction.v`'s own `four_cycle_not_repairable`). This would
not discharge `SeparatesOutside` for the abstract `VSpace`-level
interface (it says nothing about the general finite case, only one
matrix), but it would give D4's forward direction a first genuinely
concrete, checked instance — mirroring exactly how
`FourCycleObstruction.v` already gave the *reverse* implication
(`nonzero_cycle_pairing_implies_nonexact`) its own first concrete
instance, before any general theory of certificate completeness
existed.

## 5. What this document does not claim

- That `rational_repair_or_separator` or `separation_for_finite_
  rational_image` (§3.1) has been proved, or even fully stated in a
  compiling Rocq file. Both are stated here as the recommended target,
  not a result. The augmented-elimination *procedure* they would
  formalise was checked directly (§3), in Python against the real
  `rational_linear_algebra.py` functions — the Rocq proof that this
  procedure is correct, for arbitrary `m x n` inputs, does not yet
  exist.
- That Route C1 (full nullspace verification) has been ruled out
  permanently — §3 recommends C2 first and defers C1, not never; C1
  remains the right route if the actual future goal is verifying E0's
  cycle-*coverage* computation specifically, which genuinely needs a
  basis rather than one certificate.
- That the four-cycle's extracted certificate matching `z` exactly (§3,
  §4) generalises to every input — it is one striking, concrete
  confirmation on the repository's own central example, not a proof
  that the augmented-elimination procedure is correct in general.
- That the smallest first step (§4, the concrete four-cycle instance)
  is a substitute for the general theorem `SeparatesOutside` actually
  needs at the `VSpace` level — it would be a first checked instance,
  not a discharge of the abstract interface, and still needs the §4
  representational-mismatch decision (translate `vec4`, or reprove
  directly in `vec4`'s own terms) resolved either way.
- That `RatVec`/`RatMatrix`/`VecEq` (§2) have been added to any tracked
  file, or that `list Q` is the final representation to adopt rather
  than, for instance, a fixed-length vector type.
- That this is the next authorized phase. Per every prior phase in this
  research line, starting any tracked implementation from this
  document — including the smallest four-cycle-only instance in §4, or
  the augmented-elimination check's own Python prototype becoming a
  tracked file anywhere — needs its own explicit go-ahead.
