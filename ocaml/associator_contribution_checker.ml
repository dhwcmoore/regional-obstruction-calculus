(*
   associator_contribution_checker.ml

   Phase 3C.1 of the pairwise-to-global provenance bridge (docs/design/
   VERIFIED_CONTRIBUTION_CERTIFICATE.md): an independently authored
   runtime verifier for the contribution-certificate semantics
   rocq/AssociatorContributionCertificate.v formalises, following this
   repository's own established hand-written-mirror-plus-parity
   pattern (see that file's header and ocaml/assembly_checker.ml's own
   header for why this is not Rocq extraction).

   Reproduces AssociatorContributionValid's two checks exactly (the
   registered slot's other three fields are zero; the claimed
   contribution equals closed_form_delta of the committed data) PLUS
   two runtime-only concerns the Rocq model deliberately leaves out of
   scope (see AssociatorContributionCertificate.v's own header,
   Decision 1/2, and VERIFIED_CONTRIBUTION_CERTIFICATE.md section 6):
   registry lookup by interface_id, and digest binding -- recomputing
   a digest from the committed data and checking it against the
   certificate's claimed digest, rather than trusting a caller-supplied
   token the way Phase 2's fixture (contribution_fixture.py) did.

   Does NOT: call any Python verifier or import Python-generated
   expected results (the corpus below is hardcoded and independently
   computed, matching assembly_checker.ml's own discipline); check
   pairwise admissibility (R15's concern, untouched); invoke the
   assembler (PairwiseToGlobalAssembly.v / assemble_global_evidence
   remain untouched by this phase); infer orientation from delta0 (see
   AssociatorContributionCertificate.v's header, Decision 1 -- no such
   inference exists to perform); or claim to validate the full expanded
   associator_defect computation (Decision 2 -- this file, like the
   Rocq model, checks closed_form_delta's arithmetic only; the
   closed_form_delta == associator_defect equivalence is Python-level
   implementation evidence, tests/test_regional_composition.py's own
   200-case random property test, not re-derived or re-claimed here).

   Depends only on the OCaml standard library.
*)

module Q = struct
  type t = { n : int; d : int }

  let rec gcd a b =
    let a = abs a in
    let b = abs b in
    if b = 0 then a else gcd b (a mod b)

  let normalize n d =
    if d = 0 then invalid_arg "Q.normalize: zero denominator";
    let g = gcd n d in
    let g = if g = 0 then 1 else g in
    let n' = n / g in
    let d' = d / g in
    if d' < 0 then { n = -n'; d = -d' } else { n = n'; d = d' }

  let of_int n = { n; d = 1 }
  let neg a = { n = -a.n; d = a.d }
  let add a b = normalize ((a.n * b.d) + (b.n * a.d)) (a.d * b.d)
  let sub a b = add a (neg b)
  let equal a b = a.n = b.n && a.d = b.d
  let is_zero a = a.n = 0

  let to_string a =
    if a.d = 1 then string_of_int a.n else string_of_int a.n ^ "/" ^ string_of_int a.d
end

(* ---- Types, mirroring rocq/AssociatorContributionCertificate.v ---- *)

type slot = SlotVW | SlotUvV_W | SlotU_VvW | SlotUV

let slot_coefficient = function
  | SlotVW -> Q.of_int 1
  | SlotUvV_W -> Q.of_int (-1)
  | SlotU_VvW -> Q.of_int 1
  | SlotUV -> Q.of_int (-1)

let slot_name = function
  | SlotVW -> "VW" | SlotUvV_W -> "UvV_W" | SlotU_VvW -> "U_VvW" | SlotUV -> "UV"

type seam_correction_data = {
  mu_vw : Q.t; mu_uvv_w : Q.t; mu_u_vvw : Q.t; mu_uv : Q.t;
}

let closed_form_delta mu =
  Q.sub (Q.add (Q.sub mu.mu_vw mu.mu_uvv_w) mu.mu_u_vvw) mu.mu_uv

let slot_value s mu =
  match s with
  | SlotVW -> mu.mu_vw | SlotUvV_W -> mu.mu_uvv_w
  | SlotU_VvW -> mu.mu_u_vvw | SlotUV -> mu.mu_uv

(* Not cryptographic -- a canonical string commitment to the exact
   structured data, matching this project's existing treatment of
   "digest" as an identity-committing token (Phase 2's local_input_
   digest was likewise a plain string, never claimed cryptographic).
   Adequate per VERIFIED_CONTRIBUTION_CERTIFICATE.md section 6's own
   criterion: two objects with the same committed digest are
   indistinguishable to this function, by construction. *)
let compute_digest mu =
  Printf.sprintf "seam(%s,%s,%s,%s)"
    (Q.to_string mu.mu_vw) (Q.to_string mu.mu_uvv_w)
    (Q.to_string mu.mu_u_vvw) (Q.to_string mu.mu_uv)

let other_slots_zero s mu =
  match s with
  | SlotVW -> Q.is_zero mu.mu_uvv_w && Q.is_zero mu.mu_u_vvw && Q.is_zero mu.mu_uv
  | SlotUvV_W -> Q.is_zero mu.mu_vw && Q.is_zero mu.mu_u_vvw && Q.is_zero mu.mu_uv
  | SlotU_VvW -> Q.is_zero mu.mu_vw && Q.is_zero mu.mu_uvv_w && Q.is_zero mu.mu_uv
  | SlotUV -> Q.is_zero mu.mu_vw && Q.is_zero mu.mu_uvv_w && Q.is_zero mu.mu_u_vvw

type registered_interface = { reg_id : string; reg_slot : slot }

type contribution_certificate = {
  cert_interface_id : string;
  cert_digest : string;
  cert_contribution : Q.t;
  cert_witness : seam_correction_data;
}

type verify_result =
  | VerifiedContribution of Q.t
  | RejectedContribution of string

let lookup (registry : registered_interface list) (id : string) : registered_interface option =
  List.find_opt (fun r -> r.reg_id = id) registry

(* The runtime verifier: registry lookup, digest binding, slot
   correctness, arithmetic correctness -- in that order, each a
   distinct rejection reason so a caller can tell which check failed. *)
let verify_contribution (registry : registered_interface list) (cert : contribution_certificate)
    : verify_result =
  match lookup registry cert.cert_interface_id with
  | None -> RejectedContribution ("unknown interface identifier: " ^ cert.cert_interface_id)
  | Some reg ->
      let recomputed_digest = compute_digest cert.cert_witness in
      if recomputed_digest <> cert.cert_digest then
        RejectedContribution
          (Printf.sprintf "digest mismatch: certificate claims %s, recomputed %s"
             cert.cert_digest recomputed_digest)
      else if not (other_slots_zero reg.reg_slot cert.cert_witness) then
        RejectedContribution
          (Printf.sprintf "slot violation: registered slot %s requires the other three fields zero"
             (slot_name reg.reg_slot))
      else
        let expected = closed_form_delta cert.cert_witness in
        if Q.equal cert.cert_contribution expected then VerifiedContribution expected
        else
          RejectedContribution
            (Printf.sprintf "value mismatch: claimed %s, computed %s"
               (Q.to_string cert.cert_contribution) (Q.to_string expected))

(* ---- Parity corpus -----------------------------------------------

   Real four-cycle registry (matching rocq/AssociatorContributionCertificate
   .v's registered_e12/e23/e34/e14 and regional_composition.py's
   four_cycle_instances() exactly -- all four use SlotVW) plus three
   test-only interfaces exercising the other three slots, so acceptance
   is not merely special-cased to the one shape the existing fixture
   uses. *)

let seam mu_vw mu_uvv_w mu_u_vvw mu_uv =
  { mu_vw = Q.of_int mu_vw; mu_uvv_w = Q.of_int mu_uvv_w;
    mu_u_vvw = Q.of_int mu_u_vvw; mu_uv = Q.of_int mu_uv }

let registry = [
  { reg_id = "e12"; reg_slot = SlotVW };
  { reg_id = "e23"; reg_slot = SlotVW };
  { reg_id = "e34"; reg_slot = SlotVW };
  { reg_id = "e14"; reg_slot = SlotVW };
  { reg_id = "e_test_uv"; reg_slot = SlotUV };
  { reg_id = "e_test_uvvw"; reg_slot = SlotUvV_W };
  { reg_id = "e_test_u_vvw"; reg_slot = SlotU_VvW };
]

let cert ~id ~digest_of ~contribution ~witness =
  { cert_interface_id = id; cert_digest = digest_of; cert_contribution = Q.of_int contribution;
    cert_witness = witness }

type case = { name : string; input : contribution_certificate; expected : verify_result }

let accepted name id witness value =
  let w = witness in
  { name; input = cert ~id ~digest_of:(compute_digest w) ~contribution:value ~witness:w;
    expected = VerifiedContribution (Q.of_int value) }

let cases : case list = [
  accepted "e12_accepted" "e12" (seam 1 0 0 0) 1;
  accepted "e23_accepted" "e23" (seam 1 0 0 0) 1;
  accepted "e34_accepted" "e34" (seam 1 0 0 0) 1;
  accepted "e14_accepted" "e14" (seam (-2) 0 0 0) (-2);

  { name = "wrong_claimed_value";
    input = cert ~id:"e12" ~digest_of:(compute_digest (seam 1 0 0 0)) ~contribution:2 ~witness:(seam 1 0 0 0);
    expected = RejectedContribution "value mismatch: claimed 2, computed 1" };

  { name = "wrong_slot_via_registered_interface";
    (* well-formed data for SlotUV (only mu_uv nonzero) registered
       under e12, whose canonical slot is VW -- other_slots_zero(VW,_)
       requires mu_uv = 0, which fails. *)
    input = cert ~id:"e12" ~digest_of:(compute_digest (seam 0 0 0 3)) ~contribution:(-3) ~witness:(seam 0 0 0 3);
    expected = RejectedContribution
      "slot violation: registered slot VW requires the other three fields zero" };

  { name = "wrong_registered_sign_via_slot_mismatch";
    (* SlotVW's data (coefficient +1) registered against e_test_uvvw,
       whose canonical slot is UvV_W (coefficient -1) -- subsumed by
       the slot check in this model, since sign is entirely a function
       of slot choice (no independent sign field exists -- see
       AssociatorContributionCertificate.v's header). *)
    input = cert ~id:"e_test_uvvw" ~digest_of:(compute_digest (seam 5 0 0 0)) ~contribution:(-5) ~witness:(seam 5 0 0 0);
    expected = RejectedContribution
      "slot violation: registered slot UvV_W requires the other three fields zero" };

  { name = "unknown_interface_identity";
    input = cert ~id:"e99" ~digest_of:(compute_digest (seam 1 0 0 0)) ~contribution:1 ~witness:(seam 1 0 0 0);
    expected = RejectedContribution "unknown interface identifier: e99" };

  { name = "digest_mismatch";
    input = cert ~id:"e12" ~digest_of:"seam(9,0,0,0)" ~contribution:1 ~witness:(seam 1 0 0 0);
    expected = RejectedContribution
      "digest mismatch: certificate claims seam(9,0,0,0), recomputed seam(1,0,0,0)" };

  accepted "magnitude_negation_positive" "e12" (seam 1 0 0 0) 1;
  accepted "magnitude_negation_negated" "e12" (seam (-1) 0 0 0) (-1);

  accepted "noncanonical_slot_uv" "e_test_uv" (seam 0 0 0 7) (-7);
  accepted "noncanonical_slot_uvvw" "e_test_uvvw" (seam 0 4 0 0) (-4);
  accepted "noncanonical_slot_u_vvw" "e_test_u_vvw" (seam 0 0 9 0) 9;
]

let verify_result_equal a b =
  match a, b with
  | VerifiedContribution q1, VerifiedContribution q2 -> Q.equal q1 q2
  | RejectedContribution r1, RejectedContribution r2 -> r1 = r2
  | _ -> false

let verify_result_to_string = function
  | VerifiedContribution q -> "VERIFIED " ^ Q.to_string q
  | RejectedContribution r -> "REJECTED (" ^ r ^ ")"

let run_all () =
  List.filter_map (fun c ->
    let actual = verify_contribution registry c.input in
    if verify_result_equal actual c.expected then begin
      Printf.printf "  %-38s %s\n" c.name (verify_result_to_string actual);
      None
    end else begin
      Printf.printf "  %-38s FAILED: expected %s, got %s\n"
        c.name (verify_result_to_string c.expected) (verify_result_to_string actual);
      Some c.name
    end)
    cases

let () =
  Printf.printf "associator_contribution_checker: %d parity cases\n" (List.length cases);
  match run_all () with
  | [] -> Printf.printf "associator_contribution_checker: all cases match their independently computed expected outcome.\n"
  | failures ->
      Printf.printf "associator_contribution_checker: FAILED cases: %s\n" (String.concat ", " failures);
      exit 1
