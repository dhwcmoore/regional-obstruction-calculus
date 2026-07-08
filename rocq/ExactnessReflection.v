(*
   ExactnessReflection.v

   CommonSubdivisionAgreement.v proves the obstruction-*present* side of
   common-subdivision comparison: a shared non-zero refined certificate
   implies non-exactness in both coarse presentations. This file proves
   the companion, obstruction-*absent* side: a shared refined *exactness*
   witness implies exactness in both coarse presentations.

   The two sides are NOT proved by the same argument run backwards.
   CochainNaturalityDescent.v's (N0), one-directional cochain-map
   naturality, gives exactness *preservation*:

     r = delta0 b  ==>  rho1_star r = delta12 (rho0_star b)

   i.e. coarse exactness pushes forward to refined exactness. It says
   nothing about the converse. This file's condition, (E0) exactness
   *reflection*,

     (E0)  (exists b' : C0', rho1_star r = delta0' b')
           -> exists b : C0, r = delta0 b

   is the missing converse direction: refined exactness of the
   transferred residue reflects back to coarse exactness of the original.
   (E0) is logically independent of (N0) -- neither implies the other in
   general -- and, unlike (N0), it does not require a chosen vertex-level
   pullback rho0_star at all; it is a condition purely on rho1_star.

   What (E0) actually says, structurally: writing Z1(C) for the cycle
   space dual to C1 (as in AdmissibleRefinementPersistence.v), a standard
   linear-algebra fact identifies im(delta0) with the annihilator of
   Z1(C), so (E0) is equivalent to

     Z1(coarse) subseteq rho_*(Z1(refined))

   where rho_* is the pushforward on cycles (the transpose of rho1_star)
   -- i.e. every coarse cycle is the pushforward of some refined cycle.
   This is exactly the "H1-surjectivity" condition of the four-condition
   scheme in archive/deprecated_universal_refinement_scaffold/, which
   that scaffold only ever checked with floating-point
   `numpy.linalg.lstsq` (see its `verify_condition_4_h1_surjective`).
   Nothing here revives that scaffold; (E0) is checked in
   refinement_checker.py by exact rational linear algebra (an exact
   nullspace computation, `rational_linear_algebra.nullspace_over_Q`, and
   an exact subspace-membership test, `in_span_over_Q`), not by a
   floating-point lift.

   Computationally, against the real (non-archived) witness data:
   (E0) holds for *all four* declared witnesses, including insert_bridge
   -- in each case the already-declared refined cycle z' alone already
   pushes forward to (a non-zero rational multiple of) the coarse cycle
   z, which is enough to span the (here one-dimensional) coarse cycle
   space. This is genuinely different from (N0), which fails for
   insert_bridge. The two conditions are independent: insert_bridge is a
   counterexample to "(N0) holds whenever (E0) does" (and to the
   converse), not evidence that either implies the other.

   This does NOT give insert_bridge full presentation invariance or
   verdict equivalence. (E0) alone only reflects *exactness*; the
   obstruction-present direction proved by CommonSubdivisionAgreement.v
   still requires (N0), which insert_bridge does not satisfy. The two
   sides are combined only when both hold for the same refinement map,
   for the same pair of residues -- see refinement_checker.py's
   `verdict_safe` field, which is `descent_safe and E0_exactness_
   reflection`, and which is therefore true only for the three
   subdivision witnesses. Nor is (E0)'s hypothesis relevant to the
   paper's own displayed residue r=(1,1,1,-2): that residue is
   *obstructed*, not exact, in every witness's refined complex, so this
   file's theorem is vacuous for it; (E0) matters only for some other,
   hypothetically exact residue on the same complexes.

   No `Admitted`/`Axiom`/`sorry`.
*)

(* ------------------------------------------------------------------ *)
(* Core lemma: names the condition. Deliberately near-tautological --  *)
(* its only role is to give (E0) a citable name, exactly as            *)
(* CochainNaturalityDescent.v's naturality_descent_nonexact names the   *)
(* contrapositive of (N0).                                              *)
(* ------------------------------------------------------------------ *)

Lemma reflects_exactness_applies :
  forall (C0 C1 C0' : Type)
         (delta0 : C0 -> C1)
         (coboundary' : C0' -> C1)
         (rho1_star : C1 -> C1)
         (r : C1),
    (forall x : C1,
       (exists b' : C0', rho1_star x = coboundary' b') ->
       exists b : C0, x = delta0 b) ->                          (* (E0) *)
    (exists b' : C0', rho1_star r = coboundary' b') ->
    exists b : C0, r = delta0 b.
Proof.
  intros C0 C1 C0' delta0 coboundary' rho1_star r Hreflects Hexact.
  exact (Hreflects r Hexact).
Qed.

(* ------------------------------------------------------------------ *)
(* Two-map theorem: the exactness-side companion to                     *)
(* CommonSubdivisionAgreement.v's common_subdivision_certificate_        *)
(* agreement. Deliberately conservative -- it is a separate theorem      *)
(* from that one, not a single combined "verdict" theorem, and it does   *)
(* not require (N0) at all.                                              *)
(* ------------------------------------------------------------------ *)

Theorem common_subdivision_exactness_agreement :
  forall (C0_1 C1_1 C0_2 C1_2 C0_12 C1_12 : Type)
         (delta1 : C0_1 -> C1_1)
         (delta2 : C0_2 -> C1_2)
         (delta12 : C0_12 -> C1_12)
         (rho1_1star : C1_1 -> C1_12)
         (rho2_1star : C1_2 -> C1_12)
         (r1 : C1_1) (r2 : C1_2),
    rho1_1star r1 = rho2_1star r2 ->                     (* shared transferred residue *)
    (exists b12 : C0_12, rho1_1star r1 = delta12 b12) ->  (* shared residue is exact in N12 *)
    (forall r : C1_1,                                      (* (E0) for rho1 *)
       (exists b' : C0_12, rho1_1star r = delta12 b') ->
       exists b : C0_1, r = delta1 b) ->
    (forall r : C1_2,                                      (* (E0) for rho2 *)
       (exists b' : C0_12, rho2_1star r = delta12 b') ->
       exists b : C0_2, r = delta2 b) ->
    (exists b1 : C0_1, r1 = delta1 b1)
    /\ (exists b2 : C0_2, r2 = delta2 b2).
Proof.
  intros C0_1 C1_1 C0_2 C1_2 C0_12 C1_12
         delta1 delta2 delta12 rho1_1star rho2_1star r1 r2
         Hshared Hexact12 Hreflect1 Hreflect2.
  split.
  - apply Hreflect1. exact Hexact12.
  - apply Hreflect2. rewrite <- Hshared. exact Hexact12.
Qed.
