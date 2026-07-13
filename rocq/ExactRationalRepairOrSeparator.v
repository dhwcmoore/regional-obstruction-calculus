(*
   ExactRationalRepairOrSeparator.v

   R21. A constructive exact alternative for a rational linear system
   D b = r (D: m x n, r: length m), decided by verified exact-rational
   Gauss-Jordan elimination on the augmented matrix [D | r]:

     (exists b, D b = r)
     \/
     (exists y, D^T y = 0 /\ dot y r == 1).

   Both witnesses are extracted from a single elimination run and
   proved correct against the ORIGINAL system, not merely the reduced
   matrix: the repair branch closes via a solution-set equivalence
   (SolvesAug) threaded through every elementary row operation, proved
   independently of the transformation-matrix invariant used for the
   separator branch. repair_and_separator_disjoint proves the two
   witnesses cannot coexist, by the short direct computation
   1 = y.r = y.(D b) = (D^T y).b = 0, not by appeal to the algorithm
   choosing only one branch.

   The whole development -- elimination state and invariant, pivot
   detection, row operations via elementary matrices, both extraction
   theorems, the evidence-bearing RepairOrSeparator interface, and
   independent executable checkers -- is self-contained in this file
   and carries zero project-added axioms (see the Print Assumptions
   record in docs/theory/THEOREM_CONCORDANCE.md).

   Verified against the real four-cycle obstruction witness
   (examples/four_cycle.json): the internal inconsistent-row
   extraction recovers the paper's own canonical cycle
   z = (-1,-1,-1,1) with pairing c = -5 before normalisation; the
   public certificate is the normalised -1/5 z = (1/5,1/5,1/5,-1/5).
*)

Require Import QArith.
Require Import Coq.Lists.List.
Require Import Coq.Classes.RelationClasses.
Require Import Coq.Classes.Morphisms.
Require Import Lia.
Import ListNotations.

Definition dot (u v : list Q) : Q :=
  fold_right Qplus 0 (map (fun p => fst p * snd p) (combine u v)).

Definition mat_vec (D : list (list Q)) (b : list Q) : list Q :=
  map (fun row => dot row b) D.

Definition transpose (D : list (list Q)) (ncols : nat) : list (list Q) :=
  map (fun j => map (fun row => nth j row 0) D) (seq 0 ncols).

Definition VecEq : list Q -> list Q -> Prop := Forall2 Qeq.
Definition MatEq : list (list Q) -> list (list Q) -> Prop := Forall2 VecEq.

Instance VecEq_Equivalence : Equivalence VecEq.
Proof.
  unfold VecEq. constructor.
  - intro l. induction l as [| x l IH]; constructor; [reflexivity | exact IH].
  - intro l. induction l as [| x l IH]; intros l' H; inversion H; subst; constructor.
    + symmetry. assumption.
    + apply IH. assumption.
  - intro l1. induction l1 as [| x l1 IH]; intros l2 l3 H12 H23;
      inversion H12; subst; inversion H23; subst; constructor.
    + etransitivity; eassumption.
    + eapply IH; eassumption.
Qed.

Instance MatEq_Equivalence : Equivalence MatEq.
Proof.
  unfold MatEq. constructor.
  - intro M. induction M as [| r M IH]; constructor; [reflexivity | exact IH].
  - intro M. induction M as [| r M IH]; intros M' H; inversion H; subst; constructor.
    + symmetry. assumption.
    + apply IH. assumption.
  - intro M1. induction M1 as [| r1 M1 IH]; intros M2 M3 H12 H23;
      inversion H12; subst; inversion H23; subst; constructor.
    + etransitivity; eassumption.
    + eapply IH; eassumption.
Qed.

Lemma VecEq_length : forall u v, VecEq u v -> length u = length v.
Proof. intros u v H. eapply Forall2_length; eassumption. Qed.

(* dot respects VecEq in both arguments simultaneously -- a single
   Proper instance, stronger than the two separate lemmas Stage3 had,
   and usable directly by `rewrite`/`setoid_rewrite`. *)
Lemma dot_Proper_aux : forall u1 u2, VecEq u1 u2 -> forall v1 v2, VecEq v1 v2 -> dot u1 v1 == dot u2 v2.
Proof.
  unfold VecEq. induction 1 as [| x y u1 u2 Hxy Hu12 IH]; intros v1 v2 Hv.
  - unfold dot. simpl. reflexivity.
  - destruct Hv as [| a b v1' v2' Hab Hv12].
    + unfold dot. simpl. reflexivity.
    + assert (Hrest : dot u1 v1' == dot u2 v2') by (apply IH; exact Hv12).
      unfold dot in *. simpl. rewrite Hxy, Hab, Hrest. reflexivity.
Qed.

Instance dot_Proper : Proper (VecEq ==> VecEq ==> Qeq) dot.
Proof. intros u1 u2 Hu v1 v2 Hv. apply dot_Proper_aux; assumption. Qed.

Instance mat_vec_Proper : Proper (MatEq ==> VecEq ==> VecEq) mat_vec.
Proof.
  intros D1 D2 HD b1 b2 Hb. unfold MatEq in HD. unfold mat_vec.
  induction HD as [| r1 r2 M1 M2 Hr HM IH]; constructor.
  - rewrite Hr, Hb. reflexivity.
  - exact IH.
Qed.

Lemma nth_transpose : forall (D : list (list Q)) (ncols j : nat),
  (j < ncols)%nat -> nth j (transpose D ncols) [] = map (fun row => nth j row 0) D.
Proof.
  intros D ncols j Hj. unfold transpose.
  rewrite (nth_indep _ [] (map (fun row : list Q => nth j row 0) D)).
  - rewrite (map_nth (fun k => map (fun row => nth k row 0) D) (seq 0 ncols) j j).
    rewrite seq_nth by exact Hj.
    reflexivity.
  - rewrite map_length, seq_length. exact Hj.
Qed.

Lemma length_transpose : forall (D : list (list Q)) (ncols : nat), length (transpose D ncols) = ncols.
Proof. intros D ncols. unfold transpose. rewrite map_length, seq_length. reflexivity. Qed.

(* General helper: a pointwise nth relation, respected on every valid
   index with matching length, gives Forall2. The reusable engine
   behind every congruence lemma from here on that needs to relate two
   things via their nth-indexed structure rather than by direct
   induction on cons-cells. *)
Lemma Forall2_from_nth : forall {A : Type} (R : A -> A -> Prop) (d : A) (l1 l2 : list A),
  length l1 = length l2 ->
  (forall j : nat, (j < length l1)%nat -> R (nth j l1 d) (nth j l2 d)) ->
  Forall2 R l1 l2.
Proof.
  induction l1 as [| x l1 IH]; intros l2 Hlen HR; destruct l2 as [| y l2]; simpl in Hlen; try discriminate.
  - constructor.
  - constructor.
    + apply (HR 0%nat). simpl. lia.
    + apply IH.
      * lia.
      * intros j Hj. apply (HR (S j)). simpl. lia.
Qed.

Lemma my_nth_map : forall (A B : Type) (f : A -> B) (l : list A) (j : nat) (da : A) (db : B),
  (j < length l)%nat -> nth j (map f l) db = f (nth j l da).
Proof.
  induction l as [| x l IH]; intros j da db Hj; simpl in *; [lia |].
  destruct j as [| j].
  - reflexivity.
  - apply IH. lia.
Qed.

Lemma nth_VecEq : forall u v, VecEq u v -> forall j, nth j u 0 == nth j v 0.
Proof.
  unfold VecEq. induction 1 as [| x y u v Hxy Huv IH]; intros j.
  - destruct j; simpl; reflexivity.
  - destruct j as [| j]; simpl; [exact Hxy | apply IH].
Qed.

Lemma MatEq_nth_row : forall D1 D2, MatEq D1 D2 -> forall k, VecEq (nth k D1 []) (nth k D2 []).
Proof.
  unfold MatEq. induction 1 as [| r1 r2 D1 D2 Hr Hrest IH]; intros k.
  - destruct k; simpl; apply VecEq_Equivalence.
  - destruct k as [| k]; simpl; [exact Hr | apply IH].
Qed.

Instance transpose_Proper : forall ncols, Proper (MatEq ==> MatEq) (fun D => transpose D ncols).
Proof.
  intros ncols D1 D2 HD.
  apply (Forall2_from_nth VecEq (@nil Q) (transpose D1 ncols) (transpose D2 ncols)).
  - rewrite !length_transpose. reflexivity.
  - intros j Hj. rewrite length_transpose in Hj.
    rewrite (nth_transpose D1 ncols j Hj), (nth_transpose D2 ncols j Hj).
    apply (Forall2_from_nth Qeq 0 (map (fun row => nth j row 0) D1) (map (fun row => nth j row 0) D2)).
    + rewrite !map_length. eapply Forall2_length; exact HD.
    + intros k Hk. rewrite map_length in Hk.
      rewrite (my_nth_map (list Q) Q (fun row => nth j row 0) D1 k [] 0 Hk).
      assert (Hk2 : (k < length D2)%nat) by (erewrite <- Forall2_length; eassumption).
      rewrite (my_nth_map (list Q) Q (fun row => nth j row 0) D2 k [] 0 Hk2).
      apply nth_VecEq. apply (MatEq_nth_row D1 D2 HD).
Qed.

Definition MatrixShape (m n : nat) (D : list (list Q)) : Prop :=
  length D = m /\ Forall (fun row => length row = n) D.

Definition VectorShape (n : nat) (v : list Q) : Prop := length v = n.

Definition row_vec_mat (row : list Q) (D : list (list Q)) (ncols : nat) : list Q :=
  map (fun col => dot row col) (transpose D ncols).

Definition mat_mul (A B : list (list Q)) (ncols_B : nat) : list (list Q) :=
  map (fun row_a => row_vec_mat row_a B ncols_B) A.

Instance row_vec_mat_Proper : forall ncols, Proper (VecEq ==> MatEq ==> VecEq) (fun row D => row_vec_mat row D ncols).
Proof.
  intros ncols row1 row2 Hrow D1 D2 HD.
  unfold row_vec_mat.
  assert (Htr : MatEq (transpose D1 ncols) (transpose D2 ncols)) by (apply transpose_Proper; exact HD).
  unfold MatEq in Htr.
  induction Htr as [| c1 c2 T1 T2 Hc HT IH]; constructor.
  - rewrite Hrow, Hc. reflexivity.
  - exact IH.
Qed.

Instance mat_mul_Proper : forall ncols_B, Proper (MatEq ==> MatEq ==> MatEq) (fun A B => mat_mul A B ncols_B).
Proof.
  intros ncols_B A1 A2 HA B1 B2 HB.
  unfold mat_mul. unfold MatEq in HA |- *.
  induction HA as [| r1 r2 A1 A2 Hr HA IH]; constructor.
  - apply (row_vec_mat_Proper ncols_B); assumption.
  - exact IH.
Qed.

Lemma MatEq_rows_length : forall n A B,
  MatEq A B -> Forall (fun row => length row = n) A -> Forall (fun row => length row = n) B.
