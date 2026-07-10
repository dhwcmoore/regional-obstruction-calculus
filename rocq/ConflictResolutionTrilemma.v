(*
   ConflictResolutionTrilemma.v

   Formalises docs/design/CONFLICT_RESOLUTION_TRILEMMA.md's core
   impossibility theorem. Not tied to refinement witnesses, coupled
   parallel composition, or any structure elsewhere in this project --
   this is a fact about equality and total functions of two arguments,
   true for any type. It settles nothing about WHICH conflict-resolution
   rule (if any) should ever be built for a real shared-seam interface;
   it proves only that no such rule can be simultaneously faithful to
   both sides once they actually disagree.

   Deliberately maximally abstract, in the same spirit as
   CandidateThreeBDistinctSupportClassification.v and
   CoupledParallelCompatibility.v: no Point/finiteness assumption, no
   decidable-equality hypothesis (none of the proofs below need to
   decide equality, only reason about it via Leibniz equality's own
   substitution principle).

   No `Admitted`/`Axiom`/`sorry`.
*)

Section ConflictResolutionTrilemma.

  Variable V : Type.

  (* The minimal core fact: if two declarations genuinely disagree, no
     single value can equal both of them at once. This is the load-
     bearing sentence docs/design/CONFLICT_RESOLUTION_TRILEMMA.md §3
     states in symbols. *)
  Theorem no_single_value_matches_both_declarations :
    forall x y z : V, x <> y -> ~ (z = x /\ z = y).
  Proof.
    intros x y z Hneq [Hzx Hzy].
    apply Hneq.
    transitivity z.
    - symmetry. exact Hzx.
    - exact Hzy.
  Qed.

  (* A resolver is any function V -> V -> V -- deliberately total, per
     the design doc's §2: "Refusal" is treated there as the alternative
     to having a resolver at all, not as a property a resolver can hold
     alongside the others (see §5). *)

  (* If a resolver has BOTH full left fidelity (always returns its first
     argument) and full right fidelity (always returns its second),
     then EVERY pair of elements of V must be equal -- V collapses to at
     most one distinguishable element. This is the general form of the
     impossibility: not just "you can't have both on a disagreement,"
     but "having both forces there to be no disagreement possible at
     all, anywhere in V." *)
  Theorem full_fidelity_forces_trivial_domain :
    forall resolve : V -> V -> V,
      (forall x y, resolve x y = x) ->
      (forall x y, resolve x y = y) ->
      forall x y : V, x = y.
  Proof.
    intros resolve Hleft Hright x y.
    transitivity (resolve x y).
    - symmetry. apply Hleft.
    - apply Hright.
  Qed.

  (* The operationally meaningful contrapositive: given ANY witness that
     V has two distinct elements (true of every real interface-value
     type this project's shared-seam construction actually uses -- Q,
     Edge data, coarse-parent labels all have more than one value), no
     resolver can have both fidelities. This is the theorem that
     actually rules out "just satisfy both branches" for any resolver
     ever proposed for a real shared-seam interface, not merely for the
     single disagreeing pair that triggered the conflict. *)
  Theorem no_resolver_has_both_fidelities_on_nontrivial_domain :
    forall (resolve : V -> V -> V) (a b : V),
      a <> b ->
      ~ ((forall x y, resolve x y = x) /\ (forall x y, resolve x y = y)).
  Proof.
    intros resolve a b Hneq [Hleft Hright].
    apply Hneq.
    exact (full_fidelity_forces_trivial_domain resolve Hleft Hright a b).
  Qed.

End ConflictResolutionTrilemma.

(* ------------------------------------------------------------------ *)
(* Lossy versus structured resolvers.                                  *)
(*                                                                       *)
(* The impossibility above is specifically about resolvers whose OUTPUT *)
(* is the same type V as the two disagreeing declarations ("lossy"      *)
(* resolvers). Nothing forces that. A resolver can instead be           *)
(* "structured": its codomain is some other type carrying both original *)
(* declarations, recoverable by projection. This section shows such a   *)
(* resolver always exists (trivially, by pairing) -- existence, not     *)
(* impossibility -- and that wrapping a scalar summary field inside a   *)
(* structured object does not exempt THAT field from the theorems       *)
(* above: it is still a plain V -> V -> V function on its own terms.    *)
(* ------------------------------------------------------------------ *)

Section StructuredResolvers.

  Variable V : Type.

  (* The simplest possible non-lossy resolver: keep both declarations,
     verbatim, rather than collapsing them. Not a proposed
     implementation -- an existence witness that structured resolution
     is possible at all, at essentially no cost. *)
  Definition pair_resolver (x y : V) : V * V := (x, y).

  Theorem pair_resolver_preserves_both_claims :
    forall x y : V, fst (pair_resolver x y) = x /\ snd (pair_resolver x y) = y.
  Proof.
    intros x y. split; reflexivity.
  Qed.

  (* What structure does NOT buy you: if a structured resolver also
     exposes a single "resolved" scalar field of type V, that field is
     still governed by the original impossibility, unchanged. This is
     literally no_resolver_has_both_fidelities_on_nontrivial_domain,
     restated at this scalar field to make the point explicit rather
     than left implicit. *)
  Theorem structure_does_not_exempt_the_resolved_field :
    forall (resolved : V -> V -> V) (a b : V),
      a <> b ->
      ~ ((forall x y, resolved x y = x) /\ (forall x y, resolved x y = y)).
  Proof.
    exact (no_resolver_has_both_fidelities_on_nontrivial_domain V).
  Qed.

End StructuredResolvers.
