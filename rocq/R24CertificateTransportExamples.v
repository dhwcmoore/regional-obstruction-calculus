(*
   R24CertificateTransportExamples.v

   R24, layer 3: concrete regression instances of `CertificateTransport.v`
   -- a coordinate swap, a nonzero rational scaling, an elementary shear
   (coordinate addition), and R1's own four-cycle obstruction
   (`rocq/FourCycleObstruction.v` / `rocq/R21CycleQuotientBridge.v`'s
   `D4`/`r4`/`y4`, restated over `qcvec`), transported by a residue-space
   coordinate swap.

   For the four-cycle case, every fact is checked TWO ways: directly by
   computation, and by applying `CertificateTransport.v`'s generic
   theorems. Each catches a different class of mistake -- direct
   computation checks the concrete matrices are what they claim to be;
   theorem application checks that the generic infrastructure actually
   instantiates correctly against a real instance, not merely that both
   routes happen to compute to the same normal form by coincidence.

   IMPLEMENTATION NOTE, since it will otherwise look like a soundness bug
   the next time someone hits it: several of the vector-equality facts
   below cannot be closed by plain `vm_compute; reflexivity`, even though
   the rational values agree. Summing several `1#5` terms to exactly `0`
   (as `D4`/`y4`'s dot products do) can reach the same canonical `Qc`
   value through two different computation paths whose `canon` proof
   components differ syntactically (confirmed with `Set Printing All`:
   one path produced `Qred_involutive 0`, the other `Qred_involutive
   (0#25)`) -- Coq has no default proof irrelevance for `Prop`, so
   `vm_compute; reflexivity` can fail on the whole `Qcmake this canon`
   record even though the `this` (rational) components match. The
   correct repair is `Qc_is_canon` (an existing `Qcanon` lemma, needing
   only `Qeq`, not a custom axiom), applied per vector index via
   `qcvec_eq_nth_Qeq` below.

   Depends on CertificateTransport.v only.
*)

Require Import Coq.QArith.QArith.
Require Import Coq.QArith.Qcanon.
Require Import Coq.Vectors.Vector.
Require Import Coq.Vectors.Fin.
Import VectorNotations.
Require Import RationalCanonicalVectors.
Require Import InvertiblePresentation.
Require Import CertificateTransport.

Lemma qcvec_eq_nth_Qeq : forall (n : nat) (u v : qcvec n),
  (forall p : Fin.t n, (Vector.nth u p : Q) == (Vector.nth v p : Q)) -> u = v.
Proof.
  intros n u v H.
  apply Vector.eq_nth_iff. intros p1 p2 Hp. subst p2.
  apply Qc_is_canon. apply (H p1).
Qed.

(* ------------------------------------------------------------------ *)
(* 1. Coordinate swap (2-dimensional): self-inverse. *)
(* ------------------------------------------------------------------ *)

Definition swap2 : MatrixQc 2 2 :=
  [ [ Q2Qc 0; Q2Qc 1 ] ; [ Q2Qc 1; Q2Qc 0 ] ].

Lemma swap2_self_inverse : mat_mat_qc swap2 swap2 = identity_qc 2.
Proof. vm_compute. reflexivity. Qed.

Definition InvSwap2 : InvertibleMatrix 2 :=
  mkInvertibleMatrix 2 swap2 swap2 swap2_self_inverse swap2_self_inverse.

(* ------------------------------------------------------------------ *)
(* 2. Nonzero rational scaling (2-dimensional: scale coordinate 0 by 3,
   leave coordinate 1 fixed; inverse scales by 1/3). *)
(* ------------------------------------------------------------------ *)

Definition scale2 : MatrixQc 2 2 :=
  [ [ Q2Qc 3; Q2Qc 0 ] ; [ Q2Qc 0; Q2Qc 1 ] ].

Definition scale2_inv : MatrixQc 2 2 :=
  [ [ Q2Qc (1#3); Q2Qc 0 ] ; [ Q2Qc 0; Q2Qc 1 ] ].

Lemma scale2_inv_left : mat_mat_qc scale2_inv scale2 = identity_qc 2.
Proof. vm_compute. reflexivity. Qed.

Lemma scale2_inv_right : mat_mat_qc scale2 scale2_inv = identity_qc 2.
Proof. vm_compute. reflexivity. Qed.

Definition InvScale2 : InvertibleMatrix 2 :=
  mkInvertibleMatrix 2 scale2 scale2_inv scale2_inv_left scale2_inv_right.

(* ------------------------------------------------------------------ *)
(* 3. Elementary shear / coordinate addition (2-dimensional: row 1 <-
   row 1 + 3 * row 0; inverse subtracts the same multiple back). *)
(* ------------------------------------------------------------------ *)

Definition shear2 : MatrixQc 2 2 :=
  [ [ Q2Qc 1; Q2Qc 0 ] ; [ Q2Qc 3; Q2Qc 1 ] ].

Definition shear2_inv : MatrixQc 2 2 :=
  [ [ Q2Qc 1; Q2Qc 0 ] ; [ Q2Qc (-3); Q2Qc 1 ] ].

Lemma shear2_inv_left : mat_mat_qc shear2_inv shear2 = identity_qc 2.
Proof. vm_compute. reflexivity. Qed.

Lemma shear2_inv_right : mat_mat_qc shear2 shear2_inv = identity_qc 2.
Proof. vm_compute. reflexivity. Qed.

Definition InvShear2 : InvertibleMatrix 2 :=
  mkInvertibleMatrix 2 shear2 shear2_inv shear2_inv_left shear2_inv_right.

(* ------------------------------------------------------------------ *)
(* 4. R1's own four-cycle obstruction (D4, r4, y4 exactly as in
   R21CycleQuotientBridge.v's FourCycleExample, restated over qcvec),
   under a residue-space coordinate swap (indices 0 and 1) as B, with
   the repair-space transform A left as the identity so the swap's
   effect on the separator/annihilation calculation is isolated and
   legible. *)
(* ------------------------------------------------------------------ *)

Section FourCycleTransport.

  Definition D4 : MatrixQc 4 4 :=
    [ [ Q2Qc (-1); Q2Qc 1; Q2Qc 0; Q2Qc 0 ]
    ; [ Q2Qc 0; Q2Qc (-1); Q2Qc 1; Q2Qc 0 ]
    ; [ Q2Qc 0; Q2Qc 0; Q2Qc (-1); Q2Qc 1 ]
    ; [ Q2Qc (-1); Q2Qc 0; Q2Qc 0; Q2Qc 1 ]
    ].
  Definition r4 : qcvec 4 := [ Q2Qc 1; Q2Qc 1; Q2Qc 1; Q2Qc (-2) ].
  Definition y4 : qcvec 4 := [ Q2Qc (1#5); Q2Qc (1#5); Q2Qc (1#5); Q2Qc (-1#5) ].

  Definition swap4 : MatrixQc 4 4 :=
    [ [ Q2Qc 0; Q2Qc 1; Q2Qc 0; Q2Qc 0 ]
    ; [ Q2Qc 1; Q2Qc 0; Q2Qc 0; Q2Qc 0 ]
    ; [ Q2Qc 0; Q2Qc 0; Q2Qc 1; Q2Qc 0 ]
    ; [ Q2Qc 0; Q2Qc 0; Q2Qc 0; Q2Qc 1 ]
    ].

  Lemma swap4_self_inverse : mat_mat_qc swap4 swap4 = identity_qc 4.
  Proof. vm_compute. reflexivity. Qed.

  Definition InvSwap4 : InvertibleMatrix 4 :=
    mkInvertibleMatrix 4 swap4 swap4 swap4_self_inverse swap4_self_inverse.

  Lemma identity4_self_inverse : mat_mat_qc (identity_qc 4) (identity_qc 4) = identity_qc 4.
  Proof. vm_compute. reflexivity. Qed.

  Definition InvId4 : InvertibleMatrix 4 :=
    mkInvertibleMatrix 4 (identity_qc 4) (identity_qc 4)
      identity4_self_inverse identity4_self_inverse.

  Definition D4' : MatrixQc 4 4 := transform_operator InvId4 InvSwap4 D4.
  Definition r4' : qcvec 4 := transform_residue InvSwap4 r4.
  Definition y4' : qcvec 4 := transport_separator_vector InvSwap4 y4.

  (* (a) the original separator is accepted: annihilates D4 and pairs to
     exactly 1 against r4 -- reproducing R21CycleQuotientBridge.v's own
     four-cycle facts natively over qcvec, not re-derived via R21's
     checker. *)
  Example four_cycle_original_separator_annihilates :
    mat_vec_qc (transpose_qc D4) y4 = Vector.const (Q2Qc 0) 4.
  Proof.
    apply qcvec_eq_nth_Qeq. intros p.
    apply (Fin.caseS' p); [ vm_compute; reflexivity | intros p1 ].
    apply (Fin.caseS' p1); [ vm_compute; reflexivity | intros p2 ].
    apply (Fin.caseS' p2); [ vm_compute; reflexivity | intros p3 ].
    apply (Fin.caseS' p3); [ vm_compute; reflexivity | intros p4; inversion p4 ].
  Qed.

  Example four_cycle_original_pairing_is_one :
    dot_qc y4 r4 = Q2Qc 1.
  Proof. apply Qc_is_canon. vm_compute. reflexivity. Qed.

  (* (b) the transported separator annihilates the transformed matrix,
     checked directly. *)
  Example four_cycle_transported_separator_annihilates :
    mat_vec_qc (transpose_qc D4') y4' = Vector.const (Q2Qc 0) 4.
  Proof.
    apply qcvec_eq_nth_Qeq. intros p.
    apply (Fin.caseS' p); [ vm_compute; reflexivity | intros p1 ].
    apply (Fin.caseS' p1); [ vm_compute; reflexivity | intros p2 ].
    apply (Fin.caseS' p2); [ vm_compute; reflexivity | intros p3 ].
    apply (Fin.caseS' p3); [ vm_compute; reflexivity | intros p4; inversion p4 ].
  Qed.

  (* ... and again by applying the generic theorem, confirming the
     infrastructure actually instantiates against this real matrix. *)
  Example four_cycle_transported_separator_via_theorem :
    mat_vec_qc (transpose_qc D4') y4' = Vector.const (Q2Qc 0) 4 :=
    transport_separator 4 4 InvId4 InvSwap4 D4 y4
      four_cycle_original_separator_annihilates.

  (* (c) the pairing against the transformed residue remains exactly 1,
     checked directly and via the theorem. *)
  Example four_cycle_transported_pairing_is_one :
    dot_qc y4' r4' = Q2Qc 1.
  Proof. apply Qc_is_canon. vm_compute. reflexivity. Qed.

  Example four_cycle_transported_pairing_via_theorem :
    dot_qc y4' r4' = Q2Qc 1 :=
    transport_pairing 4 4 InvId4 InvSwap4 D4 r4 y4
      four_cycle_original_pairing_is_one.

  (* (d) transporting back (applying the swap's own inverse -- itself,
     since swap4 is self-inverse) recovers the original separator
     exactly, under plain Leibniz vector equality (qcvec, not VecEq/Qeq)
     -- checked directly and via mat_vec_qc_transpose_inverse. *)
  Example four_cycle_back_transport_recovers_separator :
    mat_vec_qc (transpose_qc (fwd InvSwap4)) y4' = y4.
  Proof.
    apply qcvec_eq_nth_Qeq. intros p.
    apply (Fin.caseS' p); [ vm_compute; reflexivity | intros p1 ].
    apply (Fin.caseS' p1); [ vm_compute; reflexivity | intros p2 ].
    apply (Fin.caseS' p2); [ vm_compute; reflexivity | intros p3 ].
    apply (Fin.caseS' p3); [ vm_compute; reflexivity | intros p4; inversion p4 ].
  Qed.

  Example four_cycle_back_transport_via_theorem :
    mat_vec_qc (transpose_qc (fwd InvSwap4))
               (mat_vec_qc (transpose_qc (bwd InvSwap4)) y4) = y4 :=
    mat_vec_qc_transpose_inverse 4 (fwd InvSwap4) (bwd InvSwap4)
      (inv_left InvSwap4) y4.

  (* Verdict invariance, instantiated: the four-cycle's residue is
     unrepairable, and stays unrepairable after transport -- the
     original obstruction (`repair_and_separator_disjoint`-style
     disjointness) is R21's own result; what R24 adds is that the SAME
     verdict holds for the transformed system, via the generic iff. *)
  Example four_cycle_repairable_iff_transported_repairable :
    (exists b, mat_vec_qc D4 b = r4) <->
    (exists b', mat_vec_qc D4' b' = r4') :=
    repairable_iff_transport_repairable 4 4 InvId4 InvSwap4 D4 r4.

End FourCycleTransport.
