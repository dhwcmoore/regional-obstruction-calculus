(*
   CommonSubdivisionAgreement.v

   CochainNaturalityDescent.v's `admissible_refinement_persistence_with_
   descent` uses (A1)-(A4) plus (N0) to descend from refined non-exactness
   to coarse non-exactness for a *single* refinement map. This file uses
   it *twice*, for two descent-safe refinement maps into a shared common
   subdivision, to get a real (but limited) form of presentation
   comparison:

     N12 --rho1--> N1
     N12 --rho2--> N2

   If a coarse residue `r1` on `N1` and a coarse residue `r2` on `N2`
   transfer to the *same* residue in the common subdivision `N12`
   (`rho1_1star r1 = rho2_1star r2`), and that shared transferred residue
   has a non-zero cycle-pairing certificate in `N12`, then both `r1` and
   `r2` are non-exact in their own original coarse presentations. Two
   different coarse descriptions of the same regional situation, compared
   through a shared refinement, agree that an obstruction is present.

   Call this **common-subdivision certificate agreement** (the theorem
   below, `common_subdivision_certificate_agreement`) -- not
   "presentation invariance". It is deliberately narrower:

   - It requires both refinement maps to already be descent-safe (N0
     holds for each -- see CochainNaturalityDescent.v), so it inherits
     that restriction: it says nothing about topology-changing
     refinements such as bridge insertion, which is exactly why bridge
     insertion is excluded from this file's scope, not an oversight.
   - It proves only the obstruction-*present* side: shared non-zero
     certificate implies non-exactness on both sides. It does not prove
     full verdict equivalence `[r1] <> 0 <-> [r2] <> 0` for arbitrary
     `r1`, `r2` -- that would additionally need an exactness-side
     theorem (shared *zero* certificate, or shared coboundary, implies
     exactness on both sides), which is not attempted here.
   - It is deliberately abstract, exactly like AdmissibleRefinementPersis
     -tence.v and CochainNaturalityDescent.v: `C0_1`, `C1_1`, `C0_2`,
     `C1_2`, `C0_12`, `C1_12`, `Z1_12` are opaque `Type`s, not concrete
     vectors or matrices. It certifies the inference pattern, not that
     any concrete pair of witnesses in refinement_witnesses.py satisfies
     its hypotheses -- no such pair is constructed or claimed here.

   Proof shape: apply AdmissibleRefinementPersistence.v's
   `nonzero_cycle_pairing_implies_nonexact` once, to the shared
   transferred residue `rho1_1star r1` in `N12`, to get its non-exactness
   there; transport that fact across `rho2_1star r2 = rho1_1star r1` for
   the second side; then apply CochainNaturalityDescent.v's
   `naturality_descent_nonexact` once per side to descend each one back
   down to its own coarse complex.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import AdmissibleRefinementPersistence.
Require Import CochainNaturalityDescent.

Theorem common_subdivision_certificate_agreement :
  forall (C0_1 C1_1 C0_2 C1_2 C0_12 C1_12 Z1_12 : Type)
         (delta1 : C0_1 -> C1_1)
         (delta2 : C0_2 -> C1_2)
         (delta12 : C0_12 -> C1_12)
         (rho1_0star : C0_1 -> C0_12) (rho1_1star : C1_1 -> C1_12)
         (rho2_0star : C0_2 -> C0_12) (rho2_1star : C1_2 -> C1_12)
         (pairing12 : Z1_12 -> C1_12 -> Q)
         (cycle12 : Z1_12 -> Prop)
         (z12 : Z1_12) (r1 : C1_1) (r2 : C1_2),
    (forall b : C0_1, rho1_1star (delta1 b) = delta12 (rho1_0star b)) -> (* (N0), rho1 *)
    (forall b : C0_2, rho2_1star (delta2 b) = delta12 (rho2_0star b)) -> (* (N0), rho2 *)
    cycle12 z12 ->                                          (* part of (A3) *)
    (forall b : C0_12, pairing12 z12 (delta12 b) == 0) ->   (* (A3) *)
    rho1_1star r1 = rho2_1star r2 ->                        (* shared transferred residue *)
    ~ (pairing12 z12 (rho1_1star r1) == 0) ->               (* (A4), on the shared residue *)
    ~ (exists b1 : C0_1, r1 = delta1 b1)
    /\ ~ (exists b2 : C0_2, r2 = delta2 b2).
Proof.
  intros C0_1 C1_1 C0_2 C1_2 C0_12 C1_12 Z1_12
         delta1 delta2 delta12
         rho1_0star rho1_1star rho2_0star rho2_1star
         pairing12 cycle12 z12 r1 r2
         Hnat1 Hnat2 Hcycle Hannihilates Hshared Hnonzero.
  assert (Hrefined1_nonexact : ~ (exists b' : C0_12, rho1_1star r1 = delta12 b')).
  {
    exact (nonzero_cycle_pairing_implies_nonexact
             C0_12 C1_12 Z1_12 delta12 pairing12 cycle12 z12 (rho1_1star r1)
             Hcycle Hannihilates Hnonzero).
  }
  split.
  - exact (naturality_descent_nonexact
             C0_1 C1_1 C0_12 C1_12 delta1 delta12 rho1_0star rho1_1star r1
             Hnat1 Hrefined1_nonexact).
  - assert (Hrefined2_nonexact : ~ (exists b' : C0_12, rho2_1star r2 = delta12 b')).
    { rewrite <- Hshared. exact Hrefined1_nonexact. }
    exact (naturality_descent_nonexact
             C0_2 C1_2 C0_12 C1_12 delta2 delta12 rho2_0star rho2_1star r2
             Hnat2 Hrefined2_nonexact).
Qed.
