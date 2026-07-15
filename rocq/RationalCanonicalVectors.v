(*
   RationalCanonicalVectors.v

   R22, concrete layer, part 1: `Vector.t Qc n` (length-indexed vectors
   of Rocq's canonical-rational type `Qc`) instantiates
   `AbstractSeparation.AbelianVSpace` -- all ten laws, confirmed by an
   actual compiling proof, not merely argued for.

   WHY Qc, NOT list Q: `AbstractSeparation.v`'s own header already found
   that plain `Q` cannot instantiate a Leibniz-equality vector space
   (`Qplus_assoc`/`Qmult_assoc` are `Qeq`, not Leibniz, facts in the
   standard library) -- and the identical problem recurs for `list Q`
   under pointwise operations, checked directly: the general/symbolic
   statement `forall a b c : Q, Qplus (Qplus a b) c = Qplus a (Qplus b c)`
   is not provable by `reflexivity`/`ring` (only specific numeral
   instances happen to compute out equal, because Coq's kernel reduces
   concrete Z arithmetic to a shared normal form; the general statement
   has no such reduction available). `Qc` (`Coq.QArith.Qcanon`) exists
   precisely to fix this: a `Qc` value is a pair of a `Q` and a proof
   that it is already in `Qred` normal form, so two `Qeq`-equal `Qc`
   values are automatically Leibniz-equal (`Qc_is_canon`), and the
   library's own `Qcplus_assoc`, `Qcplus_comm`, `Qcplus_0_l`,
   `Qcplus_opp_r`, `Qcmult_1_l`, `Qcmult_assoc`, `Qcmult_plus_distr_l/r`
   are all already stated with Leibniz `=`.

   WHY Vector.t, NOT list Qc: a plain `list Qc` cannot instantiate a
   single `AbelianVSpace` (one fixed carrier, one fixed `vzero`) at all,
   since `vadd`/`vscale` would need to behave sensibly on lists of
   differing lengths, which is not possible for a real vector space
   (`vadd_comm`, in particular, has no sensible meaning between a
   length-2 and a length-3 list). `Vector.t Qc n`, for a FIXED `n`, is
   closed under pointwise operations by construction -- length mismatch
   cannot arise, checked directly here rather than assumed.

   Depends on AbstractSeparation.v only.
*)

Require Import Coq.QArith.QArith.
Require Import Coq.QArith.Qcanon.
Require Import Coq.QArith.Qreduction.
Require Import Coq.Vectors.Vector.
Require Import Coq.Vectors.Fin.
Require Import AbstractSeparation.

(* ------------------------------------------------------------------ *)
(* Q2Qc is a ring homomorphism (Q, Qeq) -> (Qc, =). Neither fact is in
   the standard library under an obvious name; both checked directly.
   The key move, in both proofs: keep Qred opaque (never `simpl` into
   its Z.ggcd-based implementation, which exposes Qnum/Qden -- NOT
   Proper for Qeq, so reasoning gets stuck there, confirmed directly
   when first attempted) -- use `change` to fix the goal shape at the
   Qred/Qplus level, then Qred_correct (Qred x == x) plus ring. *)
(* ------------------------------------------------------------------ *)

Lemma Q2Qc_plus : forall c d : Q, Q2Qc (c + d) = Qcplus (Q2Qc c) (Q2Qc d).
Proof.
  intros c d. apply Qc_is_canon.
  change (Qred (c + d) == Qred (Qred c + Qred d)).
  rewrite (Qred_correct (c + d)), (Qred_correct (Qred c + Qred d)), (Qred_correct c), (Qred_correct d).
  reflexivity.
Qed.

Lemma Q2Qc_mult : forall c d : Q, Q2Qc (c * d) = Qcmult (Q2Qc c) (Q2Qc d).
Proof.
  intros c d. apply Qc_is_canon.
  change (Qred (c * d) == Qred (Qred c * Qred d)).
  rewrite (Qred_correct (c * d)), (Qred_correct (Qred c * Qred d)), (Qred_correct c), (Qred_correct d).
  reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* Vector.t Qc n: the carrier, its operations, and the ten laws. *)
(* ------------------------------------------------------------------ *)

