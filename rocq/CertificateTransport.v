(*
   CertificateTransport.v

   R24, layer 2: the headline theorem. Certified invertible linear
   presentation changes on the repair space (`A`) and residue space
   (`B`) transport repair witnesses, separator witnesses, and separator
   pairings EXACTLY, in both directions -- and therefore transport the
   repairable-versus-obstructed VERDICT, not merely individual
   witnesses:

     r in im(D)      <->  r' in im(D')
     r not in im(D)  <->  r' not in im(D')

   where D' = transform_operator A B D = B D A^{-1} and
   r' = transform_residue B r = B r, exactly
   `docs/design/CERTIFICATE_TRANSPORT_SPEC.md` §1-2's formulas.

   The forward halves (`transport_repair`, `transport_separator`,
   `transport_pairing`) were the untracked spike's own content, each
   proved via `InvertiblePresentation.v`'s vector-action lemmas
   (associativity, the transpose adjoint identity, and the two
   inverse-action facts) rather than any full matrix Leibniz identity
   beyond what that file already established. The backward halves
   (`transport_repair_backward`, `transport_separator_backward`,
   `transport_pairing_reverse`) are new, and stay at the same level:
   `transport_repair_backward` needs only `mat_vec_qc_left_inverse` and
   `f_equal` (no nondegeneracy -- cancelling an invertible matrix's
   DIRECT action from both sides of an equation is pure substitution);
   `transport_separator_backward` needs the full chain (adjoint +
   associativity + both inverse-action facts + nondegeneracy) because it
   is proving a vector equals zero, not merely simplifying an existing
   equation.

   `PresentationEquivalence` bundles a `D`/`D'`/`r`/`r'` quadruple with
   the `InvertibleMatrix` witnesses and the two transport equations, so
   later results (R23 signature transport, compositional transport,
   application-facing presentation changes) can depend on one clean
   proposition instead of repeatedly unfolding `transform_operator`/
   `transform_residue`.

   SCOPE: exactly `InvertiblePresentation.v`'s -- certified invertible
   LINEAR presentation changes over exact rationals; witness transport,
   pairing preservation, and verdict invariance. It does NOT cover
   translations, affine maps, projections, cropping, resolution loss,
   dimension changes, nonlinear transformations, approximate numerical
   equivalence, or arbitrary refinement/common-subdivision. The correct
   summary phrase is invariance under CERTIFIED INVERTIBLE LINEAR
   presentation changes, not "presentation invariance" unqualified.

   Depends on InvertiblePresentation.v only.
*)

Require Import Coq.QArith.QArith.
Require Import Coq.QArith.Qcanon.
Require Import Coq.Vectors.Vector.
Require Import RationalCanonicalVectors.
Require Import InvertiblePresentation.

(* ------------------------------------------------------------------ *)
(* Repair witness transport, both directions, and the verdict-invariance
   iff this section exists to establish. *)
(* ------------------------------------------------------------------ *)

Theorem transport_repair :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r : qcvec m) (b : qcvec n),
    mat_vec_qc D b = r ->
    mat_vec_qc (transform_operator A B D) (transport_repair_vector A b) = transform_residue B r.
Proof.
  intros m n A B D r b Hb.
  unfold transform_operator, transform_residue, transport_repair_vector.
  rewrite (mat_vec_qc_mat_mat_assoc m n n (mat_mat_qc (fwd B) D) (bwd A) (mat_vec_qc (fwd A) b)).
  rewrite (mat_vec_qc_left_inverse n (fwd A) (bwd A) (inv_left A) b).
  rewrite (mat_vec_qc_mat_mat_assoc m m n (fwd B) D b).
  rewrite Hb.
  reflexivity.
Qed.

