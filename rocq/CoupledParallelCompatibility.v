(*
   CoupledParallelCompatibility.v

   Phase 5c. refinement_witness_coupled_parallel_probe.py (Phase 5b)
   probed a conservative compatibility gate for shared-seam coupled
   parallel composition: a glued composite witness is built only when
   both branches' own declarations for the shared seam agree exactly;
   when they disagree, no composite is built at all, and the case is
   reported as `interface_conflict`, not as an (N0)/(A4)/(E0) failure.

   This file formalises exactly that gate -- NOT full coupled parallel
   composition, NOT any (N0)/(A4)/(E0) behaviour of the glued composite,
   and NOT a conflict-resolution rule. Per the design doc (docs/design/
   COUPLED_PARALLEL_COMPOSITION_PROBLEM.md) and the probe's own findings,
   choosing a merge rule (averaging, branch-preference, or otherwise) is
   a genuinely separate, later, and still-undecided question. What this
   file proves is the safety property underneath the probe's refusal
   behaviour: an incompatible interface does not merely make a bad
   composite -- no composite satisfying both branches' declarations
   exists AT ALL, so it would be a mistake to test (N0)/(A4)/(E0) against
   one.

   Deliberately abstract, in the same spirit as CandidateThreeBDistinct
   SupportClassification.v: no `Point`/finiteness assumption, no
   decidable-equality hypothesis on the key type (none of the proofs
   below need to compare keys for equality, only to pattern-match on
   each branch's own declaration at a given key). A branch's interface
   declaration is modelled as a partial function `Key -> option Value`
   -- "this branch declares value v for key k" or "this branch has no
   declaration for key k" -- matching the probe's own shape (only the
   shared seam's key ever needs comparing; every other key is, by
   construction, disjoint and never checked).

   A second section (CompatibleAggregateCancellation, below) formalises
   refinement_witness_coupled_a4_cancellation_probe.py's (Phase 5d)
   finding: shared-seam compatibility makes the glued composite
   well-defined but does NOT force the aggregate (A4) to compose --
   branchwise (A4) can hold on both branches while the aggregate still
   cancels. This is an EXAMPLE (a concrete existential witness, grounded
   in the probe's own computed numbers), not a general theorem, exactly
   as Part 1's disjoint-parallel analogue
   (RefinementWitnessParallelComposition.v's
   A4_parallel_aggregate_can_fail_despite_branchwise) was. Still no
   conflict-resolution rule anywhere in this file.

   No `Admitted`/`Axiom`/`sorry`.
*)

Require Import QArith.

Section CoupledParallelCompatibility.

  Variables Key Value : Type.

  Definition Declaration := Key -> option Value.

  (* Key k is a SHARED key of the two declarations when both branches
     declare something for it -- this alone is exactly what a naive
     "same edge name present in both refined complexes" check would
     detect, and exactly what the probe's organic `e12p` case shows is
     NOT sufficient for compatibility (see shared_label_not_sufficient_
     for_agreement below). *)
  Definition SharedKey (dA dB : Declaration) (k : Key) : Prop :=
    (exists vA, dA k = Some vA) /\ (exists vB, dB k = Some vB).

  (* The two branches AGREE at k when every value either declares for k
     is the same value -- vacuously true if at most one branch declares
     k at all. *)
  Definition Agree (dA dB : Declaration) (k : Key) : Prop :=
    forall vA vB, dA k = Some vA -> dB k = Some vB -> vA = vB.

  (* Compatible: every SHARED key is agreed on. Keys declared by only
     one branch, or by neither, impose no constraint -- matching the
     probe's construction, where every non-seam key is independently
     renamed and never shared at all. *)
  Definition Compatible (dA dB : Declaration) : Prop :=
    forall k, SharedKey dA dB k -> Agree dA dB k.

  (* A glued declaration must reproduce EACH branch's own declaration
     wherever that branch alone declares a key, and must reproduce BOTH
     branches' declared values at a shared key -- which is possible only
     when those two values coincide. This is the Rocq-level shadow of
     "the composite witness must actually carry the data both branches
     said it should carry," not an arbitrary combination rule. *)
  Definition IsGlue (dA dB g : Declaration) : Prop :=
    (forall k v, dA k = Some v -> dB k = None -> g k = Some v) /\
    (forall k v, dB k = Some v -> dA k = None -> g k = Some v) /\
    (forall k vA vB, dA k = Some vA -> dB k = Some vB -> g k = Some vA /\ g k = Some vB).

  (* The one candidate glue construction: prefer branch A's declaration
     where it exists, fall back to branch B's otherwise. This is NOT a
     branch-preference merge rule in the sense the design doc warns
     against -- it is only ever invoked once Compatible has already
     guaranteed the two branches agree wherever both declare a key, so
     "prefer A" and "prefer B" produce the identical result at every
     shared key. The choice of A-first is bookkeeping, not resolution. *)
  Definition candidate_glue (dA dB : Declaration) : Declaration :=
    fun k => match dA k with
             | Some v => Some v
             | None => dB k
             end.

  Theorem interface_agreement_allows_glue :
    forall dA dB : Declaration,
      Compatible dA dB -> exists g, IsGlue dA dB g.
  Proof.
    intros dA dB Hcompat.
    exists (candidate_glue dA dB).
    unfold candidate_glue, IsGlue.
    split; [| split].
    - intros k v HdA HdB. rewrite HdA. reflexivity.
    - intros k v HdB HdA. rewrite HdA. exact HdB.
    - intros k vA vB HdA HdB.
      assert (Heq : vA = vB).
      { apply (Hcompat k).
        - split; [exists vA | exists vB]; assumption.
        - exact HdA.
        - exact HdB.
      }
      subst vB.
      rewrite HdA.
      split; reflexivity.
  Qed.

  Theorem interface_disagreement_blocks_glue :
    forall (dA dB : Declaration) (k : Key) (vA vB : Value),
      dA k = Some vA -> dB k = Some vB -> vA <> vB ->
      forall g : Declaration, ~ IsGlue dA dB g.
  Proof.
    intros dA dB k vA vB HdA HdB Hneq g [_ [_ H3]].
    destruct (H3 k vA vB HdA HdB) as [Hg1 Hg2].
    rewrite Hg1 in Hg2.
    injection Hg2 as Heq.
    exact (Hneq Heq).
  Qed.

  (* The refusal rule, restated as a corollary in the exact shape the
     probe's `interface_conflict` behaviour needs: an incompatible pair
     of declarations has NO glue at all, not merely an unproved one. *)
  Corollary incompatible_has_no_glue :
    forall dA dB : Declaration,
      (exists k vA vB, dA k = Some vA /\ dB k = Some vB /\ vA <> vB) ->
      ~ (exists g, IsGlue dA dB g).
  Proof.
    intros dA dB [k [vA [vB [HdA [HdB Hneq]]]]] [g Hglue].
    exact (interface_disagreement_blocks_glue dA dB k vA vB HdA HdB Hneq g Hglue).
  Qed.

End CoupledParallelCompatibility.

(* ------------------------------------------------------------------ *)
(* A concrete witness: the same key ("shared label") present in both   *)
(* branches' declarations is NOT sufficient for compatibility -- the   *)
(* Rocq-level counterpart of the probe's organic `e12p` finding        *)
(* (SUBDIVIDE_U1 and SUBDIVIDE_U2 both name an edge `e12p`, but declare *)
(* different endpoints for it). Instantiated with the probe's own       *)
(* mechanism in miniature: Key := nat (a stand-in for an edge name),    *)
(* Value := Q (a stand-in for one piece of declared interface data,     *)
(* e.g. the declared-cycle coefficient at that edge -- see the probe's  *)
(* Case 5, where the conflict is exactly a z' value of 1 vs -1 at the   *)
(* same shared edge name).                                              *)
(* ------------------------------------------------------------------ *)

Definition branch_A_declares : Declaration nat Q :=
  fun k => if Nat.eqb k 0 then Some (1#1) else None.

Definition branch_B_declares : Declaration nat Q :=
  fun k => if Nat.eqb k 0 then Some (-(1#1)) else None.

Example shared_label_not_sufficient_for_agreement :
  SharedKey nat Q branch_A_declares branch_B_declares 0%nat /\
  ~ Compatible nat Q branch_A_declares branch_B_declares.
Proof.
  unfold branch_A_declares, branch_B_declares.
  split.
  - split; [exists (1#1) | exists (-(1#1))]; reflexivity.
  - intro Hcompat.
    assert (Heq' : (1#1) = (-(1#1))).
    { apply (Hcompat 0%nat).
      - split; [exists (1#1) | exists (-(1#1))]; reflexivity.
      - reflexivity.
      - reflexivity.
    }
    discriminate Heq'.
Qed.

Example shared_label_not_sufficient_for_agreement_no_glue :
  ~ (exists g, IsGlue nat Q branch_A_declares branch_B_declares g).
Proof.
  apply incompatible_has_no_glue.
  exists 0%nat, (1#1), (-(1#1)).
  unfold branch_A_declares, branch_B_declares.
  repeat split; try reflexivity.
  discriminate.
Qed.

(* ------------------------------------------------------------------ *)
(* Compatible aggregate-A4 cancellation (Phase 5d).                    *)
(*                                                                      *)
(* A branch's own (A4) pairing, once a shared seam is agreed, splits    *)
(* into a piece contributed by data unique to that branch and a piece   *)
(* contributed by the shared seam itself (the SAME value in both        *)
(* branches, by agreement):                                             *)
(*                                                                       *)
(*     left_total  = left_unique  + shared                              *)
(*     right_total = right_unique + shared                              *)
(*                                                                       *)
(* The glued composite's AGGREGATE pairing is NOT left_total +           *)
(* right_total: in the glued complex the shared seam appears ONCE, not   *)
(* twice (unlike disjoint parallel composition's literal concatenation,  *)
(* where nothing is shared and the naive sum is exactly right), so the   *)
(* aggregate is                                                          *)
(*                                                                        *)
(*     glued_aggregate = left_unique + right_unique + shared             *)
(*                     = left_total + right_total - shared.              *)
(*                                                                        *)
(* This single-counting correction is exactly the mistake the Python     *)
(* probe caught and fixed mid-search (see docs/design/                   *)
(* REFINEMENT_WITNESS_COMPOSITION_STATUS.md, Phase 5d): a first solve     *)
(* that assumed glued_aggregate = left_total + right_total was silently   *)
(* correct only when shared = 0, and wrong everywhere else.               *)
(* ------------------------------------------------------------------ *)

Section CompatibleAggregateCancellation.

  Variables shared left_unique right_unique : Q.

  Definition left_total : Q := left_unique + shared.
  Definition right_total : Q := right_unique + shared.
  Definition glued_aggregate : Q := left_unique + right_unique + shared.

  (* The single-counting correction, made explicit and proved, not just
     asserted in a comment: the glued aggregate is the naive disjoint-
     style sum MINUS one extra copy of the shared contribution. *)
  Theorem glued_aggregate_vs_naive_sum :
    (glued_aggregate == left_total + right_total - shared)%Q.
  Proof.
    unfold glued_aggregate, left_total, right_total.
    ring.
  Qed.

End CompatibleAggregateCancellation.

(* The example itself, grounded in the probe's own computed numbers
   (INSERT_BRIDGE, shared edge e23): the shared seam's own contribution
   is -1 (the declared-cycle coefficient -1 at e23, times the pulled-back
   residue 1 there); branch A's off-seam contribution is -4 (giving
   left_total = -5, matching the probe's branch_a pairing exactly);
   branch B's off-seam contribution is 5 (giving right_total = 4,
   matching the probe's branch_b pairing exactly). Both branch totals are
   nonzero (branchwise (A4) holds on both) yet the glued aggregate is
   exactly zero -- the same fact the probe found computationally, now
   checked independently of the Python machinery entirely. *)
Example compatible_glue_can_cancel_aggregate_A4 :
  exists (shared left_unique right_unique : Q),
    ~ (left_total shared left_unique == 0) /\
    ~ (right_total shared right_unique == 0) /\
    (glued_aggregate shared left_unique right_unique == 0).
Proof.
  exists (-(1#1)), (-(4#1)), (5#1).
  unfold left_total, right_total, glued_aggregate.
  repeat split.
  - intro H. discriminate H.
  - intro H. discriminate H.
Qed.
