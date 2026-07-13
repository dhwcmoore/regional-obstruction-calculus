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

The governing question, unchanged from how it was posed:

> What is the smallest exact rational matrix representation in Rocq
> that can prove `r notin im(D) iff exists y, y*D = 0 and y(r) = 1`,
> while matching the coordinate and orientation conventions already
> used by `rational_linear_algebra.py`?

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

## 3. What proving this theorem actually requires — the real scope question

This is not a small lemma. `nullspace_over_Q` and `solve_over_Q` in
`rational_linear_algebra.py` are a real, general Gauss-Jordan
elimination implementation — pivot selection, row reduction, free-
column basis extraction — for arbitrary `m x n` matrices. Matching that
generality in Rocq means one of two real, differently-sized
undertakings, and this document does not choose between them:

- **Mirror the algorithm.** Write a Rocq `mat_vec`/`transpose`/Gauss-
  Jordan elimination function structurally following the Python
  implementation (a `fixpoint` over rows/columns, exactly as
  `nullspace_over_Q`'s own `for col in range(n)` loop does), then prove
  its output satisfies `separation_for_finite_rational_image`'s
  conclusion. This is executable, decidable, and would give a genuine
  third independent implementation of the same algorithm this
  repository already has in Python and (for a narrower purpose)
  OCaml — a real, substantial, but *bounded and precedented* piece of
  work, matching this repository's own established "independently
  written, not extracted" discipline (`ocaml/refinement_checker.ml`'s
  own header) applied to a third language for the first time.
- **Prove existence abstractly, by induction on dimension, without
  building an executable elimination function.** A pure existence proof
  (rank-nullity-style induction: either `r` is already expressible or
  adding one more constraint strictly reduces a free-dimension count)
  can establish `separation_for_finite_rational_image` without ever
  producing a decision procedure — smaller in one sense (no executable
  algorithm to verify terminates and is correct step by step), but
  loses the direct, checkable correspondence to `nullspace_over_Q`'s own
  actual computation that mirroring the algorithm would give, and
  arguably answers a different, weaker question than "does this
  repository's actual Python computation correspond to a Rocq proof."

**This document's own recommendation, stated but not decided**:
mirroring the algorithm (the first option) is more consistent with why
Route C was chosen over Route A alone — the whole point was to close
the gap between the abstract layer and `rational_linear_algebra.py`'s
real computation (`CYCLE_QUOTIENT_DUALITY_SPEC.md` §0), and an existence-
only proof would leave that gap exactly as open as it is today, just
one abstraction layer further down. But mirroring the algorithm is
real, scoped work, not a one-file afternoon, and should be its own
explicitly authorized phase, not started as a side effect of this
document.

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
fact: exhibiting a witness `y` (computable once, by hand or by running
`nullspace_over_Q`/`solve_over_Q` on this file's own matrix and reading
off the answer) with `z`'s own annihilation property and `dot(y, r) ==
1` (or, in `vec4` terms, `pairing y r == 1` after rescaling `z`, since
`pairing z r == -5` already, and `z` already satisfies `cycle z` — see
`FourCycleObstruction.v`'s own `four_cycle_not_repairable`). This would
not discharge `SeparatesOutside` for the abstract `VSpace`-level
interface (it says nothing about the general finite case, only one
matrix), but it would give D4's forward direction a first genuinely
concrete, checked instance — mirroring exactly how
`FourCycleObstruction.v` already gave the *reverse* implication
(`nonzero_cycle_pairing_implies_nonexact`) its own first concrete
instance, before any general theory of certificate completeness
existed.

## 5. What this document does not claim

- That `separation_for_finite_rational_image` (§2) or
  `separation_for_the_four_cycle` (§4) has been proved, or even fully
  stated in a compiling Rocq file. Both are stated here as targets, not
  results.
- That mirroring `nullspace_over_Q`'s algorithm in Rocq (§3) has been
  attempted, scoped in detail, or estimated for size beyond "real,
  substantial, bounded."
- That the choice between mirroring the algorithm and an abstract
  existence proof (§3) has been made. Both remain open; this document
  states their trade-off, not a decision.
- That the smallest first step (§4, the concrete four-cycle instance)
  is a substitute for the general theorem `SeparatesOutside` actually
  needs at the `VSpace` level — it would be a first checked instance,
  not a discharge of the abstract interface.
- That `RatVec`/`RatMatrix`/`VecEq` (§2) have been added to any tracked
  file, or that `list Q` is the final representation to adopt rather
  than, for instance, a fixed-length vector type.
- That this is the next authorized phase. Per every prior phase in this
  research line, starting any tracked implementation from this
  document — including the smallest four-cycle-only instance in §4 —
  needs its own explicit go-ahead.
