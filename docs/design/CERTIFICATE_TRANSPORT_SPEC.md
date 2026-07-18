# Certificate Transport Under Presentation Change (R24)

**Status (2026-07-15): PROVED and committed.** `rocq/InvertiblePresentation.v`,
`rocq/CertificateTransport.v`, and `rocq/R24CertificateTransportExamples.v`
implement and check everything this document originally scoped. This
file has been rewritten from prospective design wording into a record
of what was actually proved, per this repository's own discipline: the
open questions in §5 (original) were resolved by an untracked spike
before any tracked file was written, the spike is reported in full
below, and the theorem statements quoted here are the actual, compiled,
`coqchk`-clean statements, not proposals.

The governing question, answered:

> If the same finite rational system is expressed in two presentations
> related by a *certified invertible linear change of basis* on both
> the repair space and the residue space, do repairability,
> non-repairability, and the exact certificate values transport
> correctly between the two presentations?

Yes, in both directions, exactly (not merely up to scalar), and the
transport promotes to a verdict-invariance theorem, not just witness
manipulation. This is deliberately narrower than "presentation
invariance" in general -- §4 states precisely what is excluded, because
the applied motivation for this document (representation changes
from zoom, resolution, and coordinate-frame changes) mostly does
**not** live inside this narrow class, and claiming otherwise would
repeat the archived scaffold's mistake recorded in
`PRESENTATION_INVARIANCE_SPEC.md` §0.

## 0. What already existed, reused as-is

R22 (`rocq/RationalCanonicalVectors.v`) already had `qcvec n :=
Vector.t Qc n` and its `AbelianVSpace` instance; R24 reuses `qcvec`
directly rather than redefining it. R22's own adjoint identity
technique (proving a matrix-transpose/vector-action fact by induction
on the matrix, not by a full matrix Leibniz identity) turned out to be
exactly the right template for `InvertiblePresentation.v`'s
`dot_qc_mat_vec_adjoint`.

R21 (`rocq/ExactRationalRepairOrSeparator.v`) is **not** a dependency of
any R24 file. §5.3 (below) records why: the spike found `Vector.t Qc n`
smoother than R21's own `list Q`/`VecEq` representation for this
purpose, with no friction cost worth taking on `list Q`'s `Qeq`/setoid
equality just to reuse R21's `mat_vec`/`transpose`/`dot`. R24 defines
its own `MatrixQc`/`dot_qc`/`mat_vec_qc`/`transpose_qc`/`mat_mat_qc`/
`identity_qc` over `qcvec`, independent of R21, matching R22's own
`R21VectorTransport.v` precedent of building a small one-directional
bridge only where one is actually needed (here, none is needed at all
for the mathematics itself; R1's four-cycle numbers are simply
re-entered as `qcvec` literals in the examples file).

## 1. The transformation class, as proved

