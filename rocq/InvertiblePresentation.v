(*
   InvertiblePresentation.v

   R24, layer 1: the reusable algebraic vocabulary for certificate
   transport under a certified invertible linear presentation change --
   matrices and vector actions over `RationalCanonicalVectors.qcvec`
   (canonical rationals, R22's own representation), an explicit
   `InvertibleMatrix` record (two-sided-inverse witnesses supplied by
   the caller, no constructive inversion procedure built), and the four
   transformation operators the R24 theorems are stated in terms of.

   SCOPE, stated once, precisely: certified invertible LINEAR changes of
   basis on a finite-dimensional domain and residue space, over exact
   rationals. This file and `CertificateTransport.v` do NOT cover
   translations, affine maps, projections, cropping, resolution loss,
   dimension changes, nonlinear transformations, approximate numerical
   equivalence, or arbitrary refinement/common-subdivision -- see
   `docs/design/CERTIFICATE_TRANSPORT_SPEC.md` §4 for the full list and
   the reasoning behind excluding each.

   WHY `qcvec`, NOT R21's `list Q`: this file was spiked first, entirely
   untracked, exactly to answer whether the transpose/inverse identities
   `CERTIFICATE_TRANSPORT_SPEC.md` §2 needed would actually compile, and
   whether they would need a large amount of new matrix-algebra
   infrastructure. Neither `list Q`'s `VecEq`/`Qeq` friction nor a large
   library turned out to be necessary: `Qc`'s Leibniz-equality ring laws
   (the same reason R22 chose `qcvec` over `list Q`) made every identity
   below go through with ordinary `rewrite`, and only ONE full matrix
   Leibniz identity was needed anywhere (`transpose_qc_involutive`) --
   everything else is proved at the level of how matrices ACT on
   vectors, per the proof hierarchy actually used throughout: matrix
   multiplication acts associatively on vectors; transpose reverses
   multiplication under vector action; transposing (or left-multiplying
   with) a two-sided inverse undoes the original action; the transport
   equations follow from chaining these three facts.

   THE ONE CANONICALITY WRINKLE, worth recording so it is not
   rediscovered as if it were a soundness problem: exact-rational
   cancellation (e.g. several `1/5` terms summing to exactly `0`) can
   reach the SAME canonical `Qc` value via two different computation
   paths whose `canon` proof components differ syntactically even
   though the `this` (rational) components agree -- confirmed directly
   with `Set Printing All` (one path's proof was `Qred_involutive 0`,
   the other's `Qred_involutive (0#25)`). Coq has no default proof
   irrelevance for `Prop`, so plain `vm_compute; reflexivity` can then
   fail on a whole `Qcmake this canon` record even though the rational
   values are equal. This is not a mathematical inequality and does not
   need a custom extensionality axiom: `Qc_is_canon` (an existing
   `Qcanon` lemma, needing only `Qeq`) is the correct repair, used in
   `R24CertificateTransportExamples.v`.

   Depends on RationalCanonicalVectors.v only (for `qcvec`); independent
   of R21 and of the four-cycle example, by design -- this file is pure
   algebraic infrastructure, reusable by anything that needs certified
   invertible presentation changes over `qcvec`, not specific to any one
   certificate or example.
*)

Require Import Coq.QArith.QArith.
Require Import Coq.QArith.Qcanon.
Require Import Coq.Vectors.Vector.
Require Import Coq.Vectors.Fin.
Import VectorNotations.
Require Import RationalCanonicalVectors.

(* ------------------------------------------------------------------ *)
(* Matrices over qcvec, and the operations R24 needs: dot product,
   matrix-vector action, transpose, matrix-matrix composition, identity. *)
(* ------------------------------------------------------------------ *)

Definition MatrixQc (m n : nat) := Vector.t (qcvec n) m.

Definition dot_qc {n : nat} (u v : qcvec n) : Qc :=
  Vector.fold_right Qcplus (Vector.map2 Qcmult u v) (Q2Qc 0).

Definition mat_vec_qc {m n : nat} (D : MatrixQc m n) (x : qcvec n) : qcvec m :=
  Vector.map (fun row => dot_qc row x) D.

Fixpoint transpose_qc {A : Type} {m n : nat} (D : Vector.t (Vector.t A n) m) : Vector.t (Vector.t A m) n :=
  match D in Vector.t _ m0 return Vector.t (Vector.t A m0) n with
  | Vector.nil _ => Vector.const (Vector.nil A) n
  | Vector.cons _ row m' D' => Vector.map2 (fun x col => Vector.cons A x m' col) row (transpose_qc D')
  end.

Definition mat_mat_qc {m n p : nat} (D1 : MatrixQc m n) (D2 : MatrixQc n p) : MatrixQc m p :=
  Vector.map (fun row1 => Vector.map (fun col2 => dot_qc row1 col2) (transpose_qc D2)) D1.

Fixpoint identity_qc (n : nat) : MatrixQc n n :=
  match n with
  | O => Vector.nil (qcvec 0)
  | S n' => Vector.cons _ (Vector.cons _ (Q2Qc 1) n' (Vector.const (Q2Qc 0) n'))
                        n' (Vector.map (fun row => Vector.cons _ (Q2Qc 0) n' row) (identity_qc n'))
  end.

(* ------------------------------------------------------------------ *)
(* dot_qc: basic algebra. *)
(* ------------------------------------------------------------------ *)

Lemma dot_qc_cons : forall (n : nat) (x y : Qc) (u v : qcvec n),
  dot_qc (x :: u) (y :: v) = Qcplus (Qcmult x y) (dot_qc u v).
Proof. intros. unfold dot_qc. simpl. reflexivity. Qed.

Lemma dot_qc_nil : forall (u v : qcvec 0), dot_qc u v = Q2Qc 0.
Proof.
  intros u v.
  apply Vector.case0 with (v := u).
  apply Vector.case0 with (v := v).
  reflexivity.
Qed.

Lemma dot_qc_comm : forall (n : nat) (u v : qcvec n), dot_qc u v = dot_qc v u.
Proof.
  induction n as [| n' IH]; intros u v.
  - apply Vector.case0 with (v := u). apply Vector.case0 with (v := v). reflexivity.
  - revert u. apply (Vector.caseS' v). intros hv tv u.
    revert hv tv. apply (Vector.caseS' u). intros hu tu hv tv.
    rewrite (dot_qc_cons n' hu hv tu tv).
    rewrite (dot_qc_cons n' hv hu tv tu).
    rewrite (IH tu tv).
    rewrite (Qcmult_comm hu hv).
    reflexivity.
Qed.

Definition vadd_qc {n : nat} (u v : qcvec n) : qcvec n := Vector.map2 Qcplus u v.
Definition vscale_qc {n : nat} (c : Qc) (v : qcvec n) : qcvec n := Vector.map (Qcmult c) v.

Lemma dot_qc_additive_r : forall (n : nat) (x u v : qcvec n),
  dot_qc x (vadd_qc u v) = Qcplus (dot_qc x u) (dot_qc x v).
Proof.
  induction n as [| n' IH]; intros x u v.
  - apply Vector.case0 with (v := x). apply Vector.case0 with (v := u). apply Vector.case0 with (v := v).
    unfold vadd_qc. simpl. unfold dot_qc. simpl. ring.
  - revert u v. apply (Vector.caseS' x). intros hx tx u v.
    revert v. apply (Vector.caseS' u). intros hu tu v.
    apply (Vector.caseS' v). intros hv tv.
    unfold vadd_qc.
    change (Vector.map2 Qcplus (hu :: tu) (hv :: tv)) with (Qcplus hu hv :: Vector.map2 Qcplus tu tv).
    rewrite (dot_qc_cons n' hx (Qcplus hu hv) tx (Vector.map2 Qcplus tu tv)).
    rewrite (dot_qc_cons n' hx hu tx tu).
    rewrite (dot_qc_cons n' hx hv tx tv).
    fold (vadd_qc tu tv).
    rewrite (IH tx tu tv).
    ring.
Qed.

Lemma dot_qc_scale_r : forall (n : nat) (c : Qc) (x v : qcvec n),
  dot_qc x (vscale_qc c v) = Qcmult c (dot_qc x v).
Proof.
  induction n as [| n' IH]; intros c x v.
  - apply Vector.case0 with (v := x). apply Vector.case0 with (v := v).
    unfold vscale_qc. simpl. unfold dot_qc. simpl. ring.
  - revert v. apply (Vector.caseS' x). intros hx tx v.
    apply (Vector.caseS' v). intros hv tv.
    unfold vscale_qc.
    change (Vector.map (Qcmult c) (hv :: tv)) with (Qcmult c hv :: Vector.map (Qcmult c) tv).
    rewrite (dot_qc_cons n' hx (Qcmult c hv) tx (Vector.map (Qcmult c) tv)).
    rewrite (dot_qc_cons n' hx hv tx tv).
    fold (vscale_qc c tv).
    rewrite (IH c tx tv).
    ring.
Qed.

Lemma mat_vec_qc_zero_dot : forall (n : nat) (x : qcvec n), dot_qc x (Vector.const (Q2Qc 0) n) = Q2Qc 0.
Proof.
  induction n as [| n' IH]; intros x.
  - apply Vector.case0 with (v := x). reflexivity.
  - apply (Vector.caseS' x). intros hx tx.
    change (Vector.const (Q2Qc 0) (S n')) with (Q2Qc 0 :: Vector.const (Q2Qc 0) n').
    rewrite (dot_qc_cons n' hx (Q2Qc 0) tx (Vector.const (Q2Qc 0) n')).
    rewrite (IH tx).
    ring.
Qed.

(* ------------------------------------------------------------------ *)
(* transpose_qc / mat_vec_qc interaction, culminating in the adjoint
   identity `dot_qc (mat_vec_qc D x) y = dot_qc x (mat_vec_qc (transpose_qc D) y)`
   -- proved once, reused for every transport theorem below. *)
(* ------------------------------------------------------------------ *)

Lemma transpose_qc_cons :
  forall (m n : nat) (row : qcvec n) (D' : MatrixQc m n),
    transpose_qc (row :: D') = Vector.map2 (fun a col => a :: col) row (transpose_qc D').
Proof. intros. reflexivity. Qed.

(* NOTE on the two `rewrite`-matching wrinkles below (both confirmed
   with `Set Printing All`, not guessed): (1) instantiating a lemma's
   implicit length argument explicitly (e.g. `dot_qc_cons p ...`) freezes
   its vector-type arguments as `qcvec p` syntactically, while
   `nth_map`/`nth_map2`'s OWN unification can expose the *unfolded*
   `Vector.t Qc p` in the actual goal -- the same rational number, a
   different head symbol, so plain (keyed, syntactic) `rewrite` fails to
   find it even though the printed goal looks identical; passing such
   arguments as `_` lets `rewrite`'s unification pick whichever head
   symbol is actually present. (2) `apply` on an `<->` lemma applied
   TWICE in a row to nested vector-of-vector equalities can mis-unify
   (confirmed via `Show`: it spawned a spurious `p = p` goal and left the
   real goal untouched); `rewrite <-` on the same iff does not have this
   problem. *)

Lemma mat_vec_qc_map2_cons_row :
  forall (n p : nat) (row : qcvec n) (Dt : MatrixQc n p) (hy : Qc) (ty : qcvec p),
    mat_vec_qc (Vector.map2 (fun a col => a :: col) row Dt) (hy :: ty) =
    vadd_qc (vscale_qc hy row) (mat_vec_qc Dt ty).
Proof.
  intros n p row Dt hy ty.
  unfold mat_vec_qc, vadd_qc, vscale_qc.
  apply Vector.eq_nth_iff. intros p1 p2 Hp. subst p2.
  rewrite (nth_map _ _ p1 p1 eq_refl).
  rewrite (nth_map2 _ _ _ p1 p1 p1 eq_refl eq_refl).
  rewrite (dot_qc_cons _ _ _ _ _).
  rewrite (nth_map2 _ _ _ p1 p1 p1 eq_refl eq_refl).
  rewrite (nth_map _ _ p1 p1 eq_refl).
  rewrite (nth_map _ _ p1 p1 eq_refl).
  f_equal. apply Qcmult_comm.
Qed.

Lemma mat_vec_qc_transpose_nil :
  forall (n : nat) (y : qcvec 0),
    mat_vec_qc (transpose_qc (Vector.nil (qcvec n))) y = Vector.const (Q2Qc 0) n.
Proof.
  intros n y.
  unfold mat_vec_qc. simpl.
  induction n as [| n' IHn].
  - reflexivity.
  - simpl. f_equal.
    + apply dot_qc_nil.
    + exact IHn.
Qed.

Theorem dot_qc_mat_vec_adjoint :
  forall (m n : nat) (D : MatrixQc m n) (x : qcvec n) (y : qcvec m),
    dot_qc (mat_vec_qc D x) y = dot_qc x (mat_vec_qc (transpose_qc D) y).
Proof.
  induction m as [| m' IH]; intros n D x y.
  - apply Vector.case0 with (v := D). apply Vector.case0 with (v := y).
    (* Targeted `change`, not a blanket `simpl`: a blanket simplification
       would also compute away `transpose_qc (Vector.nil (qcvec n))` on
       the RHS (its argument is a literal constructor), resolving
       transpose_qc's implicit `A` by unifying `qcvec n` against
       `Vector.t Qc n` and swapping the head symbol from `qcvec` to the
       unfolded form -- which then makes `mat_vec_qc_transpose_nil`
       (stated using `qcvec`) fail to `rewrite` against it, even though
       the two terms are convertible and print identically. *)
    change (mat_vec_qc (Vector.nil (qcvec n)) x) with (Vector.nil Qc).
    rewrite dot_qc_nil.
    rewrite (mat_vec_qc_transpose_nil n (Vector.nil Qc)).
    symmetry. apply mat_vec_qc_zero_dot.
  - apply (Vector.caseS' D). intros row D'.
    apply (Vector.caseS' y). intros hy ty.
    change (mat_vec_qc (row :: D') x) with (dot_qc row x :: mat_vec_qc D' x).
    rewrite (dot_qc_cons m' (dot_qc row x) hy (mat_vec_qc D' x) ty).
    rewrite (IH n D' x ty).
    rewrite (transpose_qc_cons _ _ _ _).
    rewrite (mat_vec_qc_map2_cons_row _ _ _ _ _ _).
    rewrite (dot_qc_additive_r n x (vscale_qc hy row) (mat_vec_qc (transpose_qc D') ty)).
    rewrite (dot_qc_scale_r n hy x row).
    rewrite (dot_qc_comm n x row).
    ring.
Qed.

(* ------------------------------------------------------------------ *)
(* Double transpose, matrix-multiplication/vector-action associativity,
   and identity-matrix action -- the three remaining supporting facts,
   each proved once and reused. `transpose_qc_involutive` is the ONE
   full matrix Leibniz identity this file needs. *)
(* ------------------------------------------------------------------ *)

Lemma vec0_eq_nil : forall (A : Type) (v : Vector.t A 0), v = Vector.nil A.
Proof. intros A v. apply Vector.case0 with (v := v). reflexivity. Qed.

Lemma mat_vec_qc_nth :
  forall (m n : nat) (M : MatrixQc m n) (v : qcvec n) (p : Fin.t m),
    Vector.nth (mat_vec_qc M v) p = dot_qc (Vector.nth M p) v.
Proof.
  intros m n M v p. unfold mat_vec_qc. apply (nth_map (fun row => dot_qc row v) M p p eq_refl).
Qed.

Lemma nth_transpose_qc :
  forall (A : Type) (m n : nat) (D : Vector.t (Vector.t A n) m) (i : Fin.t m) (j : Fin.t n),
    Vector.nth (Vector.nth (transpose_qc D) j) i = Vector.nth (Vector.nth D i) j.
Proof.
  intros A m. induction m as [|m' IH]; intros n D i j.
  - inversion i.
  - apply (Vector.caseS' D). intros row D'.
    apply (Fin.caseS' i).
    + change (transpose_qc (row :: D')) with (Vector.map2 (fun a col => a :: col) row (transpose_qc D')).
      rewrite (nth_map2 _ _ _ j j j eq_refl eq_refl).
      reflexivity.
    + intros i'.
      change (transpose_qc (row :: D')) with (Vector.map2 (fun a col => a :: col) row (transpose_qc D')).
      rewrite (nth_map2 _ _ _ j j j eq_refl eq_refl).
      simpl.
      apply (IH n D' i' j).
Qed.

Lemma transpose_qc_involutive :
  forall (A : Type) (m n : nat) (D : Vector.t (Vector.t A n) m), transpose_qc (transpose_qc D) = D.
Proof.
  intros A m n D.
  apply Vector.eq_nth_iff. intros i1 i2 Hi. subst i2.
  rewrite <- Vector.eq_nth_iff. intros j1 j2 Hj. subst j2.
  rewrite (nth_transpose_qc A n m (transpose_qc D) j1 i1).
  apply (nth_transpose_qc A m n D i1 j1).
Qed.

Lemma mat_vec_qc_row_dot_assoc :
  forall (n p : nat) (row1 : qcvec n) (D2 : MatrixQc n p) (x : qcvec p),
    dot_qc (Vector.map (fun col2 => dot_qc row1 col2) (transpose_qc D2)) x =
    dot_qc row1 (mat_vec_qc D2 x).
Proof.
  intros n p row1 D2 x.
  rewrite (Vector.map_ext _ _ (fun col2 => dot_qc row1 col2) (fun col2 => dot_qc col2 row1) (fun col2 => dot_qc_comm n row1 col2) p (transpose_qc D2)).
  fold (mat_vec_qc (transpose_qc D2) row1).
  rewrite (dot_qc_mat_vec_adjoint p n (transpose_qc D2) row1 x).
  rewrite (transpose_qc_involutive Qc n p D2).
  reflexivity.
Qed.

Theorem mat_vec_qc_mat_mat_assoc :
  forall (m n p : nat) (D1 : MatrixQc m n) (D2 : MatrixQc n p) (x : qcvec p),
    mat_vec_qc (mat_mat_qc D1 D2) x = mat_vec_qc D1 (mat_vec_qc D2 x).
Proof.
  intros m n p D1 D2 x.
  apply Vector.eq_nth_iff. intros i1 i2 Hi. subst i2.
  unfold mat_vec_qc, mat_mat_qc.
  rewrite (nth_map _ _ i1 i1 eq_refl).
  rewrite (nth_map _ _ i1 i1 eq_refl).
  rewrite (nth_map _ _ i1 i1 eq_refl).
  apply (mat_vec_qc_row_dot_assoc n p (Vector.nth D1 i1) D2 x).
Qed.

Theorem mat_vec_qc_identity : forall (n : nat) (x : qcvec n), mat_vec_qc (identity_qc n) x = x.
Proof.
  induction n as [| n' IH]; intros x.
  - apply Vector.case0 with (v := x). reflexivity.
  - apply (Vector.caseS' x). intros hx tx.
    change (mat_vec_qc (identity_qc (S n')) (hx :: tx))
      with (dot_qc (Q2Qc 1 :: Vector.const (Q2Qc 0) n') (hx :: tx)
            :: mat_vec_qc (Vector.map (fun row => Q2Qc 0 :: row) (identity_qc n')) (hx :: tx)).
    rewrite (dot_qc_cons n' (Q2Qc 1) hx (Vector.const (Q2Qc 0) n') tx).
    rewrite (dot_qc_comm n' (Vector.const (Q2Qc 0) n') tx).
    rewrite mat_vec_qc_zero_dot.
    assert (Htail : mat_vec_qc (Vector.map (fun row => Q2Qc 0 :: row) (identity_qc n')) (hx :: tx) = tx).
    { unfold mat_vec_qc.
      apply Vector.eq_nth_iff. intros p1 p2 Hp. subst p2.
      rewrite (nth_map _ _ p1 p1 eq_refl).
      rewrite (nth_map _ _ p1 p1 eq_refl).
      rewrite (dot_qc_cons _ _ _ _ _).
      rewrite <- (mat_vec_qc_nth _ _ _ tx p1).
      rewrite (IH tx).
      ring.
    }
    rewrite Htail.
    f_equal. ring.
Qed.

(* ------------------------------------------------------------------ *)
(* Nondegeneracy of dot_qc, via standard basis vectors -- needed once,
   to promote a pairing-universal fact ("forall b, dot_qc b v = dot_qc b
   w") to the vector Leibniz equality v = w. *)
(* ------------------------------------------------------------------ *)

Fixpoint unit_vec {n : nat} (p : Fin.t n) : qcvec n :=
  match p with
  | Fin.F1 => Vector.cons Qc (Q2Qc 1) _ (Vector.const (Q2Qc 0) _)
  | Fin.FS p' => Vector.cons Qc (Q2Qc 0) _ (unit_vec p')
  end.

Lemma dot_qc_unit_vec_l : forall (n : nat) (p : Fin.t n) (v : qcvec n),
  dot_qc (unit_vec p) v = Vector.nth v p.
Proof.
  induction n as [| n' IH]; intros p v.
  - inversion p.
  - apply (Fin.caseS' p).
    + apply (Vector.caseS' v). intros hv tv.
      change (unit_vec (@Fin.F1 n')) with (Vector.cons Qc (Q2Qc 1) n' (Vector.const (Q2Qc 0) n')).
      change (Vector.nth (hv :: tv) (@Fin.F1 n')) with hv.
      rewrite (dot_qc_cons _ _ _ _ _).
      rewrite (dot_qc_comm _ _ _).
      rewrite mat_vec_qc_zero_dot.
      ring.
    + intros p'.
      apply (Vector.caseS' v). intros hv tv.
      change (unit_vec (Fin.FS p')) with (Vector.cons Qc (Q2Qc 0) n' (unit_vec p')).
      change (Vector.nth (hv :: tv) (Fin.FS p')) with (Vector.nth tv p').
      rewrite (dot_qc_cons _ _ _ _ _).
      rewrite (IH p' tv).
      ring.
Qed.

Theorem dot_qc_ext : forall (n : nat) (v w : qcvec n),
  (forall b : qcvec n, dot_qc b v = dot_qc b w) -> v = w.
Proof.
  intros n v w H.
  apply Vector.eq_nth_iff. intros p1 p2 Hp. subst p2.
  rewrite <- (dot_qc_unit_vec_l n p1 v).
  rewrite <- (dot_qc_unit_vec_l n p1 w).
  apply (H (unit_vec p1)).
Qed.

Lemma dot_qc_ext_zero : forall (n : nat) (v : qcvec n),
  (forall b : qcvec n, dot_qc b v = Q2Qc 0) -> v = Vector.const (Q2Qc 0) n.
Proof.
  intros n v H.
  apply dot_qc_ext. intros b.
  rewrite (H b).
  symmetry. apply mat_vec_qc_zero_dot.
Qed.

(* ------------------------------------------------------------------ *)
(* The two inverse-action facts every transport theorem is built from:
   a two-sided matrix inverse undoes its own DIRECT action
   (`mat_vec_qc_left_inverse`, pure equational -- no nondegeneracy
   needed), and undoes its TRANSPOSE's action (`mat_vec_qc_transpose_inverse`,
   needs nondegeneracy since transpose doesn't commute with the matrix
   equation the same way). *)
(* ------------------------------------------------------------------ *)

Theorem mat_vec_qc_left_inverse :
  forall (m : nat) (Bf Bi : MatrixQc m m),
    mat_mat_qc Bi Bf = identity_qc m ->
    forall (x : qcvec m), mat_vec_qc Bi (mat_vec_qc Bf x) = x.
Proof.
  intros m Bf Bi Hinv x.
  rewrite <- (mat_vec_qc_mat_mat_assoc m m m Bi Bf x).
  rewrite Hinv.
  apply mat_vec_qc_identity.
Qed.

Theorem mat_vec_qc_transpose_inverse :
  forall (m : nat) (Bf Bi : MatrixQc m m),
    mat_mat_qc Bi Bf = identity_qc m ->
    forall (y : qcvec m),
      mat_vec_qc (transpose_qc Bf) (mat_vec_qc (transpose_qc Bi) y) = y.
Proof.
  intros m Bf Bi Hinv y.
  apply dot_qc_ext. intros z.
  rewrite <- (dot_qc_mat_vec_adjoint m m Bf z (mat_vec_qc (transpose_qc Bi) y)).
  rewrite <- (dot_qc_mat_vec_adjoint m m Bi (mat_vec_qc Bf z) y).
  rewrite <- (mat_vec_qc_mat_mat_assoc m m m Bi Bf z).
  rewrite Hinv.
  rewrite (mat_vec_qc_identity m z).
  reflexivity.
Qed.

(* ------------------------------------------------------------------ *)
(* InvertibleMatrix: explicit two-sided-inverse witnesses, supplied by
   the caller -- no constructive rational matrix inversion is built here
   (deferred, per CERTIFICATE_TRANSPORT_SPEC.md §5.1's "smaller first
   step"). The four transformation operators R24's theorems are stated
   over: the transformed operator D' = B D A^{-1}, the transformed
   residue r' = B r, the transported repair witness A b, and the
   transported separator witness B^{-T} y. *)
(* ------------------------------------------------------------------ *)

Record InvertibleMatrix (n : nat) := mkInvertibleMatrix {
  fwd : MatrixQc n n;
  bwd : MatrixQc n n;
  inv_left : mat_mat_qc bwd fwd = identity_qc n;
  inv_right : mat_mat_qc fwd bwd = identity_qc n;
}.

Arguments fwd {n} _.
Arguments bwd {n} _.
Arguments inv_left {n} _.
Arguments inv_right {n} _.

Definition transform_operator {m n : nat}
  (A : InvertibleMatrix n) (B : InvertibleMatrix m) (D : MatrixQc m n) : MatrixQc m n :=
  mat_mat_qc (mat_mat_qc (fwd B) D) (bwd A).

Definition transform_residue {m : nat} (B : InvertibleMatrix m) (r : qcvec m) : qcvec m :=
  mat_vec_qc (fwd B) r.

Definition transport_repair_vector {n : nat} (A : InvertibleMatrix n) (b : qcvec n) : qcvec n :=
  mat_vec_qc (fwd A) b.

Definition transport_separator_vector {m : nat} (B : InvertibleMatrix m) (y : qcvec m) : qcvec m :=
  mat_vec_qc (transpose_qc (bwd B)) y.

(* The inverse presentation change, as its own InvertibleMatrix: swapping
   `fwd`/`bwd` swaps `inv_left`/`inv_right` -- used by
   CertificateTransport.v to state the backward halves of the transport
   equivalences without re-deriving inverse existence. *)
Definition invert_InvertibleMatrix {n : nat} (A : InvertibleMatrix n) : InvertibleMatrix n :=
  mkInvertibleMatrix n (bwd A) (fwd A) (inv_right A) (inv_left A).
