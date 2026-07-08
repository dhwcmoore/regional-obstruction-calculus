(*
   FirstOrderClassifierCertificate.v

   The Python first-order classifier pipeline (associator_residue.py,
   regional_composition.py, repair_solver.py, certificate_emitter.py) is
   not part of the trusted base -- it is ordinary, tested-but-unverified
   Python. This file does not try to change that by verifying the Python
   program itself; instead it proves that the two certificate *forms* the
   pipeline emits are sound, so that a verdict is trustworthy exactly when
   it is accompanied by a certificate independently accepted by
   first_order_certificate_checker.py.

   There are exactly two certificate forms, one per verdict:

   1. `exact_certificate_sound` -- an exactness ("globally_repairable")
      verdict is witnessed by a correction `b` with `r = delta0 b`.
      Deliberately trivial to prove (existential introduction); its only
      role is to give the certificate form a name that
      first_order_certificate_checker.py's Layer-3 repairable-branch check
      can be said to implement.

   2. `obstruction_certificate_sound` -- a non-repairability
      ("nontrivial_associator_obstruction") verdict is witnessed by a
      cycle `z` that annihilates every coboundary and pairs non-zero with
      `r`. This is not reproved from scratch: it is
      AdmissibleRefinementPersistence.v's `nonzero_cycle_pairing_implies_
      nonexact`, applied directly (same statement, renamed for this
      file's certificate vocabulary) -- the two theorems have the same
      logical content because both certificate forms are instances of the
      one non-exactness argument (paper Lemma lem:cycle-pairing) this
      repository already proved once.

   What this file does NOT do:

   - It does not verify that the Python classifier's residue was actually
     assembled from the declared associator/regional-composition data
     (Layer 1 of first_order_certificate_checker.py's three-layer check);
     that is a Python-side recomputation of the closed-form formula
     (Proposition prop:four-term), not a Rocq-checkable fact about opaque
     types, and it is not attempted here.
   - It does not verify closedness (Layer 2, delta^1 r = 0) as a separate
     theorem; closedness is a hypothesis of both certificate forms below
     via `r`'s membership in the appropriate ambient complex, exactly as
     it is a hypothesis of AdmissibleRefinementPersistence.v's theorem.
   - It does not extract or otherwise formally connect to
     first_order_certificate_checker.py itself; that Python module is an
     independent, from-scratch reimplementation of the same two checks,
     not a mechanically-derived artefact of this file.
   - It does not formalise finite_algebra.py, regional_composition.py, or
     any concrete structure constants -- exactly the deferral already
     recorded for AssociatorResidueRepair.v (item 8 in the README).

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import AdmissibleRefinementPersistence.

(* ------------------------------------------------------------------ *)
(* Certificate form 1: exactness ("globally_repairable").              *)
(* ------------------------------------------------------------------ *)

Theorem exact_certificate_sound :
  forall (C0 C1 : Type)
         (delta0 : C0 -> C1)
         (r : C1) (b : C0),
    r = delta0 b ->
    exists b : C0, r = delta0 b.
Proof.
  intros C0 C1 delta0 r b Heq.
  exists b.
  exact Heq.
Qed.

(* ------------------------------------------------------------------ *)
(* Certificate form 2: obstruction ("nontrivial_associator_obstruction"). *)
(* Direct application of AdmissibleRefinementPersistence.v's cycle-      *)
(* pairing lemma, renamed to this file's certificate vocabulary.         *)
(* ------------------------------------------------------------------ *)

Theorem obstruction_certificate_sound :
  forall (C0 C1 Z1 : Type)
         (delta0 : C0 -> C1)
         (pairing : Z1 -> C1 -> Q)
         (cycle : Z1 -> Prop)
         (z : Z1) (r : C1),
    cycle z ->
    (forall b : C0, pairing z (delta0 b) == 0) ->
    ~ (pairing z r == 0) ->
    ~ (exists b : C0, r = delta0 b).
Proof.
  exact nonzero_cycle_pairing_implies_nonexact.
Qed.
