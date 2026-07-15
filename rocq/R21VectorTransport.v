(*
   R21VectorTransport.v

   R22, concrete layer, part 2: the correspondence between
   `RationalCanonicalVectors.qcvec n` (`Vector.t Qc n`, the AbelianVSpace
   instance) and R21's own representation (`list Q`, with `VecEq`/`Qeq`
   throughout, `rocq/ExactRationalRepairOrSeparator.v`). Proves exactly
   the facts `RationalSeparationInstance.v` needs -- not every conceivable
   property of the conversion.

   DESIGN CHOICE, stated once: only ONE conversion direction is needed --
   `Qc` vector to `list Q` (`vec_to_list`/`mat_to_list`). The reverse
   direction (`list Q` to a FIXED-length `Qc` vector) is never required:
   the concrete membership predicate `RationalSeparationInstance.v`
   builds (`B D r := exists b_list, VectorShape n b_list /\ VecEq
   (mat_vec (mat_to_list D) b_list) (vec_to_list r)`) quantifies over a
   `list Q` witness directly, never over a `qcvec n` witness, and the
   linear functional built from a separator witness (`fun v => dot
   y_list (vec_to_list v)`) only ever needs the forward conversion too.
   This sidesteps entirely the much harder problem of transporting a
   `list Q` value into a `Vector.t Qc n` while preserving *Leibniz*
   equality (which would need Q2Qc-canonicalisation of possibly
   non-canonical list entries, exactly the representation problem `Qc`
   exists to avoid re-introducing) -- not attempted here, and not needed.

   Rational values compared through `Qc` are Leibniz `=` throughout
   (that is `Qc`'s entire purpose); rational values compared through
   `list Q` on the R21 side are `VecEq` (`Forall2 Qeq`) throughout,
   matching R21's own discipline. No lemma here claims literal Leibniz
   equality between arbitrary `list Q` values.

   Depends on RationalCanonicalVectors.v and ExactRationalRepairOrSeparator.v (R21).
*)

Require Import Coq.QArith.QArith.
Require Import Coq.QArith.Qcanon.
Require Import Coq.QArith.Qreduction.
Require Import Coq.Lists.List.
Require Import Coq.Vectors.Vector.
Import ListNotations.
Require Import RationalCanonicalVectors.
Require Import ExactRationalRepairOrSeparator.

(* ------------------------------------------------------------------ *)
(* QcToQ: the trivial projection (a Qc value already IS a Q value plus
   a canonicity proof), and its ring-homomorphism facts -- proved the
   same way as RationalCanonicalVectors.v's Q2Qc_plus/Q2Qc_mult: keep
   Qred/this opaque via `change`, never `simpl` into Qred's Z.ggcd-based
   implementation (which exposes Qnum/Qden -- NOT Proper for Qeq). *)
(* ------------------------------------------------------------------ *)

Definition QcToQ (x : Qc) : Q := this x.

Lemma QcToQ_Q2Qc_id : forall x : Qc, QcToQ (Q2Qc (QcToQ x)) = QcToQ x.
Proof. intros x. unfold QcToQ, Q2Qc. simpl. apply canon. Qed.

Lemma QcToQ_plus : forall x y : Qc, QcToQ (Qcplus x y) == QcToQ x + QcToQ y.
Proof.
  intros x y. unfold QcToQ, Qcplus.
  change (Qred (this x + this y) == this x + this y).
  apply Qred_correct.
Qed.

Lemma QcToQ_mult : forall x y : Qc, QcToQ (Qcmult x y) == QcToQ x * QcToQ y.
Proof.
  intros x y. unfold QcToQ, Qcmult.
  change (Qred (this x * this y) == this x * this y).
  apply Qred_correct.
Qed.

