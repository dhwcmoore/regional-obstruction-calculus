(*
   RefinementWitnessSequentialComposition.v

   Phase 4a: does binary refinement-witness composition (N0_composes,
   A4_composes, E0_composes, all proved in rocq/RefinementWitnessComposition
   .v and rocq/RefinementWitnessVerdictComposition.v) extend to three-step
   chains P -> Q -> R -> S? Yes, and each condition's three-step
   dependency profile is exactly the two-step profile applied once more
   -- not "safe chains compose" as one flat fact, three genuinely
   different profiles:

       N0_composes_three : needs ALL THREE steps' own N0.
       A4_composes_three : needs ONLY the LAST step's own A4, applied to
                            the fully-pushed-forward residue -- steps 1
                            and 2's own A4 are not hypotheses at all.
       E0_composes_three : needs ALL THREE steps' own E0, and (as in the
                            binary case) none of their N0.

   Each proof is a direct, self-contained restatement of the
   corresponding binary proof's technique (rewrite/unfold for N0 and A4;
   InSpan_transport applied twice for E0), not a black-box reapplication
   of the binary theorems -- reapplying them directly is possible but
   syntactically awkward here, since their conclusions are stated in
   terms of section-local `Definition`s (rho0_CR/rho1_CR/composite_push)
   that generalise along with every other section variable once the
   section closes. Restating directly is more robust and no more work,
   given how short each binary proof already was.

   Scope, stated precisely: this file proves three-step composition
   only, not composition of an arbitrary finite chain. Formalising a
   heterogeneous chain of arbitrarily many steps in Rocq needs dependent
   list/vector machinery (each step's codomain type must match the next
   step's domain type) that nothing in this project has built yet; that
   is left as explicit future work, not attempted here, rather than
   forced into a fragile construction. See "What this does not do" below.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import Coq.Lists.List.
Import ListNotations.
Require Import RefinementWitnessVerdictComposition.

(* ------------------------------------------------------------------ *)
(* Part 1: (N0) over three steps -- needs all three steps' own N0.     *)
(* ------------------------------------------------------------------ *)

Section N0ComposesThree.

  Variables C0_P C1_P C0_Q C1_Q C0_R C1_R C0_S C1_S : Type.
  Variable delta_P : C0_P -> C1_P.
  Variable delta_Q : C0_Q -> C1_Q.
  Variable delta_R : C0_R -> C1_R.
  Variable delta_S : C0_S -> C1_S.
  Variable rho0_PQ : C0_P -> C0_Q. Variable rho1_PQ : C1_P -> C1_Q.
  Variable rho0_QR : C0_Q -> C0_R. Variable rho1_QR : C1_Q -> C1_R.
  Variable rho0_RS : C0_R -> C0_S. Variable rho1_RS : C1_R -> C1_S.

  Hypothesis N0_1 : forall c, delta_Q (rho0_PQ c) = rho1_PQ (delta_P c).
  Hypothesis N0_2 : forall q, delta_R (rho0_QR q) = rho1_QR (delta_Q q).
  Hypothesis N0_3 : forall r, delta_S (rho0_RS r) = rho1_RS (delta_R r).

  Theorem N0_composes_three :
    forall c, delta_S (rho0_RS (rho0_QR (rho0_PQ c))) = rho1_RS (rho1_QR (rho1_PQ (delta_P c))).
  Proof.
    intro c.
    rewrite N0_3, N0_2, N0_1.
    reflexivity.
  Qed.

End N0ComposesThree.

(* ------------------------------------------------------------------ *)
(* Part 2: (A4) over three steps -- needs only the LAST step's own A4. *)
(* ------------------------------------------------------------------ *)

Section A4ComposesThree.

  Variables C1_P C1_Q C1_R C1_S : Type.
  Variable rho1_PQ : C1_P -> C1_Q.
  Variable rho1_QR : C1_Q -> C1_R.
  Variable rho1_RS : C1_R -> C1_S.
  Variable pairing_S : C1_S -> Q.
  Variable r : C1_P.

  (* The only hypothesis: the LAST step's own A4, stated against the
     residue it actually receives after two pushforwards. Steps 1 and 2's
     own A4 are not hypotheses of this theorem at all -- matching the
     binary case, where step 1's A4 was never needed either. *)
  Hypothesis step3_A4 : ~ (pairing_S (rho1_RS (rho1_QR (rho1_PQ r))) == 0).

  Theorem A4_composes_three :
    ~ (pairing_S (rho1_RS (rho1_QR (rho1_PQ r))) == 0).
  Proof. exact step3_A4. Qed.

End A4ComposesThree.

(* ------------------------------------------------------------------ *)
(* Part 3: (E0) over three steps -- needs all three steps' own E0, none *)
(* of their N0 (exactly the binary case's pattern, applied twice).      *)
(* ------------------------------------------------------------------ *)

Section E0ComposesThree.

  Variables SP SQ SR SS : VSpace.
  Variable push_QP : carrier SQ -> carrier SP.
  Variable push_RQ : carrier SR -> carrier SQ.
  Variable push_SR : carrier SS -> carrier SR.
  Hypothesis push_QP_linear : IsLinear SQ SP push_QP.
  Hypothesis push_RQ_linear : IsLinear SR SQ push_RQ.
  Hypothesis push_SR_linear : IsLinear SS SR push_SR.

  Variable Z1_P : list (carrier SP).
  Variable Z1_Q : list (carrier SQ).
  Variable Z1_R : list (carrier SR).
  Variable Z1_S : list (carrier SS).

  Hypothesis step1_E0 : forall z, In z Z1_P -> InSpan SP (map push_QP Z1_Q) z.
  Hypothesis step2_E0 : forall z, In z Z1_Q -> InSpan SQ (map push_RQ Z1_R) z.
  Hypothesis step3_E0 : forall z, In z Z1_R -> InSpan SR (map push_SR Z1_S) z.

  Definition composite_push_three (z : carrier SS) : carrier SP :=
    push_QP (push_RQ (push_SR z)).

  Theorem E0_composes_three :
    forall z, In z Z1_P -> InSpan SP (map composite_push_three Z1_S) z.
  Proof.
    intros z Hz.
    (* Step A: combine steps 2 and 3, exactly as the binary E0_composes
       proof combines its two hypotheses, to get Z1_Q covered by the
       span of the twice-pushed-forward Z1_S. *)
    assert (Hstep23 : forall q, In q Z1_Q ->
              InSpan SQ (map (fun s => push_RQ (push_SR s)) Z1_S) q).
    { intros q Hq.
      apply (InSpan_transport SQ (map push_RQ Z1_R)
               (map (fun s => push_RQ (push_SR s)) Z1_S)).
      - intros b Hb.
        apply in_map_iff in Hb.
        destruct Hb as [rr [Heqb Hrr]].
        subst b.
        pose proof (linear_maps_preserve_span SR SQ push_RQ push_RQ_linear
                      (map push_SR Z1_S) rr (step3_E0 rr Hrr)) as Hpushed.
        rewrite (map_map push_SR push_RQ Z1_S) in Hpushed.
        exact Hpushed.
      - exact (step2_E0 q Hq). }
    (* Step B: combine step 1 with the derived fact from step A, exactly
       the same way, to reach Z1_P covered by the thrice-pushed-forward
       Z1_S. *)
    apply (InSpan_transport SP (map push_QP Z1_Q) (map composite_push_three Z1_S)).
    - intros b Hb.
      apply in_map_iff in Hb.
      destruct Hb as [q [Heqb Hq]].
      subst b.
      pose proof (linear_maps_preserve_span SQ SP push_QP push_QP_linear
                    (map (fun s => push_RQ (push_SR s)) Z1_S) q (Hstep23 q Hq)) as Hpushed.
      unfold composite_push_three.
      rewrite (map_map (fun s => push_RQ (push_SR s)) push_QP Z1_S) in Hpushed.
      exact Hpushed.
    - exact (step1_E0 z Hz).
  Qed.

End E0ComposesThree.

(* ------------------------------------------------------------------ *)
(* What this does not do                                                *)
(* ------------------------------------------------------------------ *)

(*
   - Does not prove composition for chains of arbitrary finite length --
     only exactly three steps. A general n-step theorem needs dependent
     list/vector machinery not built anywhere in this project; whether
     the pattern above ("apply the relevant lemma once per additional
     step") continues to hold for n > 3 is expected but not checked here.
   - Does not address a different formalisation of "the composite
     witness" than the one used throughout this file and its binary
     predecessors (reuse the same declared cycle/pairing at the final
     step; compose pullbacks by function composition).
   - Does not address sequential composition of heterogeneous
     transformation types (refine, restrict, merge, ...) -- only
     iterated refinement witnesses of the same kind, matching the scope
     of rocq/RefinementWitnessComposition.v and rocq/
     RefinementWitnessVerdictComposition.v.
*)