Section RatQcVSpace.
  Variable n : nat.

  Definition qcvec := Vector.t Qc n.

  Definition qcvzero : qcvec := Vector.const (Q2Qc 0) n.
  Definition qcvadd (a b : qcvec) : qcvec := Vector.map2 Qcplus a b.
  Definition qcvneg (a : qcvec) : qcvec := Vector.map Qcopp a.
  Definition qcvscale (c : Q) (a : qcvec) : qcvec := Vector.map (fun x => Qcmult (Q2Qc c) x) a.

  (* Every law reduces to a per-index Qc equation via eq_nth_iff, then
     computes both sides down with nth_map2/nth_map/const_nth, then
     closes with Qc's own Leibniz ring laws. *)
  Ltac nth_reduce := intros; apply VectorSpec.eq_nth_iff; intros p1 p2 Hp; subst p2.

  Lemma qcvadd_assoc : forall a b c : qcvec, qcvadd (qcvadd a b) c = qcvadd a (qcvadd b c).
  Proof.
    nth_reduce. unfold qcvadd.
    rewrite (nth_map2 Qcplus (Vector.map2 Qcplus a b) c p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map2 Qcplus a b p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map2 Qcplus a (Vector.map2 Qcplus b c) p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map2 Qcplus b c p1 p1 p1 eq_refl eq_refl).
    symmetry. apply Qcplus_assoc.
  Qed.

  Lemma qcvadd_zero_l : forall a : qcvec, qcvadd qcvzero a = a.
  Proof.
    nth_reduce. unfold qcvadd, qcvzero.
    rewrite (nth_map2 Qcplus (Vector.const (Q2Qc 0) n) a p1 p1 p1 eq_refl eq_refl).
    rewrite (const_nth Qc (Q2Qc 0) n p1).
    apply Qcplus_0_l.
  Qed.

  Lemma qcvadd_comm : forall a b : qcvec, qcvadd a b = qcvadd b a.
  Proof.
    nth_reduce. unfold qcvadd.
    rewrite (nth_map2 Qcplus a b p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map2 Qcplus b a p1 p1 p1 eq_refl eq_refl).
    apply Qcplus_comm.
  Qed.

  Lemma qcvadd_zero_r : forall a : qcvec, qcvadd a qcvzero = a.
  Proof. intros a. rewrite qcvadd_comm. apply qcvadd_zero_l. Qed.

  Lemma qcvadd_vneg : forall a : qcvec, qcvadd a (qcvneg a) = qcvzero.
  Proof.
    nth_reduce. unfold qcvadd, qcvneg, qcvzero.
    rewrite (nth_map2 Qcplus a (Vector.map Qcopp a) p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map Qcopp a p1 p1 eq_refl).
    rewrite (const_nth Qc (Q2Qc 0) n p1).
    apply Qcplus_opp_r.
  Qed.

  Lemma qcvscale_distrib_vadd :
    forall (c : Q) (a b : qcvec), qcvscale c (qcvadd a b) = qcvadd (qcvscale c a) (qcvscale c b).
  Proof.
    nth_reduce. unfold qcvscale, qcvadd.
    rewrite (nth_map (fun x => Qcmult (Q2Qc c) x) (Vector.map2 Qcplus a b) p1 p1 eq_refl).
    rewrite (nth_map2 Qcplus a b p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map2 Qcplus (Vector.map (fun x => Qcmult (Q2Qc c) x) a) (Vector.map (fun x => Qcmult (Q2Qc c) x) b)
               p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc c) x) a p1 p1 eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc c) x) b p1 p1 eq_refl).
    apply Qcmult_plus_distr_r.
  Qed.

  Lemma qcvscale_compose : forall (c d : Q) (a : qcvec), qcvscale c (qcvscale d a) = qcvscale (c * d) a.
  Proof.
    nth_reduce. unfold qcvscale.
    rewrite (nth_map (fun x => Qcmult (Q2Qc c) x) (Vector.map (fun x => Qcmult (Q2Qc d) x) a) p1 p1 eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc d) x) a p1 p1 eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc (c * d)) x) a p1 p1 eq_refl).
    rewrite Q2Qc_mult.
    apply Qcmult_assoc.
  Qed.

  Lemma qcvscale_vzero : forall c : Q, qcvscale c qcvzero = qcvzero.
  Proof.
    nth_reduce. unfold qcvscale, qcvzero.
    rewrite (nth_map (fun x => Qcmult (Q2Qc c) x) (Vector.const (Q2Qc 0) n) p1 p1 eq_refl).
    rewrite (const_nth Qc (Q2Qc 0) n p1).
    ring.
  Qed.

  Lemma qcvscale_one : forall a : qcvec, qcvscale 1 a = a.
  Proof.
    nth_reduce. unfold qcvscale.
    rewrite (nth_map (fun x => Qcmult (Q2Qc 1) x) a p1 p1 eq_refl).
    apply Qcmult_1_l.
  Qed.

  Lemma qcvscale_qplus :
    forall (c d : Q) (a : qcvec), qcvscale (c + d) a = qcvadd (qcvscale c a) (qcvscale d a).
  Proof.
    nth_reduce. unfold qcvscale, qcvadd.
    rewrite (nth_map2 Qcplus (Vector.map (fun x => Qcmult (Q2Qc c) x) a) (Vector.map (fun x => Qcmult (Q2Qc d) x) a)
               p1 p1 p1 eq_refl eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc (c + d)) x) a p1 p1 eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc c) x) a p1 p1 eq_refl).
    rewrite (nth_map (fun x => Qcmult (Q2Qc d) x) a p1 p1 eq_refl).
    rewrite Q2Qc_plus.
    apply Qcmult_plus_distr_l.
  Qed.

  Definition RatQcVSpace : AbelianVSpace :=
    mkAbelianVSpace qcvec qcvzero qcvadd qcvneg qcvscale
      qcvadd_assoc qcvadd_zero_l qcvadd_comm qcvadd_zero_r qcvadd_vneg
      qcvscale_distrib_vadd qcvscale_compose qcvscale_vzero qcvscale_one qcvscale_qplus.

End RatQcVSpace.

Arguments qcvzero {n}.
Arguments qcvadd {n} _ _.
Arguments qcvneg {n} _.
Arguments qcvscale {n} _ _.

(* ------------------------------------------------------------------ *)
(* Converting a canonical coordinate back to Q -- the trivial direction
   (a Qc value already IS a Q value plus a canonicity proof). The other
   direction (Q -> Qc) is Q2Qc, already used throughout. *)
(* ------------------------------------------------------------------ *)

Definition QcToQ (x : Qc) : Q := this x.

Lemma QcToQ_Q2Qc : forall x : Qc, Q2Qc (QcToQ x) = x.
Proof.
  intros [q Hq]. unfold QcToQ, Q2Qc. simpl.
  apply Qc_is_canon. simpl. rewrite Hq. reflexivity.
Qed.
