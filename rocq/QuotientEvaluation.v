(*
   QuotientEvaluation.v

   R22, layer 1 continued: evaluation of annihilator functionals on
   cosets of a subspace B, over an AbstractSeparation.AbelianVSpace.
   Proves the three items `docs/design/CYCLE_QUOTIENT_DUALITY_SPEC.md`
   scoped as needed before cycle-quotient duality: evaluation on cosets
   is well-defined, is linear, and -- the one AbstractSeparation.v's own
   header predicted would need real additive-inverse structure, now
   confirmed by an actual proof, not merely argued for -- is injective
   under SeparatesOutside.

   Deliberately does NOT construct a literal quotient type (no setoid,
   no quotient/equivalence-class type former): matching this repository's
   own established practice on the same question
   (`QuotientDescentReflection.v`'s R18-19 entry: "No typeclasses, no
   quotient/setoid construction"), "evaluation on the quotient C1/B" is
   represented here as evaluation on REPRESENTATIVES that agrees whenever
   two representatives land in the same coset (SameClass below) -- the
   standard way to reason about a quotient's structure without building
   the quotient type itself.

   Depends only on AbstractSeparation.v.
*)

Require Import Coq.QArith.QArith.
Require Import AbstractSeparation.

(* ------------------------------------------------------------------ *)
(* B as a genuine subspace predicate: contains vzero, closed under
   vadd and vscale. Needed for SameClass to be an equivalence relation
   (without it, "differs by an element of B" need not even be
   reflexive: r SameClass r needs B vzero). *)
(* ------------------------------------------------------------------ *)

Definition IsSubspace (S : AbelianVSpace) (B : carrier S -> Prop) : Prop :=
  B vzero /\
  (forall a b, B a -> B b -> B (vadd a b)) /\
  (forall (c : Q) (a : carrier S), B a -> B (vscale c a)).

Lemma subspace_closed_neg :
  forall (S : AbelianVSpace) (B : carrier S -> Prop),
    IsSubspace S B -> forall a, B a -> B (vneg a).
Proof.
  intros S B [_ [_ Hscale]] a Ha.
  rewrite (vneg_is_scale_neg_one S a).
  apply Hscale, Ha.
Qed.

(* ------------------------------------------------------------------ *)
(* SameClass: r1 and r2 land in the same coset of B, i.e. r1 - r2 in B.
   Stated via vsub, which AbstractSeparation.v supplies precisely
   because AbelianVSpace (unlike this repository's existing minimal
   VSpace) has vneg. *)
(* ------------------------------------------------------------------ *)

Definition SameClass (S : AbelianVSpace) (B : carrier S -> Prop) (r1 r2 : carrier S) : Prop :=
  B (vsub S r1 r2).

Lemma sameclass_refl :
  forall (S : AbelianVSpace) (B : carrier S -> Prop), IsSubspace S B ->
    forall r, SameClass S B r r.
Proof.
  intros S B [Hzero _] r. unfold SameClass. rewrite vsub_self. exact Hzero.
Qed.

Lemma sameclass_sym :
  forall (S : AbelianVSpace) (B : carrier S -> Prop), IsSubspace S B ->
    forall r1 r2, SameClass S B r1 r2 -> SameClass S B r2 r1.
Proof.
  intros S B Hsub r1 r2 H. unfold SameClass in *.
  assert (Hneg := subspace_closed_neg S B Hsub _ H).
  unfold vsub in Hneg |- *.
  assert (Heq : vneg (vadd r1 (vneg r2)) = vadd r2 (vneg r1)).
  {
    (* vneg (a + b) = vneg b + vneg a = vneg a + vneg b (comm) for an
       abelian group; derived here via the vadd_inverse_unique argument
       already available: both sides added to (vadd r1 (vneg r2)) give
       vzero. *)
    apply (vadd_inverse_unique S (vadd r1 (vneg r2))).
    - apply vadd_vneg.
    - rewrite <- (vadd_assoc S (vadd r1 (vneg r2)) r2 (vneg r1)).
      rewrite (vadd_assoc S r1 (vneg r2) r2).
      rewrite (vadd_comm S (vneg r2) r2).
      rewrite (vadd_vneg S r2).
      rewrite (vadd_zero_r S r1).
      apply vadd_vneg.
  }
  rewrite <- Heq. exact Hneg.
Qed.

Lemma sameclass_trans :
  forall (S : AbelianVSpace) (B : carrier S -> Prop), IsSubspace S B ->
    forall r1 r2 r3, SameClass S B r1 r2 -> SameClass S B r2 r3 -> SameClass S B r1 r3.
Proof.
  intros S B [_ [Hadd _]] r1 r2 r3 H12 H23.
  unfold SameClass, vsub in *.
  assert (Hsum := Hadd _ _ H12 H23).
  assert (Heq : vadd (vadd r1 (vneg r2)) (vadd r2 (vneg r3)) = vadd r1 (vneg r3)).
  {
    rewrite (vadd_assoc S r1 (vneg r2) (vadd r2 (vneg r3))).
    rewrite <- (vadd_assoc S (vneg r2) r2 (vneg r3)).
    rewrite (vadd_comm S (vneg r2) r2).
    rewrite (vadd_vneg S r2).
    rewrite (vadd_zero_l S (vneg r3)).
    reflexivity.
  }
  rewrite <- Heq. exact Hsum.
Qed.

(* ------------------------------------------------------------------ *)
(* Evaluation on cosets: well-defined, linear (both automatic from
   IsLinearFunctional/Annihilator alone), and -- the substantive new
   result -- injective under SeparatesOutside. *)
(* ------------------------------------------------------------------ *)

Theorem eval_well_defined :
  forall (S : AbelianVSpace) (B : carrier S -> Prop) (phi : carrier S -> Q),
    IsLinearFunctional S phi -> Annihilator S B phi ->
    forall r1 r2, SameClass S B r1 r2 -> phi r1 == phi r2.
Proof.
  intros S B phi Hlin Hann r1 r2 Hsc.
  unfold SameClass in Hsc.
  assert (Hval := linear_functional_vsub S phi r1 r2 Hlin).
  assert (Hzero := Hann _ Hsc).
  rewrite Hzero in Hval.
  (* Hval : 0 == phi r1 - phi r2; conclude phi r1 == phi r2 by field algebra. *)
  setoid_replace (phi r1) with ((phi r1 - phi r2) + phi r2) by ring.
  rewrite <- Hval.
  ring.
Qed.

(* Evaluation is additive and homogeneous in r, for any fixed annihilator
   functional phi -- immediate from phi's own linearity, stated here for
   completeness of the "evaluation map is linear" claim. *)
Theorem eval_additive :
  forall (S : AbelianVSpace) (phi : carrier S -> Q),
    IsLinearFunctional S phi ->
    forall r1 r2, phi (vadd r1 r2) == phi r1 + phi r2.
Proof. intros S phi [_ [Hadd _]] r1 r2. apply Hadd. Qed.

Theorem eval_homogeneous :
  forall (S : AbelianVSpace) (phi : carrier S -> Q),
    IsLinearFunctional S phi ->
    forall (c : Q) (r : carrier S), phi (vscale c r) == c * phi r.
Proof. intros S phi [_ [_ Hscale]] c r. apply Hscale. Qed.

(* The substantive result: SeparatesOutside makes evaluation injective on
   cosets -- confirmed provable once AbelianVSpace supplies vneg,
   resolving exactly the gap AbstractSeparation.v's header predicted.

   Needs B decidable (an explicit HYPOTHESIS here, not a standing
   Classical axiom -- kept local so this file adds no project-wide
   axiom, matching every other file's "Closed under the global context"
   record): for an arbitrary Prop-valued B with no further structure,
   going from "no phi separates r1, r2" to "B (vsub r1 r2) holds" is a
   double-negation-elimination step (Hout : ~ B x used to derive False,
   concluding B x), which is not available intuitionistically for a
   fully general B. R21's own concrete B = im D is decidable (finite
   exact-rational elimination decides membership), so this hypothesis
   costs nothing once RationalSeparationInstance.v supplies it -- it is
   not a hypothetical gap, just one this abstract layer states honestly
   rather than paper over with a global excluded-middle axiom. *)
Theorem eval_injective :
  forall (S : AbelianVSpace) (B : carrier S -> Prop),
    (forall x, B x \/ ~ B x) ->
    SeparatesOutside S B ->
    forall r1 r2 : carrier S,
      (forall phi, IsLinearFunctional S phi -> Annihilator S B phi -> phi r1 == phi r2) ->
      SameClass S B r1 r2.
Proof.
  intros S B Hdec Hsep r1 r2 Hagree.
  unfold SameClass.
  destruct (Hdec (vsub S r1 r2)) as [Hin | Hout].
  - exact Hin.
  - exfalso.
    destruct (Hsep (vsub S r1 r2) Hout) as [phi [Hlin [Hann Hne]]].
    apply Hne.
    assert (Hval := linear_functional_vsub S phi r1 r2 Hlin).
    assert (Heq := Hagree phi Hlin Hann).
    rewrite Hval.
    rewrite Heq.
    ring.
Qed.
