(*
   CycleQuotientDuality.v

   R22, layer 1, headline result: the abstract cycle-quotient duality
   theorem `docs/design/CYCLE_QUOTIENT_DUALITY_SPEC.md` named D4
   (certificate completeness) --

     r in B  <->  every annihilator functional of B vanishes at r

   -- i.e. membership in B is completely determined by evaluation
   against B's own annihilator space (B^perp in the design document's
   notation), not merely witnessed by one separator when r is outside B.
   This is the abstract content behind calling a separator "the complete
   dual description of the obstruction quotient," not just one convenient
   witness R21 happens to produce.

   Combines AbstractSeparation.v's SeparatesOutside/Annihilator with
   QuotientEvaluation.v's eval_injective (specialised to r2 := vzero,
   where SameClass B r vzero literally reduces to B r).

   WHAT THIS FILE DOES NOT CLAIM: the R22 proposal's item 4 -- "finite-
   dimensionality plus matching dimensions gives the isomorphism
   C1/B ~= (B^perp)*" -- is NOT proved here. That needs a basis/dimension
   theory this repository does not have (`docs/design/
   CYCLE_QUOTIENT_DUALITY_SPEC.md` Route B, flagged there as the highest-
   risk route, "a real precedent for stalling out unfinished," the same
   shape of expansion that produced the archived four-condition
   scaffold). This file proves exactly, and only, the completeness
   theorem (D4): membership is determined by the annihilator space. That
   is the concrete, checked content "duality" cashes out to at this
   layer, not a claim that the vector-space isomorphism itself has been
   built.

   Depends on AbstractSeparation.v and QuotientEvaluation.v.
*)

Require Import Coq.QArith.QArith.
Require Import AbstractSeparation.
Require Import QuotientEvaluation.

Theorem membership_iff_all_annihilate :
  forall (S : AbelianVSpace) (B : carrier S -> Prop),
    (forall x, B x \/ ~ B x) ->
    SeparatesOutside S B ->
    forall r : carrier S,
      B r <-> (forall phi, IsLinearFunctional S phi -> Annihilator S B phi -> phi r == 0).
Proof.
  intros S B Hdec Hsep r.
  split.
  - intros Hr phi Hlin Hann. apply (Hann r Hr).
  - intros Hall.
    assert (Hagree : forall phi, IsLinearFunctional S phi -> Annihilator S B phi -> phi r == phi vzero).
    {
      intros phi Hlin Hann.
      rewrite (Hall phi Hlin Hann).
      destruct Hlin as [Hzero _].
      symmetry. exact Hzero.
    }
    assert (Hsc := eval_injective S B Hdec Hsep r vzero Hagree).
    unfold SameClass, vsub in Hsc.
    rewrite (vneg_is_scale_neg_one S vzero) in Hsc.
    rewrite (vscale_vzero S (-1)) in Hsc.
    rewrite (vadd_zero_r S r) in Hsc.
    exact Hsc.
Qed.

(* The forward, "certificate is sufficient" direction restated in the
   design document's own SeparatesOutside vocabulary directly: a residue
   outside B is detected, exactly, by some element of B's own annihilator
   space -- D4's forward direction, immediate from SeparatesOutside
   itself, included here for the headline statement to be self-contained
   without needing to unfold SeparatesOutside by hand. *)
Corollary not_in_B_iff_detected :
  forall (S : AbelianVSpace) (B : carrier S -> Prop),
    (forall x, B x \/ ~ B x) ->
    SeparatesOutside S B ->
    forall r : carrier S,
      ~ B r <-> (exists phi, IsLinearFunctional S phi /\ Annihilator S B phi /\ ~ (phi r == 0)).
Proof.
  intros S B Hdec Hsep r.
  split.
  - intro Hout. apply (Hsep r Hout).
  - intros [phi [Hlin [Hann Hne]]] Hr.
    apply Hne, (Hann r Hr).
Qed.
