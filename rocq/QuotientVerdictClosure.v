(*
   QuotientVerdictClosure.v

   R20. A closure theorem, not a new mechanism: reproves R17's own
   conclusion (CommonSubdivisionVerdictInvariance.v's `common_
   subdivision_verdict_invariance`, "the transported residues are both
   repairable or neither is") via the R18-R19 quotient machinery
   (QuotientDescentReflection.v's `N0_E0_give_faithful_quotient_
   descent`) instead of the direct route
   (`common_subdivision_exactness_agreement`) R17 itself used.

   This is the "scoped class-level statement for a common subdivision"
   docs/design/QUOTIENT_DESCENT_AND_REFLECTION_SPEC.md's section 5
   named as the honest next target, not the stronger, unproved claim
   that would say the two full quotient spaces are isomorphic:

     rho1_1star r1 = rho2_1star r2   (the shared-transferred-residue
                                       hypothesis every theorem in this
                                       line already carries)
       gives, by mere reflexivity substitution,
     CobEquiv S1_12 delta12 (rho1_1star r1) (rho2_1star r2)
       -- "the two distinguished residues have equivalent transferred
          representatives in the common-subdivision coboundary
          quotient" -- and each leg's own faithful quotient descent
          (preservation from N0, reflection from E0) then transports
          that fact back down to
     CobEquiv S1_1 delta1 r1 (vzero S1_1)
       <-> CobEquiv S1_2 delta2 r2 (vzero S1_2),
   which unfolds, via CoboundaryQuotientLaws-derived vsub_zero_r, to
   exactly R17's own "(exists b1, r1 = delta1 b1) <-> (exists b2, r2 =
   delta2 b2)" -- the same conclusion, reached by a structurally
   different proof.

   WHAT THIS DOES ESTABLISH: that the two independently developed proof
   routes to verdict invariance -- R17's direct residue manipulation
   (built on CommonSubdivisionAgreement.v/ExactnessReflection.v) and
   R18-R19's abstract quotient formalism (built on
   QuotientDescentReflection.v) -- agree, for the same hypotheses, on
   the same conclusion. That agreement is a genuine, if modest,
   consistency finding: it was not assumed, it required a small proof
   (below), and it could in principle have failed to go through cleanly
   if the two formalisations were subtly inconsistent with each other.

   WHAT THIS DOES NOT ESTABLISH, stated precisely because "closure" is
   easy to over-read: this is not class-level invariance in the strong
   sense (an isomorphism, or even a stated correspondence, between the
   full quotients `C1_1/im(delta1)` and `C1_2/im(delta2)` as objects --
   only that one specific pair of residues, r1 and r2, lands in
   equivalent classes). It does not compare arbitrary elements of
   either quotient, only the two distinguished residues each theorem in
   this whole refinement-comparison line has always been about. It adds
   no new mechanism -- every step below is direct application of
   N0_E0_give_faithful_quotient_descent, once per leg, plus the zero-
   identity simplification CoboundaryQuotientLaws already supplies.

   No axioms, typeclasses, quotient constructions, adjunctions, or new
   morphism scaffold. No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import RefinementWitnessVerdictComposition.
Require Import QuotientDescentReflection.

Section Closure.

  Variables S0_1 S1_1 S0_2 S1_2 S0_12 S1_12 : VSpace.
  Variable delta1 : carrier S0_1 -> carrier S1_1.
  Variable delta2 : carrier S0_2 -> carrier S1_2.
  Variable delta12 : carrier S0_12 -> carrier S1_12.
  Variable rho1_0star : carrier S0_1 -> carrier S0_12.
  Variable rho1_1star : carrier S1_1 -> carrier S1_12.
  Variable rho2_0star : carrier S0_2 -> carrier S0_12.
  Variable rho2_1star : carrier S1_2 -> carrier S1_12.
  Variable r1 : carrier S1_1.
  Variable r2 : carrier S1_2.

  Theorem quotient_verdict_closure :
    N0 S0_1 S1_1 S0_12 S1_12 delta1 delta12 rho1_0star rho1_1star ->
    N0 S0_2 S1_2 S0_12 S1_12 delta2 delta12 rho2_0star rho2_1star ->
    E0 S0_1 S1_1 S0_12 S1_12 delta1 delta12 rho1_1star ->
    E0 S0_2 S1_2 S0_12 S1_12 delta2 delta12 rho2_1star ->
    IsLinear S1_1 S1_12 rho1_1star ->
    IsLinear S1_2 S1_12 rho2_1star ->
    CoboundaryQuotientLaws S1_1 -> CoboundaryQuotientLaws S1_2 -> CoboundaryQuotientLaws S1_12 ->
    rho1_1star r1 = rho2_1star r2 ->
    (CobEquiv S0_1 S1_1 delta1 r1 (vzero S1_1) <-> CobEquiv S0_2 S1_2 delta2 r2 (vzero S1_2)).
  Proof.
    intros HN0_1 HN0_2 HE0_1 HE0_2 Hlin1 Hlin2 Laws1 Laws2 Laws12 Hshared.
    destruct (N0_E0_give_faithful_quotient_descent S0_1 S1_1 S0_12 S1_12
                delta1 delta12 rho1_0star rho1_1star
                HN0_1 HE0_1 Laws1 Laws12 Hlin1) as [Preserve1 Reflect1].
    destruct (N0_E0_give_faithful_quotient_descent S0_2 S1_2 S0_12 S1_12
                delta2 delta12 rho2_0star rho2_1star
                HN0_2 HE0_2 Laws2 Laws12 Hlin2) as [Preserve2 Reflect2].
    split.
    - intro H1.
      apply Reflect2.
      assert (Hz2 : rho2_1star (vzero S1_2) = vzero S1_12).
      { destruct Hlin2 as [Hz2' _]. exact Hz2'. }
      rewrite Hz2, <- Hshared.
      assert (Hz1 : rho1_1star (vzero S1_1) = vzero S1_12).
      { destruct Hlin1 as [Hz1' _]. exact Hz1'. }
      rewrite <- Hz1.
      apply Preserve1.
      exact H1.
    - intro H2.
      apply Reflect1.
      assert (Hz1 : rho1_1star (vzero S1_1) = vzero S1_12).
      { destruct Hlin1 as [Hz1' _]. exact Hz1'. }
      rewrite Hz1, Hshared.
      assert (Hz2 : rho2_1star (vzero S1_2) = vzero S1_12).
      { destruct Hlin2 as [Hz2' _]. exact Hz2'. }
      rewrite <- Hz2.
      apply Preserve2.
      exact H2.
  Qed.

End Closure.
