(*
   GlobalCoherenceCertificate.v

   R16. A global-coherence analogue of R15
   (rocq/PairwiseDiagnosticCertificate.v), scoped narrowly to the
   already-proved abstract theorem this project already has.
   AssociatorResidueRepair.v's Layer 1 -- nonzero_pairing_blocks_
   repair_mod_ceq -- is imported directly, not modified or duplicated.

   Where R15 packages CoupledParallelCompatibility.v's two-branch,
   one-seam gluing theory, this file packages AssociatorResidueRepair.v's
   pure-cohomology repair/obstruction theory. Neither packaging adds new
   mathematics; both turn an already-proved abstract theorem into
   evidence-carrying certificate constructors with a soundness theorem.

   Per docs/design/GLOBAL_COHERENCE_CERTIFICATE_SPEC.md:

   - This does NOT reuse ConflictDiagnostic, SoundL, or SoundR. The
     global problem (one residue, a repair potential, an obstruction
     cycle) has no left/right declarations to recover and no role for
     R14's pairwise vocabulary -- see the design doc's §3 for why
     forcing this into ConflictDiagnostic would overload
     RefuseDiagnostic with two genuinely different obstruction
     theories, exactly the conflation docs/design/
     CERTIFICATE_COMPOSITION_SPEC.md's pairwise_compatibility/
     global_coherence split already exists to prevent.

   - This does NOT claim H^1 nontriviality anywhere. nonzero_pairing_
     blocks_repair_mod_ceq proves ~(exists b, ceq (delta0 b) r) -- r is
     not a coboundary -- which does NOT require or establish
     delta1 r = 0 (that r is a cocycle). Every obstruction fact here is
     named "not repairable," never "nontrivial cohomology class." A
     later, separate layer could add the cocycle condition honestly;
     nothing here does.

   - This does NOT add a fourth "already coherent" (zero-residue) case.
     The Layer-1 interface supplies no distinguished zero of C1 and the
     central theorem needs none.

   - DecisiveGlobalEvidence is a plain sum type, not the GADT-indexed
     form (a separate GlobalCoherenceStatus enum) sketched during
     design -- mirrors DecisivePairwiseEvidence/PairwiseResult's own
     successful shape in R15 exactly; indexing by a status enum would
     add dependent-elimination complexity for no soundness content.

   - repairable_requires_repair_witness and obstructed_requires_cycle_
     witness, as originally proposed as two separate theorems, would
     each have had no content beyond a constructor's own carried
     hypothesis restated verbatim. Merged into one honest fact,
     decisive_global_evidence_is_repair_or_obstruction, instead of
     padding to a target theorem count with vacuous restatements.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.
Require Import Coq.Classes.RelationClasses.
Require Import AssociatorResidueRepair.

Section GlobalCoherenceCertificate.

  Variables C0 C1 Z1 : Type.
  Variable delta0 : C0 -> C1.
  Variable pairing : Z1 -> C1 -> Q.
  Variable cycle : Z1 -> Prop.
  Variable ceq : C1 -> C1 -> Prop.
  Variable ceq_equiv : Equivalence ceq.
  Variable pairing_respects_ceq :
    forall (z : Z1) (r r' : C1), ceq r r' -> pairing z r == pairing z r'.
  Variable coboundaries_pair_zero :
    forall (z : Z1) (b : C0), cycle z -> pairing z (delta0 b) == 0.

  (* The asymmetry is deliberate, matching R15's own: repairability
     carries a positive repair witness; obstruction carries a positive
     cycle witness. There is no constructor for a bare "not repairable"
     claim independent of an actual cycle witness. *)
  Inductive DecisiveGlobalEvidence (r : C1) : Type :=
    | RepairEvidence :
        forall b : C0, ceq (delta0 b) r -> DecisiveGlobalEvidence r
    | ObstructionEvidence :
        forall z : Z1, cycle z -> ~ (pairing z r == 0) -> DecisiveGlobalEvidence r.

  (* Unresolved lives OUTSIDE the decisive certificate, exactly as
     PairwiseResult's Unresolved did in R15: it means only "no validated
     repair or obstruction certificate is being presented," not that
     any search was exhaustive, bounded, or correctly executed. *)
  Inductive GlobalCoherenceResult (r : C1) : Type :=
    | GlobalDecided : DecisiveGlobalEvidence r -> GlobalCoherenceResult r
    | GlobalUnresolvedResult : GlobalCoherenceResult r.

  (* The central theorem. The obstruction branch's conclusion is
     OBTAINED from nonzero_pairing_blocks_repair_mod_ceq, applied to the
     evidence's own (z, Hcyc, Hnz) -- never re-derived or stored
     separately. The Unresolved branch's `True` is deliberately the
     weakest possible statement: it asserts nothing about search
     completeness -- concretely, it must NOT be read as implying either
       ~ (exists b : C0, ceq (delta0 b) r)
     or
       ~ (exists z : Z1, cycle z /\ ~ (pairing z r == 0)).
     The underlying residue may already be repairable or already
     obstructed even when no witness is presented; GlobalUnresolvedResult
     is a fact about what evidence was SUPPLIED, never a fact about
     whether such evidence EXISTS. `True` is exactly weak enough to make
     this failure mode syntactically impossible to smuggle in later. *)
  Theorem global_coherence_certificate_sound :
    forall (r : C1) (result : GlobalCoherenceResult r),
      match result with
      | GlobalDecided _ (RepairEvidence _ b Hrepair) => ceq (delta0 b) r
      | GlobalDecided _ (ObstructionEvidence _ z Hcyc Hnz) =>
          ~ exists b : C0, ceq (delta0 b) r
      | GlobalUnresolvedResult _ => True
      end.
  Proof.
    intros r result.
    destruct result as [ev | ].
    - destruct ev as [b Hrepair | z Hcyc Hnz].
      + exact Hrepair.
      + exact (nonzero_pairing_blocks_repair_mod_ceq C0 C1 Z1 delta0 pairing cycle ceq
                 ceq_equiv pairing_respects_ceq coboundaries_pair_zero r z Hcyc Hnz).
    - exact I.
  Qed.

  (* Any decisive evidence testifies to EITHER a repair witness or an
     obstruction witness -- the two constructors are exhaustive for
     whatever evidence was actually constructed. *)
  Theorem decisive_global_evidence_is_repair_or_obstruction :
    forall (r : C1) (ev : DecisiveGlobalEvidence r),
      (exists b : C0, ceq (delta0 b) r) \/
      (exists z : Z1, cycle z /\ ~ (pairing z r == 0)).
  Proof.
    intros r ev.
    destruct ev as [b Hb | z Hcyc Hnz].
    - left. exists b. exact Hb.
    - right. exists z. split; assumption.
  Qed.

  (* A checked obstruction witness entails no b satisfies the repair
     equation for r -- direct restatement of the central theorem's
     obstruction branch as a standalone, citable fact. *)
  Theorem obstruction_certificate_blocks_every_repair :
    forall (r : C1) (z : Z1), cycle z -> ~ (pairing z r == 0) ->
      ~ exists b : C0, ceq (delta0 b) r.
  Proof.
    intros r z Hcyc Hnz.
    exact (nonzero_pairing_blocks_repair_mod_ceq C0 C1 Z1 delta0 pairing cycle ceq
             ceq_equiv pairing_respects_ceq coboundaries_pair_zero r z Hcyc Hnz).
  Qed.

  (* A constructor-distinctness fact, matching R15's certified_
     pairwise_never_scalar in spirit: GlobalUnresolvedResult never
     coincides with any GlobalDecided value. *)
  Theorem unresolved_result_carries_no_decisive_evidence :
    forall (r : C1) (ev : DecisiveGlobalEvidence r),
      GlobalUnresolvedResult r <> GlobalDecided r ev.
  Proof.
    intros r ev Heq. discriminate.
  Qed.

  (* The genuine consistency property this bridge earns: no residue can
     simultaneously have a checked repair witness and a checked
     obstruction witness. Follows immediately from the obstruction
     theorem applied to the repair witness itself. *)
  Theorem repair_and_obstruction_evidence_are_disjoint :
    forall (r : C1) (b : C0) (z : Z1),
      ceq (delta0 b) r -> cycle z -> ~ (pairing z r == 0) -> False.
  Proof.
    intros r b z Hrepair Hcyc Hnz.
    apply (nonzero_pairing_blocks_repair_mod_ceq C0 C1 Z1 delta0 pairing cycle ceq
             ceq_equiv pairing_respects_ceq coboundaries_pair_zero r z Hcyc Hnz).
    exists b. exact Hrepair.
  Qed.

End GlobalCoherenceCertificate.
