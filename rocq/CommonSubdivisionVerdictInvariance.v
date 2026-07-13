(*
   CommonSubdivisionVerdictInvariance.v

   R17. Combines CommonSubdivisionAgreement.v's obstruction-present half
   and ExactnessReflection.v's obstruction-absent half into a single,
   unconditional theorem: for two coarse presentations sharing a common
   subdivision through refinement maps that are both descent-safe (N0)
   and reflecting (E0) -- exactly refinement_checker.py's `verdict_safe`
   -- the obstruction verdict of one presentation determines the
   obstruction verdict of the other. This is the first theorem in this
   repository that deserves to be called presentation invariance, even
   though its proof is short.

   No new primitive hypotheses or local preservation mechanisms are
   introduced. Both halves being combined were already proved,
   independently, before this file existed; the contribution here is
   the first formal assembly of those existing preservation and
   reflection results into a single verdict-invariance theorem, not a
   new proof technique. The paper's own remark on the two halves
   (`paper/associator_fields_ACS_revised.tex`, "Result ladder, and what
   remains open") states explicitly that this assembly had not been
   done: "this paper does not, however, assemble that into a single
   combined verdict-equivalence theorem covering both directions at
   once, and no such combined theorem is claimed."

   HOW THE COMBINATION ACTUALLY WORKS, PRECISELY:

   The theorem below, `common_subdivision_verdict_invariance`, is
   proved using only (N0) and (E0) for both refinement legs, applied
   symmetrically -- it does NOT invoke CommonSubdivisionAgreement.v's
   `common_subdivision_certificate_agreement` inside its own proof term,
   even though that file is `Require Import`-ed below and its theorem
   remains fully available under its own name. This is a deliberate
   scoping decision, not an oversight, and is worth stating precisely
   because a less careful assembly could have gotten this wrong:

   `common_subdivision_certificate_agreement` proves non-exactness of
   both `r1` and `r2` GIVEN an explicit witnessing cycle `z12` with
   non-zero pairing against the shared transferred residue -- that
   witness is an extra, freely supplied hypothesis, not something
   derived from (N0) and (E0) alone. Turning that theorem into an
   unconditional "`r1` non-exact implies `r2` non-exact" step would
   require an additional fact this repository does not prove anywhere:
   that non-exactness of a residue always comes with such an explicit
   cycle-pairing witness (a finite-dimensional duality/completeness
   statement -- the image of a coboundary map is the annihilator of the
   cycle space, so this is very likely true, but "very likely true" is
   exactly the standard PRESENTATION_INVARIANCE_SPEC.md section 4.4
   already refused to assume for the analogous E0-versus-quotient-
   injectivity question). Assuming it silently here would repeat that
   exact mistake in the opposite direction. See that document's section
   1.4 and 4.4 for the full discussion; this file does not resolve the
   open question, only avoids depending on an unproved answer to it.

   What does close the whole argument, unconditionally, is (E0) alone,
   applied twice, together with one small, previously-unnamed
   consequence of (N0): CochainNaturalityDescent.v's own header already
   states, in prose, that "(N0) ... [pushes] a coarse exactness witness
   `b` forward along the vertex-level pullback `rho0_star` [landing] on
   a refined exactness witness for the transferred residue" -- this is
   (N0)'s forward direction, used inline inside that file's own proof
   but never extracted as its own lemma (PRESENTATION_INVARIANCE_SPEC.md
   section 1.2 names this "packaging work, not new mathematics"). It is
   named `naturality_descent_exact` below, kept local to this file
   rather than added to CochainNaturalityDescent.v itself, so that this
   purely-synthesis file is the only new surface touched by R17.

   `common_subdivision_certificate_agreement` remains genuinely useful
   on its own: for the real four-cycle witness data, the shared
   transferred residue is actually obstructed, not exact (a fact
   ExactnessReflection.v's own header already notes makes its own
   exactness-agreement theorem vacuous for that residue) -- so it is
   `common_subdivision_certificate_agreement`, not this file's theorem,
   that is the one that concretely fires for the paper's own displayed
   residue r=(1,1,1,-2), and it does so via an independent, N0-only
   argument that needs no E0 at all. The two routes to "both obstructed"
   -- this file's contraposed iff, and the certificate-based theorem
   applied to an actual witness -- are two different sufficient
   arguments for related conclusions, not one argument restated twice;
   this file does not merge them into one proof term because there is
   no proved fact connecting them beyond what each already establishes
   on its own.

   INSTANTIATION: refinement_checker.py's `verdict_safe` field (`bool
   (descent_safe and exactness_reflection)`, i.e. (N0) and (E0) both
   hold) is exactly the hypothesis set this theorem's two refinement
   legs must each satisfy. It is `True` for the three subdivision
   witnesses (subdivide_U1, subdivide_U2, subdivide_all) and `False`
   for insert_bridge, which fails (N0). As with every other file in
   this refinement-comparison line, the abstract theorem below is
   stated over opaque `Type`s and is not itself instantiated against
   concrete four-cycle matrices in Rocq -- that cross-check is the
   Python side's job, exactly as for AdmissibleRefinementPersistence.v,
   CochainNaturalityDescent.v, CommonSubdivisionAgreement.v, and
   ExactnessReflection.v before it.

   SCOPE, restated once more because it is easy to over-read a theorem
   named "invariance": this applies only to descent-safe, reflecting
   (verdict_safe) common subdivisions -- not to arbitrary admissible
   refinements, and not to topology-changing refinements such as
   bridge insertion, which fails (N0) and is therefore outside this
   theorem's hypotheses entirely, exactly as it is outside
   CommonSubdivisionAgreement.v's and half of ExactnessReflection.v's
   own stated scope. This is verdict-level invariance ([r_P]=0 iff
   [r_Q]=0) for that fragment, not full presentation invariance, and
   not class-level invariance (a correspondence between [r_P] and
   [r_Q] themselves, R20 in PRESENTATION_INVARIANCE_SPEC.md's proposed
   later ladder).

   No axioms, typeclasses, quotient constructions, adjunctions, or new
   morphism scaffold. No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import CommonSubdivisionAgreement.
Require Import ExactnessReflection.

(* ------------------------------------------------------------------ *)
(* Local helper: names (N0)'s forward direction, stated in prose in    *)
(* CochainNaturalityDescent.v's own header but never extracted there   *)
(* as its own lemma. Deliberately near-tautological, exactly like      *)
(* that file's naturality_descent_nonexact (its contrapositive) and    *)
(* ExactnessReflection.v's reflects_exactness_applies -- its only role *)
(* is to give this direction a citable name.                           *)
(* ------------------------------------------------------------------ *)

Lemma naturality_descent_exact :
  forall (C0 C1 C0' C1' : Type)
         (delta0 : C0 -> C1)
         (coboundary' : C0' -> C1')
         (rho0_star : C0 -> C0')
         (rho1_star : C1 -> C1')
         (r : C1),
    (forall b : C0, rho1_star (delta0 b) = coboundary' (rho0_star b)) -> (* (N0) *)
    (exists b : C0, r = delta0 b) ->
    exists b' : C0', rho1_star r = coboundary' b'.
Proof.
  intros C0 C1 C0' C1' delta0 coboundary' rho0_star rho1_star r Hnat [b Hr].
  exists (rho0_star b). rewrite Hr. apply Hnat.
Qed.

(* ------------------------------------------------------------------ *)
(* Main theorem: verdict-level presentation invariance for a           *)
(* verdict-safe common subdivision. Both directions invoke             *)
(* ExactnessReflection.v's common_subdivision_exactness_agreement,     *)
(* the "already-proved half" that is actually sufficient on its own,   *)
(* combined with naturality_descent_exact above.                       *)
(* ------------------------------------------------------------------ *)

Theorem common_subdivision_verdict_invariance :
  forall (C0_1 C1_1 C0_2 C1_2 C0_12 C1_12 : Type)
         (delta1 : C0_1 -> C1_1)
         (delta2 : C0_2 -> C1_2)
         (delta12 : C0_12 -> C1_12)
         (rho1_0star : C0_1 -> C0_12) (rho1_1star : C1_1 -> C1_12)
         (rho2_0star : C0_2 -> C0_12) (rho2_1star : C1_2 -> C1_12)
         (r1 : C1_1) (r2 : C1_2),
    (forall b : C0_1, rho1_1star (delta1 b) = delta12 (rho1_0star b)) -> (* (N0), leg 1 *)
    (forall b : C0_2, rho2_1star (delta2 b) = delta12 (rho2_0star b)) -> (* (N0), leg 2 *)
    (forall r : C1_1,                                                    (* (E0), leg 1 *)
       (exists b' : C0_12, rho1_1star r = delta12 b') ->
       exists b : C0_1, r = delta1 b) ->
    (forall r : C1_2,                                                    (* (E0), leg 2 *)
       (exists b' : C0_12, rho2_1star r = delta12 b') ->
       exists b : C0_2, r = delta2 b) ->
    rho1_1star r1 = rho2_1star r2 ->                        (* shared transferred residue *)
    (exists b1 : C0_1, r1 = delta1 b1) <-> (exists b2 : C0_2, r2 = delta2 b2).
Proof.
  intros C0_1 C1_1 C0_2 C1_2 C0_12 C1_12
         delta1 delta2 delta12
         rho1_0star rho1_1star rho2_0star rho2_1star
         r1 r2 Hnat1 Hnat2 Hreflect1 Hreflect2 Hshared.
  split.
  - intro Hexact1.
    assert (Hexact12 : exists b12 : C0_12, rho1_1star r1 = delta12 b12).
    { exact (naturality_descent_exact C0_1 C1_1 C0_12 C1_12 delta1 delta12
               rho1_0star rho1_1star r1 Hnat1 Hexact1). }
    destruct (common_subdivision_exactness_agreement
                C0_1 C1_1 C0_2 C1_2 C0_12 C1_12
                delta1 delta2 delta12 rho1_1star rho2_1star r1 r2
                Hshared Hexact12 Hreflect1 Hreflect2) as [_ Hr2].
    exact Hr2.
  - intro Hexact2.
    assert (Hexact12 : exists b12 : C0_12, rho1_1star r1 = delta12 b12).
    { rewrite Hshared.
      exact (naturality_descent_exact C0_2 C1_2 C0_12 C1_12 delta2 delta12
               rho2_0star rho2_1star r2 Hnat2 Hexact2). }
    destruct (common_subdivision_exactness_agreement
                C0_1 C1_1 C0_2 C1_2 C0_12 C1_12
                delta1 delta2 delta12 rho1_1star rho2_1star r1 r2
                Hshared Hexact12 Hreflect1 Hreflect2) as [Hr1 _].
    exact Hr1.
Qed.

(* ------------------------------------------------------------------ *)
(* Corollary: the obstruction-side restatement, by pure contraposition *)
(* of the theorem above -- no classical axiom, no excluded middle, no  *)
(* new hypothesis. This is the form that actually matches how the      *)
(* repository's other files phrase a verdict ("non-exact" / obstructed *)
(* rather than "exact"): CommonSubdivisionAgreement.v's own conclusion *)
(* is stated this way.                                                 *)
(* ------------------------------------------------------------------ *)

Corollary common_subdivision_verdict_invariance_obstructed :
  forall (C0_1 C1_1 C0_2 C1_2 C0_12 C1_12 : Type)
         (delta1 : C0_1 -> C1_1)
         (delta2 : C0_2 -> C1_2)
         (delta12 : C0_12 -> C1_12)
         (rho1_0star : C0_1 -> C0_12) (rho1_1star : C1_1 -> C1_12)
         (rho2_0star : C0_2 -> C0_12) (rho2_1star : C1_2 -> C1_12)
         (r1 : C1_1) (r2 : C1_2),
    (forall b : C0_1, rho1_1star (delta1 b) = delta12 (rho1_0star b)) ->
    (forall b : C0_2, rho2_1star (delta2 b) = delta12 (rho2_0star b)) ->
    (forall r : C1_1,
       (exists b' : C0_12, rho1_1star r = delta12 b') ->
       exists b : C0_1, r = delta1 b) ->
    (forall r : C1_2,
       (exists b' : C0_12, rho2_1star r = delta12 b') ->
       exists b : C0_2, r = delta2 b) ->
    rho1_1star r1 = rho2_1star r2 ->
    ~ (exists b1 : C0_1, r1 = delta1 b1) <-> ~ (exists b2 : C0_2, r2 = delta2 b2).
Proof.
  intros C0_1 C1_1 C0_2 C1_2 C0_12 C1_12
         delta1 delta2 delta12
         rho1_0star rho1_1star rho2_0star rho2_1star
         r1 r2 Hnat1 Hnat2 Hreflect1 Hreflect2 Hshared.
  destruct (common_subdivision_verdict_invariance
              C0_1 C1_1 C0_2 C1_2 C0_12 C1_12
              delta1 delta2 delta12
              rho1_0star rho1_1star rho2_0star rho2_1star
              r1 r2 Hnat1 Hnat2 Hreflect1 Hreflect2 Hshared) as [Hfwd Hbwd].
  split.
  - intros Hnon1 Hexact2. apply Hnon1. exact (Hbwd Hexact2).
  - intros Hnon2 Hexact1. apply Hnon2. exact (Hfwd Hexact1).
Qed.
