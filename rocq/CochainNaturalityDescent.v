(*
   CochainNaturalityDescent.v

   AdmissibleRefinementPersistence.v proves that the *transferred* residue
   rho^*r is not exact *inside the refined complex* (conditions (A1)-(A4)).
   It proves nothing about the residue r itself back in the coarse complex:
   its conclusion is `~ (exists b' : C0', rho_star_r = coboundary' b')`,
   not `~ (exists b : C0, r = delta0 b)`. Descending from the refined
   statement to the coarse one needs one extra, separate ingredient:
   one-directional cochain-map naturality,

     (N0)  forall b : C0, rho1_star (delta0 b) = coboundary' (rho0_star b)

   i.e. pushing a coarse exactness witness `b` forward along the
   vertex-level pullback rho0_star always lands on a refined exactness
   witness for the transferred residue. Its contrapositive is exactly the
   missing step: if rho^*r is *not* exact in the refined complex, then r
   cannot have been exact in the coarse complex either.

   (N0) is condition 1 ("cochain map") of the four-condition scheme in the
   archived archive/deprecated_universal_refinement_scaffold/ (cochain-map
   naturality, chain-map naturality, pairing adjointness, H1-surjectivity).
   Only condition 1 is used here, and only in this one direction -- not
   the other three, and not as a characterisation of rho^* (an
   isomorphism, an adjoint, or a surjection on H1). This file does NOT
   prove presentation invariance: it does not compare two different
   coarse presentations of the same regional situation, only whether a
   single refinement's coarse-to-refined round trip preserves an
   exactness witness. A1-A4 together with (N0) is called *descent-safe*
   in refinement_checker.py, not "presentation-invariant".

   Checked computationally in exact rational arithmetic against the real
   (non-archived) witness data of refinement_witnesses.py: (N0) holds for
   the three subdivision witnesses (subdivide_U1, subdivide_U2,
   subdivide_all), using the natural vertex projection rho_0^* that sends
   each split half to its coarse parent, and *fails* for the bridge
   witness (insert_bridge) at exactly its new edge b12, which runs
   between two distinct coarse vertices rather than lying over a
   collapsed parent -- see refinement_checker.py's
   `N0_cochain_naturality_delta0` / `naturality_failures` fields, and the
   README's three-level distinction (A1-A4 persistence / descent-safe
   subdivision persistence / full presentation invariance -- the last
   remains unproved and is not claimed here or anywhere in this
   repository).

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import AdmissibleRefinementPersistence.

(* ------------------------------------------------------------------ *)
(* Core lemma: cochain-map naturality gives descent.                    *)
(* ------------------------------------------------------------------ *)

Lemma naturality_descent_nonexact :
  forall (C0 C1 C0' C1' : Type)
         (delta0 : C0 -> C1)
         (coboundary' : C0' -> C1')
         (rho0_star : C0 -> C0')
         (rho1_star : C1 -> C1')
         (r : C1),
    (forall b : C0, rho1_star (delta0 b) = coboundary' (rho0_star b)) ->
    ~ (exists b' : C0', rho1_star r = coboundary' b') ->
    ~ (exists b : C0, r = delta0 b).
Proof.
  intros C0 C1 C0' C1' delta0 coboundary' rho0_star rho1_star r Hnat Hrefined_nonexact.
  intros [b Heq].
  apply Hrefined_nonexact.
  exists (rho0_star b).
  rewrite Heq.
  apply Hnat.
Qed.

(* ------------------------------------------------------------------ *)
(* Combined theorem: (A1)-(A4), applied to the transferred residue      *)
(* rho1_star r, together with (N0), gives non-exactness both in the     *)
(* refined complex (as AdmissibleRefinementPersistence.v already gives)  *)
(* and, newly, back in the coarse complex.                               *)
(* ------------------------------------------------------------------ *)

Theorem admissible_refinement_persistence_with_descent :
  forall (C0 C1 C0' C1' Z1' : Type)
         (delta0 : C0 -> C1)
         (coboundary' : C0' -> C1')
         (rho0_star : C0 -> C0')
         (rho1_star : C1 -> C1')
         (pairing' : Z1' -> C1' -> Q)
         (cycle' : Z1' -> Prop)
         (A1_closed_base : Prop)
         (A2_closed_refined : Prop)
         (z' : Z1') (r : C1),
    A1_closed_base ->                                        (* (A1) *)
    A2_closed_refined ->                                      (* (A2) *)
    cycle' z' ->                                              (* part of (A3) *)
    (forall b : C0', pairing' z' (coboundary' b) == 0) ->     (* (A3) *)
    ~ (pairing' z' (rho1_star r) == 0) ->                     (* (A4), on the transferred residue *)
    (forall b : C0, rho1_star (delta0 b) = coboundary' (rho0_star b)) -> (* (N0) *)
    A2_closed_refined
    /\ ~ (exists b' : C0', rho1_star r = coboundary' b')
    /\ ~ (exists b : C0, r = delta0 b).
Proof.
  intros C0 C1 C0' C1' Z1' delta0 coboundary' rho0_star rho1_star pairing' cycle'
         A1_closed_base A2_closed_refined z' r
         HA1 HA2 Hcycle Hannihilates Hnonzero Hnat.
  destruct (admissible_refinement_persistence
              C0' C1' Z1' coboundary' pairing' cycle'
              A1_closed_base A2_closed_refined z' (rho1_star r)
              HA1 HA2 Hcycle Hannihilates Hnonzero) as [HA2' Hrefined_nonexact].
  split; [| split].
  - exact HA2'.
  - exact Hrefined_nonexact.
  - exact (naturality_descent_nonexact
             C0 C1 C0' C1' delta0 coboundary' rho0_star rho1_star r
             Hnat Hrefined_nonexact).
Qed.
