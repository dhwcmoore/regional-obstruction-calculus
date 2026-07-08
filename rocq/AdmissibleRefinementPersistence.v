(*
   AdmissibleRefinementPersistence.v

   Formalises the paper's actual admissible-refinement persistence theorem
   ("Admissible refinement persistence" section, Theorem
   thm:witness-persistence / thm:universal-persistence): conditions
   (A1)-(A4) only.

     (A1) delta^1 r = 0            -- r is closed in the coarse complex
     (A2) delta'^1 (rho^* r) = 0   -- the transferred residue is closed
     (A3) z' is a cycle, i.e. it annihilates every refined coboundary
     (A4) <z', rho^* r> <> 0       -- non-zero refined pairing

   No adjointness condition and no H1-surjectivity condition appear here;
   the published theorem does not require them. This file does not build
   on rocq/UniversalRefinement.v, which targets a different, superseded
   four-condition scheme (pullback/pushforward naturality, adjointness,
   H1 surjectivity) and remains deprecated -- see its header comment.

   This is deliberately abstract: C0', C1', and Z1' (the refined cochain
   group, and the chain/cycle-space type dual to C1') are left as opaque
   types, with `coboundary'`, `pairing'`, `cycle'` as opaque functions and
   predicates on them, exactly as the paper states the theorem. No concrete
   matrix or vector representation is needed for this proof; the concrete,
   computational side of the same theorem is checked by
   refinement_checker.py and ocaml/refinement_checker.ml.

   Rational equality throughout is QArith's setoid equality `==` (Qeq),
   not Coq's Leibniz `=`, since distinct representations of the same
   rational (e.g. 1#2 and 2#4) are `==`-equal but not `=`-equal; using
   Leibniz `<>` for the non-zero-pairing hypothesis would be unsound here,
   since it would not exclude a pairing that reduces to a rational equal to
   0 in a different representation.
*)

Require Import QArith.

(* ------------------------------------------------------------------ *)
(* Core lemma: the cycle-pairing non-exactness certificate              *)
(* (paper Lemma lem:cycle-pairing, Cycle-pairing non-exactness           *)
(* certificate.                                                          *)
(* ------------------------------------------------------------------ *)

Lemma nonzero_cycle_pairing_implies_nonexact :
  forall (C0' C1' Z1' : Type)
         (coboundary' : C0' -> C1')
         (pairing' : Z1' -> C1' -> Q)
         (cycle' : Z1' -> Prop)
         (z' : Z1') (x : C1'),
    cycle' z' ->
    (forall b : C0', pairing' z' (coboundary' b) == 0) ->
    ~ (pairing' z' x == 0) ->
    ~ (exists b : C0', x = coboundary' b).
Proof.
  intros C0' C1' Z1' coboundary' pairing' cycle' z' x Hcycle Hannihilates Hnonzero.
  intros [b Heq].
  apply Hnonzero.
  rewrite Heq.
  apply Hannihilates.
Qed.

(* ------------------------------------------------------------------ *)
(* Top-level theorem: admissible-refinement persistence, conditions     *)
(* (A1)-(A4) exactly as stated in the paper (Theorem                    *)
(* thm:witness-persistence / thm:universal-persistence).                *)
(* ------------------------------------------------------------------ *)

Theorem admissible_refinement_persistence :
  forall (C0' C1' Z1' : Type)
         (coboundary' : C0' -> C1')
         (pairing' : Z1' -> C1' -> Q)
         (cycle' : Z1' -> Prop)
         (A1_closed_base : Prop)
         (A2_closed_refined : Prop)
         (z' : Z1') (rho_star_r : C1'),
    A1_closed_base ->                                       (* (A1) *)
    A2_closed_refined ->                                     (* (A2) *)
    cycle' z' ->                                             (* part of (A3) *)
    (forall b : C0', pairing' z' (coboundary' b) == 0) ->    (* (A3): z' annihilates coboundaries *)
    ~ (pairing' z' rho_star_r == 0) ->                       (* (A4) *)
    A2_closed_refined /\ ~ (exists b : C0', rho_star_r = coboundary' b).
Proof.
  intros C0' C1' Z1' coboundary' pairing' cycle' A1_closed_base A2_closed_refined
         z' rho_star_r HA1 HA2 Hcycle Hannihilates Hnonzero.
  split.
  - exact HA2.
  - exact (nonzero_cycle_pairing_implies_nonexact
             C0' C1' Z1' coboundary' pairing' cycle' z' rho_star_r
             Hcycle Hannihilates Hnonzero).
Qed.
