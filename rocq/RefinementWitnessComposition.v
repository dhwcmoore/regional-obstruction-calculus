(*
   RefinementWitnessComposition.v

   Promotes the N0-composability finding of refinement_witness_
   composition_probe.py / docs/design/REFINEMENT_WITNESS_COMPOSITION_
   STATUS.md from "probed" to "proved": if two refinement witnesses each
   satisfy (N0) cochain-map naturality, `delta'^0 rho_0^* = rho_1^*
   delta^0`, their composite satisfies (N0) too.

   This needs no linear-algebra machinery at all -- not even the notion
   of a matrix. (N0) is an equality of two composite FUNCTIONS
   (coboundary map composed with vertex pullback, versus edge pullback
   composed with coboundary map), and the composite case is exactly the
   same equality one level up, provable by associativity of function
   composition alone -- unfold the composites and rewrite twice.

   The concrete Python-level statement
   (`refinement_witness_composition_probe.py`: an equality of matrices,
   `delta0_R . rho0_star_QR = rho_star_QR . delta0_Q`, checked
   entry-by-entry there, and by `refinement_checker.check_witness`'s
   `N0_cochain_naturality_delta0` field for single witnesses) is the
   special case where `C0/C1/Q0/Q1/R0/R1` are all `Q^n` for various `n`
   and `delta_*`/`rho*_**` are given by matrices acting via `mat_vec`.
   A matrix IS a linear function of its argument, and matrix
   multiplication IS function composition on the represented functions
   (`mat_vec (mat_mat A B) v = mat_vec A (mat_vec B v)`, which
   `rational_linear_algebra.py` and every matrix-shaped Rocq file in
   this project already relies on implicitly). This file proves the
   general fact once, abstractly, rather than re-deriving it for a
   specific matrix shape; no Rocq matrix type is introduced because none
   is needed.

   (A4) nonzero pairing and (E0) exactness reflection composability are
   NOT addressed here -- see docs/design/REFINEMENT_WITNESS_COMPOSITION_
   STATUS.md and refinement_witness_a4_e0_counterexample_search.py for
   why those remain open, tested-not-proved questions, deliberately not
   attempted in this file.

   No `Admitted`/`Axiom`/`sorry`.
*)

Section N0Composition.

  Variables C0 C1 Q0 Q1 R0 R1 : Type.

  Variable delta_C : C0 -> C1.
  Variable delta_Q : Q0 -> Q1.
  Variable delta_R : R0 -> R1.

  (* Vertex-level (degree 0) and edge-level (degree 1) pullbacks for each
     step, matching refinement_checker.py's rho_0^*/rho_1^* naming. *)
  Variable rho0_CQ : C0 -> Q0.
  Variable rho1_CQ : C1 -> Q1.
  Variable rho0_QR : Q0 -> R0.
  Variable rho1_QR : Q1 -> R1.

  (* (N0) at step C -> Q: delta_Q . rho0_CQ = rho1_CQ . delta_C *)
  Hypothesis N0_step1 :
    forall c : C0, delta_Q (rho0_CQ c) = rho1_CQ (delta_C c).

  (* (N0) at step Q -> R: delta_R . rho0_QR = rho1_QR . delta_Q *)
  Hypothesis N0_step2 :
    forall q : Q0, delta_R (rho0_QR q) = rho1_QR (delta_Q q).

  (* The composite pullbacks, built by function composition -- exactly
     what refinement_witness_composition_probe.py builds by matrix
     multiplication (composite_rho0_star = rho0_QR @ rho0_CQ, and
     likewise for rho1). *)
  Definition rho0_CR (c : C0) : R0 := rho0_QR (rho0_CQ c).
  Definition rho1_CR (c1 : C1) : R1 := rho1_QR (rho1_CQ c1).

  Theorem N0_composes :
    forall c : C0, delta_R (rho0_CR c) = rho1_CR (delta_C c).
  Proof.
    intro c.
    unfold rho0_CR, rho1_CR.
    rewrite N0_step2.
    rewrite N0_step1.
    reflexivity.
  Qed.

End N0Composition.