For `D : MatrixQc m n` (`m` rows = residue space, `n` columns = repair
space, matching R21's own traced convention), a presentation change is
a pair of `InvertibleMatrix` records:

```coq
Record InvertibleMatrix (n : nat) := mkInvertibleMatrix {
  fwd : MatrixQc n n;
  bwd : MatrixQc n n;
  inv_left : mat_mat_qc bwd fwd = identity_qc n;
  inv_right : mat_mat_qc fwd bwd = identity_qc n;
}.
```

`A : InvertibleMatrix n` changes the repair space's basis; `B :
InvertibleMatrix m` changes the residue space's. Explicit two-sided
inverse witnesses are supplied by the caller -- no constructive
rational matrix-inversion procedure was built, resolving §5.1
(original) in favour of the smaller first step, as recommended there.
The transformed system:

```coq
Definition transform_operator (A : InvertibleMatrix n) (B : InvertibleMatrix m)
  (D : MatrixQc m n) : MatrixQc m n :=
  mat_mat_qc (mat_mat_qc (fwd B) D) (bwd A).   (* D' = B D A^{-1} *)

Definition transform_residue (B : InvertibleMatrix m) (r : qcvec m) : qcvec m :=
  mat_vec_qc (fwd B) r.                          (* r' = B r *)
```

## 2. What transports, and how -- traced by an actual compiling proof, not assumed

Given `D b = r`, `b' := transport_repair_vector A b = A b` is a repair
for `D'`, `r'` (`transport_repair`). Given `D^T y = 0` and `y . r = 1`,
`y' := transport_separator_vector B y = B^{-T} y` annihilates `D'^T`
(`transport_separator`) and pairs exactly (`transport_pairing`); both
have proved backward directions
(`transport_repair_backward`/`transport_separator_backward`/
`transport_pairing_reverse`), combining into full `<->`s
(`repairable_iff_transport_repairable`,
`separator_annihilates_iff_transport_annihilates`).

Critically, **the transpose-of-product / inverse-of-transpose
identities this section originally worried about needing were never
proved as matrix identities at all.** The spike found a cleaner route:
every transport theorem is proved at the level of how matrices ACT on
vectors, via a five-step hierarchy that held up exactly as hoped:

1. Matrix multiplication acts associatively on vectors
   (`mat_vec_qc_mat_mat_assoc`).
2. Transpose reverses multiplication under vector action
   (`dot_qc_mat_vec_adjoint`, `dot (D x) y = dot x (D^T y)` -- reused
   directly from R22).
3. A two-sided inverse undoes its own DIRECT action
   (`mat_vec_qc_left_inverse`, pure equational, no nondegeneracy
   needed -- cancelling an invertible matrix's action from both sides
   of an equation is substitution) and undoes its TRANSPOSE's action,
   given nondegeneracy (`mat_vec_qc_transpose_inverse`).
4. The separator/repair/pairing equations, and their backward
   directions, follow by chaining 1-3.
5. Only ONE full matrix Leibniz identity was needed anywhere in the
   entire development: `transpose_qc_involutive` (double transpose is
   the identity), used inside a single supporting lemma
   (`mat_vec_qc_row_dot_assoc`). No `transpose(P.Q) =
   transpose(Q).transpose(P)` identity, and no general
   matrix-inversion or determinant machinery, was ever required.

The one new piece of infrastructure step 3 needed: nondegeneracy of
`dot_qc` (`dot_qc_ext`/`dot_qc_ext_zero`), proved once via standard
basis vectors (`unit_vec`), to promote a pairing-universal fact
("`forall b, dot b v = dot b w`") to the vector Leibniz equality `v =
w`. This is the only place nondegeneracy is needed; `transport_repair`
and its backward direction need no nondegeneracy at all (cancelling an
invertible matrix's *direct* action, as opposed to showing a vector is
exactly zero, is pure substitution).

## 3. The theorems actually proved

```coq
Theorem transport_repair :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r : qcvec m) (b : qcvec n),
    mat_vec_qc D b = r ->
    mat_vec_qc (transform_operator A B D) (transport_repair_vector A b)
    = transform_residue B r.

Theorem transport_separator :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (y : qcvec m),
    mat_vec_qc (transpose_qc D) y = Vector.const (Q2Qc 0) n ->
    mat_vec_qc (transpose_qc (transform_operator A B D))
               (transport_separator_vector B y) = Vector.const (Q2Qc 0) n.

Theorem transport_pairing :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r y : qcvec m),
    dot_qc y r = Q2Qc 1 ->
    dot_qc (transport_separator_vector B y) (transform_residue B r) = Q2Qc 1.

Theorem repairable_iff_transport_repairable :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r : qcvec m),
    (exists b, mat_vec_qc D b = r) <->
    (exists b', mat_vec_qc (transform_operator A B D) b' = transform_residue B r).

Corollary nonrepairable_iff_transport_nonrepairable : (* the negation of the above *)

Theorem separator_annihilates_iff_transport_annihilates :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (y : qcvec m),
    mat_vec_qc (transpose_qc D) y = Vector.const (Q2Qc 0) n <->
    mat_vec_qc (transpose_qc (transform_operator A B D))
               (transport_separator_vector B y) = Vector.const (Q2Qc 0) n.

Theorem transport_pairing_reverse : (* the converse of transport_pairing *)
Corollary transport_normalized_separator : (* transport_separator /\ transport_pairing, bundled *)
```

`PresentationEquivalence` (`rocq/CertificateTransport.v`) bundles a
`D`/`D'`/`r`/`r'` quadruple with the `InvertibleMatrix` witnesses and
the two transport equations, so later results can depend on one clean
proposition instead of repeatedly unfolding `transform_operator`/
`transform_residue`; `repairable_iff_presentation_equivalent` restates
the repair iff in terms of it.

All of the above -- and every supporting lemma in
`InvertiblePresentation.v` -- is `coqchk`-clean: `make check-rocq-trust`
reports the full 37-module dependency closure introduces no
project-added axioms or admitted proofs.

## 4. What this explicitly does not cover -- stated because the applied motivation mostly lives here, not in §1-3

None of the following are invertible linear changes of basis, and the
proved theorems say nothing about them:

- lossy downsampling or resolution reduction;
- cropping or field-of-view restriction (changes the *dimension*, not
  just the basis);
- occlusion (information genuinely disappears, not merely re-expressed);
- nonlinear projection (e.g. perspective, bearing-range transforms);
- feature re-extraction or re-detection after resampling;
- thresholding;
- reassociation of detections between frames;
- any transformation that is not a bijection on the same-dimensional
  space it maps.

Zoom, in particular, is usually **not** a single invertible linear map
in the sense §1 needs: it typically combines a genuinely invertible
scale change with a non-invertible crop or resolution change. A
zoom scenario would need to be decomposed into its
invertible part (in scope here) and its lossy part (needing a
refinement/quotient theory this document does not attempt) before this
theorem applies to any of it. This document does not perform that
decomposition for any real deployment scenario -- that is exactly the
domain-adapter-level work `docs/design/R21_CERTIFICATE_TCB.md` already
says is out of scope for the calculus itself.

Also not covered: **affine** changes of presentation (a translation
plus a linear map, `x' = Bx + t`) are not linear maps and are not
covered by §1's `D' = B D A^{-1}` form -- pixel-coordinate translation
(part of the crop/pan scenario) is affine, not linear.
Whether to extend to affine transformations is deferred to a follow-up
document, not attempted here or implicitly assumed by any proof above.

## 5. The spike's resolution of the original open questions

This section is now a historical record of how the questions this
document originally left open (§5, prior revision) were actually
resolved, checked directly rather than decided in the abstract.

1. **Matrix representation of `A`, `B`, and their inverses.** Resolved:
   explicit two-sided-inverse witnesses (`InvertibleMatrix`), not a
   constructive inversion procedure -- confirmed the smaller, sufficient
   first step; no need for a rational matrix-inversion development was
   ever exposed.
2. **Whether to prove the transpose/inverse identities abstractly or
   per-instance.** Resolved: abstractly, once, for arbitrary invertible
   matrices (§2 above) -- and at LOWER cost than feared, since the
   abstract route needed no new "general matrix-inverse algebra" beyond
   associativity, the adjoint identity, and the two inverse-action
   facts. No `transpose_mat_mul`/`inverse_transpose_comm`-style matrix
   identity was needed.
3. **`list Q` or `Vector.t Qc n`.** Resolved in favour of `qcvec`
   (`Vector.t Qc n`), the OPPOSITE of this document's original leaning.
   The original reasoning (`list Q` is what R21's own theorems and any
   adapter would manipulate) turned out not to matter: R24 needs no
   bridge to R21 at all (see §0), and `Qc`'s Leibniz-equality ring laws
   made every identity in `InvertiblePresentation.v` go through with
   ordinary `rewrite`, avoiding `list Q`'s `Qeq`/setoid friction
   entirely -- the same reason R22 chose `qcvec` over `list Q`.
4. **Affine transformations.** Still deferred to a follow-up document,
   as recommended; not attempted here.
5. **Certificate-schema changes.** Still out of scope for this Rocq
   development, as recommended -- no `presentation_transform` schema
   field was added, and none of R21's certificate pipeline files were
   touched. Whether one is needed remains a question for a concrete
   adapter, not decided here.

## 6. Instantiations

`rocq/R24CertificateTransportExamples.v` checks four concrete cases,
each both directly (`vm_compute`/`Qc_is_canon`) and by applying the
generic theorems:

- a self-inverse 2-dimensional coordinate swap;
- a nonzero rational scaling (x3 on one coordinate, inverse x1/3);
- an elementary shear (row addition, +3x one coordinate onto another,
  inverse -3x back);
- R1's own four-cycle obstruction (`D4`, `r4`, `y4` exactly as in
  `rocq/R21CycleQuotientBridge.v`'s `FourCycleExample`, restated over
  `qcvec`), transported by a residue-space coordinate swap: the
  original separator is verified accepted, the transported separator
  verified to annihilate the transformed matrix, the pairing verified
  to remain exactly 1, and back-transport verified to recover the
  original separator exactly.

One implementation wrinkle surfaced and is recorded in that file's own
header rather than left for the next person to rediscover as if it
were a soundness bug: summing several `1/5` terms to exactly `0` can
reach the same canonical `Qc` value via two computation paths whose
`canon` proof components differ syntactically even though the
underlying rational values agree (Coq has no default proof irrelevance
for `Prop`) -- the repair is `Qc_is_canon` (an existing `Qcanon`
lemma), not a custom extensionality axiom.

## 7. What this document does not claim

- That this covers, decomposes, or says anything about any actual
  zoom, resolution, or coordinate-frame scenario -- §4 states
  plainly that most such scenarios are not purely linear and invertible,
  and no decomposition of a real scenario is attempted here.
- That affine transformations, lossy transformations, or any of §4's
  excluded cases are covered, planned for this same file, or scoped at
  all beyond being named as explicitly out of scope.
- That a certificate-schema field for presentation transport exists or
  is needed -- §5.5 leaves this for a concrete adapter to decide.
- That R23 (complete obstruction signatures), compositional transport,
  or any other later result has been implemented here -- R24 is
  complete and self-contained as committed; anything built on top of
  `PresentationEquivalence` is future work, not claimed by this
  document.