Lemma transport_repair_backward :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r : qcvec m) (b' : qcvec n),
    mat_vec_qc (transform_operator A B D) b' = transform_residue B r ->
    mat_vec_qc D (mat_vec_qc (bwd A) b') = r.
Proof.
  intros m n A B D r b' Hb'.
  unfold transform_operator, transform_residue in Hb'.
  assert (Heq : mat_vec_qc (fwd B) (mat_vec_qc D (mat_vec_qc (bwd A) b')) = mat_vec_qc (fwd B) r).
  { rewrite <- (mat_vec_qc_mat_mat_assoc m m n (fwd B) D (mat_vec_qc (bwd A) b')).
    rewrite <- (mat_vec_qc_mat_mat_assoc m n n (mat_mat_qc (fwd B) D) (bwd A) b').
    exact Hb'.
  }
  pose proof (f_equal (mat_vec_qc (bwd B)) Heq) as Heq2.
  rewrite (mat_vec_qc_left_inverse m (fwd B) (bwd B) (inv_left B) (mat_vec_qc D (mat_vec_qc (bwd A) b'))) in Heq2.
  rewrite (mat_vec_qc_left_inverse m (fwd B) (bwd B) (inv_left B) r) in Heq2.
  exact Heq2.
Qed.

Theorem repairable_iff_transport_repairable :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r : qcvec m),
    (exists b, mat_vec_qc D b = r) <->
    (exists b', mat_vec_qc (transform_operator A B D) b' = transform_residue B r).
Proof.
  intros m n A B D r. split.
  - intros [b Hb]. exists (transport_repair_vector A b). apply (transport_repair m n A B D r b Hb).
  - intros [b' Hb']. exists (mat_vec_qc (bwd A) b'). apply (transport_repair_backward m n A B D r b' Hb').
Qed.

Corollary nonrepairable_iff_transport_nonrepairable :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r : qcvec m),
    ~ (exists b, mat_vec_qc D b = r) <->
    ~ (exists b', mat_vec_qc (transform_operator A B D) b' = transform_residue B r).
Proof.
  intros m n A B D r.
  split; intros H Hex; apply H.
  - apply <- (repairable_iff_transport_repairable m n A B D r). exact Hex.
  - apply -> (repairable_iff_transport_repairable m n A B D r). exact Hex.
Qed.

(* ------------------------------------------------------------------ *)
(* Separator witness transport, both directions -- the annihilation
   half of the verdict-invariance argument. *)
(* ------------------------------------------------------------------ *)

Theorem transport_separator :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (y : qcvec m),
    mat_vec_qc (transpose_qc D) y = Vector.const (Q2Qc 0) n ->
    mat_vec_qc (transpose_qc (transform_operator A B D)) (transport_separator_vector B y)
    = Vector.const (Q2Qc 0) n.
Proof.
  intros m n A B D y Hsep.
  unfold transform_operator, transport_separator_vector.
  apply dot_qc_ext_zero. intros b.
  rewrite <- (dot_qc_mat_vec_adjoint m n
                (mat_mat_qc (mat_mat_qc (fwd B) D) (bwd A)) b
                (mat_vec_qc (transpose_qc (bwd B)) y)).
  rewrite (mat_vec_qc_mat_mat_assoc m n n (mat_mat_qc (fwd B) D) (bwd A) b).
  rewrite (mat_vec_qc_mat_mat_assoc m m n (fwd B) D (mat_vec_qc (bwd A) b)).
  rewrite (dot_qc_mat_vec_adjoint m m (fwd B)
                (mat_vec_qc D (mat_vec_qc (bwd A) b))
                (mat_vec_qc (transpose_qc (bwd B)) y)).
  rewrite (mat_vec_qc_transpose_inverse m (fwd B) (bwd B) (inv_left B) y).
  rewrite (dot_qc_mat_vec_adjoint m n D (mat_vec_qc (bwd A) b) y).
  rewrite Hsep.
  apply mat_vec_qc_zero_dot.
Qed.

Lemma transport_separator_backward :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (y : qcvec m),
    mat_vec_qc (transpose_qc (transform_operator A B D)) (transport_separator_vector B y)
    = Vector.const (Q2Qc 0) n ->
    mat_vec_qc (transpose_qc D) y = Vector.const (Q2Qc 0) n.
Proof.
  intros m n A B D y Hsep.
  unfold transform_operator, transport_separator_vector in Hsep.
  apply dot_qc_ext_zero. intros x.
  rewrite <- (dot_qc_mat_vec_adjoint m n D x y).
  rewrite <- (mat_vec_qc_transpose_inverse m (fwd B) (bwd B) (inv_left B) y).
  rewrite <- (dot_qc_mat_vec_adjoint m m (fwd B) (mat_vec_qc D x) (mat_vec_qc (transpose_qc (bwd B)) y)).
  rewrite <- (mat_vec_qc_mat_mat_assoc m m n (fwd B) D x).
  rewrite <- (mat_vec_qc_left_inverse n (fwd A) (bwd A) (inv_left A) x) at 1.
  rewrite <- (mat_vec_qc_mat_mat_assoc m n n (mat_mat_qc (fwd B) D) (bwd A) (mat_vec_qc (fwd A) x)).
  rewrite (dot_qc_mat_vec_adjoint m n (mat_mat_qc (mat_mat_qc (fwd B) D) (bwd A)) (mat_vec_qc (fwd A) x)
             (mat_vec_qc (transpose_qc (bwd B)) y)).
  rewrite Hsep.
  apply mat_vec_qc_zero_dot.
Qed.

Theorem separator_annihilates_iff_transport_annihilates :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (y : qcvec m),
    mat_vec_qc (transpose_qc D) y = Vector.const (Q2Qc 0) n <->
    mat_vec_qc (transpose_qc (transform_operator A B D)) (transport_separator_vector B y)
    = Vector.const (Q2Qc 0) n.
Proof.
  intros m n A B D y. split.
  - apply (transport_separator m n A B D y).
  - apply (transport_separator_backward m n A B D y).
Qed.

(* ------------------------------------------------------------------ *)
(* Exact pairing preservation, both directions, and the normalized-
   separator corollary. *)
(* ------------------------------------------------------------------ *)

Theorem transport_pairing :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r y : qcvec m),
    dot_qc y r = Q2Qc 1 ->
    dot_qc (transport_separator_vector B y) (transform_residue B r) = Q2Qc 1.
Proof.
  intros m n A B D r y Hpair.
  unfold transport_separator_vector, transform_residue.
  rewrite (dot_qc_comm m (mat_vec_qc (transpose_qc (bwd B)) y) (mat_vec_qc (fwd B) r)).
  rewrite (dot_qc_mat_vec_adjoint m m (fwd B) r (mat_vec_qc (transpose_qc (bwd B)) y)).
  rewrite (mat_vec_qc_transpose_inverse m (fwd B) (bwd B) (inv_left B) y).
  rewrite (dot_qc_comm m r y).
  exact Hpair.
Qed.

Theorem transport_pairing_reverse :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r y : qcvec m),
    dot_qc (transport_separator_vector B y) (transform_residue B r) = Q2Qc 1 ->
    dot_qc y r = Q2Qc 1.
Proof.
  intros m n A B D r y Hpair.
  unfold transport_separator_vector, transform_residue in Hpair.
  rewrite (dot_qc_comm m y r).
  rewrite <- (mat_vec_qc_left_inverse m (fwd B) (bwd B) (inv_left B) r).
  rewrite (dot_qc_mat_vec_adjoint m m (bwd B) (mat_vec_qc (fwd B) r) y).
  rewrite <- Hpair.
  rewrite (dot_qc_comm m (mat_vec_qc (fwd B) r) (mat_vec_qc (transpose_qc (bwd B)) y)).
  reflexivity.
Qed.

Corollary transport_normalized_separator :
  forall (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m)
         (D : MatrixQc m n) (r y : qcvec m),
    mat_vec_qc (transpose_qc D) y = Vector.const (Q2Qc 0) n ->
    dot_qc y r = Q2Qc 1 ->
    mat_vec_qc (transpose_qc (transform_operator A B D)) (transport_separator_vector B y)
    = Vector.const (Q2Qc 0) n
    /\
    dot_qc (transport_separator_vector B y) (transform_residue B r) = Q2Qc 1.
Proof.
  intros m n A B D r y Hsep Hpair.
  split.
  - exact (transport_separator m n A B D y Hsep).
  - exact (transport_pairing m n A B D r y Hpair).
Qed.

(* ------------------------------------------------------------------ *)
(* PresentationEquivalence: the clean proposition later results should
   depend on, instead of repeatedly unfolding transform_operator/
   transform_residue. `build_presentation_equivalence` is the smart
   constructor for the common case (D'/r' already computed via the
   transform functions), proved by `eq_refl` since the equations hold
   definitionally in that case. *)
(* ------------------------------------------------------------------ *)

Record PresentationEquivalence (m n : nat) (D D' : MatrixQc m n) (r r' : qcvec m) := mkPresentationEquivalence {
  domain_change : InvertibleMatrix n;
  residue_change : InvertibleMatrix m;
  operator_transport : D' = transform_operator domain_change residue_change D;
  residue_transport : r' = transform_residue residue_change r;
}.

Arguments domain_change {m n D D' r r'} _.
Arguments residue_change {m n D D' r r'} _.
Arguments operator_transport {m n D D' r r'} _.
Arguments residue_transport {m n D D' r r'} _.

Definition build_presentation_equivalence
  (m n : nat) (A : InvertibleMatrix n) (B : InvertibleMatrix m) (D : MatrixQc m n) (r : qcvec m)
  : PresentationEquivalence m n D (transform_operator A B D) r (transform_residue B r) :=
  mkPresentationEquivalence m n D (transform_operator A B D) r (transform_residue B r) A B eq_refl eq_refl.

Theorem repairable_iff_presentation_equivalent :
  forall (m n : nat) (D D' : MatrixQc m n) (r r' : qcvec m),
    PresentationEquivalence m n D D' r r' ->
    (exists b, mat_vec_qc D b = r) <-> (exists b', mat_vec_qc D' b' = r').
Proof.
  intros m n D D' r r' [A B HD Hr].
  subst D' r'.
  apply (repairable_iff_transport_repairable m n A B D r).
Qed.