(* R21's own dot, one cons unfolded -- proved once, in isolation, with no
   Qc-valued subterm anywhere in sight. Used everywhere below instead of
   `unfold dot; simpl`, which (confirmed directly) unfolds too far when
   any Qc/QcToQ/Qcplus term is also present in the goal, reaching into
   Qcplus's own Q2Qc/Qred internals inconsistently between occurrences --
   the same failure mode RationalCanonicalVectors.v's header already
   found for `simpl` in general, now hitting `dot`'s unfolding too. *)
Lemma dot_cons : forall (x y : Q) (u v : list Q), dot (x :: u) (y :: v) == x * y + dot u v.
Proof. intros x y u v. unfold dot. simpl. ring. Qed.

Lemma QcToQ_Q2Qc_zero : QcToQ (Q2Qc 0) = 0.
Proof. reflexivity. Qed.

(* ------------------------------------------------------------------ *)
(* Qc vector/matrix -> list Q (always total; no length proof needed). *)
(* ------------------------------------------------------------------ *)

Definition vec_to_list {n : nat} (v : qcvec n) : list Q :=
  Vector.to_list (Vector.map QcToQ v).

Lemma length_vec_to_list : forall (n : nat) (v : qcvec n), length (vec_to_list v) = n.
Proof. intros n v. unfold vec_to_list. apply (Vector.length_to_list Q n (Vector.map QcToQ v)). Qed.

Lemma vec_to_list_shape : forall (n : nat) (v : qcvec n), VectorShape n (vec_to_list v).
Proof. intros n v. unfold VectorShape. apply length_vec_to_list. Qed.

Definition mat_to_list {m n : nat} (D : Vector.t (qcvec n) m) : list (list Q) :=
  Vector.to_list (Vector.map (@vec_to_list n) D).

Lemma mat_to_list_cons :
  forall (m n : nat) (row : qcvec n) (D : Vector.t (qcvec n) m),
    mat_to_list (Vector.cons _ row m D) = vec_to_list row :: mat_to_list D.
Proof.
  intros m n row D. unfold mat_to_list.
  change (Vector.map (@vec_to_list n) (Vector.cons _ row m D))
    with (Vector.cons (list Q) (vec_to_list row) m (Vector.map (@vec_to_list n) D)).
  apply (to_list_cons (list Q) (vec_to_list row) m (Vector.map (@vec_to_list n) D)).
Qed.

Lemma mat_to_list_shape :
  forall (m n : nat) (D : Vector.t (qcvec n) m), MatrixShape m n (mat_to_list D).
Proof.
  intros m n D. unfold MatrixShape.
  induction D as [| row0 m' D0 IH].
  - split; [reflexivity | constructor].
  - rewrite mat_to_list_cons.
    destruct IH as [IHlen IHall].
    split.
    + simpl. f_equal. exact IHlen.
    + constructor.
      * apply length_vec_to_list.
      * exact IHall.
Qed.

(* ------------------------------------------------------------------ *)
(* dot y (vec_to_list v) is linear in v, over the AbelianVSpace
   structure RationalCanonicalVectors.v equips qcvec n with (qcvadd,
   qcvzero, qcvscale) -- exactly the three facts needed to show a
   functional built this way satisfies AbstractSeparation.
   IsLinearFunctional. Each proved by explicit vector induction, using
   `change` to fix cons/map/map2's reduced shape precisely (blind `simpl`
   partially unfolds Vector.to_list's own internal helper fixpoint
   inconsistently between occurrences, confirmed directly when first
   attempted, breaking `ring`'s atom-matching) before converting to
   `list Q` via `to_list_cons`/`to_list_nil`. *)
(* ------------------------------------------------------------------ *)

Lemma dot_vec_to_list_qcvzero : forall (n : nat) (y : list Q), dot y (vec_to_list (@qcvzero n)) == 0.
Proof.
  unfold vec_to_list, qcvzero.
  induction n as [| n' IH]; intros y.
  - unfold dot. simpl. rewrite (to_list_nil Q). destruct y; simpl; ring.
  - change (Vector.const (Q2Qc 0) (S n')) with (Vector.cons Qc (Q2Qc 0) n' (Vector.const (Q2Qc 0) n')).
    change (Vector.map QcToQ (Vector.cons Qc (Q2Qc 0) n' (Vector.const (Q2Qc 0) n')))
      with (Vector.cons Q (QcToQ (Q2Qc 0)) n' (Vector.map QcToQ (Vector.const (Q2Qc 0) n'))).
    rewrite (to_list_cons Q (QcToQ (Q2Qc 0)) n' (Vector.map QcToQ (Vector.const (Q2Qc 0) n'))).
    destruct y as [| hy ty].
    + unfold dot. simpl. ring.
    + rewrite (dot_cons hy (QcToQ (Q2Qc 0)) ty (Vector.to_list (Vector.map QcToQ (Vector.const (Q2Qc 0) n')))).
      rewrite QcToQ_Q2Qc_zero.
      rewrite (IH ty). ring.
Qed.

Lemma dot_vec_to_list_qcvadd :
  forall (n : nat) (y : list Q) (a b : qcvec n),
    length y = n ->
    dot y (vec_to_list (qcvadd a b)) == dot y (vec_to_list a) + dot y (vec_to_list b).
Proof.
  unfold vec_to_list, qcvadd.
  intros n y a b Hlen.
  revert y Hlen.
  induction a as [| x n' a IH]; intros y Hlen.
  - apply Vector.case0 with (v := b). simpl in Hlen. unfold dot.
    destruct y; simpl in *; try discriminate; ring.
  - revert Hlen. apply (Vector.caseS' b). intros hb tb Hlen.
    destruct y as [| hy ty]; simpl in Hlen; try discriminate.
    change (Vector.map2 Qcplus (Vector.cons Qc x n' a) (Vector.cons Qc hb n' tb))
      with (Vector.cons Qc (Qcplus x hb) n' (Vector.map2 Qcplus a tb)).
    change (Vector.map QcToQ (Vector.cons Qc (Qcplus x hb) n' (Vector.map2 Qcplus a tb)))
      with (Vector.cons Q (QcToQ (Qcplus x hb)) n' (Vector.map QcToQ (Vector.map2 Qcplus a tb))).
    change (Vector.map QcToQ (Vector.cons Qc x n' a)) with (Vector.cons Q (QcToQ x) n' (Vector.map QcToQ a)).
    change (Vector.map QcToQ (Vector.cons Qc hb n' tb)) with (Vector.cons Q (QcToQ hb) n' (Vector.map QcToQ tb)).
    rewrite (to_list_cons Q (QcToQ (Qcplus x hb)) n' (Vector.map QcToQ (Vector.map2 Qcplus a tb))).
    rewrite (to_list_cons Q (QcToQ x) n' (Vector.map QcToQ a)).
    rewrite (to_list_cons Q (QcToQ hb) n' (Vector.map QcToQ tb)).
    rewrite (dot_cons hy (QcToQ (Qcplus x hb)) ty (Vector.to_list (Vector.map QcToQ (Vector.map2 Qcplus a tb)))).
    rewrite (dot_cons hy (QcToQ x) ty (Vector.to_list (Vector.map QcToQ a))).
    rewrite (dot_cons hy (QcToQ hb) ty (Vector.to_list (Vector.map QcToQ tb))).
    rewrite (IH tb ty (eq_add_S _ _ Hlen)).
    rewrite (QcToQ_plus x hb).
    ring.
Qed.

Lemma dot_vec_to_list_qcvscale :
  forall (n : nat) (c : Q) (y : list Q) (a : qcvec n),
    length y = n ->
    dot y (vec_to_list (qcvscale c a)) == c * dot y (vec_to_list a).
Proof.
  unfold vec_to_list, qcvscale.
  intros n c y a.
  revert y.
  induction a as [| x n' a IH]; intros y Hlen.
  - unfold dot. simpl. destruct y; simpl in *; try discriminate. ring.
  - destruct y as [| hy ty]; simpl in Hlen; try discriminate.
    change (Vector.map (fun x0 => Qcmult (Q2Qc c) x0) (Vector.cons Qc x n' a))
      with (Vector.cons Qc (Qcmult (Q2Qc c) x) n' (Vector.map (fun x0 => Qcmult (Q2Qc c) x0) a)).
    change (Vector.map QcToQ (Vector.cons Qc (Qcmult (Q2Qc c) x) n' (Vector.map (fun x0 => Qcmult (Q2Qc c) x0) a)))
      with (Vector.cons Q (QcToQ (Qcmult (Q2Qc c) x)) n' (Vector.map QcToQ (Vector.map (fun x0 => Qcmult (Q2Qc c) x0) a))).
    change (Vector.map QcToQ (Vector.cons Qc x n' a)) with (Vector.cons Q (QcToQ x) n' (Vector.map QcToQ a)).
    rewrite (to_list_cons Q (QcToQ (Qcmult (Q2Qc c) x)) n'
               (Vector.map QcToQ (Vector.map (fun x0 => Qcmult (Q2Qc c) x0) a))).
    rewrite (to_list_cons Q (QcToQ x) n' (Vector.map QcToQ a)).
    rewrite (dot_cons hy (QcToQ (Qcmult (Q2Qc c) x)) ty
               (Vector.to_list (Vector.map QcToQ (Vector.map (fun x0 => Qcmult (Q2Qc c) x0) a)))).
    rewrite (dot_cons hy (QcToQ x) ty (Vector.to_list (Vector.map QcToQ a))).
    rewrite (IH ty (eq_add_S _ _ Hlen)).
    rewrite (QcToQ_mult (Q2Qc c) x).
    unfold QcToQ at 1.
    change (this (Q2Qc c)) with (Qred c).
    rewrite Qred_correct.
    ring.
Qed.
