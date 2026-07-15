(*
   RationalSeparationInstance.v

   R22, concrete layer, part 3: discharges `AbstractSeparation.
   SeparatesOutside` concretely, for `B D r := "r is repairable by D"`
   over `RationalCanonicalVectors.RatQcVSpace m`, using R21's own proved
   `rational_repair_or_separator`/`repair_and_separator_disjoint` --
   Route C of `docs/design/EXACT_RATIONAL_SEPARATION_SPEC.md` and
   `docs/design/CYCLE_QUOTIENT_DUALITY_SPEC.md` §5, now actually built
   rather than merely scoped.

   Decidability of `B D r` is derived from R21's own computation
   (`compute_repair_or_separator`), not imported as a classical axiom:
   the repair branch gives `B D r` directly; the separator branch gives
   `~ B D r` via R21's own `repair_and_separator_disjoint`. This is
   exactly the "decidability should come from R21, not classical logic"
   design point -- the double-negation step `QuotientEvaluation.
   eval_injective` otherwise needs is discharged here by an actual
   verified decision procedure, for this specific `B`, not a blanket
   excluded-middle axiom.

   Depends on RationalCanonicalVectors.v, R21VectorTransport.v,
   AbstractSeparation.v, and ExactRationalRepairOrSeparator.v (R21).
*)

Require Import Coq.QArith.QArith.
Require Import Coq.QArith.Qcanon.
Require Import Coq.Lists.List.
Require Import Coq.Vectors.Vector.
Import ListNotations.
Require Import AbstractSeparation.
Require Import RationalCanonicalVectors.
Require Import R21VectorTransport.
Require Import ExactRationalRepairOrSeparator.

Section RationalSeparationInstance.
  Variable m n : nat.
  Variable D : Vector.t (qcvec n) m.

  (* "r is repairable by D": exists a list-Q witness (not a qcvec n
     witness -- see R21VectorTransport.v's header for why the reverse
     conversion is never needed), matching R21's own repair predicate
     exactly, applied to the converted (mat_to_list D, vec_to_list r). *)
  Definition B (r : qcvec m) : Prop :=
    exists b_list, VectorShape n b_list /\ VecEq (mat_vec (mat_to_list D) b_list) (vec_to_list r).

  Lemma B_decidable : forall r : qcvec m, B r \/ ~ B r.
  Proof.
    intros r.
    destruct (mat_to_list_shape m n D) as [HDlen HDrows].
    pose proof (compute_repair_or_separator_correct m n (mat_to_list D) (vec_to_list r)
                  (conj HDlen HDrows) (vec_to_list_shape m r)) as Hcorrect.
    destruct (compute_repair_or_separator m n (mat_to_list D) (vec_to_list r)) as [b_list | y_list] eqn:Hcomp.
    - left. destruct Hcorrect as [Hshape Heq]. exists b_list. split; assumption.
    - right. intros [b_list' [Hshape' Heq']].
      destruct Hcorrect as [Hyshape [Hann Hpair]].
      apply (repair_and_separator_disjoint m n (mat_to_list D) (vec_to_list r) b_list' y_list
               (conj HDlen HDrows) Hshape' Hyshape Heq' Hann Hpair).
  Qed.

  Lemma separates_outside_B : SeparatesOutside (RatQcVSpace m) B.
  Proof.
    intros r Hout.
    destruct (mat_to_list_shape m n D) as [HDlen HDrows].
    pose proof (compute_repair_or_separator_correct m n (mat_to_list D) (vec_to_list r)
                  (conj HDlen HDrows) (vec_to_list_shape m r)) as Hcorrect.
    destruct (compute_repair_or_separator m n (mat_to_list D) (vec_to_list r)) as [b_list | y_list] eqn:Hcomp.
    - exfalso. apply Hout. destruct Hcorrect as [Hshape Heq]. exists b_list. split; assumption.
    - destruct Hcorrect as [Hyshape [Hann Hpair]].
      exists (fun v => dot y_list (vec_to_list v)).
      assert (Hylen : length y_list = m) by exact Hyshape.
      split; [| split].
      + (* IsLinearFunctional *)
        split; [| split].
        * apply dot_vec_to_list_qcvzero.
        * intros a b. apply dot_vec_to_list_qcvadd. exact Hylen.
        * intros c a. apply dot_vec_to_list_qcvscale. exact Hylen.
      + (* Annihilator (RatQcVSpace m) B (fun v => dot y_list (vec_to_list v)) *)
        intros b' [b_list' [Hshape' Heq']].
        assert (Hstep1 : dot y_list (vec_to_list b') == dot y_list (mat_vec (mat_to_list D) b_list')).
        { apply dot_Proper. - reflexivity. - symmetry. exact Heq'. }
        rewrite Hstep1.
        assert (Hstep2 : dot y_list (mat_vec (mat_to_list D) b_list') ==
                          dot (row_vec_mat y_list (mat_to_list D) n) b_list').
        { apply dot_mat_vec_assoc. - exact HDrows. - rewrite Hylen. symmetry. exact HDlen. }
        rewrite Hstep2.
        assert (Hstep3 : dot (row_vec_mat y_list (mat_to_list D) n) b_list' ==
                          dot (mat_vec (transpose (mat_to_list D) n) y_list) b_list').
        { apply dot_Proper. - apply row_vec_mat_eq_mat_vec_transpose. - reflexivity. }
        rewrite Hstep3.
        assert (Hstep4 : dot (mat_vec (transpose (mat_to_list D) n) y_list) b_list' ==
                          dot (repeat (0%Q) n) b_list').
        { apply dot_Proper. - exact Hann. - reflexivity. }
        rewrite Hstep4.
        apply dot_zero_l.
      + (* ~ (phi r == 0) *)
        intros Hzero.
        assert (Hone : dot y_list (vec_to_list r) == 1) by exact Hpair.
        rewrite Hone in Hzero.
        (* Hzero : 1 == 0, a genuine contradiction over Q *)
        discriminate Hzero.
  Qed.

End RationalSeparationInstance.
