(*
   QuotientDescentReflection.v

   R18-R19. docs/design/QUOTIENT_DESCENT_AND_REFLECTION_SPEC.md answers
   this file's own governing question -- under (N0), does residue
   transport descend to equivalence classes modulo coboundaries, and is
   (E0) precisely the condition that the descended map is faithful --
   and states, checked by an actual (uncommitted) compiling prototype
   before any tracked code was written, exactly which hypotheses each
   piece needs. This file is that tracked, `coqchk`-checked proof.

   ARCHITECTURE, kept deliberately visible rather than folded into one
   theorem: a refinement map's obligations split into two independent
   logical functions on the coboundary-equivalence relation `~`
   (`r ~ s` iff `r - s` is a coboundary):

     (N0)  =  PRESERVATION of `~`  (forward: `r ~ s` implies the
              transferred residues are `~'`-related)
     (E0)  =  REFLECTION of `~`    (backward: transferred `~'`-related
              implies the originals were `~`-related)
     (N0) and (E0) together  =  FAITHFUL quotient descent.

   This mirrors, at the quotient level, exactly the same split
   CommonSubdivisionVerdictInvariance.v (R17) already made at the
   verdict level -- N0 transports exactness forward, E0 transports it
   backward. R18-R19 is not that theorem re-proved with equivalence
   classes; it needs strictly more structure (linearity of the
   refinement map) than R17 required of an arbitrary function, and it
   answers a different question (what N0/E0 mean algebraically, not
   what a particular pair of residues' verdicts are). See
   PRESENTATION_INVARIANCE_SPEC.md's own caution against presenting
   R17 and this file as one strengthening ladder -- they are not.

   WHY A NEW RECORD, NOT AN ENLARGED VSpace: RefinementWitnessVerdict
   Composition.v's `VSpace` was built as the minimum structure its own
   span-transport proofs needed -- addition and scaling, never
   subtraction or a scalar identity. Adding vadd_comm/an additive-
   inverse law/scalar identity directly to that record would silently
   strengthen every existing `VSpace` parameter in that file and every
   file built on it, including ones whose own theorems do not need the
   extra structure. `CoboundaryQuotientLaws` below is a separate,
   parallel extension record, applied only where this file's own
   theorems actually need it. It is deliberately not named `FullVSpace`
   -- even with these three additional laws it still falls short of a
   textbook rational vector space axiomatisation (no full distributivity
   over a scalar sum is stated, for instance, only what these proofs
   use); it is exactly the additional structure the coboundary quotient
   argument needs, no more.

   HYPOTHESIS MINIMALITY, checked per theorem by the same prototype,
   not assumed:
     - CobEquiv_equivalence_source needs CoboundaryQuotientLaws S1 and
       IsLinear S0 S1 delta0. Nothing about S1', delta0', rho0star, or
       rho1star.
     - CobEquiv_equivalence_target is the mirror image on the primed
       side -- CoboundaryQuotientLaws S1' and IsLinear S0' S1' delta0'.
     - quotient_descent needs ONLY (N0) and IsLinear S1 S1' rho1star --
       sharper than first suspected while writing the design document:
       it needs neither CoboundaryQuotientLaws on either side, nor
       delta0/delta0' linearity, nor rho0star linearity. The witness
       for the transferred equivalence is exhibited directly
       (`rho0star b`); no subtraction is ever performed on the target
       side.
     - E0_iff_reflects_CobEquiv needs IsLinear S1 S1' rho1star and
       CoboundaryQuotientLaws on BOTH S1 and S1' (the reverse direction
       needs each side's own zero-identity law) -- and, exactly as
       docs/design/QUOTIENT_DESCENT_AND_REFLECTION_SPEC.md's section 3
       specifies, does NOT need (N0) at all.
     - N0_E0_give_faithful_quotient_descent needs everything above
       combined: (N0), (E0), IsLinear S1 S1' rho1star, and
       CoboundaryQuotientLaws on both S1 and S1'.

   No axioms, no typeclasses (deliberately: Coq.Classes.RelationClasses
   .Equivalence is available and would be the "expected" way to state
   "this is an equivalence relation," but no other file in this
   refinement-comparison line uses typeclasses anywhere, and reaching
   for one here for the first time, only for stylistic uniformity, is
   exactly the kind of unnecessary generality docs/design/
   PRESENTATION_INVARIANCE_SPEC.md's section 0 warns against). No
   quotient type or setoid construction -- N0_E0_give_faithful_
   quotient_descent packages preservation and reflection as a plain
   conjunction of two `Prop`s rather than committing to an induced
   quotient map's own type, exactly the lighter of the two
   formulations the design document's section 4 named as sufficient
   for "the exact mathematics" without extra machinery.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import RefinementWitnessVerdictComposition.

(* ------------------------------------------------------------------ *)
(* The extension record: exactly the three laws
   docs/design/QUOTIENT_DESCENT_AND_REFLECTION_SPEC.md's section 1
   found missing from VSpace, confirmed by trying (and failing) to
   prove subtraction facts without them. Every concrete instance these
   theorems will ever run against (finite-dimensional Q^n under
   componentwise operations) satisfies all three for free.            *)
(* ------------------------------------------------------------------ *)

Record CoboundaryQuotientLaws (S : VSpace) := mkCoboundaryQuotientLaws {
  quotient_vadd_comm :
    forall a b : carrier S, vadd S a b = vadd S b a;
  quotient_vadd_inv :
    forall a : carrier S, vadd S a (vscale S (-1) a) = vzero S;
  quotient_vscale_one :
    forall a : carrier S, vscale S 1 a = a;
}.

(* ------------------------------------------------------------------ *)
(* Algebraic foundation: subtraction and its properties, for any one
   VSpace equipped with CoboundaryQuotientLaws. Kept generic (not tied
   to S1/S1' by name) so CobEquiv_equivalence_source and _target below
   can both instantiate it, rather than duplicating the same five
   lemmas twice under different names.                                *)
(* ------------------------------------------------------------------ *)

Section CoboundaryAlgebra.

  Variable S : VSpace.
  Variable Laws : CoboundaryQuotientLaws S.

  Definition vsub (a b : carrier S) : carrier S :=
    vadd S a (vscale S (-1)%Q b).

  Lemma vadd_zero_r : forall a : carrier S, vadd S a (vzero S) = a.
  Proof.
    intros a. rewrite (quotient_vadd_comm S Laws a (vzero S)).
    apply (vadd_zero_l S).
  Qed.

  Lemma vsub_self : forall a : carrier S, vsub a a = vzero S.
  Proof. intros a. unfold vsub. exact (quotient_vadd_inv S Laws a). Qed.

  Lemma vsub_zero_r : forall a : carrier S, vsub a (vzero S) = a.
  Proof. intros a. unfold vsub. rewrite (vscale_vzero S). apply vadd_zero_r. Qed.

  Lemma vsub_antisym : forall a b : carrier S, vscale S (-1) (vsub a b) = vsub b a.
  Proof.
    intros a b. unfold vsub.
    rewrite (vscale_distrib_vadd S).
    rewrite (vscale_compose S).
    replace (-1 * -1)%Q with 1%Q by reflexivity.
    rewrite (quotient_vscale_one S Laws b).
    rewrite (quotient_vadd_comm S Laws (vscale S (-1) a) b).
    reflexivity.
  Qed.

  Lemma vsub_add : forall a b c : carrier S, vadd S (vsub a b) (vsub b c) = vsub a c.
  Proof.
    intros a b c. unfold vsub.
    rewrite (vadd_assoc S).
    rewrite <- (vadd_assoc S (vscale S (-1) b) b (vscale S (-1) c)).
    rewrite (quotient_vadd_comm S Laws (vscale S (-1) b) b).
    rewrite (quotient_vadd_inv S Laws b).
    rewrite (vadd_zero_l S).
    reflexivity.
  Qed.

End CoboundaryAlgebra.

(* ------------------------------------------------------------------ *)
(* Image and CobEquiv: fully generic, no CoboundaryQuotientLaws needed
   to state either -- only to prove CobEquiv is an equivalence
   relation, below.                                                    *)
(* ------------------------------------------------------------------ *)

Definition Image (SA SB : VSpace) (f : carrier SA -> carrier SB) (v : carrier SB) : Prop :=
  exists u, f u = v.

Definition CobEquiv (S0 S1 : VSpace) (d : carrier S0 -> carrier S1) (r s : carrier S1) : Prop :=
  Image S0 S1 d (vsub S1 r s).

(* ------------------------------------------------------------------ *)
(* R18a: CobEquiv is an equivalence relation, generically over any one
   VSpace pair and coboundary map -- instantiated twice below, once
   per side, rather than proved twice.                                 *)
(* ------------------------------------------------------------------ *)

Section CobEquivIsEquivalence.

  Variables S0 S1 : VSpace.
  Variable Laws1 : CoboundaryQuotientLaws S1.
  Variable d : carrier S0 -> carrier S1.
  Hypothesis d_linear : IsLinear S0 S1 d.

  Theorem CobEquiv_reflexive : forall r : carrier S1, CobEquiv S0 S1 d r r.
  Proof.
    intros r. exists (vzero S0).
    destruct d_linear as [Hz _].
    rewrite Hz. symmetry. exact (vsub_self S1 Laws1 r).
  Qed.

  Theorem CobEquiv_symmetric :
    forall r s : carrier S1, CobEquiv S0 S1 d r s -> CobEquiv S0 S1 d s r.
  Proof.
    intros r s [b Hb]. exists (vscale S0 (-1) b).
    destruct d_linear as [_ [_ Hsc]].
    rewrite Hsc, Hb.
    apply vsub_antisym. exact Laws1.
  Qed.

  Theorem CobEquiv_transitive :
    forall r s t : carrier S1,
      CobEquiv S0 S1 d r s -> CobEquiv S0 S1 d s t -> CobEquiv S0 S1 d r t.
  Proof.
    intros r s t [b1 Hb1] [b2 Hb2]. exists (vadd S0 b1 b2).
    destruct d_linear as [_ [Ha _]].
    rewrite Ha, Hb1, Hb2.
    apply vsub_add. exact Laws1.
  Qed.

End CobEquivIsEquivalence.

(* ------------------------------------------------------------------ *)
(* The running example this whole file is about: two presentations,
   S0/S1 and S0'/S1', and a refinement map between them.                *)
(* ------------------------------------------------------------------ *)

Section Refinement.

  Variables S0 S1 S0' S1' : VSpace.
  Variable delta0 : carrier S0 -> carrier S1.
  Variable delta0' : carrier S0' -> carrier S1'.
  Variable rho0star : carrier S0 -> carrier S0'.
  Variable rho1star : carrier S1 -> carrier S1'.

  (* R18a instantiated on each side -- see the section above; nothing
     new proved here, only named for this running example. *)

  Definition CobEquiv_equivalence_source
    (Laws1 : CoboundaryQuotientLaws S1) (delta0_linear : IsLinear S0 S1 delta0) :
    (forall r, CobEquiv S0 S1 delta0 r r)
    /\ (forall r s, CobEquiv S0 S1 delta0 r s -> CobEquiv S0 S1 delta0 s r)
    /\ (forall r s t, CobEquiv S0 S1 delta0 r s -> CobEquiv S0 S1 delta0 s t -> CobEquiv S0 S1 delta0 r t)
    := conj (CobEquiv_reflexive S0 S1 Laws1 delta0 delta0_linear)
       (conj (CobEquiv_symmetric S0 S1 Laws1 delta0 delta0_linear)
             (CobEquiv_transitive S0 S1 Laws1 delta0 delta0_linear)).

  Definition CobEquiv_equivalence_target
    (Laws1' : CoboundaryQuotientLaws S1') (delta0'_linear : IsLinear S0' S1' delta0') :
    (forall r, CobEquiv S0' S1' delta0' r r)
    /\ (forall r s, CobEquiv S0' S1' delta0' r s -> CobEquiv S0' S1' delta0' s r)
    /\ (forall r s t, CobEquiv S0' S1' delta0' r s -> CobEquiv S0' S1' delta0' s t -> CobEquiv S0' S1' delta0' r t)
    := conj (CobEquiv_reflexive S0' S1' Laws1' delta0' delta0'_linear)
       (conj (CobEquiv_symmetric S0' S1' Laws1' delta0' delta0'_linear)
             (CobEquiv_transitive S0' S1' Laws1' delta0' delta0'_linear)).

  (* --- N0 and E0, named locally for this file's own convenience since
     both are referenced by more than one theorem below. Stated
     identically, in mathematical content, to how CochainNaturalityDescent
     .v and ExactnessReflection.v state them inline everywhere else in
     this repository -- these are not new conditions. --------------- *)

  Definition N0 : Prop :=
    forall b : carrier S0, rho1star (delta0 b) = delta0' (rho0star b).

  Definition E0 : Prop :=
    forall x : carrier S1,
      (exists b' : carrier S0', rho1star x = delta0' b') ->
      exists b : carrier S0, x = delta0 b.

  (* --- R18b: quotient descent = preservation of CobEquiv. --------- *)

  Definition PreservesCobEquiv : Prop :=
    forall r s : carrier S1,
      CobEquiv S0 S1 delta0 r s -> CobEquiv S0' S1' delta0' (rho1star r) (rho1star s).

  Theorem quotient_descent :
    N0 -> IsLinear S1 S1' rho1star -> PreservesCobEquiv.
  Proof.
    intros HN0 Hrho1_linear r s [b Hb]. exists (rho0star b).
    rewrite <- (HN0 b).
    destruct Hrho1_linear as [_ [Ha Hsc]].
    unfold vsub in Hb |- *.
    rewrite Hb, Ha, Hsc.
    reflexivity.
  Qed.

  (* --- R19a: E0 iff reflection of CobEquiv. No (N0) anywhere in this
     theorem's hypotheses or its proof. ------------------------------ *)

  Definition ReflectsCobEquiv : Prop :=
    forall r s : carrier S1,
      CobEquiv S0' S1' delta0' (rho1star r) (rho1star s) -> CobEquiv S0 S1 delta0 r s.

  Theorem E0_iff_reflects_CobEquiv :
    CoboundaryQuotientLaws S1 -> CoboundaryQuotientLaws S1' ->
    IsLinear S1 S1' rho1star ->
    (E0 <-> ReflectsCobEquiv).
  Proof.
    intros Laws1 Laws1' Hrho1_linear.
    split.
    - intros HE0 r s [b' Hb'].
      assert (Hx : rho1star (vsub S1 r s) = delta0' b').
      { destruct Hrho1_linear as [_ [Ha Hsc]].
        unfold vsub. rewrite Ha, Hsc. unfold vsub in Hb'. symmetry. exact Hb'. }
      destruct (HE0 (vsub S1 r s) (ex_intro _ b' Hx)) as [b Hb].
      exists b. symmetry. exact Hb.
    - intros Hrefl x [b' Hb'].
      assert (Hshift : CobEquiv S0' S1' delta0' (rho1star x) (rho1star (vzero S1))).
      { exists b'.
        destruct Hrho1_linear as [Hz _].
        rewrite Hz.
        rewrite (vsub_zero_r S1' Laws1').
        symmetry. exact Hb'. }
      destruct (Hrefl x (vzero S1) Hshift) as [b Hb].
      exists b.
      rewrite <- (vsub_zero_r S1 Laws1 x).
      symmetry. exact Hb.
  Qed.

  (* --- R19b: (N0) and (E0) together give faithful quotient descent --
     the exact packaging docs/design/QUOTIENT_DESCENT_AND_REFLECTION_
     SPEC.md's section 4 recommended: a plain conjunction of the two
     `Prop`s above, not a committed quotient-map type. --------------- *)

  Theorem N0_E0_give_faithful_quotient_descent :
    N0 -> E0 ->
    CoboundaryQuotientLaws S1 -> CoboundaryQuotientLaws S1' ->
    IsLinear S1 S1' rho1star ->
    PreservesCobEquiv /\ ReflectsCobEquiv.
  Proof.
    intros HN0 HE0 Laws1 Laws1' Hrho1_linear.
    split.
    - exact (quotient_descent HN0 Hrho1_linear).
    - exact (proj1 (E0_iff_reflects_CobEquiv Laws1 Laws1' Hrho1_linear) HE0).
  Qed.

End Refinement.