Proof.
  intros n A B HAB. unfold MatEq in HAB.
  induction HAB as [| ra rb A' B' Hr Hrest IH]; intros Hrows.
  - constructor.
  - apply Forall_cons_iff in Hrows. destruct Hrows as [Hra Hrows'].
    constructor.
    + rewrite <- (VecEq_length _ _ Hr). exact Hra.
    + apply IH. exact Hrows'.
Qed.

Lemma MatEq_MatrixShape : forall m n A B, MatEq A B -> MatrixShape m n A -> MatrixShape m n B.
Proof.
  intros m n A B HAB [Hlen Hrows].
  split.
  - rewrite <- (Forall2_length HAB). exact Hlen.
  - apply (MatEq_rows_length n A B HAB Hrows).
Qed.

Lemma VecEq_VectorShape : forall n x y, VecEq x y -> VectorShape n x -> VectorShape n y.
Proof. intros n x y Hxy Hx. unfold VectorShape in *. rewrite <- (VecEq_length _ _ Hxy). exact Hx. Qed.

(* Recursive (not map/seq) so induction on m is direct: identity_row m p
   is the length-m row with 1 at position p and 0 elsewhere. *)
Fixpoint identity_row (m p : nat) : list Q :=
  match m with
  | O => []
  | S m' =>
      match p with
      | O => 1 :: repeat 0 m'
      | S p' => 0 :: identity_row m' p'
      end
  end.

Definition identity_matrix (m : nat) : list (list Q) :=
  map (identity_row m) (seq 0 m).

Lemma length_identity_row : forall m p, length (identity_row m p) = m.
Proof.
  induction m as [| m IH]; intros p; simpl; [reflexivity |].
  destruct p as [| p]; simpl.
  - rewrite repeat_length. reflexivity.
  - rewrite IH. reflexivity.
Qed.

Lemma dot_cons : forall x y u v, dot (x :: u) (y :: v) == x * y + dot u v.
Proof. intros. unfold dot. simpl. ring. Qed.

Lemma dot_nil_l : forall v, dot [] v == 0.
Proof. intros v. unfold dot. reflexivity. Qed.

Lemma dot_zero_l : forall (n : nat) (v : list Q), dot (repeat 0 n) v == 0.
Proof.
  induction n as [| n IH]; intros v; simpl; [apply dot_nil_l |].
  destruct v as [| y v]; unfold dot in *; simpl in *.
  - reflexivity.
  - rewrite (IH v). ring.
Qed.

Lemma dot_identity_row : forall m p col, (p < m)%nat -> length col = m ->
  dot (identity_row m p) col == nth p col 0.
Proof.
  induction m as [| m IH]; intros p col Hp Hcol.
  - lia.
  - destruct col as [| c col']; simpl in Hcol; try discriminate.
    injection Hcol as Hcol'.
    destruct p as [| p'].
    + simpl. rewrite dot_cons, dot_zero_l. ring.
    + simpl. rewrite dot_cons.
      assert (Hp' : (p' < m)%nat) by lia.
      rewrite (IH p' col' Hp' Hcol'). ring.
Qed.

Lemma row_vec_mat_unit : forall m ncols A p,
  MatrixShape m ncols A -> (p < m)%nat ->
  VecEq (row_vec_mat (identity_row m p) A ncols) (nth p A []).
Proof.
  intros m ncols A p [Hlen Hrows] Hp.
  assert (HpltA : (p < length A)%nat) by (rewrite Hlen; exact Hp).
  unfold row_vec_mat.
  apply (Forall2_from_nth Qeq 0 (map (fun col => dot (identity_row m p) col) (transpose A ncols)) (nth p A [])).
  - rewrite map_length, length_transpose.
    rewrite Forall_forall in Hrows.
    symmetry. apply Hrows, nth_In, HpltA.
  - intros j Hj.
    assert (Hjtr : (j < length (transpose A ncols))%nat) by (rewrite map_length in Hj; exact Hj).
    assert (Hjnc : (j < ncols)%nat) by (rewrite length_transpose in Hjtr; exact Hjtr).
    assert (Heq1 : nth j (map (fun col => dot (identity_row m p) col) (transpose A ncols)) 0
                 = dot (identity_row m p) (nth j (transpose A ncols) [])).
    { apply (my_nth_map (list Q) Q (fun col => dot (identity_row m p) col) (transpose A ncols) j [] 0 Hjtr). }
    rewrite Heq1.
    rewrite (nth_transpose A ncols j Hjnc).
    assert (HjA : length (map (fun row => nth j row 0) A) = m) by (rewrite map_length; exact Hlen).
    rewrite (dot_identity_row m p (map (fun row => nth j row 0) A) Hp HjA).
    assert (Heq2 : nth p (map (fun row => nth j row 0) A) 0 = nth j (nth p A []) 0).
    { apply (my_nth_map (list Q) Q (fun row => nth j row 0) A p [] 0 HpltA). }
    rewrite Heq2.
    reflexivity.
Qed.

Fixpoint vscale (c : Q) (u : list Q) : list Q :=
  match u with
  | [] => []
  | x :: u' => (c * x) :: vscale c u'
  end.

Fixpoint vadd (u v : list Q) : list Q :=
  match u, v with
  | [], _ => v
  | x :: u', [] => x :: u'
  | x :: u', y :: v' => (x + y) :: vadd u' v'
  end.

Lemma length_vscale : forall c u, length (vscale c u) = length u.
Proof. induction u; simpl; [reflexivity | now rewrite IHu]. Qed.

Lemma length_vadd : forall u v, length u = length v -> length (vadd u v) = length u.
Proof.
  induction u as [| x u IH]; intros v Hlen; destruct v as [| y v]; simpl in Hlen; try discriminate.
  - reflexivity.
  - simpl. now rewrite IH by lia.
Qed.

Instance vscale_Proper : Proper (Qeq ==> VecEq ==> VecEq) vscale.
Proof.
  intros c1 c2 Hc u1 u2 Hu. unfold VecEq in *.
  induction Hu as [| x y u1 u2 Hxy Hrest IH]; constructor.
  - rewrite Hc, Hxy. reflexivity.
  - exact IH.
Qed.

Lemma vadd_Proper_aux : forall u1 u2, VecEq u1 u2 -> forall v1 v2, VecEq v1 v2 -> VecEq (vadd u1 v1) (vadd u2 v2).
Proof.
  unfold VecEq. induction 1 as [| x y u1 u2 Hxy Hrest IH]; intros v1 v2 Hv.
  - exact Hv.
  - destruct Hv as [| a b v1' v2' Hab Hv']; simpl.
    + constructor; [exact Hxy | exact Hrest].
    + constructor; [rewrite Hxy, Hab; reflexivity | apply IH; exact Hv'].
Qed.

Instance vadd_Proper : Proper (VecEq ==> VecEq ==> VecEq) vadd.
Proof. intros u1 u2 Hu v1 v2 Hv. apply vadd_Proper_aux; assumption. Qed.

Lemma dot_vscale_l : forall c u v, dot (vscale c u) v == c * dot u v.
Proof.
  intros c u.
  induction u as [| x u IH]; intros v; simpl.
  - unfold dot. simpl. ring.
  - destruct v as [| y v]; unfold dot in *; simpl in *.
    + ring.
    + rewrite IH. ring.
Qed.

Lemma dot_vadd_l : forall u1 u2 v,
  length u1 = length u2 -> dot (vadd u1 u2) v == dot u1 v + dot u2 v.
Proof.
  induction u1 as [| x u1 IH]; intros u2 v Hlen; destruct u2 as [| y u2]; simpl in Hlen; try discriminate.
  - unfold dot. simpl. ring.
  - destruct v as [| z v]; unfold dot in *; simpl in *.
    + ring.
    + assert (Hlen' : length u1 = length u2) by lia.
      rewrite (IH u2 v Hlen'). ring.
Qed.

Lemma row_vec_mat_vscale : forall c row D ncols,
  VecEq (row_vec_mat (vscale c row) D ncols) (vscale c (row_vec_mat row D ncols)).
Proof.
  intros c row D ncols. unfold row_vec_mat.
  induction (transpose D ncols) as [| col rest IH]; simpl; constructor.
  - apply dot_vscale_l.
  - exact IH.
Qed.

Lemma row_vec_mat_vadd : forall row1 row2 D ncols,
  length row1 = length row2 ->
  VecEq (row_vec_mat (vadd row1 row2) D ncols) (vadd (row_vec_mat row1 D ncols) (row_vec_mat row2 D ncols)).
Proof.
  intros row1 row2 D ncols Hlen. unfold row_vec_mat.
  induction (transpose D ncols) as [| col rest IH]; simpl; constructor.
  - apply dot_vadd_l. exact Hlen.
  - exact IH.
Qed.

(* Purely structural (no arithmetic): prepending row0 to D' prepends
   row0's own entries onto each column of transpose D'. Leibniz `=` is
   fine here, matching the discipline established in Stage3. *)
Lemma transpose_cons : forall (row0 : list Q) (D' : list (list Q)) (ncols : nat),
  length row0 = ncols ->
  transpose (row0 :: D') ncols = map (fun p => fst p :: snd p) (combine row0 (transpose D' ncols)).
Proof.
  intros row0 D' ncols Hrow0.
  apply nth_ext with (d := @nil Q) (d' := @nil Q).
  - rewrite map_length, combine_length, length_transpose, Hrow0, length_transpose. lia.
  - intros j Hj. rewrite length_transpose in Hj.
    transitivity (nth j row0 0 :: nth j (transpose D' ncols) (@nil Q)).
    + rewrite (nth_transpose (row0 :: D') ncols j Hj). simpl.
      f_equal. symmetry. apply (nth_transpose D' ncols j Hj).
    + assert (Hpair : nth j (combine row0 (transpose D' ncols)) (0, @nil Q)
                     = (nth j row0 0, nth j (transpose D' ncols) (@nil Q))).
      { apply combine_nth. rewrite Hrow0, length_transpose. reflexivity. }
      assert (Hjlen : (j < length (combine row0 (transpose D' ncols)))%nat).
      { rewrite combine_length, Hrow0, length_transpose. lia. }
      rewrite (my_nth_map (Q * list Q) (list Q) (fun p => fst p :: snd p)
                 (combine row0 (transpose D' ncols)) j (0, @nil Q) (@nil Q) Hjlen).
      rewrite Hpair. reflexivity.
Qed.

(* "Expand by first row": the local core the shaped mat_mul_assoc rests
   on. Argument order in dot doesn't matter for dot_cons to fire -- both
   the row vector (a::u) and each column (row-entry :: column-tail) are
   cons'd in lockstep by transpose_cons. *)
Lemma row_vec_mat_cons : forall a u row M ncols,
  length row = ncols ->
  VecEq (row_vec_mat (a :: u) (row :: M) ncols) (vadd (vscale a row) (row_vec_mat u M ncols)).
Proof.
  intros a u row M ncols Hrow.
  unfold row_vec_mat.
  rewrite (transpose_cons row M ncols Hrow).
  rewrite map_map.
  assert (Hlen : length row = length (transpose M ncols)).
  { rewrite length_transpose. exact Hrow. }
  clear Hrow.
  revert Hlen. generalize (transpose M ncols) as T. revert row.
  induction row as [| r row IHrow]; intros T Hlen; destruct T as [| t T]; simpl in Hlen; try discriminate.
  - simpl. apply VecEq_Equivalence.
  - simpl combine. simpl map. unfold vadd, vscale. fold vadd. fold vscale. simpl.
    constructor.
    + rewrite dot_cons. ring.
    + apply IHrow. lia.
Qed.

Lemma length_row_vec_mat : forall row D ncols, length (row_vec_mat row D ncols) = ncols.
Proof. intros row D ncols. unfold row_vec_mat. rewrite map_length. apply length_transpose. Qed.

Lemma length_mat_mul : forall A B ncols_B, length (mat_mul A B ncols_B) = length A.
Proof. intros A B ncols_B. unfold mat_mul. apply map_length. Qed.

Lemma nth_mat_mul : forall A B ncols_B j, (j < length A)%nat ->
  nth j (mat_mul A B ncols_B) [] = row_vec_mat (nth j A []) B ncols_B.
Proof. intros A B ncols_B j Hj. unfold mat_mul. apply (my_nth_map (list Q) (list Q) (fun row_a => row_vec_mat row_a B ncols_B) A j [] [] Hj). Qed.

Lemma nth_repeat_eq : forall (x : Q) (n j : nat), (j < n)%nat -> nth j (repeat x n) 0 = x.
Proof.
  induction n as [| n IH]; intros j Hj; [lia |].
  destruct j as [| j]; simpl.
  - reflexivity.
  - apply IH. lia.
Qed.

(* row_vec_mat of an all-zero row is the all-zero vector, regardless of
   the target matrix -- the base case row_vec_mat_assoc's induction
   rests on. dot_zero_l holds for a zero row of ANY declared length k
   against a column of any length (combine just truncates), so this
   holds independent of D's actual row count. *)
Lemma row_vec_mat_zero : forall k D ncols, VecEq (row_vec_mat (repeat 0 k) D ncols) (repeat 0 ncols).
Proof.
  intros k D ncols.
  apply (Forall2_from_nth Qeq 0 (row_vec_mat (repeat 0 k) D ncols) (repeat 0 ncols)).
  - rewrite length_row_vec_mat, repeat_length. reflexivity.
  - intros j Hj. rewrite length_row_vec_mat in Hj.
    unfold row_vec_mat.
    assert (Heq : nth j (map (fun col => dot (repeat 0 k) col) (transpose D ncols)) 0
                = dot (repeat 0 k) (nth j (transpose D ncols) [])).
    { apply (my_nth_map (list Q) Q (fun col => dot (repeat 0 k) col) (transpose D ncols) j [] 0).
      rewrite length_transpose. exact Hj. }
    rewrite Heq, dot_zero_l, (nth_repeat_eq 0 ncols j Hj). reflexivity.
Qed.

(* Single-row associativity: r^T(BC) = (r^T B)C. The real inductive
   content mat_mul_assoc rests on -- paired induction on r and B,
   using row_vec_mat_cons to peel one row/entry off at a time. *)
Lemma row_vec_mat_assoc_row : forall B C n p,
  MatrixShape (length B) n B -> MatrixShape n p C ->
  forall r, length r = length B ->
  VecEq (row_vec_mat (row_vec_mat r B n) C p) (row_vec_mat r (mat_mul B C p) p).
Proof.
  induction B as [| b0 B' IH]; intros C n p [HlenB HrowsB] [HlenC HrowsC] r Hr.
  - destruct r as [| x r]; simpl in Hr; try discriminate.
    assert (Hgoal : VecEq (row_vec_mat (row_vec_mat (@nil Q) (@nil (list Q)) n) C p)
                           (row_vec_mat (@nil Q) (mat_mul (@nil (list Q)) C p) p)).
    { assert (H1 : VecEq (row_vec_mat (@nil Q) (@nil (list Q)) n) (repeat 0 n))
        by (apply (row_vec_mat_zero 0%nat (@nil (list Q)) n)).
      assert (H2 : VecEq (row_vec_mat (row_vec_mat (@nil Q) (@nil (list Q)) n) C p) (row_vec_mat (repeat 0 n) C p)).
      { apply (row_vec_mat_Proper p); [exact H1 | reflexivity]. }
      assert (H3 : VecEq (row_vec_mat (repeat 0 n) C p) (repeat 0 p)) by (apply row_vec_mat_zero).
      assert (H4 : VecEq (row_vec_mat (@nil Q) (mat_mul (@nil (list Q)) C p) p) (repeat 0 p))
        by (apply (row_vec_mat_zero 0%nat (mat_mul (@nil (list Q)) C p) p)).
      rewrite H2, H3. symmetry. exact H4. }
    exact Hgoal.
  - destruct r as [| x r']; simpl in Hr; try discriminate.
    injection Hr as Hr'.
    apply Forall_cons_iff in HrowsB. destruct HrowsB as [Hb0 HrowsB'].
    assert (IHB' : VecEq (row_vec_mat (row_vec_mat r' B' n) C p) (row_vec_mat r' (mat_mul B' C p) p)).
    { apply IH; [split; [reflexivity | exact HrowsB'] | split; assumption | exact Hr']. }
    assert (Hstep : VecEq (row_vec_mat (x :: r') (b0 :: B') n) (vadd (vscale x b0) (row_vec_mat r' B' n)))
      by (apply row_vec_mat_cons; exact Hb0).
    assert (Hlhs : VecEq (row_vec_mat (row_vec_mat (x :: r') (b0 :: B') n) C p)
                          (row_vec_mat (vadd (vscale x b0) (row_vec_mat r' B' n)) C p)).
    { apply (row_vec_mat_Proper p); [exact Hstep | reflexivity]. }
    assert (Hlhs2 : VecEq (row_vec_mat (vadd (vscale x b0) (row_vec_mat r' B' n)) C p)
                           (vadd (row_vec_mat (vscale x b0) C p) (row_vec_mat (row_vec_mat r' B' n) C p))).
    { apply row_vec_mat_vadd. rewrite length_vscale, length_row_vec_mat. exact Hb0. }
    assert (Hlhs3 : VecEq (row_vec_mat (vscale x b0) C p) (vscale x (row_vec_mat b0 C p)))
      by (apply row_vec_mat_vscale).
    assert (Hrhs : mat_mul (b0 :: B') C p = row_vec_mat b0 C p :: mat_mul B' C p) by reflexivity.
    assert (Hrhs2 : VecEq (row_vec_mat (x :: r') (mat_mul (b0 :: B') C p) p)
                           (vadd (vscale x (row_vec_mat b0 C p)) (row_vec_mat r' (mat_mul B' C p) p))).
    { rewrite Hrhs. apply row_vec_mat_cons. apply length_row_vec_mat. }
    rewrite Hlhs, Hlhs2, Hlhs3, Hrhs2, IHB'.
    reflexivity.
Qed.

Lemma mat_mul_MatrixShape : forall m k n A B, MatrixShape m k A -> MatrixShape k n B -> MatrixShape m n (mat_mul A B n).
Proof.
  intros m k n A B [HlenA HrowsA] [HlenB HrowsB].
  split.
  - rewrite length_mat_mul. exact HlenA.
  - apply Forall_forall. intros row Hrow.
    apply In_nth with (d := @nil Q) in Hrow. destruct Hrow as [j [Hj Hnth]].
    rewrite length_mat_mul in Hj.
    rewrite (nth_mat_mul A B n j Hj) in Hnth.
    rewrite <- Hnth. apply length_row_vec_mat.
Qed.

Lemma mat_mul_assoc_core : forall (A B C : list (list Q)) (k n p : nat),
  Forall (fun row => length row = k) A ->
  MatrixShape k n B -> MatrixShape n p C ->
  MatEq (mat_mul (mat_mul A B n) C p) (mat_mul A (mat_mul B C p) p).
Proof.
  induction A as [| a0 A' IH]; intros B C k n p HrowsA HB HC.
  - simpl. constructor.
  - apply Forall_cons_iff in HrowsA. destruct HrowsA as [Ha0 HrowsA'].
    assert (HB' : MatrixShape (length B) n B) by (destruct HB as [HlenB HrowsB]; split; [reflexivity | exact HrowsB]).
    assert (Ha0len : length a0 = length B) by (destruct HB as [HlenB _]; rewrite HlenB; exact Ha0).
    assert (Hhead : VecEq (row_vec_mat (row_vec_mat a0 B n) C p) (row_vec_mat a0 (mat_mul B C p) p))
      by (apply row_vec_mat_assoc_row; assumption).
    assert (Htail : MatEq (mat_mul (mat_mul A' B n) C p) (mat_mul A' (mat_mul B C p) p))
      by (apply IH with (k := k); assumption).
    change (mat_mul (a0 :: A') B n) with (row_vec_mat a0 B n :: mat_mul A' B n).
    change (mat_mul (row_vec_mat a0 B n :: mat_mul A' B n) C p)
      with (row_vec_mat (row_vec_mat a0 B n) C p :: mat_mul (mat_mul A' B n) C p).
    change (mat_mul (a0 :: A') (mat_mul B C p) p)
      with (row_vec_mat a0 (mat_mul B C p) p :: mat_mul A' (mat_mul B C p) p).
    constructor; assumption.
Qed.

Theorem mat_mul_assoc : forall m k n p (A B C : list (list Q)),
  MatrixShape m k A -> MatrixShape k n B -> MatrixShape n p C ->
  MatEq (mat_mul (mat_mul A B n) C p) (mat_mul A (mat_mul B C p) p).
Proof.
  intros m k n p A B C [HlenA HrowsA] HB HC.
  apply mat_mul_assoc_core with (k := k); assumption.
Qed.

(* The generic pattern every elementary row operation's invariant
   preservation reduces to: given work ~ T A0 and rowop(work) ~ E work
   (rowop's own semantics theorem, proved separately per operation),
   left-multiplication by E carries the invariant to E T, A0. *)
Lemma left_mul_preserves_transform_invariant : forall m k n E T A0 work width,
  MatrixShape m k E -> MatrixShape k n T -> MatrixShape n width A0 ->
  MatEq work (mat_mul T A0 width) ->
  MatEq (mat_mul E work width) (mat_mul (mat_mul E T n) A0 width).
Proof.
  intros m k n E T A0 work width HE HT HA0 Hwork.
  assert (H1 : MatEq (mat_mul E work width) (mat_mul E (mat_mul T A0 width) width)).
  { apply (mat_mul_Proper width); [reflexivity | exact Hwork]. }
  assert (H2 : MatEq (mat_mul (mat_mul E T n) A0 width) (mat_mul E (mat_mul T A0 width) width)).
  { apply (mat_mul_assoc m k n width E T A0); assumption. }
  rewrite H1, H2. reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* Item 6: elementary row operations.                                 *)
(* ------------------------------------------------------------------ *)

Definition replace_nth (i : nat) (x : list Q) (D : list (list Q)) : list (list Q) :=
  map (fun j => if Nat.eqb j i then x else nth j D []) (seq 0 (length D)).

Lemma length_replace_nth : forall i x D, length (replace_nth i x D) = length D.
Proof. intros i x D. unfold replace_nth. rewrite map_length, seq_length. reflexivity. Qed.

Lemma nth_replace_nth : forall i x D j, (j < length D)%nat ->
  nth j (replace_nth i x D) [] = if Nat.eqb j i then x else nth j D [].
Proof.
  intros i x D j Hj. unfold replace_nth.
  rewrite (nth_indep _ [] (if Nat.eqb j i then x else nth j D [])).
  - rewrite (map_nth (fun k => if Nat.eqb k i then x else nth k D []) (seq 0 (length D)) j j).
    rewrite seq_nth by exact Hj.
    reflexivity.
  - rewrite map_length, seq_length. exact Hj.
Qed.

Lemma nth_identity_matrix : forall m j, (j < m)%nat -> nth j (identity_matrix m) [] = identity_row m j.
Proof.
  intros m j Hj. unfold identity_matrix.
  rewrite (nth_indep _ [] (identity_row m j)).
  - rewrite (map_nth (identity_row m) (seq 0 m) j j).
    rewrite seq_nth by exact Hj.
    reflexivity.
  - rewrite map_length, seq_length. exact Hj.
Qed.

Lemma length_identity_matrix : forall m, length (identity_matrix m) = m.
Proof. intros m. unfold identity_matrix. rewrite map_length, seq_length. reflexivity. Qed.

Lemma identity_matrix_MatrixShape : forall m, MatrixShape m m (identity_matrix m).
Proof.
  intros m. split.
  - apply length_identity_matrix.
  - apply Forall_forall. intros row Hrow.
    apply In_nth with (d := @nil Q) in Hrow. destruct Hrow as [j [Hj Hnth]].
    rewrite length_identity_matrix in Hj.
    rewrite (nth_identity_matrix m j Hj) in Hnth.
    rewrite <- Hnth. apply length_identity_row.
Qed.

(* --- scale_row --- *)

Definition scale_row (i : nat) (a : Q) (A : list (list Q)) : list (list Q) :=
  replace_nth i (vscale a (nth i A [])) A.

Lemma length_scale_row : forall i a A, length (scale_row i a A) = length A.
Proof. intros. unfold scale_row. apply length_replace_nth. Qed.

Lemma nth_scale_row_same : forall i a A, (i < length A)%nat ->
  nth i (scale_row i a A) [] = vscale a (nth i A []).
Proof.
  intros i a A Hi. unfold scale_row. rewrite (nth_replace_nth i (vscale a (nth i A [])) A i Hi).
  rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma nth_scale_row_other : forall i a A j, j <> i -> (j < length A)%nat ->
  nth j (scale_row i a A) [] = nth j A [].
Proof.
  intros i a A j Hji Hj. unfold scale_row. rewrite (nth_replace_nth i (vscale a (nth i A [])) A j Hj).
  destruct (Nat.eqb j i) eqn:Heq.
  - apply Nat.eqb_eq in Heq. contradiction.
  - reflexivity.
Qed.

Lemma scale_row_MatrixShape : forall m n A i a, MatrixShape m n A -> (i < m)%nat -> MatrixShape m n (scale_row i a A).
Proof.
  intros m n A i a [Hlen Hrows] Hi.
  split.
  - rewrite length_scale_row. exact Hlen.
  - apply Forall_forall. intros row Hrow.
    apply In_nth with (d := @nil Q) in Hrow. destruct Hrow as [j [Hj Hnth]].
    rewrite length_scale_row in Hj.
    assert (HiA : (i < length A)%nat) by (rewrite Hlen; exact Hi).
    destruct (Nat.eq_dec j i) as [Heq | Hneq].
    + subst j. rewrite (nth_scale_row_same i a A HiA) in Hnth.
      rewrite <- Hnth, length_vscale.
      rewrite Forall_forall in Hrows. apply Hrows, nth_In. exact HiA.
    + rewrite (nth_scale_row_other i a A j Hneq Hj) in Hnth.
      rewrite <- Hnth.
      rewrite Forall_forall in Hrows. apply Hrows, nth_In. exact Hj.
Qed.

Instance scale_row_Proper : forall i a, Proper (MatEq ==> MatEq) (fun A => scale_row i a A).
Proof.
  intros i a A1 A2 HA.
  assert (Hlen : length A1 = length A2) by (eapply Forall2_length; exact HA).
  apply (Forall2_from_nth VecEq (@nil Q) (scale_row i a A1) (scale_row i a A2)).
  - rewrite !length_scale_row. exact Hlen.
  - intros j Hj. rewrite length_scale_row in Hj.
    destruct (Nat.eq_dec j i) as [Heq | Hneq].
    + subst j. assert (Hj2 : (i < length A2)%nat) by (rewrite <- Hlen; exact Hj).
      rewrite (nth_scale_row_same i a A1 Hj), (nth_scale_row_same i a A2 Hj2).
      apply vscale_Proper; [reflexivity |]. apply (MatEq_nth_row A1 A2 HA).
    + assert (Hj2 : (j < length A2)%nat) by (rewrite <- Hlen; exact Hj).
      rewrite (nth_scale_row_other i a A1 j Hneq Hj), (nth_scale_row_other i a A2 j Hneq Hj2).
      apply (MatEq_nth_row A1 A2 HA).
Qed.

Definition E_scale (m : nat) (i : nat) (a : Q) : list (list Q) := scale_row i a (identity_matrix m).

Theorem scale_row_elementary_semantics : forall m n A i a,
  MatrixShape m n A -> (i < m)%nat ->
  MatEq (scale_row i a A) (mat_mul (E_scale m i a) A n).
Proof.
  intros m n A i a HA Hi.
  apply (Forall2_from_nth VecEq (@nil Q) (scale_row i a A) (mat_mul (E_scale m i a) A n)).
  - rewrite length_scale_row, length_mat_mul.
    unfold E_scale. rewrite length_scale_row, length_identity_matrix.
    destruct HA as [HlenA _]. exact HlenA.
  - intros j Hj. rewrite length_scale_row in Hj.
    destruct HA as [HlenA HrowsA].
    assert (HjEm : (j < length (E_scale m i a))%nat)
      by (unfold E_scale; rewrite length_scale_row, length_identity_matrix; rewrite <- HlenA; exact Hj).
    rewrite (nth_mat_mul (E_scale m i a) A n j HjEm).
    unfold E_scale.
    destruct (Nat.eq_dec j i) as [Heq | Hneq].
    + subst j. assert (Hi_id : (i < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hi).
      rewrite (nth_scale_row_same i a (identity_matrix m) Hi_id).
      rewrite (nth_identity_matrix m i Hi).
      assert (Hi_A : (i < length A)%nat) by (rewrite HlenA; exact Hi).
      rewrite (nth_scale_row_same i a A Hi_A).
      assert (H1 : VecEq (row_vec_mat (vscale a (identity_row m i)) A n) (vscale a (row_vec_mat (identity_row m i) A n)))
        by apply row_vec_mat_vscale.
      assert (H2 : VecEq (row_vec_mat (identity_row m i) A n) (nth i A []))
        by (apply row_vec_mat_unit; [split; assumption | exact Hi]).
      rewrite H1, H2. reflexivity.
    + assert (Hjm : (j < m)%nat) by (rewrite <- HlenA; exact Hj).
      assert (Hj_id : (j < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hjm).
      rewrite (nth_scale_row_other i a (identity_matrix m) j Hneq Hj_id).
      rewrite (nth_identity_matrix m j Hjm).
      rewrite (nth_scale_row_other i a A j Hneq Hj).
      symmetry. apply row_vec_mat_unit; [split; assumption | exact Hjm].
Qed.

Lemma E_scale_MatrixShape : forall m i a, (i < m)%nat -> MatrixShape m m (E_scale m i a).
Proof. intros m i a Hi. unfold E_scale. apply scale_row_MatrixShape; [apply identity_matrix_MatrixShape | exact Hi]. Qed.

Corollary scale_row_preserves_transform_invariant : forall m n p work T A0 i a,
  MatrixShape m n T -> MatrixShape n p A0 -> MatEq work (mat_mul T A0 p) -> (i < m)%nat ->
  MatEq (scale_row i a work) (mat_mul (mat_mul (E_scale m i a) T n) A0 p).
Proof.
  intros m n p work T A0 i a HT HA0 Hwork Hi.
  assert (Hworkshape : MatrixShape m p work).
  { apply (MatEq_MatrixShape m p (mat_mul T A0 p) work); [symmetry; exact Hwork | apply (mat_mul_MatrixShape m n p T A0 HT HA0)]. }
  assert (H1 : MatEq (scale_row i a work) (mat_mul (E_scale m i a) work p))
    by (apply scale_row_elementary_semantics; assumption).
  assert (H2 : MatEq (mat_mul (E_scale m i a) work p) (mat_mul (mat_mul (E_scale m i a) T n) A0 p)).
  { apply (left_mul_preserves_transform_invariant m m n (E_scale m i a) T A0 work p);
      [apply E_scale_MatrixShape; exact Hi | exact HT | exact HA0 | exact Hwork]. }
  rewrite H1, H2. reflexivity.
Qed.

(* --- add_scaled_row --- *)

Definition add_scaled_row (dst src : nat) (a : Q) (A : list (list Q)) : list (list Q) :=
  replace_nth dst (vadd (nth dst A []) (vscale a (nth src A []))) A.

Lemma length_add_scaled_row : forall dst src a A, length (add_scaled_row dst src a A) = length A.
Proof. intros. unfold add_scaled_row. apply length_replace_nth. Qed.

Lemma nth_add_scaled_row_dst : forall dst src a A, (dst < length A)%nat ->
  nth dst (add_scaled_row dst src a A) [] = vadd (nth dst A []) (vscale a (nth src A [])).
Proof.
  intros dst src a A Hd. unfold add_scaled_row.
  rewrite (nth_replace_nth dst (vadd (nth dst A []) (vscale a (nth src A []))) A dst Hd).
  rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma nth_add_scaled_row_other : forall dst src a A j, j <> dst -> (j < length A)%nat ->
  nth j (add_scaled_row dst src a A) [] = nth j A [].
Proof.
  intros dst src a A j Hjd Hj. unfold add_scaled_row.
  rewrite (nth_replace_nth dst (vadd (nth dst A []) (vscale a (nth src A []))) A j Hj).
  destruct (Nat.eqb j dst) eqn:Heq.
  - apply Nat.eqb_eq in Heq. contradiction.
  - reflexivity.
Qed.

Lemma add_scaled_row_MatrixShape : forall m n A dst src a,
  MatrixShape m n A -> (dst < m)%nat -> (src < m)%nat -> MatrixShape m n (add_scaled_row dst src a A).
Proof.
  intros m n A dst src a [Hlen Hrows] Hdst Hsrc.
  split.
  - rewrite length_add_scaled_row. exact Hlen.
  - apply Forall_forall. intros row Hrow.
    apply In_nth with (d := @nil Q) in Hrow. destruct Hrow as [j [Hj Hnth]].
    rewrite length_add_scaled_row in Hj.
    assert (HdstA : (dst < length A)%nat) by (rewrite Hlen; exact Hdst).
    assert (HsrcA : (src < length A)%nat) by (rewrite Hlen; exact Hsrc).
    destruct (Nat.eq_dec j dst) as [Heq | Hneq].
    + subst j. rewrite (nth_add_scaled_row_dst dst src a A HdstA) in Hnth.
      rewrite <- Hnth.
      rewrite Forall_forall in Hrows.
      assert (Hlen_dst : length (nth dst A []) = n) by (apply Hrows, nth_In, HdstA).
      assert (Hlen_src : length (nth src A []) = n) by (apply Hrows, nth_In, HsrcA).
      rewrite (length_vadd (nth dst A []) (vscale a (nth src A [])))
        by (rewrite length_vscale, Hlen_dst, Hlen_src; reflexivity).
      exact Hlen_dst.
    + rewrite (nth_add_scaled_row_other dst src a A j Hneq Hj) in Hnth.
      rewrite <- Hnth.
      rewrite Forall_forall in Hrows. apply Hrows, nth_In, Hj.
Qed.

Instance add_scaled_row_Proper : forall dst src a, Proper (MatEq ==> MatEq) (fun A => add_scaled_row dst src a A).
Proof.
  intros dst src a A1 A2 HA.
  assert (Hlen : length A1 = length A2) by (eapply Forall2_length; exact HA).
  apply (Forall2_from_nth VecEq (@nil Q) (add_scaled_row dst src a A1) (add_scaled_row dst src a A2)).
  - rewrite !length_add_scaled_row. exact Hlen.
  - intros j Hj. rewrite length_add_scaled_row in Hj.
    destruct (Nat.eq_dec j dst) as [Heq | Hneq].
    + subst j. assert (Hj2 : (dst < length A2)%nat) by (rewrite <- Hlen; exact Hj).
      rewrite (nth_add_scaled_row_dst dst src a A1 Hj), (nth_add_scaled_row_dst dst src a A2 Hj2).
      apply vadd_Proper; [apply (MatEq_nth_row A1 A2 HA) |].
      apply vscale_Proper; [reflexivity | apply (MatEq_nth_row A1 A2 HA)].
    + assert (Hj2 : (j < length A2)%nat) by (rewrite <- Hlen; exact Hj).
      rewrite (nth_add_scaled_row_other dst src a A1 j Hneq Hj), (nth_add_scaled_row_other dst src a A2 j Hneq Hj2).
      apply (MatEq_nth_row A1 A2 HA).
Qed.

Definition E_add (m dst src : nat) (a : Q) : list (list Q) := add_scaled_row dst src a (identity_matrix m).

Theorem add_scaled_row_elementary_semantics : forall m n A dst src a,
  MatrixShape m n A -> (dst < m)%nat -> (src < m)%nat ->
  MatEq (add_scaled_row dst src a A) (mat_mul (E_add m dst src a) A n).
Proof.
  intros m n A dst src a HA Hdst Hsrc.
  apply (Forall2_from_nth VecEq (@nil Q) (add_scaled_row dst src a A) (mat_mul (E_add m dst src a) A n)).
  - rewrite length_add_scaled_row, length_mat_mul.
    unfold E_add. rewrite length_add_scaled_row, length_identity_matrix.
    destruct HA as [HlenA _]. exact HlenA.
  - intros j Hj. rewrite length_add_scaled_row in Hj.
    destruct HA as [HlenA HrowsA].
    assert (HjEm : (j < length (E_add m dst src a))%nat)
      by (unfold E_add; rewrite length_add_scaled_row, length_identity_matrix; rewrite <- HlenA; exact Hj).
    rewrite (nth_mat_mul (E_add m dst src a) A n j HjEm).
    unfold E_add.
    assert (Hdst_id : (dst < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hdst).
    assert (Hsrc_id : (src < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hsrc).
    assert (Hdst_A : (dst < length A)%nat) by (rewrite HlenA; exact Hdst).
    assert (Hsrc_A : (src < length A)%nat) by (rewrite HlenA; exact Hsrc).
    destruct (Nat.eq_dec j dst) as [Heq | Hneq].
    + subst j.
      rewrite (nth_add_scaled_row_dst dst src a (identity_matrix m) Hdst_id).
      rewrite (nth_identity_matrix m dst Hdst), (nth_identity_matrix m src Hsrc).
      rewrite (nth_add_scaled_row_dst dst src a A Hdst_A).
      assert (H1 : VecEq (row_vec_mat (vadd (identity_row m dst) (vscale a (identity_row m src))) A n)
                          (vadd (row_vec_mat (identity_row m dst) A n) (row_vec_mat (vscale a (identity_row m src)) A n))).
      { apply row_vec_mat_vadd. rewrite length_vscale, !length_identity_row. reflexivity. }
      assert (H2 : VecEq (row_vec_mat (vscale a (identity_row m src)) A n) (vscale a (row_vec_mat (identity_row m src) A n)))
        by apply row_vec_mat_vscale.
      assert (H3 : VecEq (row_vec_mat (identity_row m dst) A n) (nth dst A []))
        by (apply row_vec_mat_unit; [split; assumption | exact Hdst]).
      assert (H4 : VecEq (row_vec_mat (identity_row m src) A n) (nth src A []))
        by (apply row_vec_mat_unit; [split; assumption | exact Hsrc]).
      rewrite H1, H2, H3, H4. reflexivity.
    + assert (Hjm : (j < m)%nat) by (rewrite <- HlenA; exact Hj).
      assert (Hj_id : (j < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hjm).
      rewrite (nth_add_scaled_row_other dst src a (identity_matrix m) j Hneq Hj_id).
      rewrite (nth_identity_matrix m j Hjm).
      rewrite (nth_add_scaled_row_other dst src a A j Hneq Hj).
      symmetry. apply row_vec_mat_unit; [split; assumption | exact Hjm].
Qed.

Lemma E_add_MatrixShape : forall m dst src a, (dst < m)%nat -> (src < m)%nat -> MatrixShape m m (E_add m dst src a).
Proof.
  intros m dst src a Hdst Hsrc. unfold E_add.
  apply add_scaled_row_MatrixShape; [apply identity_matrix_MatrixShape | exact Hdst | exact Hsrc].
Qed.

Corollary add_scaled_row_preserves_transform_invariant : forall m n p work T A0 dst src a,
  MatrixShape m n T -> MatrixShape n p A0 -> MatEq work (mat_mul T A0 p) -> (dst < m)%nat -> (src < m)%nat ->
  MatEq (add_scaled_row dst src a work) (mat_mul (mat_mul (E_add m dst src a) T n) A0 p).
Proof.
  intros m n p work T A0 dst src a HT HA0 Hwork Hdst Hsrc.
  assert (Hworkshape : MatrixShape m p work).
  { apply (MatEq_MatrixShape m p (mat_mul T A0 p) work); [symmetry; exact Hwork | apply (mat_mul_MatrixShape m n p T A0 HT HA0)]. }
  assert (H1 : MatEq (add_scaled_row dst src a work) (mat_mul (E_add m dst src a) work p))
    by (apply add_scaled_row_elementary_semantics; assumption).
  assert (H2 : MatEq (mat_mul (E_add m dst src a) work p) (mat_mul (mat_mul (E_add m dst src a) T n) A0 p)).
  { apply (left_mul_preserves_transform_invariant m m n (E_add m dst src a) T A0 work p);
      [apply E_add_MatrixShape; assumption | exact HT | exact HA0 | exact Hwork]. }
  rewrite H1, H2. reflexivity.
Qed.

(* --- swap_rows --- *)

Definition swap_rows (i j : nat) (A : list (list Q)) : list (list Q) :=
  replace_nth j (nth i A []) (replace_nth i (nth j A []) A).

Lemma length_swap_rows : forall i j A, length (swap_rows i j A) = length A.
Proof. intros. unfold swap_rows. rewrite !length_replace_nth. reflexivity. Qed.

(* Single characterization covering i = j as well: checking "k =? j"
   first is exactly what the definition (outer replace_nth on j) does,
   and when i = j both branches agree since nth i A [] = nth j A []. *)
Lemma nth_swap_rows : forall i j A k, (k < length A)%nat ->
  nth k (swap_rows i j A) [] = if Nat.eqb k j then nth i A [] else if Nat.eqb k i then nth j A [] else nth k A [].
Proof.
  intros i j A k Hk. unfold swap_rows.
  assert (Hk' : (k < length (replace_nth i (nth j A []) A))%nat) by (rewrite length_replace_nth; exact Hk).
  rewrite (nth_replace_nth j (nth i A []) (replace_nth i (nth j A []) A) k Hk').
  destruct (Nat.eqb k j) eqn:Hkj.
  - reflexivity.
  - rewrite (nth_replace_nth i (nth j A []) A k Hk). reflexivity.
Qed.

Lemma swap_rows_MatrixShape : forall m n A i j, MatrixShape m n A -> (i < m)%nat -> (j < m)%nat -> MatrixShape m n (swap_rows i j A).
Proof.
  intros m n A i j [Hlen Hrows] Hi Hj.
  split.
  - rewrite length_swap_rows. exact Hlen.
  - apply Forall_forall. intros row Hrow.
    apply In_nth with (d := @nil Q) in Hrow. destruct Hrow as [k [Hk Hnth]].
    rewrite length_swap_rows in Hk.
    rewrite (nth_swap_rows i j A k Hk) in Hnth.
    rewrite Forall_forall in Hrows.
    assert (HiA : (i < length A)%nat) by (rewrite Hlen; exact Hi).
    assert (HjA : (j < length A)%nat) by (rewrite Hlen; exact Hj).
    destruct (Nat.eqb k j); [| destruct (Nat.eqb k i)];
      rewrite <- Hnth; apply Hrows, nth_In; assumption.
Qed.

Instance swap_rows_Proper : forall i j, Proper (MatEq ==> MatEq) (fun A => swap_rows i j A).
Proof.
  intros i j A1 A2 HA.
  assert (Hlen : length A1 = length A2) by (eapply Forall2_length; exact HA).
  apply (Forall2_from_nth VecEq (@nil Q) (swap_rows i j A1) (swap_rows i j A2)).
  - rewrite !length_swap_rows. exact Hlen.
  - intros k Hk. rewrite length_swap_rows in Hk.
    assert (Hk2 : (k < length A2)%nat) by (rewrite <- Hlen; exact Hk).
    rewrite (nth_swap_rows i j A1 k Hk), (nth_swap_rows i j A2 k Hk2).
    destruct (Nat.eqb k j); [| destruct (Nat.eqb k i)]; apply (MatEq_nth_row A1 A2 HA).
Qed.

Definition E_swap (m i j : nat) : list (list Q) := swap_rows i j (identity_matrix m).

Theorem swap_rows_elementary_semantics : forall m n A i j,
  MatrixShape m n A -> (i < m)%nat -> (j < m)%nat ->
  MatEq (swap_rows i j A) (mat_mul (E_swap m i j) A n).
Proof.
  intros m n A i j HA Hi Hj.
  apply (Forall2_from_nth VecEq (@nil Q) (swap_rows i j A) (mat_mul (E_swap m i j) A n)).
  - rewrite length_swap_rows, length_mat_mul.
    unfold E_swap. rewrite length_swap_rows, length_identity_matrix.
    destruct HA as [HlenA _]. exact HlenA.
  - intros k Hk. rewrite length_swap_rows in Hk.
    destruct HA as [HlenA HrowsA].
    assert (HkEm : (k < length (E_swap m i j))%nat)
      by (unfold E_swap; rewrite length_swap_rows, length_identity_matrix; rewrite <- HlenA; exact Hk).
    rewrite (nth_mat_mul (E_swap m i j) A n k HkEm).
    unfold E_swap.
    assert (Hi_id : (i < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hi).
    assert (Hj_id : (j < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hj).
    assert (Hkm : (k < m)%nat) by (rewrite <- HlenA; exact Hk).
    assert (Hk_id : (k < length (identity_matrix m))%nat) by (rewrite length_identity_matrix; exact Hkm).
    rewrite (nth_swap_rows i j (identity_matrix m) k Hk_id).
    rewrite (nth_identity_matrix m k Hkm), (nth_identity_matrix m i Hi), (nth_identity_matrix m j Hj).
    rewrite (nth_swap_rows i j A k Hk).
    destruct (Nat.eqb k j) eqn:Hkj.
    + symmetry. apply row_vec_mat_unit; [split; assumption | exact Hi].
    + destruct (Nat.eqb k i) eqn:Hki.
      * symmetry. apply row_vec_mat_unit; [split; assumption | exact Hj].
      * symmetry. apply row_vec_mat_unit; [split; assumption | exact Hkm].
Qed.

Lemma E_swap_MatrixShape : forall m i j, (i < m)%nat -> (j < m)%nat -> MatrixShape m m (E_swap m i j).
Proof.
  intros m i j Hi Hj. unfold E_swap.
  apply swap_rows_MatrixShape; [apply identity_matrix_MatrixShape | exact Hi | exact Hj].
Qed.

Corollary swap_rows_preserves_transform_invariant : forall m n p work T A0 i j,
  MatrixShape m n T -> MatrixShape n p A0 -> MatEq work (mat_mul T A0 p) -> (i < m)%nat -> (j < m)%nat ->
  MatEq (swap_rows i j work) (mat_mul (mat_mul (E_swap m i j) T n) A0 p).
Proof.
  intros m n p work T A0 i j HT HA0 Hwork Hi Hj.
  assert (Hworkshape : MatrixShape m p work).
  { apply (MatEq_MatrixShape m p (mat_mul T A0 p) work); [symmetry; exact Hwork | apply (mat_mul_MatrixShape m n p T A0 HT HA0)]. }
  assert (H1 : MatEq (swap_rows i j work) (mat_mul (E_swap m i j) work p))
    by (apply swap_rows_elementary_semantics; assumption).
  assert (H2 : MatEq (mat_mul (E_swap m i j) work p) (mat_mul (mat_mul (E_swap m i j) T n) A0 p)).
  { apply (left_mul_preserves_transform_invariant m m n (E_swap m i j) T A0 work p);
      [apply E_swap_MatrixShape; assumption | exact HT | exact HA0 | exact Hwork]. }
  rewrite H1, H2. reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* Item 7: elimination state, invariant, and pivot-prefix structure.  *)
(* ------------------------------------------------------------------ *)

Require Import Coq.Sorting.Sorted.

Lemma StronglySorted_snoc : forall (l : list nat) (x : nat),
  StronglySorted Nat.lt l -> Forall (fun y => (y < x)%nat) l -> StronglySorted Nat.lt (l ++ [x]).
Proof.
  induction l as [| a l IH]; intros x Hsorted Hall.
  - simpl. repeat constructor.
  - simpl. inversion Hsorted as [| a' l' Hsorted' HForall]; subst.
    inversion Hall as [| a'' l'' Ha Hall']; subst.
    constructor.
    + apply IH; assumption.
    + apply Forall_forall. intros y Hy.
      apply in_app_or in Hy. destruct Hy as [Hy | Hy].
      * rewrite Forall_forall in HForall. apply HForall; assumption.
      * simpl in Hy. destruct Hy as [Hy | []]; subst. exact Ha.
Qed.

Record ElimState := mkElimState {
  st_work : list (list Q);
  st_transform : list (list Q);
  st_pivot_row : nat;
  st_pivot_col : nat;
  st_pivot_cols : list nat
}.

Definition PivotAt (W : list (list Q)) (m i j : nat) : Prop :=
  nth j (nth i W []) 0 == 1 /\
  forall k, (k < m)%nat -> k <> i -> nth j (nth k W []) 0 == 0.

Definition PivotPrefix (W : list (list Q)) (m pivot_col : nat) (cols : list nat) : Prop :=
  StronglySorted Nat.lt cols /\
  Forall (fun j => (j < pivot_col)%nat) cols /\
  forall i j, nth_error cols i = Some j -> PivotAt W m i j.

(* Every column already processed (j < pivot_col) that never became a
   pivot column is entirely zero in every row not yet claimed as a
   pivot row (k >= pivot_row). PivotPrefix alone only constrains
   PIVOT columns; this is the companion fact for FREE columns, and it
   is exactly what the final nonpivot-row-is-zero theorem needs. *)
Definition FreeColumnsZeroBelow (m pivot_row pivot_col : nat) (cols : list nat) (W : list (list Q)) : Prop :=
  forall j, (j < pivot_col)%nat -> ~ In j cols ->
  forall k, (pivot_row <= k < m)%nat -> nth j (nth k W []) 0 == 0.

Definition ElimInvariant (m n : nat) (A0 : list (list Q)) (s : ElimState) : Prop :=
  MatrixShape m (S n) (st_work s) /\
  MatrixShape m m (st_transform s) /\
  (st_pivot_row s <= m)%nat /\
  (st_pivot_col s <= n)%nat /\
  length (st_pivot_cols s) = st_pivot_row s /\
  MatEq (st_work s) (mat_mul (st_transform s) A0 (S n)) /\
  PivotPrefix (st_work s) m (st_pivot_col s) (st_pivot_cols s) /\
  FreeColumnsZeroBelow m (st_pivot_row s) (st_pivot_col s) (st_pivot_cols s) (st_work s).

Lemma mat_mul_identity_l : forall m k A, MatrixShape m k A -> MatEq (mat_mul (identity_matrix m) A k) A.
Proof.
  intros m k A HA.
  apply (Forall2_from_nth VecEq (@nil Q) (mat_mul (identity_matrix m) A k) A).
  - rewrite length_mat_mul, length_identity_matrix. destruct HA as [HlenA _]. symmetry. exact HlenA.
  - intros j Hj. rewrite length_mat_mul, length_identity_matrix in Hj.
    rewrite (nth_mat_mul (identity_matrix m) A k j (eq_ind_r (fun x => (j<x)%nat) Hj (length_identity_matrix m))).
    rewrite (nth_identity_matrix m j Hj).
    apply row_vec_mat_unit; [exact HA | exact Hj].
Qed.

Definition initial_state (m : nat) (A0 : list (list Q)) : ElimState :=
  mkElimState A0 (identity_matrix m) 0%nat 0%nat [].

Theorem initial_state_invariant : forall m n A0, MatrixShape m (S n) A0 -> ElimInvariant m n A0 (initial_state m A0).
Proof.
  intros m n A0 HA0. unfold ElimInvariant, initial_state. simpl.
  split; [| split; [| split; [| split; [| split; [| split; [| split]]]]]].
  - exact HA0.
  - apply identity_matrix_MatrixShape.
  - apply Nat.le_0_l.
  - apply Nat.le_0_l.
  - reflexivity.
  - symmetry. apply mat_mul_identity_l. exact HA0.
  - unfold PivotPrefix. split; [constructor | split; [constructor |]].
    intros i j Hij. destruct i; simpl in Hij; discriminate.
  - intros j Hj. lia.
Qed.

(* ------------------------------------------------------------------ *)
(* find_pivot: search rows [pivot_row, m) for a nonzero entry in       *)
(* column pivot_col, deciding zero via Qeq (not Leibniz =).            *)
(* ------------------------------------------------------------------ *)

Definition Qnonzerob (x : Q) : bool := if Qeq_dec x 0 then false else true.

Lemma Qnonzerob_true_iff : forall x, Qnonzerob x = true <-> ~ x == 0.
Proof.
  intros x. unfold Qnonzerob. destruct (Qeq_dec x 0) as [Heq | Hneq].
  - split; [discriminate | intros H; contradiction].
  - split; [intros _; exact Hneq | intros _; reflexivity].
Qed.

Definition find_pivot (W : list (list Q)) (pivot_row m pivot_col : nat) : option nat :=
  find (fun r => Qnonzerob (nth pivot_col (nth r W []) 0)) (seq pivot_row (m - pivot_row)).

Lemma find_pivot_sound : forall W pivot_row m pivot_col r, (pivot_row <= m)%nat ->
  find_pivot W pivot_row m pivot_col = Some r ->
  (pivot_row <= r < m)%nat /\ ~ (nth pivot_col (nth r W []) 0 == 0).
Proof.
  intros W pivot_row m pivot_col r Hpm Hfind. unfold find_pivot in Hfind.
  apply find_some in Hfind. destruct Hfind as [Hin Hpred].
  apply in_seq in Hin.
  assert (Heqm : (pivot_row + (m - pivot_row))%nat = m) by lia.
  rewrite Heqm in Hin.
  apply Qnonzerob_true_iff in Hpred.
  split; [exact Hin | exact Hpred].
Qed.

Lemma find_pivot_none_complete : forall W pivot_row m pivot_col, (pivot_row <= m)%nat ->
  find_pivot W pivot_row m pivot_col = None ->
  forall r, (pivot_row <= r < m)%nat -> nth pivot_col (nth r W []) 0 == 0.
Proof.
  intros W pivot_row m pivot_col Hpm Hfind r Hr. unfold find_pivot in Hfind.
  assert (Hin : In r (seq pivot_row (m - pivot_row))) by (apply in_seq; lia).
  pose proof (find_none _ _ Hfind r Hin) as Hpred.
  destruct (Qnonzerob (nth pivot_col (nth r W []) 0)) eqn:Hb; [discriminate |].
  unfold Qnonzerob in Hb. destruct (Qeq_dec (nth pivot_col (nth r W []) 0) 0) as [Heq | Hneq].
  - exact Heq.
  - discriminate.
Qed.

(* ------------------------------------------------------------------ *)
(* clear_column: eliminate column pivot_col from every row except src, *)
(* applying the same operation to work and transform simultaneously.   *)
(* ------------------------------------------------------------------ *)

Lemma nth_vscale : forall c u j, nth j (vscale c u) 0 == c * nth j u 0.
Proof.
  intros c u. induction u as [| x u' IH]; intros j; simpl.
  - destruct j; ring.
  - destruct j as [| j'].
    + reflexivity.
    + apply IH.
Qed.

Lemma nth_vadd : forall u v j, nth j (vadd u v) 0 == nth j u 0 + nth j v 0.
Proof.
  induction u as [| x u' IHu]; intros v j.
  - destruct j as [| j']; simpl; symmetry; apply Qplus_0_l.
  - destruct v as [| y v'].
    + destruct j as [| j']; simpl; symmetry; apply Qplus_0_r.
    + destruct j as [| j'].
      * simpl. reflexivity.
      * simpl. apply IHu.
Qed.

Lemma add_scaled_row_step_preserves_invariant : forall m p A0 W T dst src a,
  MatrixShape m m T -> MatrixShape m p A0 -> (dst < m)%nat -> (src < m)%nat ->
  MatEq W (mat_mul T A0 p) ->
  MatEq (add_scaled_row dst src a W) (mat_mul (add_scaled_row dst src a T) A0 p).
Proof.
  intros m p A0 W T dst src a HT HA0 Hdst Hsrc Hinv.
  assert (H1 : MatEq (add_scaled_row dst src a W) (mat_mul (mat_mul (E_add m dst src a) T m) A0 p))
    by (apply add_scaled_row_preserves_transform_invariant; assumption).
  assert (H2 : MatEq (add_scaled_row dst src a T) (mat_mul (E_add m dst src a) T m))
    by (apply add_scaled_row_elementary_semantics; assumption).
  assert (H3 : MatEq (mat_mul (add_scaled_row dst src a T) A0 p) (mat_mul (mat_mul (E_add m dst src a) T m) A0 p))
    by (apply (mat_mul_Proper p); [exact H2 | reflexivity]).
  rewrite H1, H3. reflexivity.
Qed.

Fixpoint clear_rows (rows : list nat) (src pivot_col : nat) (W T : list (list Q)) : list (list Q) * list (list Q) :=
  match rows with
  | [] => (W, T)
  | k :: rows' =>
      if Nat.eqb k src
      then clear_rows rows' src pivot_col W T
      else
        let c := nth pivot_col (nth k W []) 0 in
        clear_rows rows' src pivot_col (add_scaled_row k src (-c) W) (add_scaled_row k src (-c) T)
  end.

Definition clear_column (m src pivot_col : nat) (W T : list (list Q)) : list (list Q) * list (list Q) :=
  clear_rows (seq 0 m) src pivot_col W T.

Lemma clear_rows_MatrixShape : forall rows src pivot_col W T m n,
  MatrixShape m (S n) W -> MatrixShape m m T -> (src < m)%nat -> Forall (fun k => (k < m)%nat) rows ->
  MatrixShape m (S n) (fst (clear_rows rows src pivot_col W T)) /\ MatrixShape m m (snd (clear_rows rows src pivot_col W T)).
Proof.
  induction rows as [| k rows IH]; intros src pivot_col W T m n HW HT Hsrc Hrows.
  - simpl. split; assumption.
  - simpl. apply Forall_cons_iff in Hrows. destruct Hrows as [Hk Hrows'].
    destruct (Nat.eqb k src) eqn:Hks.
    + apply (IH src pivot_col W T m n HW HT Hsrc Hrows').
    + apply (IH src pivot_col (add_scaled_row k src (- nth pivot_col (nth k W []) 0) W)
                (add_scaled_row k src (- nth pivot_col (nth k W []) 0) T) m n);
        [apply add_scaled_row_MatrixShape; assumption | apply add_scaled_row_MatrixShape; assumption | assumption | assumption].
Qed.

Lemma clear_rows_invariant : forall rows src pivot_col W T m n A0,
  MatrixShape m (S n) W -> MatrixShape m m T -> MatrixShape m (S n) A0 -> (src < m)%nat -> Forall (fun k => (k < m)%nat) rows ->
  MatEq W (mat_mul T A0 (S n)) ->
  MatEq (fst (clear_rows rows src pivot_col W T)) (mat_mul (snd (clear_rows rows src pivot_col W T)) A0 (S n)).
Proof.
  induction rows as [| k rows IH]; intros src pivot_col W T m n A0 HW HT HA0 Hsrc Hrows Hinv.
  - simpl. exact Hinv.
  - simpl. apply Forall_cons_iff in Hrows. destruct Hrows as [Hk Hrows'].
    destruct (Nat.eqb k src) eqn:Hks.
    + apply (IH src pivot_col W T m n A0 HW HT HA0 Hsrc Hrows' Hinv).
    + apply (IH src pivot_col (add_scaled_row k src (- nth pivot_col (nth k W []) 0) W)
                (add_scaled_row k src (- nth pivot_col (nth k W []) 0) T) m n A0);
        [apply add_scaled_row_MatrixShape; assumption | apply add_scaled_row_MatrixShape; assumption
        | assumption | assumption | assumption
        | apply (add_scaled_row_step_preserves_invariant m (S n) A0 W T k src); assumption].
Qed.

(* Generalized to allow src to occur inside rows (clear_column calls
   this with rows = seq 0 m, which always contains src = pivot_row):
   whenever k0 = src, clear_rows simply skips it and recurses, so row
   src is always exactly preserved, and the "In" formula is only
   claimed for k <> src. *)
Lemma clear_rows_effect : forall rows src pivot_col W T m,
  length W = m -> (src < m)%nat -> NoDup rows -> Forall (fun k => (k < m)%nat) rows ->
  (forall k, (k < m)%nat -> ~ In k rows -> nth k (fst (clear_rows rows src pivot_col W T)) [] = nth k W []) /\
  (forall k, In k rows -> k <> src -> nth k (fst (clear_rows rows src pivot_col W T)) [] =
      vadd (nth k W []) (vscale (- nth pivot_col (nth k W []) 0) (nth src W []))) /\
  nth src (fst (clear_rows rows src pivot_col W T)) [] = nth src W [].
Proof.
  induction rows as [| k0 rows' IH]; intros src pivot_col W T m HlenW Hsrcm HND HForall.
  - split; [| split].
    + intros k Hk Hnotin. reflexivity.
    + intros k Hin Hne. destruct Hin.
    + reflexivity.
  - inversion HND as [| k0' rows'' Hk0notin HND'']; subst k0'; subst rows''.
    apply Forall_cons_iff in HForall. destruct HForall as [Hk0m HForall'].
    simpl.
    destruct (Nat.eqb k0 src) eqn:Hks.
    + apply Nat.eqb_eq in Hks.
      destruct (IH src pivot_col W T m HlenW Hsrcm HND'' HForall') as [IHnotin [IHin IHsrc]].
      split; [| split].
      * intros k Hk Hnotin.
        assert (Hk_notin' : ~ In k rows') by (intro Hin; apply Hnotin; right; exact Hin).
        apply (IHnotin k Hk Hk_notin').
      * intros k Hin Hne. destruct Hin as [Heq | Hin].
        -- exfalso. apply Hne. rewrite <- Heq. exact Hks.
        -- apply (IHin k Hin Hne).
      * exact IHsrc.
    + apply Nat.eqb_neq in Hks.
      set (c0 := nth pivot_col (nth k0 W []) 0).
      set (W' := add_scaled_row k0 src (-c0) W).
      set (T' := add_scaled_row k0 src (-c0) T).
      assert (HlenW' : length W' = m) by (unfold W'; rewrite length_add_scaled_row; exact HlenW).
      assert (Hsrc_W' : nth src W' [] = nth src W [])
        by (unfold W'; apply nth_add_scaled_row_other; [intro Heq; apply Hks; symmetry; exact Heq | rewrite HlenW; exact Hsrcm]).
      assert (Hk0_W' : nth k0 W' [] = vadd (nth k0 W []) (vscale (-c0) (nth src W [])))
        by (unfold W'; apply nth_add_scaled_row_dst; rewrite HlenW; exact Hk0m).
      destruct (IH src pivot_col W' T' m HlenW' Hsrcm HND'' HForall') as [IHnotin [IHin IHsrc]].
      split; [| split].
      * intros k Hk Hnotin.
        assert (Hk_ne_k0 : k <> k0) by (intro Heq; apply Hnotin; left; symmetry; exact Heq).
        assert (Hk_notin' : ~ In k rows') by (intro Hin; apply Hnotin; right; exact Hin).
        rewrite (IHnotin k Hk Hk_notin').
        unfold W'. apply nth_add_scaled_row_other; [exact Hk_ne_k0 | rewrite HlenW; exact Hk].
      * intros k Hin Hne. destruct Hin as [Heq | Hin].
        -- subst k. rewrite (IHnotin k0 Hk0m Hk0notin).
           rewrite Hk0_W'. reflexivity.
        -- rewrite (IHin k Hin Hne).
           rewrite Forall_forall in HForall'. assert (Hkm : (k < m)%nat) by (apply HForall'; exact Hin).
           assert (Hk_ne_k0 : k <> k0) by (intro Heq; subst k; contradiction).
           assert (Hk_W' : nth k W' [] = nth k W [])
             by (unfold W'; apply nth_add_scaled_row_other; [exact Hk_ne_k0 | rewrite HlenW; exact Hkm]).
           rewrite Hk_W', Hsrc_W'. reflexivity.
      * rewrite IHsrc. exact Hsrc_W'.
Qed.

Lemma clear_column_MatrixShape : forall m n src pivot_col W T,
  MatrixShape m (S n) W -> MatrixShape m m T -> (src < m)%nat ->
  MatrixShape m (S n) (fst (clear_column m src pivot_col W T)) /\ MatrixShape m m (snd (clear_column m src pivot_col W T)).
Proof.
  intros m n src pivot_col W T HW HT Hsrc. unfold clear_column.
  apply clear_rows_MatrixShape; [exact HW | exact HT | exact Hsrc |].
  apply Forall_forall. intros k Hk. apply in_seq in Hk. lia.
Qed.

Lemma clear_column_invariant : forall m n src pivot_col W T A0,
  MatrixShape m (S n) W -> MatrixShape m m T -> MatrixShape m (S n) A0 -> (src < m)%nat ->
  MatEq W (mat_mul T A0 (S n)) ->
  MatEq (fst (clear_column m src pivot_col W T)) (mat_mul (snd (clear_column m src pivot_col W T)) A0 (S n)).
Proof.
  intros m n src pivot_col W T A0 HW HT HA0 Hsrc Hinv. unfold clear_column.
  apply (clear_rows_invariant (seq 0 m) src pivot_col W T m n A0);
    [exact HW | exact HT | exact HA0 | exact Hsrc | | exact Hinv].
  apply Forall_forall. intros k Hk. apply in_seq in Hk. lia.
Qed.

Lemma clear_column_effect : forall m src pivot_col W T,
  length W = m -> (src < m)%nat ->
  (forall k, (k < m)%nat -> k <> src -> nth k (fst (clear_column m src pivot_col W T)) [] =
      vadd (nth k W []) (vscale (- nth pivot_col (nth k W []) 0) (nth src W []))) /\
  nth src (fst (clear_column m src pivot_col W T)) [] = nth src W [].
Proof.
  intros m src pivot_col W T HlenW Hsrc. unfold clear_column.
  assert (HNDseq : NoDup (seq 0 m)) by apply seq_NoDup.
  assert (HForallseq : Forall (fun k => (k < m)%nat) (seq 0 m))
    by (apply Forall_forall; intros k Hk; apply in_seq in Hk; lia).
  destruct (clear_rows_effect (seq 0 m) src pivot_col W T m HlenW Hsrc HNDseq HForallseq) as [_ [IHin IHsrc]].
  split.
  + intros k Hk Hne. apply IHin; [apply in_seq; lia | exact Hne].
  + exact IHsrc.
Qed.

Lemma clear_column_entry : forall m src pivot_col W T j k,
  length W = m -> (src < m)%nat -> (k < m)%nat -> k <> src ->
  nth j (nth k (fst (clear_column m src pivot_col W T)) []) 0 ==
    nth j (nth k W []) 0 - (nth pivot_col (nth k W []) 0) * nth j (nth src W []) 0.
Proof.
  intros m src pivot_col W T j k HlenW Hsrc Hk Hne.
  destruct (clear_column_effect m src pivot_col W T HlenW Hsrc) as [Heff _].
  rewrite (Heff k Hk Hne).
  rewrite nth_vadd, nth_vscale.
  ring.
Qed.

Lemma clear_column_src_entry : forall m src pivot_col W T j,
  length W = m -> (src < m)%nat ->
  nth j (nth src (fst (clear_column m src pivot_col W T)) []) 0 == nth j (nth src W []) 0.
Proof.
  intros m src pivot_col W T j HlenW Hsrc.
  destruct (clear_column_effect m src pivot_col W T HlenW Hsrc) as [_ Heff].
  rewrite Heff. reflexivity.
Qed.

Lemma clear_column_col_preserved : forall m src pivot_col W T j,
  length W = m -> (src < m)%nat -> nth j (nth src W []) 0 == 0 ->
  forall k, (k < m)%nat -> k <> src -> nth j (nth k (fst (clear_column m src pivot_col W T)) []) 0 == nth j (nth k W []) 0.
Proof.
  intros m src pivot_col W T j HlenW Hsrc Hzero k Hk Hne.
  rewrite (clear_column_entry m src pivot_col W T j k HlenW Hsrc Hk Hne).
  rewrite Hzero. ring.
Qed.

Lemma clear_column_pivot_zero : forall m src pivot_col W T,
  length W = m -> (src < m)%nat -> nth pivot_col (nth src W []) 0 == 1 ->
  forall k, (k < m)%nat -> k <> src -> nth pivot_col (nth k (fst (clear_column m src pivot_col W T)) []) 0 == 0.
Proof.
  intros m src pivot_col W T HlenW Hsrc Hone k Hk Hne.
  rewrite (clear_column_entry m src pivot_col W T pivot_col k HlenW Hsrc Hk Hne).
  rewrite Hone. ring.
Qed.

(* ------------------------------------------------------------------ *)
(* process_column: swap a nonzero pivot into place, normalise it, and *)
(* clear its column, or advance pivot_col with no changes if the      *)
(* column is entirely zero from pivot_row downward.                   *)
(* ------------------------------------------------------------------ *)

Lemma nth_swap_rows_at_i : forall i j A, (i < length A)%nat -> (j < length A)%nat -> nth i (swap_rows i j A) [] = nth j A [].
Proof.
  intros i j A Hi Hj. rewrite (nth_swap_rows i j A i Hi).
  destruct (Nat.eqb i j) eqn:Hij.
  - apply Nat.eqb_eq in Hij. rewrite Hij. reflexivity.
  - rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma nth_swap_rows_at_j : forall i j A, (i < length A)%nat -> (j < length A)%nat -> nth j (swap_rows i j A) [] = nth i A [].
Proof.
  intros i j A Hi Hj. rewrite (nth_swap_rows i j A j Hj). rewrite Nat.eqb_refl. reflexivity.
Qed.

Lemma nth_swap_rows_at_other : forall i j A k, (k < length A)%nat -> k <> i -> k <> j -> nth k (swap_rows i j A) [] = nth k A [].
Proof.
  intros i j A k Hk Hki Hkj. rewrite (nth_swap_rows i j A k Hk).
  destruct (Nat.eqb k j) eqn:Hkj'; [apply Nat.eqb_eq in Hkj'; contradiction |].
  destruct (Nat.eqb k i) eqn:Hki'; [apply Nat.eqb_eq in Hki'; contradiction |].
  reflexivity.
Qed.

Lemma PivotAt_transport_by_col_preserved : forall W W' m i j src,
  PivotAt W m i j -> (i < m)%nat -> i <> src -> (src < m)%nat ->
  (forall k, (k < m)%nat -> k <> src -> nth j (nth k W' []) 0 == nth j (nth k W []) 0) ->
  nth j (nth src W' []) 0 == nth j (nth src W []) 0 ->
  PivotAt W' m i j.
Proof.
  intros W W' m i j src [H1 H2] Him Hisrc Hsrcm Hcol Hsrceq.
  split.
  - rewrite (Hcol i Him Hisrc). exact H1.
  - intros k Hk Hki.
    destruct (Nat.eq_dec k src) as [Heq | Hne].
    + subst k. rewrite Hsrceq. apply H2; [exact Hsrcm | intro Hc; apply Hisrc; symmetry; exact Hc].
    + rewrite (Hcol k Hk Hne). apply H2; [exact Hk | exact Hki].
Qed.

(* A free (as yet unpivoted) column j that is zero throughout the
   active row range [pivot_row, m) stays zero throughout that same
   range after a swap and a scale: swap only permutes two rows that
   both already hold 0 there, and scaling a 0 entry gives 0 regardless
   of the scalar. Simpler than pivot_step_preserves_PivotAt since there
   is no distinguished row to protect -- everything in range is 0. *)
Lemma zero_col_step_preserves : forall m work j pivot_row r (piv : Q),
  length work = m -> (pivot_row <= r < m)%nat ->
  (forall k, (pivot_row <= k < m)%nat -> nth j (nth k work []) 0 == 0) ->
  let W1 := swap_rows pivot_row r work in
  let W2 := scale_row pivot_row (/ piv) W1 in
  forall k, (pivot_row <= k < m)%nat -> nth j (nth k W2 []) 0 == 0.
Proof.
  intros m work j pivot_row r piv HlenW Hr Hzero W1 W2 k Hk.
  assert (Hpm : (pivot_row < m)%nat) by lia.
  assert (Hrm : (r < m)%nat) by lia.
  assert (Hpm_len : (pivot_row < length work)%nat) by (rewrite HlenW; exact Hpm).
  assert (Hrm_len : (r < length work)%nat) by (rewrite HlenW; exact Hrm).
  assert (HlenW1 : length W1 = m) by (unfold W1; rewrite length_swap_rows; exact HlenW).
  assert (HW1_zero : nth j (nth k W1 []) 0 == 0).
  { unfold W1. destruct (Nat.eq_dec k pivot_row) as [Heq | Hne1].
    - subst k. rewrite (nth_swap_rows_at_i pivot_row r work Hpm_len Hrm_len). apply Hzero; lia.
    - destruct (Nat.eq_dec k r) as [Heq2 | Hne2].
      + subst k. rewrite (nth_swap_rows_at_j pivot_row r work Hpm_len Hrm_len). apply Hzero; lia.
      + assert (Hk_len : (k < length work)%nat) by (rewrite HlenW; lia).
        rewrite (nth_swap_rows_at_other pivot_row r work k Hk_len Hne1 Hne2). apply Hzero; lia. }
  unfold W2. destruct (Nat.eq_dec k pivot_row) as [Heq | Hne].
  - subst k. assert (Hpr_len1 : (pivot_row < length W1)%nat) by (rewrite HlenW1; exact Hpm).
    rewrite (nth_scale_row_same pivot_row (/ piv) W1 Hpr_len1). rewrite nth_vscale. rewrite HW1_zero. ring.
  - assert (Hk_len1 : (k < length W1)%nat) by (rewrite HlenW1; lia).
    rewrite (nth_scale_row_other pivot_row (/ piv) W1 k Hne Hk_len1). exact HW1_zero.
Qed.

(* Old pivot (i,j) with i strictly before pivot_row survives the swap
   and scale steps, and picks up entry 0 at pivot_row -- exactly the
   fact clear_column_col_preserved needs to carry it through clearing. *)
Lemma pivot_step_preserves_PivotAt : forall m work i j pivot_row r (piv : Q),
  length work = m -> (pivot_row <= r < m)%nat -> (i < pivot_row)%nat ->
  PivotAt work m i j ->
  let W1 := swap_rows pivot_row r work in
  let W2 := scale_row pivot_row (/ piv) W1 in
  PivotAt W2 m i j /\ nth j (nth pivot_row W2 []) 0 == 0.
Proof.
  intros m work i j pivot_row r piv HlenW Hr Hi [H1 H2] W1 W2.
  assert (Hpm : (pivot_row < m)%nat) by lia.
  assert (Hrm : (r < m)%nat) by lia.
  assert (Him : (i < m)%nat) by lia.
  assert (Hi_ne_pr : i <> pivot_row) by lia.
  assert (Hi_ne_r : i <> r) by lia.
  assert (Hpm_len : (pivot_row < length work)%nat) by (rewrite HlenW; exact Hpm).
  assert (Hrm_len : (r < length work)%nat) by (rewrite HlenW; exact Hrm).
  assert (Him_len : (i < length work)%nat) by (rewrite HlenW; exact Him).
  assert (Hi_W1 : nth j (nth i W1 []) 0 == nth j (nth i work []) 0)
    by (unfold W1; rewrite (nth_swap_rows_at_other pivot_row r work i Him_len Hi_ne_pr Hi_ne_r); reflexivity).
  assert (Hpr_W1 : nth j (nth pivot_row W1 []) 0 == nth j (nth r work []) 0)
    by (unfold W1; rewrite (nth_swap_rows_at_i pivot_row r work Hpm_len Hrm_len); reflexivity).
  assert (Hr_W1 : nth j (nth r W1 []) 0 == nth j (nth pivot_row work []) 0)
    by (unfold W1; rewrite (nth_swap_rows_at_j pivot_row r work Hpm_len Hrm_len); reflexivity).
  assert (Hpr_W1_zero : nth j (nth pivot_row W1 []) 0 == 0) by (rewrite Hpr_W1; apply H2; [exact Hrm | lia]).
  assert (Hr_W1_zero : nth j (nth r W1 []) 0 == 0) by (rewrite Hr_W1; apply H2; [exact Hpm | lia]).
  assert (HlenW1 : length W1 = m) by (unfold W1; rewrite length_swap_rows; exact HlenW).
  assert (Hall_W1_zero : forall k, (k < m)%nat -> k <> i -> nth j (nth k W1 []) 0 == 0).
  { intros k Hk Hki.
    destruct (Nat.eq_dec k pivot_row) as [Heq | Hne1]; [subst k; exact Hpr_W1_zero |].
    destruct (Nat.eq_dec k r) as [Heq2 | Hne2]; [subst k; exact Hr_W1_zero |].
    assert (Hk_len : (k < length work)%nat) by (rewrite HlenW; exact Hk).
    unfold W1. rewrite (nth_swap_rows_at_other pivot_row r work k Hk_len Hne1 Hne2).
    apply H2; [exact Hk | exact Hki]. }
  assert (Hi_len1 : (i < length W1)%nat) by (rewrite HlenW1; exact Him).
  assert (Hpr_len1 : (pivot_row < length W1)%nat) by (rewrite HlenW1; exact Hpm).
  assert (H1_W2 : nth j (nth i W2 []) 0 == 1).
  { unfold W2. rewrite (nth_scale_row_other pivot_row (/ piv) W1 i Hi_ne_pr Hi_len1).
    rewrite Hi_W1. exact H1. }
  assert (H2_W2 : forall k, (k < m)%nat -> k <> i -> nth j (nth k W2 []) 0 == 0).
  { intros k Hk Hki.
    destruct (Nat.eq_dec k pivot_row) as [Heq | Hne].
    - subst k. unfold W2. rewrite (nth_scale_row_same pivot_row (/piv) W1 Hpr_len1).
      rewrite nth_vscale. rewrite (Hall_W1_zero pivot_row Hpm (not_eq_sym Hi_ne_pr)). ring.
    - assert (Hk_len1 : (k < length W1)%nat) by (rewrite HlenW1; exact Hk).
      unfold W2. rewrite (nth_scale_row_other pivot_row (/piv) W1 k Hne Hk_len1).
      apply Hall_W1_zero; [exact Hk | exact Hki]. }
  split.
  - split; [exact H1_W2 | exact H2_W2].
  - apply H2_W2; [exact Hpm | exact (not_eq_sym Hi_ne_pr)].
Qed.

Lemma swap_rows_step_preserves_invariant : forall m p A0 W T i j,
  MatrixShape m m T -> MatrixShape m p A0 -> (i < m)%nat -> (j < m)%nat ->
  MatEq W (mat_mul T A0 p) ->
  MatEq (swap_rows i j W) (mat_mul (swap_rows i j T) A0 p).
Proof.
  intros m p A0 W T i j HT HA0 Hi Hj Hinv.
  assert (H1 : MatEq (swap_rows i j W) (mat_mul (mat_mul (E_swap m i j) T m) A0 p))
    by (apply swap_rows_preserves_transform_invariant; assumption).
  assert (H2 : MatEq (swap_rows i j T) (mat_mul (E_swap m i j) T m))
    by (apply swap_rows_elementary_semantics; assumption).
  assert (H3 : MatEq (mat_mul (swap_rows i j T) A0 p) (mat_mul (mat_mul (E_swap m i j) T m) A0 p))
    by (apply (mat_mul_Proper p); [exact H2 | reflexivity]).
  rewrite H1, H3. reflexivity.
Qed.

Lemma scale_row_step_preserves_invariant : forall m p A0 W T i a,
  MatrixShape m m T -> MatrixShape m p A0 -> (i < m)%nat ->
  MatEq W (mat_mul T A0 p) ->
  MatEq (scale_row i a W) (mat_mul (scale_row i a T) A0 p).
Proof.
  intros m p A0 W T i a HT HA0 Hi Hinv.
  assert (H1 : MatEq (scale_row i a W) (mat_mul (mat_mul (E_scale m i a) T m) A0 p))
    by (apply scale_row_preserves_transform_invariant; assumption).
  assert (H2 : MatEq (scale_row i a T) (mat_mul (E_scale m i a) T m))
    by (apply scale_row_elementary_semantics; assumption).
  assert (H3 : MatEq (mat_mul (scale_row i a T) A0 p) (mat_mul (mat_mul (E_scale m i a) T m) A0 p))
    by (apply (mat_mul_Proper p); [exact H2 | reflexivity]).
  rewrite H1, H3. reflexivity.
Qed.

Lemma PivotPrefix_widen : forall W m pivot_col cols, PivotPrefix W m pivot_col cols -> PivotPrefix W m (S pivot_col) cols.
Proof.
  intros W m pivot_col cols [H1 [H2 H3]].
  split; [exact H1 | split; [| exact H3]].
  apply Forall_impl with (P := fun j => (j < pivot_col)%nat); [intros a Ha; lia | exact H2].
Qed.

Definition process_column (m n : nat) (s : ElimState) : ElimState :=
  match find_pivot (st_work s) (st_pivot_row s) m (st_pivot_col s) with
  | None => mkElimState (st_work s) (st_transform s) (st_pivot_row s) (S (st_pivot_col s)) (st_pivot_cols s)
  | Some r =>
      let piv := nth (st_pivot_col s) (nth r (st_work s) []) 0 in
      let W1 := swap_rows (st_pivot_row s) r (st_work s) in
      let T1 := swap_rows (st_pivot_row s) r (st_transform s) in
      let W2 := scale_row (st_pivot_row s) (/ piv) W1 in
      let T2 := scale_row (st_pivot_row s) (/ piv) T1 in
      mkElimState (fst (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2))
                  (snd (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2))
                  (S (st_pivot_row s)) (S (st_pivot_col s)) (st_pivot_cols s ++ [st_pivot_col s])
  end.

Theorem process_column_preserves_invariant : forall m n A0 s,
  MatrixShape m (S n) A0 -> ElimInvariant m n A0 s -> (st_pivot_col s < n)%nat -> ElimInvariant m n A0 (process_column m n s).
Proof.
  intros m n A0 s HA0 HInv Hpcn.
  destruct HInv as [HW [HT [Hpr [Hpc [Hlen [Hinv [[Hsort [Hbound Hpivots]] Hfree]]]]]]].
  unfold process_column.
  destruct (find_pivot (st_work s) (st_pivot_row s) m (st_pivot_col s)) eqn:Hfp.
  - destruct (find_pivot_sound (st_work s) (st_pivot_row s) m (st_pivot_col s) n0 Hpr Hfp) as [[Hr1 Hr2] Hnz].
    set (r := n0) in *.
    set (piv := nth (st_pivot_col s) (nth r (st_work s) []) 0).
    assert (Hpiv_nz : ~ piv == 0) by exact Hnz.
    set (W1 := swap_rows (st_pivot_row s) r (st_work s)).
    set (T1 := swap_rows (st_pivot_row s) r (st_transform s)).
    set (W2 := scale_row (st_pivot_row s) (/ piv) W1).
    set (T2 := scale_row (st_pivot_row s) (/ piv) T1).
    assert (Hprm : (st_pivot_row s < m)%nat) by lia.
    assert (HW1 : MatrixShape m (S n) W1) by (unfold W1; apply swap_rows_MatrixShape; [exact HW | exact Hprm | exact Hr2]).
    assert (HT1 : MatrixShape m m T1) by (unfold T1; apply swap_rows_MatrixShape; [exact HT | exact Hprm | exact Hr2]).
    assert (HW2 : MatrixShape m (S n) W2) by (unfold W2; apply scale_row_MatrixShape; [exact HW1 | exact Hprm]).
    assert (HT2 : MatrixShape m m T2) by (unfold T2; apply scale_row_MatrixShape; [exact HT1 | exact Hprm]).
    assert (HW3 : MatrixShape m (S n) (fst (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2)))
      by (apply (clear_column_MatrixShape m n (st_pivot_row s) (st_pivot_col s) W2 T2 HW2 HT2 Hprm)).
    assert (HT3 : MatrixShape m m (snd (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2)))
      by (apply (clear_column_MatrixShape m n (st_pivot_row s) (st_pivot_col s) W2 T2 HW2 HT2 Hprm)).
    assert (Hinv1 : MatEq W1 (mat_mul T1 A0 (S n))).
    { unfold W1, T1. apply (swap_rows_step_preserves_invariant m (S n) A0 (st_work s) (st_transform s));
        [exact HT | exact HA0 | exact Hprm | exact Hr2 | exact Hinv]. }
    assert (Hinv2 : MatEq W2 (mat_mul T2 A0 (S n))).
    { unfold W2, T2. apply (scale_row_step_preserves_invariant m (S n) A0 W1 T1);
        [exact HT1 | exact HA0 | exact Hprm | exact Hinv1]. }
    assert (Hinv3 : MatEq (fst (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2))
                           (mat_mul (snd (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2)) A0 (S n)))
      by (apply (clear_column_invariant m n (st_pivot_row s) (st_pivot_col s) W2 T2 A0 HW2 HT2 HA0 Hprm Hinv2)).
    assert (HlenW : length (st_work s) = m) by (destruct HW as [HlenW _]; exact HlenW).
    assert (HlenW1 : length W1 = m) by (unfold W1; rewrite length_swap_rows; exact HlenW).
    assert (Hpiv_eq : nth (st_pivot_col s) (nth (st_pivot_row s) W1 []) 0 == piv).
    { unfold W1, piv. rewrite (nth_swap_rows_at_i (st_pivot_row s) r (st_work s));
        [reflexivity | rewrite HlenW; exact Hprm | rewrite HlenW; exact Hr2]. }
    assert (Hprm_len1 : (st_pivot_row s < length W1)%nat) by (rewrite HlenW1; exact Hprm).
    assert (H1_new : nth (st_pivot_col s) (nth (st_pivot_row s) W2 []) 0 == 1).
    { unfold W2. rewrite (nth_scale_row_same (st_pivot_row s) (/ piv) W1 Hprm_len1).
      rewrite nth_vscale. rewrite Hpiv_eq.
      rewrite Qmult_comm. apply Qmult_inv_r. exact Hpiv_nz. }
    split; [| split; [| split; [| split; [| split; [| split; [| split]]]]]];
      cbn [st_work st_transform st_pivot_row st_pivot_col st_pivot_cols].
    + exact HW3.
    + exact HT3.
    + lia.
    + lia.
    + rewrite app_length. simpl. lia.
    + exact Hinv3.
    + split.
      * apply StronglySorted_snoc; [exact Hsort | rewrite Forall_forall in Hbound |- *; intros x Hx; apply Hbound; exact Hx].
      * split.
        -- apply Forall_app. split.
           ++ apply Forall_impl with (P := fun j => (j < st_pivot_col s)%nat); [intros a Ha; lia | exact Hbound].
           ++ constructor; [lia | constructor].
        -- intros i j Hij.
           destruct (Nat.lt_ge_cases i (length (st_pivot_cols s))) as [Hilt | Hige].
           ++ rewrite (nth_error_app1 (st_pivot_cols s) [st_pivot_col s] Hilt) in Hij.
              assert (Hi_pr : (i < st_pivot_row s)%nat) by (rewrite <- Hlen; exact Hilt).
              destruct (Hpivots i j Hij) as [Hp1 Hp2].
              assert (HPS : PivotAt W2 m i j /\ nth j (nth (st_pivot_row s) W2 []) 0 == 0)
                by (apply (pivot_step_preserves_PivotAt m (st_work s) i j (st_pivot_row s) r piv HlenW (conj Hr1 Hr2) Hi_pr (conj Hp1 Hp2))).
              destruct HPS as [HPAt2 Hzero2].
              apply (PivotAt_transport_by_col_preserved W2 (fst (clear_column m (st_pivot_row s) (st_pivot_col s) W2 T2)) m i j (st_pivot_row s)).
              ** exact HPAt2.
              ** lia.
              ** lia.
              ** exact Hprm.
              ** intros k Hk Hne. apply clear_column_col_preserved; try assumption.
                 destruct HW2 as [HlenW2 _]. exact HlenW2.
              ** apply clear_column_src_entry. destruct HW2 as [HlenW2 _]. exact HlenW2. exact Hprm.
           ++ assert (Hieq : i = length (st_pivot_cols s))
                by (rewrite (nth_error_app2 (st_pivot_cols s) [st_pivot_col s] Hige) in Hij;
                    destruct (i - length (st_pivot_cols s))%nat as [| k] eqn:Hk;
                    [lia | destruct k; simpl in Hij; discriminate Hij]).
              assert (Hjeq : j = st_pivot_col s).
              { rewrite (nth_error_app2 (st_pivot_cols s) [st_pivot_col s] Hige) in Hij.
                rewrite Hieq, Nat.sub_diag in Hij. simpl in Hij. injection Hij as Hij. symmetry. exact Hij. }
              rewrite Hieq, Hjeq, Hlen.
              split.
              ** assert (HlenW2 : length W2 = m) by (destruct HW2 as [HlenW2 _]; exact HlenW2).
                 rewrite (clear_column_src_entry m (st_pivot_row s) (st_pivot_col s) W2 T2 (st_pivot_col s) HlenW2 Hprm).
                 exact H1_new.
              ** intros k Hk Hne.
                 apply clear_column_pivot_zero; try assumption.
                 destruct HW2 as [HlenW2 _]; exact HlenW2.
    + intros j Hj Hnotin k Hk.
      assert (Hjne : j <> st_pivot_col s) by (intro Hc; apply Hnotin; apply in_or_app; right; subst j; left; reflexivity).
      assert (Hj' : (j < st_pivot_col s)%nat) by lia.
      assert (Hnotin' : ~ In j (st_pivot_cols s)) by (intro Hc; apply Hnotin; apply in_or_app; left; exact Hc).
      assert (HzeroW2 : forall k', (st_pivot_row s <= k' < m)%nat -> nth j (nth k' W2 []) 0 == 0).
      { apply (zero_col_step_preserves m (st_work s) j (st_pivot_row s) r piv HlenW (conj Hr1 Hr2)).
        apply (Hfree j Hj' Hnotin'). }
      assert (HlenW2 : length W2 = m) by (destruct HW2 as [HlenW2 _]; exact HlenW2).
      assert (Hpr_zero : nth j (nth (st_pivot_row s) W2 []) 0 == 0) by (apply HzeroW2; lia).
      assert (Hkm : (k < m)%nat) by lia.
      assert (Hkne : k <> st_pivot_row s) by lia.
      rewrite (clear_column_col_preserved m (st_pivot_row s) (st_pivot_col s) W2 T2 j HlenW2 Hprm Hpr_zero k Hkm Hkne).
      apply HzeroW2. lia.
  - split; [| split; [| split; [| split; [| split; [| split; [| split]]]]]];
      cbn [st_work st_transform st_pivot_row st_pivot_col st_pivot_cols].
    + exact HW.
    + exact HT.
    + exact Hpr.
    + lia.
    + exact Hlen.
    + exact Hinv.
    + apply PivotPrefix_widen. exact (conj Hsort (conj Hbound Hpivots)).
    + intros j Hj Hnotin k Hk.
      destruct (Nat.eq_dec j (st_pivot_col s)) as [Heq | Hne].
      * subst j. apply (find_pivot_none_complete (st_work s) (st_pivot_row s) m (st_pivot_col s) Hpr Hfp k Hk).
      * apply Hfree; [lia | exact Hnotin | exact Hk].
Qed.

Theorem process_column_advances : forall m n s, st_pivot_col (process_column m n s) = S (st_pivot_col s).
Proof.
  intros m n s. unfold process_column.
  destruct (find_pivot (st_work s) (st_pivot_row s) m (st_pivot_col s)); reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* eliminate: the fuel-based outer loop. Each call to process_column   *)
(* strictly advances pivot_col (process_column_advances), so fuel = n  *)
(* is always sufficient to reach pivot_col = n.                        *)
(* ------------------------------------------------------------------ *)

Fixpoint eliminate (fuel m n : nat) (s : ElimState) : ElimState :=
  match fuel with
  | O => s
  | S fuel' =>
      if Nat.leb n (st_pivot_col s) then s
      else eliminate fuel' m n (process_column m n s)
  end.

Theorem eliminate_preserves_invariant : forall fuel m n A0 s,
  MatrixShape m (S n) A0 -> ElimInvariant m n A0 s -> ElimInvariant m n A0 (eliminate fuel m n s).
Proof.
  induction fuel as [| fuel' IH]; intros m n A0 s HA0 HInv.
  - simpl. exact HInv.
  - simpl. destruct (Nat.leb n (st_pivot_col s)) eqn:Hle.
    + exact HInv.
    + apply Nat.leb_gt in Hle.
      apply (IH m n A0 (process_column m n s) HA0).
      apply process_column_preserves_invariant; assumption.
Qed.

Theorem eliminate_reaches_final_column : forall fuel m n s,
  (n <= st_pivot_col s + fuel)%nat -> (n <= st_pivot_col (eliminate fuel m n s))%nat.
Proof.
  induction fuel as [| fuel' IH]; intros m n s Hfuel.
  - simpl. rewrite Nat.add_0_r in Hfuel. exact Hfuel.
  - simpl. destruct (Nat.leb n (st_pivot_col s)) eqn:Hle.
    + apply Nat.leb_le in Hle. exact Hle.
    + apply Nat.leb_gt in Hle.
      apply IH.
      rewrite (process_column_advances m n s).
      lia.
Qed.

(* ------------------------------------------------------------------ *)
(* Final invariant checkpoint: at pivot_col = n, every row not yet     *)
(* claimed as a pivot row has all n coefficient entries zero. Combines *)
(* PivotAt (for pivot columns) with FreeColumnsZeroBelow (for free     *)
(* columns) -- exactly the reason the invariant needed strengthening.  *)
(* ------------------------------------------------------------------ *)

Definition zero_vec (n : nat) : list Q := repeat 0 n.

Definition CoefficientsZero (n : nat) (row : list Q) : Prop :=
  VecEq (firstn n row) (zero_vec n).

Lemma nth_firstn_eq : forall (l : list Q) (n j : nat), (j < n)%nat -> nth j (firstn n l) 0 = nth j l 0.
Proof.
  induction l as [| x l IH]; intros n j Hj.
  - destruct n as [| n]; [lia |]. simpl. destruct j; reflexivity.
  - destruct n as [| n]; [lia |].
    simpl. destruct j as [| j].
    + reflexivity.
    + apply IH. lia.
Qed.

Lemma length_firstn_le : forall (l : list Q) (n : nat), (n <= length l)%nat -> length (firstn n l) = n.
Proof. intros l n Hn. rewrite firstn_length. lia. Qed.

Lemma CoefficientsZero_of_forall_zero : forall n row,
  (n <= length row)%nat -> (forall j, (j < n)%nat -> nth j row 0 == 0) -> CoefficientsZero n row.
Proof.
  intros n row Hlen Hall. unfold CoefficientsZero, zero_vec.
  apply (Forall2_from_nth Qeq 0 (firstn n row) (repeat 0 n)).
  - rewrite (length_firstn_le row n Hlen), repeat_length. reflexivity.
  - intros j Hj. rewrite (length_firstn_le row n Hlen) in Hj.
    rewrite (nth_firstn_eq row n j Hj).
    rewrite (nth_repeat_eq 0 n j Hj).
    apply Hall. exact Hj.
Qed.

Theorem final_nonpivot_row_coefficients_zero : forall m n A0 s k,
  ElimInvariant m n A0 s -> st_pivot_col s = n -> (st_pivot_row s <= k < m)%nat ->
  CoefficientsZero n (nth k (st_work s) []).
Proof.
  intros m n A0 s k HInv Hpc Hk.
  destruct HInv as [HW [HT [Hpr [Hpcle [Hlen [Hinv [[Hsort [Hbound Hpivots]] Hfree]]]]]]].
  assert (Hklen : (n <= length (nth k (st_work s) []))%nat).
  { destruct HW as [HlenW HrowsW]. rewrite Forall_forall in HrowsW.
    assert (Hknth : length (nth k (st_work s) []) = S n).
    { apply HrowsW, nth_In. rewrite HlenW. lia. }
    lia. }
  apply CoefficientsZero_of_forall_zero; [exact Hklen |].
  intros j Hj.
  destruct (in_dec Nat.eq_dec j (st_pivot_cols s)) as [Hin | Hnin].
  - apply In_nth_error in Hin. destruct Hin as [i Hi].
    destruct (Hpivots i j Hi) as [Hp1 Hp2].
    apply Hp2; [lia |].
    assert (Hilt : (i < length (st_pivot_cols s))%nat) by (apply nth_error_Some; rewrite Hi; discriminate).
    rewrite Hlen in Hilt. lia.
  - apply Hfree; [rewrite Hpc; exact Hj | exact Hnin | exact Hk].
Qed.

(* ------------------------------------------------------------------ *)
(* Bridge from the augmented system back to D and r separately.       *)
(* ------------------------------------------------------------------ *)

Definition augment_rhs (D : list (list Q)) (r : list Q) : list (list Q) :=
  map (fun k => nth k D [] ++ [nth k r 0]) (seq 0 (length D)).

Lemma length_augment_rhs : forall D r, length (augment_rhs D r) = length D.
Proof. intros. unfold augment_rhs. rewrite map_length, seq_length. reflexivity. Qed.

Lemma nth_augment_rhs : forall D r k, (k < length D)%nat -> nth k (augment_rhs D r) [] = nth k D [] ++ [nth k r 0].
Proof.
  intros D r k Hk. unfold augment_rhs.
  rewrite (nth_indep _ [] (nth k D [] ++ [nth k r 0])).
  - rewrite (map_nth (fun j => nth j D [] ++ [nth j r 0]) (seq 0 (length D)) k k).
    rewrite seq_nth by exact Hk. reflexivity.
  - rewrite map_length, seq_length. exact Hk.
Qed.

Lemma transpose_augment_rhs : forall D r n m,
  MatrixShape m n D -> length r = m ->
  MatEq (transpose (augment_rhs D r) (S n)) (transpose D n ++ [r]).
Proof.
  intros D r n m [HlenD HrowsD] Hlenr.
  apply (Forall2_from_nth VecEq (@nil Q) (transpose (augment_rhs D r) (S n)) (transpose D n ++ [r])).
  - rewrite length_transpose, app_length, length_transpose. simpl. lia.
  - intros j Hj. rewrite length_transpose in Hj.
    rewrite (nth_transpose (augment_rhs D r) (S n) j Hj).
    destruct (Nat.lt_ge_cases j n) as [Hjn | Hjn].
    + assert (Hlt : (j < length (transpose D n))%nat) by (rewrite length_transpose; exact Hjn).
      rewrite (app_nth1 (transpose D n) [r] [] Hlt).
      rewrite (nth_transpose D n j Hjn).
      apply (Forall2_from_nth Qeq 0 (map (fun row => nth j row 0) (augment_rhs D r)) (map (fun row => nth j row 0) D)).
      * rewrite !map_length, length_augment_rhs, HlenD. reflexivity.
      * intros k Hk0. rewrite map_length in Hk0.
        assert (Hk' : (k < length D)%nat) by (rewrite <- (length_augment_rhs D r); exact Hk0).
        rewrite (my_nth_map (list Q) Q (fun row => nth j row 0) (augment_rhs D r) k [] 0 Hk0).
        rewrite (my_nth_map (list Q) Q (fun row => nth j row 0) D k [] 0 Hk').
        rewrite (nth_augment_rhs D r k Hk').
        rewrite Forall_forall in HrowsD.
        assert (HlenDk : length (nth k D []) = n) by (apply HrowsD, nth_In, Hk').
        assert (Hjlt : (j < length (nth k D []))%nat) by (rewrite HlenDk; exact Hjn).
        rewrite (app_nth1 (nth k D []) [nth k r 0] 0 Hjlt). reflexivity.
    + assert (Hge : (length (transpose D n) <= j)%nat) by (rewrite length_transpose; exact Hjn).
      rewrite (app_nth2 (transpose D n) [r] [] Hge).
      rewrite length_transpose.
      assert (Hjeqn : j = n) by lia.
      subst j.
      rewrite Nat.sub_diag. simpl.
      apply (Forall2_from_nth Qeq 0 (map (fun row => nth n row 0) (augment_rhs D r)) r).
      * rewrite map_length, length_augment_rhs, HlenD, Hlenr. reflexivity.
      * intros k Hk0. rewrite map_length in Hk0.
        assert (Hk' : (k < length D)%nat) by (rewrite <- (length_augment_rhs D r); exact Hk0).
        rewrite (my_nth_map (list Q) Q (fun row => nth n row 0) (augment_rhs D r) k [] 0 Hk0).
        rewrite (nth_augment_rhs D r k Hk').
        rewrite Forall_forall in HrowsD.
        assert (HlenDk : length (nth k D []) = n) by (apply HrowsD, nth_In, Hk').
        assert (Hge2 : (length (nth k D []) <= n)%nat) by lia.
        rewrite (app_nth2 (nth k D []) [nth k r 0] 0 Hge2).
        rewrite HlenDk, Nat.sub_diag. simpl. reflexivity.
Qed.

Theorem row_vec_mat_augmented : forall D r n m y,
  MatrixShape m n D -> length r = m ->
  VecEq (row_vec_mat y (augment_rhs D r) (S n)) (row_vec_mat y D n ++ [dot y r]).
Proof.
  intros D r n m y HD Hlenr.
  unfold row_vec_mat.
  assert (Ht : MatEq (transpose (augment_rhs D r) (S n)) (transpose D n ++ [r]))
    by (apply (transpose_augment_rhs D r n m HD Hlenr)).
  assert (Hmap : VecEq (map (fun col => dot y col) (transpose (augment_rhs D r) (S n)))
                        (map (fun col => dot y col) (transpose D n ++ [r]))).
  { unfold MatEq in Ht.
    induction Ht as [| c1 c2 M1 M2 Hc HM IH]; constructor.
    - rewrite Hc. reflexivity.
    - exact IH. }
  rewrite Hmap.
  rewrite map_app. simpl. reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* Inconsistent-row detection: a row whose n coefficient entries are   *)
(* all zero but whose right-hand-side entry is not.                   *)
(* ------------------------------------------------------------------ *)

Definition InconsistentRow (n : nat) (row : list Q) : Prop :=
  CoefficientsZero n row /\ ~ nth n row 0 == 0.

Definition all_zerob (l : list Q) : bool := forallb (fun x => Qeq_bool x 0) l.

Lemma all_zerob_true_iff : forall l, all_zerob l = true <-> Forall (fun x => x == 0) l.
Proof.
  intros l. unfold all_zerob. rewrite forallb_forall.
  split.
  - intros H. apply Forall_forall. intros x Hx. apply Qeq_bool_eq. apply H. exact Hx.
  - intros H x Hx. apply Qeq_eq_bool. rewrite Forall_forall in H. apply H. exact Hx.
Qed.

Definition find_inconsistent_row (n : nat) (W : list (list Q)) : option nat :=
  find (fun k => andb (all_zerob (firstn n (nth k W []))) (Qnonzerob (nth n (nth k W []) 0)))
       (seq 0 (length W)).

Lemma CoefficientsZero_iff_all_zerob : forall n row, (n <= length row)%nat ->
  (CoefficientsZero n row <-> all_zerob (firstn n row) = true).
Proof.
  intros n row Hlen. rewrite all_zerob_true_iff. unfold CoefficientsZero, zero_vec.
  split.
  - intros H. apply Forall_forall. intros x Hx.
    apply In_nth with (d := 0) in Hx. destruct Hx as [j [Hj Hnth]].
    rewrite (length_firstn_le row n Hlen) in Hj.
    assert (Heq : nth j (firstn n row) 0 == nth j (repeat 0 n) 0) by (apply nth_VecEq; exact H).
    rewrite (nth_repeat_eq 0 n j Hj) in Heq. rewrite <- Hnth. exact Heq.
  - intros H. apply (Forall2_from_nth Qeq 0 (firstn n row) (repeat 0 n)).
    + rewrite (length_firstn_le row n Hlen), repeat_length. reflexivity.
    + intros j Hj. rewrite (length_firstn_le row n Hlen) in Hj.
      rewrite (nth_repeat_eq 0 n j Hj).
      rewrite Forall_forall in H. apply H, nth_In. rewrite (length_firstn_le row n Hlen). exact Hj.
Qed.

Lemma find_inconsistent_row_sound : forall n W k,
  find_inconsistent_row n W = Some k ->
  (k < length W)%nat /\ all_zerob (firstn n (nth k W [])) = true /\ ~ nth n (nth k W []) 0 == 0.
Proof.
  intros n W k Hfind. unfold find_inconsistent_row in Hfind.
  apply find_some in Hfind. destruct Hfind as [Hin Hpred].
  apply in_seq in Hin.
  apply andb_true_iff in Hpred. destruct Hpred as [Hz Hnz].
  apply Qnonzerob_true_iff in Hnz.
  split; [lia | split; [exact Hz | exact Hnz]].
Qed.

Lemma find_inconsistent_row_none_complete : forall n W,
  find_inconsistent_row n W = None ->
  forall k, (k < length W)%nat -> all_zerob (firstn n (nth k W [])) = false \/ nth n (nth k W []) 0 == 0.
Proof.
  intros n W Hfind k Hk. unfold find_inconsistent_row in Hfind.
  assert (Hin : In k (seq 0 (length W))) by (apply in_seq; lia).
  pose proof (find_none _ _ Hfind k Hin) as Hpred.
  destruct (all_zerob (firstn n (nth k W []))) eqn:Hz.
  - right. destruct (Qnonzerob (nth n (nth k W []) 0)) eqn:Hnz.
    + simpl in Hpred. rewrite Hz, Hnz in Hpred. discriminate.
    + unfold Qnonzerob in Hnz. destruct (Qeq_dec (nth n (nth k W []) 0) 0) as [Heq | Hneq].
      * exact Heq.
      * discriminate.
  - left. reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* Separator extraction from an inconsistent row.                      *)
(* ------------------------------------------------------------------ *)

Lemma vscale_zero : forall c n, VecEq (vscale c (zero_vec n)) (zero_vec n).
Proof.
  intros c n. unfold zero_vec.
  apply (Forall2_from_nth Qeq 0 (vscale c (repeat 0 n)) (repeat 0 n)).
  - rewrite length_vscale, !repeat_length. reflexivity.
  - intros j Hj. rewrite length_vscale, repeat_length in Hj.
    rewrite nth_vscale, (nth_repeat_eq 0 n j Hj). ring.
Qed.

Theorem extract_separator : forall m n D r s k,
  MatrixShape m n D -> length r = m ->
  ElimInvariant m n (augment_rhs D r) s ->
  find_inconsistent_row n (st_work s) = Some k ->
  VecEq (row_vec_mat (nth k (st_transform s) (zero_vec m)) D n) (zero_vec n) /\
  dot (nth k (st_transform s) (zero_vec m)) r == nth n (nth k (st_work s) []) 0 /\
  ~ nth n (nth k (st_work s) []) 0 == 0.
Proof.
  intros m n D r s k HD Hlenr HInv Hfind.
  destruct HInv as [HW [HT [Hpr [Hpc [Hlen [Hinv _]]]]]].
  destruct (find_inconsistent_row_sound n (st_work s) k Hfind) as [Hk [Hz Hnz]].
  destruct HW as [HlenW HrowsW].
  set (y0 := nth k (st_transform s) (zero_vec m)).
  assert (Hkm : (k < m)%nat) by (rewrite <- HlenW; exact Hk).
  assert (HrowEq : VecEq (nth k (st_work s) []) (nth k (mat_mul (st_transform s) (augment_rhs D r) (S n)) [])).
  { apply (MatEq_nth_row (st_work s) (mat_mul (st_transform s) (augment_rhs D r) (S n)) Hinv). }
  destruct HT as [HlenT _].
  assert (Hkt : (k < length (st_transform s))%nat) by (rewrite HlenT; exact Hkm).
  assert (Hnthmm : nth k (mat_mul (st_transform s) (augment_rhs D r) (S n)) [] = row_vec_mat (nth k (st_transform s) []) (augment_rhs D r) (S n))
    by (apply (nth_mat_mul (st_transform s) (augment_rhs D r) (S n) k Hkt)).
  assert (Hy0eq : nth k (st_transform s) [] = y0).
  { unfold y0. apply nth_indep. rewrite HlenT. exact Hkm. }
  rewrite Hy0eq in Hnthmm.
  assert (Haug : VecEq (row_vec_mat y0 (augment_rhs D r) (S n)) (row_vec_mat y0 D n ++ [dot y0 r]))
    by (apply (row_vec_mat_augmented D r n m y0 HD Hlenr)).
  assert (Hfull : VecEq (nth k (st_work s) []) (row_vec_mat y0 D n ++ [dot y0 r])).
  { rewrite HrowEq, Hnthmm, Haug. reflexivity. }
  assert (Hlen_rvm : length (row_vec_mat y0 D n) = n) by (apply length_row_vec_mat).
  split; [| split].
  - apply (Forall2_from_nth Qeq 0 (row_vec_mat y0 D n) (zero_vec n)).
    + unfold zero_vec. rewrite Hlen_rvm, repeat_length. reflexivity.
    + intros j Hj. rewrite Hlen_rvm in Hj.
      assert (Hpt : nth j (nth k (st_work s) []) 0 == nth j (row_vec_mat y0 D n ++ [dot y0 r]) 0)
        by (apply nth_VecEq; exact Hfull).
      assert (Hjlt : (j < length (row_vec_mat y0 D n))%nat) by (rewrite Hlen_rvm; exact Hj).
      rewrite (app_nth1 (row_vec_mat y0 D n) [dot y0 r] 0 Hjlt) in Hpt.
      rewrite <- Hpt.
      assert (Hzc : CoefficientsZero n (nth k (st_work s) [])).
      { apply (CoefficientsZero_iff_all_zerob n (nth k (st_work s) [])); [| exact Hz].
        rewrite Forall_forall in HrowsW.
        assert (HlenWk : length (nth k (st_work s) []) = S n) by (apply HrowsW, nth_In; exact Hk).
        lia. }
      unfold CoefficientsZero in Hzc.
      assert (Hjn : (j < n)%nat) by exact Hj.
      assert (Hpt2 : nth j (firstn n (nth k (st_work s) [])) 0 == nth j (zero_vec n) 0)
        by (apply nth_VecEq; exact Hzc).
      rewrite (nth_firstn_eq (nth k (st_work s) []) n j Hjn) in Hpt2.
      exact Hpt2.
  - assert (Hpt : nth n (nth k (st_work s) []) 0 == nth n (row_vec_mat y0 D n ++ [dot y0 r]) 0)
      by (apply nth_VecEq; exact Hfull).
    assert (Hge : (length (row_vec_mat y0 D n) <= n)%nat) by lia.
    rewrite (app_nth2 (row_vec_mat y0 D n) [dot y0 r] 0 Hge) in Hpt.
    rewrite Hlen_rvm, Nat.sub_diag in Hpt. simpl in Hpt.
    symmetry. exact Hpt.
  - exact Hnz.
Qed.

Corollary extract_separator_normalized : forall m n D r s k,
  MatrixShape m n D -> length r = m ->
  ElimInvariant m n (augment_rhs D r) s ->
  find_inconsistent_row n (st_work s) = Some k ->
  let c := nth n (nth k (st_work s) []) 0 in
  let y := vscale (/ c) (nth k (st_transform s) (zero_vec m)) in
  VecEq (row_vec_mat y D n) (zero_vec n) /\ dot y r == 1.
Proof.
  intros m n D r s k HD Hlenr HInv Hfind c y.
  destruct (extract_separator m n D r s k HD Hlenr HInv Hfind) as [Hzero [Hdc Hnz]].
  split.
  - unfold y. rewrite (row_vec_mat_vscale (/ c) (nth k (st_transform s) (zero_vec m)) D n).
    rewrite Hzero. apply vscale_zero.
  - unfold y. rewrite dot_vscale_l. rewrite Hdc. fold c.
    rewrite Qmult_comm. apply Qmult_inv_r. exact Hnz.
Qed.

(* ------------------------------------------------------------------ *)
(* Solution-set equivalence: each elementary row operation preserves   *)
(* the set of b satisfying the augmented system [D|r], independent of *)
(* the transformation matrix. This is the primal counterpart to the   *)
(* dual transformation invariant used for separator extraction.       *)
(* ------------------------------------------------------------------ *)

Definition SolvesAug (n : nat) (W : list (list Q)) (b : list Q) : Prop :=
  forall i, (i < length W)%nat -> dot (firstn n (nth i W [])) b == nth n (nth i W []) 0.

Lemma firstn_app_exact : forall (l : list Q) (x : Q) (n : nat), length l = n -> firstn n (l ++ [x]) = l.
Proof.
  intros l x n Hlen. rewrite firstn_app, Hlen, Nat.sub_diag, firstn_O, app_nil_r.
  rewrite <- Hlen. apply firstn_all.
Qed.

Lemma SolvesAug_augment_rhs : forall m n D r b,
  MatrixShape m n D -> length r = m ->
  (SolvesAug n (augment_rhs D r) b <-> VecEq (mat_vec D b) r).
Proof.
  intros m n D r b [HlenD HrowsD] Hlenr.
  unfold SolvesAug, mat_vec. rewrite Forall_forall in HrowsD.
  split.
  - intros H. apply (Forall2_from_nth Qeq 0 (map (fun row => dot row b) D) r).
    + rewrite map_length, HlenD, Hlenr. reflexivity.
    + intros i Hi0. rewrite map_length in Hi0.
      assert (Hi_aug : (i < length (augment_rhs D r))%nat) by (rewrite length_augment_rhs; exact Hi0).
      pose proof (H i Hi_aug) as Hrow.
      rewrite (nth_augment_rhs D r i Hi0) in Hrow.
      assert (HlenDi : length (nth i D []) = n) by (apply HrowsD, nth_In, Hi0).
      rewrite (firstn_app_exact (nth i D []) (nth i r 0) n HlenDi) in Hrow.
      assert (Hge : (length (nth i D []) <= n)%nat) by lia.
      rewrite (app_nth2 (nth i D []) [nth i r 0] 0 Hge) in Hrow.
      rewrite HlenDi, Nat.sub_diag in Hrow. simpl in Hrow.
      rewrite (my_nth_map (list Q) Q (fun row => dot row b) D i [] 0 Hi0).
      exact Hrow.
  - intros H i Hi. rewrite length_augment_rhs in Hi.
    rewrite (nth_augment_rhs D r i Hi).
    assert (HlenDi : length (nth i D []) = n) by (apply HrowsD, nth_In; exact Hi).
    rewrite (firstn_app_exact (nth i D []) (nth i r 0) n HlenDi).
    assert (Hge : (length (nth i D []) <= n)%nat) by lia.
    rewrite (app_nth2 (nth i D []) [nth i r 0] 0 Hge).
    rewrite HlenDi, Nat.sub_diag. simpl.
    assert (Hpt : nth i (map (fun row => dot row b) D) 0 == nth i r 0) by (apply nth_VecEq; exact H).
    rewrite (my_nth_map (list Q) Q (fun row => dot row b) D i [] 0 Hi) in Hpt.
    exact Hpt.
Qed.

Lemma firstn_vscale : forall (row : list Q) (a : Q) (n : nat), firstn n (vscale a row) = vscale a (firstn n row).
Proof.
  induction row as [| x row IH]; intros a n; destruct n; simpl; try reflexivity.
  f_equal. apply IH.
Qed.

Lemma firstn_vadd : forall (u v : list Q) (n : nat), firstn n (vadd u v) = vadd (firstn n u) (firstn n v).
Proof.
  induction u as [| x u' IHu]; intros v n.
  - destruct n; reflexivity.
  - destruct n as [| n'].
    + reflexivity.
    + destruct v as [| y v']; simpl; f_equal; apply IHu.
Qed.

Lemma swap_rows_solves_iff : forall n W b i j,
  (i < length W)%nat -> (j < length W)%nat ->
  (SolvesAug n W b <-> SolvesAug n (swap_rows i j W) b).
Proof.
  intros n W b i j Hi Hj.
  assert (Hfwd : forall W', (i < length W')%nat -> (j < length W')%nat ->
                 SolvesAug n W' b -> SolvesAug n (swap_rows i j W') b).
  { intros W' Hi' Hj' H k Hk.
    rewrite length_swap_rows in Hk.
    rewrite (nth_swap_rows i j W' k Hk).
    destruct (Nat.eqb k j) eqn:Hkj.
    - apply H; exact Hi'.
    - destruct (Nat.eqb k i) eqn:Hki.
      + apply H; exact Hj'.
      + apply H; exact Hk. }
  split.
  - apply Hfwd; assumption.
  - intros H.
    assert (Hii : (i < length (swap_rows i j W))%nat) by (rewrite length_swap_rows; exact Hi).
    assert (Hjj : (j < length (swap_rows i j W))%nat) by (rewrite length_swap_rows; exact Hj).
    pose proof (Hfwd (swap_rows i j W) Hii Hjj H) as H2.
    assert (Heq : swap_rows i j (swap_rows i j W) = W).
    { apply nth_ext with (d := @nil Q) (d' := @nil Q).
      - rewrite !length_swap_rows. reflexivity.
      - intros k Hk0. rewrite length_swap_rows in Hk0.
        assert (Hk : (k < length W)%nat) by (rewrite <- length_swap_rows with (i := i) (j := j); exact Hk0).
        rewrite (nth_swap_rows i j (swap_rows i j W) k Hk0).
        destruct (Nat.eqb k j) eqn:Hkj.
        + apply Nat.eqb_eq in Hkj. subst k. apply (nth_swap_rows_at_i i j W Hi Hj).
        + destruct (Nat.eqb k i) eqn:Hki.
          * apply Nat.eqb_eq in Hki. subst k. apply (nth_swap_rows_at_j i j W Hi Hj).
          * apply Nat.eqb_neq in Hkj. apply Nat.eqb_neq in Hki.
            apply (nth_swap_rows_at_other i j W k Hk Hki Hkj). }
    rewrite Heq in H2. exact H2.
Qed.

Lemma scale_row_solves_iff : forall n W b i a,
  (i < length W)%nat -> ~ a == 0 ->
  (SolvesAug n W b <-> SolvesAug n (scale_row i a W) b).
Proof.
  intros n W b i a Hi Ha.
  split.
  - intros H k Hk. rewrite length_scale_row in Hk.
    destruct (Nat.eq_dec k i) as [Heq | Hne].
    + subst k. rewrite (nth_scale_row_same i a W Hi).
      rewrite firstn_vscale, dot_vscale_l, nth_vscale.
      rewrite (H i Hi). reflexivity.
    + rewrite (nth_scale_row_other i a W k Hne Hk). apply H; exact Hk.
  - intros H k Hk.
    destruct (Nat.eq_dec k i) as [Heq | Hne].
    + subst k.
      assert (Hii : (i < length (scale_row i a W))%nat) by (rewrite length_scale_row; exact Hi).
      pose proof (H i Hii) as Hrow.
      rewrite (nth_scale_row_same i a W Hi) in Hrow.
      rewrite firstn_vscale, dot_vscale_l, nth_vscale in Hrow.
      apply (Qmult_inj_l (dot (firstn n (nth i W [])) b) (nth n (nth i W []) 0) a Ha).
      exact Hrow.
    + assert (Hkk : (k < length (scale_row i a W))%nat) by (rewrite length_scale_row; exact Hk).
      pose proof (H k Hkk) as Hrow.
      rewrite (nth_scale_row_other i a W k Hne Hk) in Hrow. exact Hrow.
Qed.

Lemma firstn_VecEq : forall u v n, VecEq u v -> VecEq (firstn n u) (firstn n v).
Proof.
  induction u as [| x u' IH]; intros v n Huv.
  - inversion Huv as [| ]; subst. destruct n; simpl; constructor.
  - destruct v as [| y v']; [inversion Huv |].
    inversion Huv as [| x' y' u'' v'' Hxy Huv' Heq1 Heq2]; subst.
    destruct n as [| n']; simpl; [constructor |].
    constructor; [exact Hxy | apply IH; exact Huv'].
Qed.

Lemma SolvesAug_MatEq : forall n W1 W2 b, MatEq W1 W2 -> SolvesAug n W1 b -> SolvesAug n W2 b.
Proof.
  intros n W1 W2 b HM H k Hk.
  assert (Hk1 : (k < length W1)%nat) by (rewrite (Forall2_length HM); exact Hk).
  pose proof (H k Hk1) as Hrow.
  assert (Hroweq : VecEq (nth k W1 []) (nth k W2 [])) by (apply MatEq_nth_row; exact HM).
  assert (Hfirsteq : VecEq (firstn n (nth k W1 [])) (firstn n (nth k W2 []))) by (apply firstn_VecEq; exact Hroweq).
  rewrite <- (dot_Proper _ _ Hfirsteq b b (VecEq_Equivalence.(Equivalence_Reflexive) b)).
  rewrite <- (nth_VecEq _ _ Hroweq n).
  exact Hrow.
Qed.

Lemma add_scaled_row_solves_forward : forall m n W b dst src a,
  MatrixShape m (S n) W -> (dst < m)%nat -> (src < m)%nat ->
  SolvesAug n W b -> SolvesAug n (add_scaled_row dst src a W) b.
Proof.
  intros m n W b dst src a [HlenW HrowsW] Hdst Hsrc H k Hk.
  rewrite length_add_scaled_row in Hk.
  assert (Hdstlen : (dst < length W)%nat) by (rewrite HlenW; exact Hdst).
  assert (Hsrclen : (src < length W)%nat) by (rewrite HlenW; exact Hsrc).
  destruct (Nat.eq_dec k dst) as [Heq | Hkne].
  - subst k. rewrite (nth_add_scaled_row_dst dst src a W Hdstlen).
    rewrite Forall_forall in HrowsW.
    assert (HlenDst : length (nth dst W []) = S n) by (apply HrowsW, nth_In, Hdstlen).
    assert (HlenSrc : length (nth src W []) = S n) by (apply HrowsW, nth_In, Hsrclen).
    rewrite firstn_vadd, firstn_vscale.
    rewrite dot_vadd_l by (rewrite !firstn_length, length_vscale, !firstn_length, HlenDst, HlenSrc; reflexivity).
    rewrite dot_vscale_l, nth_vadd, nth_vscale.
    rewrite (H dst Hdstlen), (H src Hsrclen). reflexivity.
  - rewrite (nth_add_scaled_row_other dst src a W k Hkne Hk). apply H; exact Hk.
Qed.

Lemma add_scaled_row_solves_iff : forall m n W b dst src a,
  MatrixShape m (S n) W -> (dst < m)%nat -> (src < m)%nat -> dst <> src ->
  (SolvesAug n W b <-> SolvesAug n (add_scaled_row dst src a W) b).
Proof.
  intros m n W b dst src a HW Hdst Hsrc Hne.
  split.
  - apply (add_scaled_row_solves_forward m n W b dst src a HW Hdst Hsrc).
  - intros H.
    assert (HW2 : MatrixShape m (S n) (add_scaled_row dst src a W))
      by (apply add_scaled_row_MatrixShape; assumption).
    pose proof (add_scaled_row_solves_forward m n (add_scaled_row dst src a W) b dst src (- a) HW2 Hdst Hsrc H) as H2.
    assert (Hdstlen : (dst < length W)%nat) by (destruct HW as [HlenW _]; rewrite HlenW; exact Hdst).
    assert (Hsrclen : (src < length W)%nat) by (destruct HW as [HlenW _]; rewrite HlenW; exact Hsrc).
    assert (Heq : MatEq (add_scaled_row dst src (- a) (add_scaled_row dst src a W)) W).
    { apply (Forall2_from_nth VecEq (@nil Q)).
      - rewrite !length_add_scaled_row. reflexivity.
      - intros k Hk. rewrite length_add_scaled_row in Hk.
        destruct (Nat.eq_dec k dst) as [Heqk | Hkne].
        + subst k.
          assert (Hdst3 : (dst < length (add_scaled_row dst src a W))%nat) by (rewrite length_add_scaled_row; exact Hdstlen).
          rewrite (nth_add_scaled_row_dst dst src (- a) (add_scaled_row dst src a W) Hdst3).
          rewrite (nth_add_scaled_row_dst dst src a W Hdstlen).
          rewrite (nth_add_scaled_row_other dst src a W src (Nat.neq_sym _ _ Hne) Hsrclen).
          destruct HW as [HlenWm HrowsWm]. rewrite Forall_forall in HrowsWm.
          assert (HlenDstRow : length (nth dst W []) = S n) by (apply HrowsWm, nth_In, Hdstlen).
          assert (HlenSrcRow : length (nth src W []) = S n) by (apply HrowsWm, nth_In, Hsrclen).
          assert (HlenScA : length (vscale a (nth src W [])) = S n) by (rewrite length_vscale; exact HlenSrcRow).
          assert (HlenScNegA : length (vscale (- a) (nth src W [])) = S n) by (rewrite length_vscale; exact HlenSrcRow).
          assert (HlenInner : length (vadd (nth dst W []) (vscale a (nth src W []))) = S n)
            by (rewrite (length_vadd (nth dst W []) (vscale a (nth src W [])) (eq_trans HlenDstRow (eq_sym HlenScA))); exact HlenDstRow).
          apply (Forall2_from_nth Qeq 0).
          * rewrite (length_vadd (vadd (nth dst W []) (vscale a (nth src W []))) (vscale (- a) (nth src W []))
                       (eq_trans HlenInner (eq_sym HlenScNegA))).
            rewrite HlenInner, HlenDstRow. reflexivity.
          * intros j Hj.
            rewrite (nth_vadd (vadd (nth dst W []) (vscale a (nth src W []))) (vscale (- a) (nth src W [])) j).
            rewrite (nth_vadd (nth dst W []) (vscale a (nth src W [])) j).
            rewrite (nth_vscale (- a) (nth src W []) j), (nth_vscale a (nth src W []) j).
            ring.
        + assert (Hklen : (k < length W)%nat) by (rewrite length_add_scaled_row in Hk; exact Hk).
          rewrite (nth_add_scaled_row_other dst src (- a) (add_scaled_row dst src a W) k Hkne Hk).
          rewrite (nth_add_scaled_row_other dst src a W k Hkne Hklen). reflexivity. }
    apply (SolvesAug_MatEq n (add_scaled_row dst src (- a) (add_scaled_row dst src a W)) W b Heq).
    exact H2.
Qed.

(* ------------------------------------------------------------------ *)
(* Thread SolvesAug equivalence through the whole elimination trace.  *)
(* ------------------------------------------------------------------ *)

Lemma clear_rows_solves_iff : forall m n rows W T b src pivot_col,
  MatrixShape m (S n) W -> (src < m)%nat -> Forall (fun k => (k < m)%nat) rows ->
  (SolvesAug n W b <-> SolvesAug n (fst (clear_rows rows src pivot_col W T)) b).
Proof.
  induction rows as [| k0 rows' IH]; intros W T b src pivot_col HW Hsrc Hrows.
  - simpl. reflexivity.
  - simpl. apply Forall_cons_iff in Hrows. destruct Hrows as [Hk0 Hrows'].
    destruct (Nat.eqb k0 src) eqn:Hks.
    + apply (IH W T b src pivot_col HW Hsrc Hrows').
    + assert (Hk0src : k0 <> src) by (apply Nat.eqb_neq; exact Hks).
      assert (HW' : MatrixShape m (S n) (add_scaled_row k0 src (- nth pivot_col (nth k0 W []) 0) W))
        by (apply add_scaled_row_MatrixShape; assumption).
      rewrite (add_scaled_row_solves_iff m n W b k0 src (- nth pivot_col (nth k0 W []) 0) HW Hk0 Hsrc Hk0src).
      apply (IH (add_scaled_row k0 src (- nth pivot_col (nth k0 W []) 0) W)
                (add_scaled_row k0 src (- nth pivot_col (nth k0 W []) 0) T) b src pivot_col HW' Hsrc Hrows').
Qed.

Lemma clear_column_solves_iff : forall m n W T b src pivot_col,
  MatrixShape m (S n) W -> (src < m)%nat ->
  (SolvesAug n W b <-> SolvesAug n (fst (clear_column m src pivot_col W T)) b).
Proof.
  intros m n W T b src pivot_col HW Hsrc. unfold clear_column.
  apply (clear_rows_solves_iff m n (seq 0 m) W T b src pivot_col HW Hsrc).
  apply Forall_forall. intros k Hk. apply in_seq in Hk. lia.
Qed.

Lemma Qinv_nonzero : forall x : Q, ~ x == 0 -> ~ / x == 0.
Proof.
  intros x Hx Hinv.
  apply Hx.
  assert (H1 : x * / x == 1) by (apply Qmult_inv_r; exact Hx).
  rewrite Hinv in H1. rewrite Qmult_0_r in H1.
  unfold Qeq in H1. simpl in H1. discriminate H1.
Qed.

Theorem process_column_solves_iff : forall m n W T b s,
  st_work s = W -> st_transform s = T ->
  MatrixShape m (S n) W -> (st_pivot_row s <= m)%nat ->
  (SolvesAug n W b <-> SolvesAug n (st_work (process_column m n s)) b).
Proof.
  intros m n W T b s HeqW HeqT HW Hpr.
  unfold process_column.
  destruct (find_pivot (st_work s) (st_pivot_row s) m (st_pivot_col s)) eqn:Hfp.
  - destruct (find_pivot_sound (st_work s) (st_pivot_row s) m (st_pivot_col s) n0 Hpr Hfp) as [[Hr1 Hr2] Hnz].
    assert (Hprlt : (st_pivot_row s < m)%nat) by lia.
    assert (HlenW : length (st_work s) = m) by (destruct HW as [HlenW _]; rewrite HeqW; exact HlenW).
    assert (Hprlt_len : (st_pivot_row s < length (st_work s))%nat) by (rewrite HlenW; exact Hprlt).
    assert (Hr2_len : (n0 < length (st_work s))%nat) by (rewrite HlenW; exact Hr2).
    simpl.
    rewrite <- HeqW.
    assert (HW1 : MatrixShape m (S n) (swap_rows (st_pivot_row s) n0 (st_work s)))
      by (apply swap_rows_MatrixShape; [rewrite HeqW; exact HW | exact Hprlt | exact Hr2]).
    rewrite (swap_rows_solves_iff n (st_work s) b (st_pivot_row s) n0 Hprlt_len Hr2_len).
    assert (HlenW1 : length (swap_rows (st_pivot_row s) n0 (st_work s)) = m)
      by (destruct HW1 as [HlenW1 _]; exact HlenW1).
    assert (Hprlt_len1 : (st_pivot_row s < length (swap_rows (st_pivot_row s) n0 (st_work s)))%nat) by (rewrite HlenW1; exact Hprlt).
    assert (HW2 : MatrixShape m (S n) (scale_row (st_pivot_row s) (/ nth (st_pivot_col s) (nth n0 (st_work s) []) 0) (swap_rows (st_pivot_row s) n0 (st_work s))))
      by (apply scale_row_MatrixShape; [exact HW1 | exact Hprlt]).
    rewrite (scale_row_solves_iff n (swap_rows (st_pivot_row s) n0 (st_work s)) b (st_pivot_row s)
               (/ nth (st_pivot_col s) (nth n0 (st_work s) []) 0) Hprlt_len1 (Qinv_nonzero _ Hnz)).
    apply (clear_column_solves_iff m n
             (scale_row (st_pivot_row s) (/ nth (st_pivot_col s) (nth n0 (st_work s) []) 0) (swap_rows (st_pivot_row s) n0 (st_work s)))
             (scale_row (st_pivot_row s) (/ nth (st_pivot_col s) (nth n0 (st_work s) []) 0) (swap_rows (st_pivot_row s) n0 (st_transform s)))
             b (st_pivot_row s) (st_pivot_col s) HW2 Hprlt).
  - simpl. rewrite HeqW. reflexivity.
Qed.

Theorem eliminate_solves_iff : forall fuel m n A0 s b,
  MatrixShape m (S n) A0 -> ElimInvariant m n A0 s ->
  (SolvesAug n (st_work s) b <-> SolvesAug n (st_work (eliminate fuel m n s)) b).
Proof.
  induction fuel as [| fuel' IH]; intros m n A0 s b HA0 HInv.
  - simpl. reflexivity.
  - simpl. destruct (Nat.leb n (st_pivot_col s)) eqn:Hle.
    + reflexivity.
    + apply Nat.leb_gt in Hle.
      pose proof HInv as HInv'.
      destruct HInv as [HW [HT [Hpr [Hpc [Hlen [Hinv [HPP Hfree]]]]]]].
      rewrite (process_column_solves_iff m n (st_work s) (st_transform s) b s eq_refl eq_refl HW Hpr).
      apply (IH m n A0 (process_column m n s) b HA0).
      apply process_column_preserves_invariant; [exact HA0 | exact HInv' | exact Hle].
Qed.

(* ------------------------------------------------------------------ *)
(* Repair construction: assign each pivot column its row's right-hand *)
(* side, leaving free columns at zero. Scalar analogue of replace_nth *)
(* (which is typed for matrix rows), needed here for the vector b.    *)
(* ------------------------------------------------------------------ *)

Definition replace_nth_q (i : nat) (x : Q) (v : list Q) : list Q :=
  map (fun j => if Nat.eqb j i then x else nth j v 0) (seq 0 (length v)).

Lemma length_replace_nth_q : forall i x v, length (replace_nth_q i x v) = length v.
Proof. intros i x v. unfold replace_nth_q. rewrite map_length, seq_length. reflexivity. Qed.

Lemma nth_replace_nth_q : forall i x v j, (j < length v)%nat ->
  nth j (replace_nth_q i x v) 0 = if Nat.eqb j i then x else nth j v 0.
Proof.
  intros i x v j Hj. unfold replace_nth_q.
  rewrite (nth_indep _ 0 (if Nat.eqb j i then x else nth j v 0)).
  - rewrite (map_nth (fun k => if Nat.eqb k i then x else nth k v 0) (seq 0 (length v)) j j).
    rewrite seq_nth by exact Hj. reflexivity.
  - rewrite map_length, seq_length. exact Hj.
Qed.

Fixpoint assign_pivots (n row_index : nat) (cols : list nat) (W : list (list Q)) (b : list Q) : list Q :=
  match cols with
  | [] => b
  | j :: cols' => assign_pivots n (S row_index) cols' W (replace_nth_q j (nth n (nth row_index W []) 0) b)
  end.

Definition construct_repair (n : nat) (s : ElimState) : list Q :=
  assign_pivots n 0 (st_pivot_cols s) (st_work s) (zero_vec n).

Lemma length_assign_pivots : forall n row_index cols W b, length (assign_pivots n row_index cols W b) = length b.
Proof.
  intros n row_index cols. revert row_index.
  induction cols as [| c0 cols' IH]; intros row_index W b; simpl.
  - reflexivity.
  - rewrite (IH (S row_index) W (replace_nth_q c0 (nth n (nth row_index W []) 0) b)).
    apply length_replace_nth_q.
Qed.

Lemma assign_pivots_other : forall n row_index cols W b j,
  (j < length b)%nat -> ~ In j cols -> nth j (assign_pivots n row_index cols W b) 0 = nth j b 0.
Proof.
  intros n row_index cols. revert row_index.
  induction cols as [| c0 cols' IH]; intros row_index W b j Hjb Hnin; simpl.
  - reflexivity.
  - assert (Hjc0 : j <> c0) by (intro Hc; apply Hnin; left; symmetry; exact Hc).
    assert (Hnin' : ~ In j cols') by (intro Hc; apply Hnin; right; exact Hc).
    assert (Hjb' : (j < length (replace_nth_q c0 (nth n (nth row_index W []) 0%Q) b))%nat)
      by (rewrite length_replace_nth_q; exact Hjb).
    rewrite (IH (S row_index) W (replace_nth_q c0 (nth n (nth row_index W []) 0) b) j Hjb' Hnin').
    rewrite (nth_replace_nth_q c0 (nth n (nth row_index W []) 0) b j Hjb).
    destruct (Nat.eqb j c0) eqn:Hjc0'; [apply Nat.eqb_eq in Hjc0'; contradiction | reflexivity].
Qed.

Lemma assign_pivots_at : forall n row_index cols W b i j,
  NoDup cols -> nth_error cols i = Some j -> (j < length b)%nat ->
  nth j (assign_pivots n row_index cols W b) 0 == nth n (nth (row_index + i) W []) 0.
Proof.
  intros n row_index cols. revert row_index.
  induction cols as [| c0 cols' IH]; intros row_index W b i j HND Hi Hjb.
  - destruct i; simpl in Hi; discriminate.
  - inversion HND as [| c0' cols'' Hc0notin HND'']; subst c0'; subst cols''.
    destruct i as [| i'].
    + simpl in Hi. injection Hi as Hi. subst j. simpl.
      assert (Hc0b : (c0 < length b)%nat) by exact Hjb.
      assert (Hnin' : ~ In c0 cols') by exact Hc0notin.
      assert (Hc0b' : (c0 < length (replace_nth_q c0 (nth n (nth row_index W []) 0%Q) b))%nat)
        by (rewrite length_replace_nth_q; exact Hc0b).
      rewrite (assign_pivots_other n (S row_index) cols' W (replace_nth_q c0 (nth n (nth row_index W []) 0) b) c0 Hc0b' Hnin').
      rewrite (nth_replace_nth_q c0 (nth n (nth row_index W []) 0) b c0 Hc0b).
      rewrite Nat.eqb_refl. rewrite Nat.add_0_r. reflexivity.
    + simpl in Hi. simpl.
      assert (Hjb' : (j < length (replace_nth_q c0 (nth n (nth row_index W []) 0%Q) b))%nat)
        by (rewrite length_replace_nth_q; exact Hjb).
      rewrite (IH (S row_index) W (replace_nth_q c0 (nth n (nth row_index W []) 0) b) i' j HND'' Hi Hjb').
      rewrite Nat.add_succ_r, <- Nat.add_succ_l. reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* dot reduces to a single surviving term when every other product    *)
(* vanishes -- the key combinatorial fact repair-row satisfaction      *)
(* rests on (all pivot/free-column contributions except one cancel).  *)
(* ------------------------------------------------------------------ *)

Lemma fold_right_Qplus_zero : forall l, (forall j, (j < length l)%nat -> nth j l 0 == 0) -> fold_right Qplus 0 l == 0.
Proof.
  induction l as [| x l IH]; intros H.
  - reflexivity.
  - simpl.
    assert (Hx : x == 0) by (apply (H 0%nat); simpl; lia).
    assert (Hrest : fold_right Qplus 0 l == 0)
      by (apply IH; intros j Hj; apply (H (S j)); simpl; lia).
    rewrite Hx, Hrest. ring.
Qed.

Lemma fold_right_Qplus_single : forall (l : list Q) (j0 : nat) (x : Q),
  (j0 < length l)%nat -> nth j0 l 0 == x -> (forall j, (j < length l)%nat -> j <> j0 -> nth j l 0 == 0) ->
  fold_right Qplus 0 l == x.
Proof.
  induction l as [| y l IH]; intros j0 x Hj0 Hx Hz.
  - simpl in Hj0. lia.
  - destruct j0 as [| j0'].
    + simpl in Hx. simpl.
      assert (Hrest : fold_right Qplus 0 l == 0)
        by (apply fold_right_Qplus_zero; intros j Hj; apply (Hz (S j)); simpl; lia).
      rewrite Hx, Hrest. ring.
    + simpl in Hj0. assert (Hj0' : (j0' < length l)%nat) by lia.
      simpl in Hx.
      assert (Hy0 : y == 0) by (apply (Hz 0%nat); simpl; lia).
      simpl. rewrite Hy0.
      rewrite (IH j0' x Hj0' Hx); [ring |].
      intros j Hj Hjne. apply (Hz (S j)); simpl; lia.
Qed.

Lemma dot_single_term : forall u v n j0,
  length u = n -> length v = n -> (j0 < n)%nat ->
  (forall j, (j < n)%nat -> j <> j0 -> nth j u 0 * nth j v 0 == 0) ->
  dot u v == nth j0 u 0 * nth j0 v 0.
Proof.
  intros u v n j0 Hu Hv Hj0 Hz.
  unfold dot.
  apply (fold_right_Qplus_single (map (fun p => fst p * snd p) (combine u v)) j0 (nth j0 u 0 * nth j0 v 0)).
  - rewrite map_length, combine_length, Hu, Hv, Nat.min_id. exact Hj0.
  - assert (Hlen_comb : (j0 < length (combine u v))%nat) by (rewrite combine_length, Hu, Hv, Nat.min_id; exact Hj0).
    rewrite (my_nth_map (Q * Q) Q (fun p => fst p * snd p) (combine u v) j0 (0, 0) 0 Hlen_comb).
    rewrite (combine_nth u v j0 0 0 (eq_trans Hu (eq_sym Hv))).
    simpl. reflexivity.
  - intros j Hj Hjne.
    rewrite map_length, combine_length, Hu, Hv, Nat.min_id in Hj.
    assert (Hlen_comb : (j < length (combine u v))%nat) by (rewrite combine_length, Hu, Hv, Nat.min_id; exact Hj).
    rewrite (my_nth_map (Q * Q) Q (fun p => fst p * snd p) (combine u v) j (0, 0) 0 Hlen_comb).
    rewrite (combine_nth u v j 0 0 (eq_trans Hu (eq_sym Hv))).
    simpl. apply Hz; [exact Hj | exact Hjne].
Qed.

(* ------------------------------------------------------------------ *)
(* The constructed repair satisfies every row of the final work       *)
(* matrix: pivot rows via the single-surviving-term argument, nonpivot *)
(* rows via final_nonpivot_row_coefficients_zero + no inconsistency.   *)
(* ------------------------------------------------------------------ *)

Lemma StronglySorted_NoDup : forall l, StronglySorted Nat.lt l -> NoDup l.
Proof.
  induction l as [| x l IH]; intros H.
  - constructor.
  - inversion H as [| x' l' Hss Hall]; subst.
    constructor.
    + intro Hin. rewrite Forall_forall in Hall. specialize (Hall x Hin). lia.
    + apply IH. exact Hss.
Qed.

Theorem construct_repair_solves : forall m n A0 s,
  ElimInvariant m n A0 s -> st_pivot_col s = n -> find_inconsistent_row n (st_work s) = None ->
  SolvesAug n (st_work s) (construct_repair n s).
Proof.
  intros m n A0 s HInv Hpc Hfindnone.
  pose proof HInv as HInv0.
  destruct HInv as [HW [HT [Hpr [Hpcle [Hlen [Hinv [[Hsort [Hbound Hpivots]] Hfree]]]]]]].
  set (b := construct_repair n s).
  intros k Hk.
  destruct HW as [HlenW HrowsW]. rewrite Forall_forall in HrowsW.
  assert (HrowSn : length (nth k (st_work s) []) = S n) by (apply HrowsW, nth_In; exact Hk).
  assert (Hfirstn_len : length (firstn n (nth k (st_work s) [])) = n) by (apply length_firstn_le; lia).
  assert (Hblen : length b = n) by (unfold b, construct_repair; rewrite length_assign_pivots; apply repeat_length).
  assert (Hkm : (k < m)%nat) by (rewrite <- HlenW; exact Hk).
  destruct (Nat.lt_ge_cases k (st_pivot_row s)) as [Hklt | Hkge].
  - (* pivot row *)
    assert (Hk_pc : (k < length (st_pivot_cols s))%nat) by (rewrite Hlen; exact Hklt).
    set (jk := nth k (st_pivot_cols s) 0%nat).
    assert (Hjk_err : nth_error (st_pivot_cols s) k = Some jk) by (apply (nth_error_nth' (st_pivot_cols s) 0%nat Hk_pc)).
    destruct (Hpivots k jk Hjk_err) as [HPAt1 HPAt2].
    assert (Hjk_bound : (jk < st_pivot_col s)%nat) by (rewrite Forall_forall in Hbound; apply Hbound, nth_In, Hk_pc).
    assert (Hjkn : (jk < n)%nat) by (rewrite <- Hpc; exact Hjk_bound).
    assert (Hb_jk : nth jk b 0 == nth n (nth (0 + k) (st_work s) []) 0)
      by (apply (assign_pivots_at n 0 (st_pivot_cols s) (st_work s) (zero_vec n) k jk (StronglySorted_NoDup _ Hsort) Hjk_err);
          unfold zero_vec; rewrite repeat_length; exact Hjkn).
    rewrite Nat.add_0_l in Hb_jk.
    assert (Hsingle : dot (firstn n (nth k (st_work s) [])) b == nth jk (firstn n (nth k (st_work s) [])) 0 * nth jk b 0).
    { apply (dot_single_term (firstn n (nth k (st_work s) [])) b n jk Hfirstn_len Hblen Hjkn).
      intros j Hjn Hjne.
      destruct (in_dec Nat.eq_dec j (st_pivot_cols s)) as [Hin | Hnin].
      - apply In_nth_error in Hin. destruct Hin as [k' Hk'].
        destruct (Hpivots k' j Hk') as [HPAt1' HPAt2'].
        assert (Hk'k : k' <> k).
        { intro Heq. subst k'. rewrite Hjk_err in Hk'. injection Hk' as Hk'. apply Hjne. symmetry. exact Hk'. }
        assert (Hentry0 : nth j (nth k (st_work s) []) 0 == 0) by (apply HPAt2'; [exact Hkm | exact (not_eq_sym Hk'k)]).
        rewrite (nth_firstn_eq (nth k (st_work s) []) n j Hjn).
        rewrite Hentry0. ring.
      - assert (Hb_j0 : nth j b 0 = nth j (zero_vec n) 0)
          by (apply (assign_pivots_other n 0 (st_pivot_cols s) (st_work s) (zero_vec n) j);
              [unfold zero_vec; rewrite repeat_length; exact Hjn | exact Hnin]).
        unfold zero_vec in Hb_j0. rewrite (nth_repeat_eq 0 n j Hjn) in Hb_j0.
        rewrite Hb_j0. ring. }
    rewrite Hsingle.
    rewrite (nth_firstn_eq (nth k (st_work s) []) n jk Hjkn).
    rewrite HPAt1, Hb_jk. ring.
  - (* nonpivot row *)
    assert (HCZ : CoefficientsZero n (nth k (st_work s) [])) by (apply (final_nonpivot_row_coefficients_zero m n A0 s k HInv0 Hpc); lia).
    unfold CoefficientsZero, zero_vec in HCZ.
    assert (Hdot0 : dot (firstn n (nth k (st_work s) [])) b == 0).
    { rewrite (dot_Proper _ _ HCZ b b (VecEq_Equivalence.(Equivalence_Reflexive) b)). apply dot_zero_l. }
    rewrite Hdot0.
    assert (Hzerob : all_zerob (firstn n (nth k (st_work s) [])) = true)
      by (apply (CoefficientsZero_iff_all_zerob n (nth k (st_work s) [])); [lia | unfold CoefficientsZero; exact HCZ]).
    destruct (find_inconsistent_row_none_complete n (st_work s) Hfindnone k Hk) as [Hcontra | Hrhs0].
    + rewrite Hzerob in Hcontra. discriminate.
    + symmetry. exact Hrhs0.
Qed.

(* ------------------------------------------------------------------ *)
(* Final assembly: the constructed repair solves the ORIGINAL system  *)
(* D b = r, not just the reduced work matrix -- closing the gap via   *)
(* solution-set equivalence threaded through the whole elimination run.*)
(* ------------------------------------------------------------------ *)

Lemma augment_rhs_MatrixShape : forall m n D r, MatrixShape m n D -> length r = m -> MatrixShape m (S n) (augment_rhs D r).
Proof.
  intros m n D r [HlenD HrowsD] Hlenr.
  split.
  - rewrite length_augment_rhs. exact HlenD.
  - apply Forall_forall. intros row Hrow.
    apply In_nth with (d := @nil Q) in Hrow. destruct Hrow as [k [Hk Hnth]].
    rewrite length_augment_rhs in Hk.
    rewrite (nth_augment_rhs D r k Hk) in Hnth.
    rewrite <- Hnth, app_length. simpl.
    rewrite Forall_forall in HrowsD.
    assert (HlenDk : length (nth k D []) = n) by (apply HrowsD, nth_In, Hk).
    lia.
Qed.

Theorem repair_correct : forall m n D r fuel,
  MatrixShape m n D -> length r = m ->
  let sf := eliminate fuel m n (initial_state m (augment_rhs D r)) in
  st_pivot_col sf = n -> find_inconsistent_row n (st_work sf) = None ->
  VecEq (mat_vec D (construct_repair n sf)) r.
Proof.
  intros m n D r fuel HD Hlenr sf Hpcf Hfindf.
  assert (HA0 : MatrixShape m (S n) (augment_rhs D r)) by (apply augment_rhs_MatrixShape; assumption).
  assert (HInv0 : ElimInvariant m n (augment_rhs D r) (initial_state m (augment_rhs D r)))
    by (apply initial_state_invariant; exact HA0).
  assert (HInvf : ElimInvariant m n (augment_rhs D r) sf)
    by (apply eliminate_preserves_invariant; assumption).
  set (b := construct_repair n sf).
  assert (Hsolvesf : SolvesAug n (st_work sf) b) by (apply (construct_repair_solves m n (augment_rhs D r) sf HInvf Hpcf Hfindf)).
  assert (Hiff : SolvesAug n (st_work (initial_state m (augment_rhs D r))) b <-> SolvesAug n (st_work sf) b)
    by (apply (eliminate_solves_iff fuel m n (augment_rhs D r) (initial_state m (augment_rhs D r)) b HA0 HInv0)).
  assert (Hsolves0 : SolvesAug n (st_work (initial_state m (augment_rhs D r))) b) by (apply Hiff; exact Hsolvesf).
  unfold initial_state in Hsolves0. simpl in Hsolves0.
  apply (SolvesAug_augment_rhs m n D r b HD Hlenr). exact Hsolves0.
Qed.

(* ------------------------------------------------------------------ *)
(* Packaging: raw executable result, its correctness theorem, and the *)
(* evidence-bearing public interface.                                 *)
(* ------------------------------------------------------------------ *)

Lemma dot_comm : forall u v, dot u v == dot v u.
Proof.
  induction u as [| x u' IH]; intros v; destruct v as [| y v'].
  - reflexivity.
  - unfold dot. simpl. reflexivity.
  - unfold dot. simpl. reflexivity.
  - rewrite dot_cons, dot_cons. rewrite (IH v'). ring.
Qed.

Lemma row_vec_mat_eq_mat_vec_transpose : forall y D n, VecEq (row_vec_mat y D n) (mat_vec (transpose D n) y).
Proof.
  intros y D n. unfold row_vec_mat, mat_vec.
  apply (Forall2_from_nth Qeq 0).
  - rewrite !map_length. reflexivity.
  - intros j Hj. rewrite map_length in Hj.
    rewrite (my_nth_map (list Q) Q (fun col => dot y col) (transpose D n) j [] 0 Hj).
    rewrite (my_nth_map (list Q) Q (fun row => dot row y) (transpose D n) j [] 0 Hj).
    apply dot_comm.
Qed.

Inductive RawRepairOrSeparator : Type :=
| RawRepair : list Q -> RawRepairOrSeparator
| RawSeparator : list Q -> RawRepairOrSeparator.

Definition extract_separator_vector (m n : nat) (s : ElimState) (k : nat) : list Q :=
  vscale (/ nth n (nth k (st_work s) []) 0) (nth k (st_transform s) (zero_vec m)).

Definition compute_repair_or_separator (m n : nat) (D : list (list Q)) (r : list Q) : RawRepairOrSeparator :=
  let A0 := augment_rhs D r in
  let final := eliminate n m n (initial_state m A0) in
  match find_inconsistent_row n (st_work final) with
  | Some k => RawSeparator (extract_separator_vector m n final k)
  | None => RawRepair (construct_repair n final)
  end.

Theorem compute_repair_or_separator_correct : forall m n D r,
  MatrixShape m n D -> VectorShape m r ->
  match compute_repair_or_separator m n D r with
  | RawRepair b => VectorShape n b /\ VecEq (mat_vec D b) r
  | RawSeparator y => VectorShape m y /\ VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1
  end.
Proof.
  intros m n D r HD Hr. unfold VectorShape in Hr.
  assert (HA0 : MatrixShape m (S n) (augment_rhs D r)) by (apply augment_rhs_MatrixShape; assumption).
  assert (HInv0 : ElimInvariant m n (augment_rhs D r) (initial_state m (augment_rhs D r)))
    by (apply initial_state_invariant; exact HA0).
  set (final := eliminate n m n (initial_state m (augment_rhs D r))).
  assert (HInvf : ElimInvariant m n (augment_rhs D r) final)
    by (apply eliminate_preserves_invariant; assumption).
  unfold compute_repair_or_separator. fold final.
  destruct (find_inconsistent_row n (st_work final)) eqn:Hfind.
  - assert (Hsep := extract_separator_normalized m n D r final n0 HD Hr HInvf Hfind).
    unfold extract_separator_vector.
    destruct Hsep as [Hzero Hdot1].
    assert (Hk : (n0 < length (st_work final))%nat)
      by (destruct (find_inconsistent_row_sound n (st_work final) n0 Hfind) as [Hk0 _]; exact Hk0).
    destruct HInvf as [HWf [HTf _]].
    destruct HWf as [HlenWf _]. destruct HTf as [HlenTf HrowsTf].
    assert (Hkm : (n0 < m)%nat) by (rewrite <- HlenWf; exact Hk).
    assert (Hkt : (n0 < length (st_transform final))%nat) by (rewrite HlenTf; exact Hkm).
    rewrite Forall_forall in HrowsTf.
    assert (HlenRow : length (nth n0 (st_transform final) []) = m) by (apply HrowsTf, nth_In, Hkt).
    assert (Hnthind : nth n0 (st_transform final) (zero_vec m) = nth n0 (st_transform final) [])
      by (apply nth_indep; rewrite HlenTf; exact Hkm).
    rewrite Hnthind in Hzero, Hdot1.
    rewrite Hnthind.
    split; [| split].
    + unfold VectorShape. rewrite length_vscale. exact HlenRow.
    + rewrite <- (row_vec_mat_eq_mat_vec_transpose (vscale (/ nth n (nth n0 (st_work final) []) 0) (nth n0 (st_transform final) [])) D n).
      exact Hzero.
    + exact Hdot1.
  - destruct HInvf as [_ [_ [_ [Hpcle _]]]].
    assert (Hpcge : (n <= st_pivot_col final)%nat).
    { apply (eliminate_reaches_final_column n m n (initial_state m (augment_rhs D r))).
      unfold initial_state. simpl. lia. }
    assert (Hpceq : st_pivot_col final = n) by lia.
    split.
    + unfold VectorShape, construct_repair.
      rewrite length_assign_pivots. apply repeat_length.
    + apply (repair_correct m n D r n HD Hr); fold final; [exact Hpceq | exact Hfind].
Qed.

Inductive RepairOrSeparator (m n : nat) (D : list (list Q)) (r : list Q) : Type :=
| RepairFound : forall b, VectorShape n b -> VecEq (mat_vec D b) r -> RepairOrSeparator m n D r
| SeparatorFound : forall y, VectorShape m y -> VecEq (mat_vec (transpose D n) y) (repeat 0 n) -> dot y r == 1 -> RepairOrSeparator m n D r.

Arguments RepairFound {m n D r} b _ _.
Arguments SeparatorFound {m n D r} y _ _ _.

Definition certified_repair_or_separator (m n : nat) (D : list (list Q)) (r : list Q)
  (HD : MatrixShape m n D) (Hr : VectorShape m r) : RepairOrSeparator m n D r :=
  match compute_repair_or_separator m n D r as res
    return (match res with
            | RawRepair b => VectorShape n b /\ VecEq (mat_vec D b) r
            | RawSeparator y => VectorShape m y /\ VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1
            end -> RepairOrSeparator m n D r)
  with
  | RawRepair b => fun H => RepairFound b (proj1 H) (proj2 H)
  | RawSeparator y => fun H => SeparatorFound y (proj1 H) (proj1 (proj2 H)) (proj2 (proj2 H))
  end (compute_repair_or_separator_correct m n D r HD Hr).

Theorem rational_repair_or_separator : forall m n D r,
  MatrixShape m n D -> VectorShape m r ->
  (exists b, VectorShape n b /\ VecEq (mat_vec D b) r) \/
  (exists y, VectorShape m y /\ VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1).
Proof.
  intros m n D r HD Hr.
  pose proof (compute_repair_or_separator_correct m n D r HD Hr) as H.
  destruct (compute_repair_or_separator m n D r) as [b | y].
  - left. exists b. exact H.
  - right. exists y. exact H.
Qed.

Corollary separation_for_finite_rational_image : forall m n D r,
  MatrixShape m n D -> VectorShape m r ->
  ~ (exists b, VectorShape n b /\ VecEq (mat_vec D b) r) ->
  exists y, VectorShape m y /\ VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1.
Proof.
  intros m n D r HD Hr Hnob.
  destruct (rational_repair_or_separator m n D r HD Hr) as [Hrep | Hsep].
  - contradiction.
  - exact Hsep.
Qed.

(* The classical adjoint identity y . (D b) = (y^T D) . b, needed to
   turn the two witness properties into a numeric contradiction.
   row_vec_mat y D n plays the role of y^T D; dot_mat_vec_assoc relates
   it to dot y (mat_vec D b) by "expand by first row" (row_vec_mat_cons)
   plus dot's bilinearity, exactly mirroring the technique already used
   for shaped mat_mul_assoc. *)
Lemma dot_mat_vec_assoc : forall D y b n,
  Forall (fun row => length row = n) D -> length y = length D ->
  dot y (mat_vec D b) == dot (row_vec_mat y D n) b.
Proof.
  induction D as [| row0 D' IH]; intros y b n Hrows Hy.
  - destruct y as [| y0 y']; simpl in Hy; try discriminate.
    unfold mat_vec. simpl.
    assert (Hzero : VecEq (row_vec_mat (@nil Q) (@nil (list Q)) n) (repeat 0 n)).
    { apply (Forall2_from_nth Qeq 0).
      - rewrite length_row_vec_mat, repeat_length. reflexivity.
      - intros j Hj. rewrite length_row_vec_mat in Hj.
        assert (Hjt : (j < length (transpose (@nil (list Q)) n))%nat) by (rewrite length_transpose; exact Hj).
        unfold row_vec_mat.
        rewrite (my_nth_map (list Q) Q (fun col => dot (@nil Q) col) (transpose (@nil (list Q)) n) j [] 0 Hjt).
        rewrite dot_nil_l. rewrite (nth_repeat_eq 0 n j Hj). reflexivity. }
    rewrite Hzero, dot_nil_l, dot_zero_l. reflexivity.
  - destruct y as [| y0 y']; simpl in Hy; try discriminate.
    injection Hy as Hy'.
    apply Forall_cons_iff in Hrows. destruct Hrows as [Hrow0 Hrows'].
    unfold mat_vec. simpl. rewrite dot_cons.
    fold (mat_vec D' b).
    rewrite (IH y' b n Hrows' Hy').
    assert (Hcons : VecEq (row_vec_mat (y0 :: y') (row0 :: D') n) (vadd (vscale y0 row0) (row_vec_mat y' D' n)))
      by (apply row_vec_mat_cons; exact Hrow0).
    rewrite Hcons.
    assert (Hlen1 : length (vscale y0 row0) = length (row_vec_mat y' D' n))
      by (rewrite length_vscale, Hrow0; symmetry; apply length_row_vec_mat).
    rewrite (dot_vadd_l (vscale y0 row0) (row_vec_mat y' D' n) b Hlen1).
    rewrite dot_vscale_l. ring.
Qed.

Theorem repair_and_separator_disjoint : forall m n D r b y,
  MatrixShape m n D -> VectorShape n b -> VectorShape m y ->
  VecEq (mat_vec D b) r -> VecEq (mat_vec (transpose D n) y) (repeat 0 n) -> dot y r == 1 -> False.
Proof.
  intros m n D r b y HD Hb Hy Hrepair Hsep Hdot1.
  destruct HD as [HlenD HrowsD].
  unfold VectorShape in Hb, Hy.
  assert (H2 : dot y r == dot y (mat_vec D b)) by (apply dot_Proper; [reflexivity | symmetry; exact Hrepair]).
  assert (H3 : dot y (mat_vec D b) == dot (row_vec_mat y D n) b) by (apply dot_mat_vec_assoc; [exact HrowsD | rewrite Hy, HlenD; reflexivity]).
  assert (H4 : dot (row_vec_mat y D n) b == dot (mat_vec (transpose D n) y) b)
    by (apply dot_Proper; [apply row_vec_mat_eq_mat_vec_transpose | reflexivity]).
  assert (H5 : dot (mat_vec (transpose D n) y) b == dot (repeat 0 n) b) by (apply dot_Proper; [exact Hsep | reflexivity]).
  assert (H6 : dot (repeat 0 n) b == 0) by (apply dot_zero_l).
  assert (Hcontra : (1:Q) == 0) by (rewrite <- Hdot1, H2, H3, H4, H5, H6; reflexivity).
  unfold Qeq in Hcontra. simpl in Hcontra. discriminate Hcontra.
Qed.

(* ------------------------------------------------------------------ *)
(* Shape-safe public boundary: dependent records wrapping raw lists,  *)
(* so malformed data is excluded before certified_repair_or_separator *)
(* is ever called.                                                    *)
(* ------------------------------------------------------------------ *)

Record RatVec (n : nat) := mkRatVec {
  ratvec_data : list Q;
  ratvec_shape : VectorShape n ratvec_data
}.

Record RatMatrix (m n : nat) := mkRatMatrix {
  ratmatrix_data : list (list Q);
  ratmatrix_shape : MatrixShape m n ratmatrix_data
}.

Arguments ratvec_data {n} _.
Arguments ratvec_shape {n} _.
Arguments ratmatrix_data {m n} _.
Arguments ratmatrix_shape {m n} _.

Definition decide_repair_or_separator (m n : nat) (D : RatMatrix m n) (r : RatVec m)
  : RepairOrSeparator m n (ratmatrix_data D) (ratvec_data r) :=
  certified_repair_or_separator m n (ratmatrix_data D) (ratvec_data r) (ratmatrix_shape D) (ratvec_shape r).

(* ------------------------------------------------------------------ *)
(* Independent executable checkers for the sandbox demonstrations,    *)
(* deliberately not reusing any elimination machinery.                *)
(* ------------------------------------------------------------------ *)

Fixpoint veceqb (u v : list Q) : bool :=
  match u, v with
  | [], [] => true
  | x :: u', y :: v' => andb (Qeq_bool x y) (veceqb u' v')
  | _, _ => false
  end.

Lemma veceqb_true_iff : forall u v, veceqb u v = true <-> VecEq u v.
Proof.
  induction u as [| x u' IH]; intros v; destruct v as [| y v']; simpl.
  - split; intros; constructor.
  - split; intros H; [discriminate | inversion H].
  - split; intros H; [discriminate | inversion H].
  - rewrite andb_true_iff, Qeq_bool_iff, IH.
    split.
    + intros [Hxy Huv]. constructor; assumption.
    + intros H. inversion H as [| x' y' u'' v'' Hxy Huv]; subst. split; assumption.
Qed.

Definition check_repair (D : list (list Q)) (r b : list Q) : bool := veceqb (mat_vec D b) r.

Definition check_separator (D : list (list Q)) (r y : list Q) (n : nat) : bool :=
  andb (veceqb (mat_vec (transpose D n) y) (repeat 0 n)) (Qeq_bool (dot y r) 1).

Theorem check_repair_correct : forall D r b, check_repair D r b = true -> VecEq (mat_vec D b) r.
Proof. intros D r b H. apply veceqb_true_iff. exact H. Qed.

Theorem check_separator_correct : forall D r y n, check_separator D r y n = true ->
  VecEq (mat_vec (transpose D n) y) (repeat 0 n) /\ dot y r == 1.
Proof.
  intros D r y n H. unfold check_separator in H. apply andb_true_iff in H. destruct H as [H1 H2].
  split; [apply veceqb_true_iff; exact H1 | apply Qeq_bool_iff; exact H2].
Qed.

(* ------------------------------------------------------------------ *)
(* Sandbox evaluation: repairable system, inconsistent synthetic       *)
(* system, the real four-cycle obstruction witness, and four tamper   *)
(* rejection cases.                                                    *)
(* ------------------------------------------------------------------ *)

(* 1. A repairable system: identity matrix, arbitrary rhs. *)
Definition ex1_D : list (list Q) := [[1;0];[0;1]].
Definition ex1_r : list Q := [3;5].

Example ex1_result_is_repair :
  match compute_repair_or_separator 2 2 ex1_D ex1_r with RawRepair _ => True | RawSeparator _ => False end.
Proof. vm_compute. exact I. Qed.

Example ex1_repair_checks :
  match compute_repair_or_separator 2 2 ex1_D ex1_r with
  | RawRepair b => check_repair ex1_D ex1_r b = true
  | RawSeparator _ => False
  end.
Proof. vm_compute. reflexivity. Qed.

(* 2. A synthetic inconsistent system: 0 = 1. *)
Definition ex2_D : list (list Q) := [[0]].
Definition ex2_r : list Q := [1].

Example ex2_result_is_separator :
  match compute_repair_or_separator 1 1 ex2_D ex2_r with RawRepair _ => False | RawSeparator _ => True end.
Proof. vm_compute. exact I. Qed.

Example ex2_separator_checks :
  match compute_repair_or_separator 1 1 ex2_D ex2_r with
  | RawRepair _ => False
  | RawSeparator y => check_separator ex2_D ex2_r y 1 = true
  end.
Proof. vm_compute. reflexivity. Qed.

(* 3. The real four-cycle obstruction witness (Figure 3), from
   examples/four_cycle.json: coboundary_0 as D, residue as r. The
   internal inconsistent-row extraction recovers the paper's own
   canonical cycle z = (-1,-1,-1,1) with pairing c = -5 before
   normalisation; the public certificate is -1/5 z. *)
Definition fc_D : list (list Q) := [[-1;1;0;0]; [0;-1;1;0]; [0;0;-1;1]; [-1;0;0;1]].
Definition fc_r : list Q := [1;1;1;-2].

Example fc_result_is_separator :
  match compute_repair_or_separator 4 4 fc_D fc_r with RawRepair _ => False | RawSeparator _ => True end.
Proof. vm_compute. exact I. Qed.

Example fc_separator_value :
  match compute_repair_or_separator 4 4 fc_D fc_r with
  | RawRepair _ => False
  | RawSeparator y => y = [1#5; 1#5; 1#5; -1#5]
  end.
Proof. vm_compute. reflexivity. Qed.

Example fc_separator_checks :
  match compute_repair_or_separator 4 4 fc_D fc_r with
  | RawRepair _ => False
  | RawSeparator y => check_separator fc_D fc_r y 4 = true
  end.
Proof. vm_compute. reflexivity. Qed.

(* Also record the raw unnormalised internal witness explicitly. *)
Example fc_raw_cycle_matches_paper :
  let A0 := augment_rhs fc_D fc_r in
  let final := eliminate 4 4 4 (initial_state 4 A0) in
  match find_inconsistent_row 4 (st_work final) with
  | Some k => nth 4 (nth k (st_work final) []) 0 == -5
  | None => False
  end.
Proof. vm_compute. reflexivity. Qed.

(* 4. Altered repair witness rejected. *)
Example ex1_altered_repair_rejected : check_repair ex1_D ex1_r [3; 6] = false.
Proof. vm_compute. reflexivity. Qed.

(* 5. Altered separator entry rejected. *)
Example fc_altered_separator_rejected : check_separator fc_D fc_r [1#5; 1#5; 1#5; 1#5] 4 = false.
Proof. vm_compute. reflexivity. Qed.

(* 6. Annihilating but unnormalised separator rejected: the raw cycle
   witness z = (-1,-1,-1,1) satisfies D^T z = 0 but dot z r = -5 <> 1. *)
Example fc_unnormalised_separator_rejected : check_separator fc_D fc_r [-1; -1; -1; 1] 4 = false.
Proof. vm_compute. reflexivity. Qed.

(* 7. Normalised (dot = 1) but non-annihilating separator rejected. *)
Example fc_non_annihilating_separator_rejected : check_separator fc_D fc_r [1; 0; 0; 0] 4 = false.
Proof. vm_compute. reflexivity. Qed.
