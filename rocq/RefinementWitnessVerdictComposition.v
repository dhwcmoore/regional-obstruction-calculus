(*
   RefinementWitnessVerdictComposition.v

   Phase 2c: the proof attempt. rocq/RefinementWitnessComposition.v
   proved N0_composes. This file proves A4_composes and E0_composes --
   the two conditions refinement_witness_composition_boundary_search.py
   probed adversarially (~175,000 cases, 0 counterexamples) without
   proving.

   Both proofs succeed, but the mechanism is worth stating precisely
   rather than oversold.

   (A4) composes almost definitionally: the composite's pairing test,
   once the composite pullback is defined as literal function
   composition, is the SAME expression as step 2's own pairing test
   applied to the already-once-pushed-forward residue. No property of
   the pairing beyond its being a function is used -- not even
   linearity. This needs the SAME witness cycle to be reused at the
   composite level, not re-derived; it is not a claim that A4 holds for
   an arbitrary NEW witness cycle chosen at the composite level.

   (E0) composes for a real, short reason that turned out to need LESS
   than first suspected: only step 1's own (E0) and step 2's own (E0),
   chained through linearity of the pullback maps. An earlier hand
   derivation (recorded in docs/design/REFINEMENT_WITNESS_COMPOSITION_
   STATUS.md's discussion) reached for step 2's (N0) as well, via a
   "pushforward of Z1(R) equals Z1(Q) exactly" detour; the direct
   argument here (span-transport through linearity) does not need that
   detour or (N0) at all. Composing the "coverage" maps is enough.

   Minimal finite-dimensional linear-algebra infrastructure (spans,
   linear maps, over an abstract Q-vector-space record) is built from
   scratch here, in the same minimal spirit as rocq/
   RefinementWitnessComposition.v avoided building a Rocq matrix type:
   only what these two theorems need, nothing more general. This is
   larger than a matrix type would have been for the concrete Python
   case, but is honestly the general fact, not a restatement of one
   dimension.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import Coq.Lists.List.
Import ListNotations.

(* ------------------------------------------------------------------ *)
(* Part 1: (A4) composes -- no vector-space structure needed at all.   *)
(* ------------------------------------------------------------------ *)

Section A4Composes.

  Variables C1_P C1_Q C1_R : Type.
  Variable rho1_PQ : C1_P -> C1_Q.
  Variable rho1_QR : C1_Q -> C1_R.
  Variable pairing_R : C1_R -> Q.
  Variable r : C1_P.

  Definition composite_rho1 (p : C1_P) : C1_R := rho1_QR (rho1_PQ p).

  (* Step 2's own (A4), applied to the residue Q inherits from step 1
     (rho1_PQ r): the pairing is nonzero. *)
  Hypothesis step2_A4 : ~ (pairing_R (rho1_QR (rho1_PQ r)) == 0).

  Theorem A4_composes : ~ (pairing_R (composite_rho1 r) == 0).
  Proof.
    unfold composite_rho1.
    exact step2_A4.
  Qed.

End A4Composes.

(* ------------------------------------------------------------------ *)
(* Part 2: minimal finite-dimensional Q-vector-space infrastructure,   *)
(* just enough to state and prove span-transport under linear maps.    *)
(* ------------------------------------------------------------------ *)

Record VSpace := mkVSpace {
  carrier : Type;
  vzero : carrier;
  vadd : carrier -> carrier -> carrier;
  vscale : Q -> carrier -> carrier;
  vadd_assoc : forall a b c, vadd (vadd a b) c = vadd a (vadd b c);
  vadd_zero_l : forall a, vadd vzero a = a;
  vscale_distrib_vadd : forall c a b, vscale c (vadd a b) = vadd (vscale c a) (vscale c b);
  vscale_compose : forall c d a, vscale c (vscale d a) = vscale (c * d) a;
  vscale_vzero : forall c, vscale c vzero = vzero;
}.

Fixpoint LinComb (S : VSpace) (terms : list (Q * carrier S)) : carrier S :=
  match terms with
  | nil => vzero S
  | (c, v) :: rest => vadd S (vscale S c v) (LinComb S rest)
  end.

(* v is in the span of `basis` iff v is SOME finite linear combination of
   vectors drawn from `basis` -- matching in_span_over_Q's meaning in
   rational_linear_algebra.py (existence of coefficients). *)
Definition InSpan (S : VSpace) (basis : list (carrier S)) (v : carrier S) : Prop :=
  exists terms : list (Q * carrier S),
    (forall p, In p terms -> In (snd p) basis) /\ v = LinComb S terms.

Definition IsLinear (S1 S2 : VSpace) (f : carrier S1 -> carrier S2) : Prop :=
  f (vzero S1) = vzero S2 /\
  (forall a b, f (vadd S1 a b) = vadd S2 (f a) (f b)) /\
  (forall c a, f (vscale S1 c a) = vscale S2 c (f a)).

Lemma linear_LinComb :
  forall (S1 S2 : VSpace) (f : carrier S1 -> carrier S2),
    IsLinear S1 S2 f ->
    forall terms : list (Q * carrier S1),
      f (LinComb S1 terms) = LinComb S2 (map (fun p => (fst p, f (snd p))) terms).
Proof.
  intros S1 S2 f [Hz [Ha Hs]] terms.
  induction terms as [| [c v] rest IH]; simpl.
  - exact Hz.
  - rewrite Ha, Hs, IH. reflexivity.
Qed.

Theorem linear_maps_preserve_span :
  forall (S1 S2 : VSpace) (f : carrier S1 -> carrier S2),
    IsLinear S1 S2 f ->
    forall (basis : list (carrier S1)) (v : carrier S1),
      InSpan S1 basis v -> InSpan S2 (map f basis) (f v).
Proof.
  intros S1 S2 f HLin basis v [terms [Hin Heq]].
  exists (map (fun p => (fst p, f (snd p))) terms).
  split.
  - intros p Hp.
    apply in_map_iff in Hp.
    destruct Hp as [[c u] [Heqp Hu]].
    simpl in Heqp. subst p. simpl.
    apply in_map. exact (Hin (c, u) Hu).
  - rewrite Heq. apply linear_LinComb. exact HLin.
Qed.

Lemma InSpan_vzero : forall (S : VSpace) (basis : list (carrier S)), InSpan S basis (vzero S).
Proof. intros S basis. exists nil. split; [intros p []|reflexivity]. Qed.

Lemma LinComb_app :
  forall (S : VSpace) (t1 t2 : list (Q * carrier S)),
    LinComb S (t1 ++ t2) = vadd S (LinComb S t1) (LinComb S t2).
Proof.
  intros S t1 t2.
  induction t1 as [| [c v] rest IH]; simpl.
  - rewrite (vadd_zero_l S). reflexivity.
  - rewrite IH, (vadd_assoc S). reflexivity.
Qed.

Lemma InSpan_vadd :
  forall (S : VSpace) (basis : list (carrier S)) (v1 v2 : carrier S),
    InSpan S basis v1 -> InSpan S basis v2 -> InSpan S basis (vadd S v1 v2).
Proof.
  intros S basis v1 v2 [t1 [Hin1 Heq1]] [t2 [Hin2 Heq2]].
  exists (t1 ++ t2).
  split.
  - intros p Hp. apply in_app_or in Hp.
    destruct Hp as [Hp|Hp]; [exact (Hin1 p Hp) | exact (Hin2 p Hp)].
  - rewrite Heq1, Heq2. symmetry. apply LinComb_app.
Qed.

Lemma LinComb_scale :
  forall (S : VSpace) (c : Q) (terms : list (Q * carrier S)),
    vscale S c (LinComb S terms) = LinComb S (map (fun p => (c * fst p, snd p)) terms).
Proof.
  intros S c terms.
  induction terms as [| [d v] rest IH]; simpl.
  - apply (vscale_vzero S).
  - rewrite (vscale_distrib_vadd S), (vscale_compose S), IH. reflexivity.
Qed.

Lemma InSpan_vscale :
  forall (S : VSpace) (basis : list (carrier S)) (c : Q) (v : carrier S),
    InSpan S basis v -> InSpan S basis (vscale S c v).
Proof.
  intros S basis c v [terms [Hin Heq]].
  exists (map (fun p => (c * fst p, snd p)) terms).
  split.
  - intros p Hp. apply in_map_iff in Hp.
    destruct Hp as [[d u] [Heqp Hu]].
    simpl in Heqp. subst p. simpl. exact (Hin (d, u) Hu).
  - rewrite Heq. apply LinComb_scale.
Qed.

(* The key transport fact: if v is in the span of basis1, and every
   element of basis1 is itself in the span of basis2, then v is in the
   span of basis2. This is what lets step 1's (E0) coverage of Z1(P) by
   (pushforward of Z1(Q)) be re-expressed in terms of Z1(R), once step
   2's (E0) shows each of THOSE Z1(Q) elements is itself covered. *)
Theorem InSpan_transport :
  forall (S : VSpace) (basis1 basis2 : list (carrier S)),
    (forall b, In b basis1 -> InSpan S basis2 b) ->
    forall v, InSpan S basis1 v -> InSpan S basis2 v.
Proof.
  intros S basis1 basis2 Hsub v [terms [Hin Heq]].
  subst v.
  induction terms as [| [c b] rest IH].
  - simpl. apply InSpan_vzero.
  - simpl.
    assert (Hb : In b basis1) by (apply (Hin (c, b)); left; reflexivity).
    assert (Hrest : forall p, In p rest -> In (snd p) basis1)
      by (intros p Hp; apply Hin; right; exact Hp).
    apply InSpan_vadd.
    + apply InSpan_vscale. exact (Hsub b Hb).
    + exact (IH Hrest).
Qed.

(* ------------------------------------------------------------------ *)
(* Part 3: (E0) composes, using only Part 2 and each step's own (E0).  *)
(* ------------------------------------------------------------------ *)

Section E0Composes.

  Variables SP SQ SR : VSpace.

  (* Pullbacks (coarse-to-fine direction, as in refinement_checker.py's
     rho_star), and their transposes/pushforwards in the OPPOSITE
     direction (fine-to-coarse, as (E0) itself uses -- rho_push in
     refinement_checker.py is literally transpose(rho_star)). Both
     directions are given as separate maps here rather than derived from
     a single matrix and its transpose, since no matrix type is built in
     this file; the only property used below is that push_QP and
     push_RQ are each linear. *)
  Variable push_QP : carrier SQ -> carrier SP.
  Variable push_RQ : carrier SR -> carrier SQ.
  Hypothesis push_QP_linear : IsLinear SQ SP push_QP.
  Hypothesis push_RQ_linear : IsLinear SR SQ push_RQ.

  Variable Z1_P : list (carrier SP).
  Variable Z1_Q : list (carrier SQ).
  Variable Z1_R : list (carrier SR).

  (* Step 1's own (E0): every coarse cycle is in the span of the
     pushforward of Z1(Q). *)
  Hypothesis step1_E0 : forall z, In z Z1_P -> InSpan SP (map push_QP Z1_Q) z.

  (* Step 2's own (E0): every Q-level cycle is in the span of the
     pushforward of Z1(R). *)
  Hypothesis step2_E0 : forall z, In z Z1_Q -> InSpan SQ (map push_RQ Z1_R) z.

  Definition composite_push (z : carrier SR) : carrier SP := push_QP (push_RQ z).

  Theorem E0_composes :
    forall z, In z Z1_P -> InSpan SP (map composite_push Z1_R) z.
  Proof.
    intros z Hz.
    apply (InSpan_transport SP (map push_QP Z1_Q) (map composite_push Z1_R)).
    - intros b Hb.
      apply in_map_iff in Hb.
      destruct Hb as [q [Heqb Hq]].
      subst b.
      pose proof (linear_maps_preserve_span SQ SP push_QP push_QP_linear
                    (map push_RQ Z1_R) q (step2_E0 q Hq)) as Hpushed.
      rewrite (map_map push_RQ push_QP Z1_R) in Hpushed.
      exact Hpushed.
    - exact (step1_E0 z Hz).
  Qed.

End E0Composes.
