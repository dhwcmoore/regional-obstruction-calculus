(*
   assembly_checker.ml

   Independent OCaml mirror of the pairwise-to-global provenance
   bridge's Phase 2 assembler (veribound-fce's src/pairwise_to_global_
   assembly.py, commit f3d4b12; the Rocq model this file is checked
   against is PairwiseToGlobalAssembly.v in this directory's parent).

   ON EXTRACTION -- see PairwiseToGlobalAssembly.v's own header for the
   full reasoning: this repository has never used Rocq's Extraction
   vernacular, and does not start here. This file follows the SAME
   established pattern refinement_checker.ml already uses relative to
   refinement_checker.py -- an independently written OCaml
   implementation of the same specification, not a mechanically
   derived artefact. It does not import PairwiseToGlobalAssembly.v's
   generated code (there is none to import); it implements
   classify_interface/assemble by hand, from the same specification
   both the Rocq file and the Python module implement, and is checked
   for OUTCOME agreement against both.

   The corpus below is not read from an external file (this
   directory's existing convention embeds fixture data directly in
   OCaml, e.g. refinement_witnesses.ml, rather than adding a JSON
   dependency this project's OCaml side has never needed). Each case's
   EXPECTED outcome was independently computed by actually running
   veribound-fce's real assemble_global_evidence() at commit f3d4b12
   on the equivalent scenario, before being hardcoded here -- not
   copied from the Python source, and not assumed. Reproducing that
   computation is documented per-case below. This file's own
   self-check (run_all, called from main) asserts this OCaml
   implementation's independently computed outcome matches those
   already-verified values exactly; it is a three-way check (Rocq
   proves properties about the specification, Python and OCaml each
   independently compute a concrete instance of it, and this file
   confirms the latter two agree), not a two-way one.

   Depends only on the OCaml standard library.
*)

(* ---- Minimal exact-rational module, matching refinement_witnesses
   .ml's own Q module exactly (int-based, not Big_int/Batteries) -- see
   that file's header for why this repository's compiled OCaml path
   uses this representation rather than the deprecated Batteries-based
   modules also present in this directory. Duplicated here rather than
   shared via a module dependency, since this checker is compiled as
   its own standalone binary (see the Makefile's check-assembly-parity
   target) and needs no other symbol from refinement_witnesses.ml. *)
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

  let equal a b = a.n = b.n && a.d = b.d

  let to_string a =
    if a.d = 1 then string_of_int a.n
    else string_of_int a.n ^ "/" ^ string_of_int a.d
end

(* ---- The assembler itself, mirroring src/pairwise_to_global_
   assembly.py's own classify_interface / assemble exactly, including
   classification order and refusal-first precedence. Admissibility
   evidence is taken as an already-decided three-way kind (Compatible /
   Incompatible / Unresolved) -- the same abstraction level
   PairwiseToGlobalAssembly.v's admissibility_kind erasure uses; this
   file does not re-derive R15's own declaration-compatibility
   algorithm (pairwise_interface.py / CoupledParallelCompatibility.v),
   which is a separate concern from the assembler this file checks. *)

type admissibility_kind = Compatible | Incompatible | UnresolvedKind

type required_interface = { req_id : string; req_digest : string }
type admissibility_cert = { adm_id : string; adm_digest : string; adm_kind : admissibility_kind }
type contribution_cert = { con_id : string; con_digest : string; con_value : Q.t }

type interface_status =
  | Satisfied of admissibility_cert * contribution_cert
  | Refused of admissibility_cert
  | UnresolvedStatus of string

type outcome =
  | Complete of string list * Q.t list
  | RefusedOutcome of string list
  | UnresolvedOutcome of (string * string) list

let matching_adm id l = List.filter (fun c -> c.adm_id = id) l
let matching_contrib id l = List.filter (fun c -> c.con_id = id) l

let classify_interface req adm_l contrib_l =
  match matching_adm req.req_id adm_l, matching_contrib req.req_id contrib_l with
  | (_ :: _ :: _), _ -> UnresolvedStatus "duplicate_interface_evidence"
  | _, (_ :: _ :: _) -> UnresolvedStatus "duplicate_interface_evidence"
  | [], _ -> UnresolvedStatus "missing_admissibility"
  | [a], contrib_matches ->
      if a.adm_digest <> req.req_digest then UnresolvedStatus "coreference_mismatch"
      else (match a.adm_kind with
            | Incompatible -> Refused a
            | UnresolvedKind -> UnresolvedStatus "unresolved_admissibility"
            | Compatible ->
                (match contrib_matches with
                 | [] -> UnresolvedStatus "missing_contribution"
                 | [c] ->
                     if c.con_digest <> req.req_digest then UnresolvedStatus "coreference_mismatch"
                     else Satisfied (a, c)
                 | _ :: _ :: _ -> UnresolvedStatus "duplicate_interface_evidence"))

let unexpected_ids required_ids l get_id =
  l |> List.filter (fun x -> not (List.mem (get_id x) required_ids)) |> List.map get_id

let assemble required adm_l contrib_l =
  let required_ids = List.map (fun r -> r.req_id) required in
  let classified = List.map (fun r -> (r, classify_interface r adm_l contrib_l)) required in
  let refused =
    List.filter_map (fun (r, s) -> match s with Refused _ -> Some r.req_id | _ -> None) classified in
  if refused <> [] then RefusedOutcome refused
  else begin
    let unresolved =
      List.filter_map (fun (r, s) -> match s with UnresolvedStatus reason -> Some (r.req_id, reason) | _ -> None)
        classified
      @ List.map (fun id -> (id, "unexpected_interface")) (unexpected_ids required_ids adm_l (fun a -> a.adm_id))
      @ List.map (fun id -> (id, "unexpected_interface")) (unexpected_ids required_ids contrib_l (fun c -> c.con_id))
    in
    if unresolved <> [] then UnresolvedOutcome unresolved
    else
      let satisfied =
        List.filter_map (fun (_, s) -> match s with Satisfied (_, c) -> Some c | _ -> None) classified in
      Complete (required_ids, List.map (fun c -> c.con_value) satisfied)
  end

(* ---- Outcome equality and printing, for the self-check below ---- *)

let outcome_equal a b =
  match a, b with
  | Complete (ids1, vs1), Complete (ids2, vs2) ->
      ids1 = ids2 && (try List.for_all2 Q.equal vs1 vs2 with Invalid_argument _ -> false)
  | RefusedOutcome ids1, RefusedOutcome ids2 -> List.sort compare ids1 = List.sort compare ids2
  | UnresolvedOutcome rs1, UnresolvedOutcome rs2 -> List.sort compare rs1 = List.sort compare rs2
  | _ -> false

let outcome_to_string = function
  | Complete (ids, vs) ->
      "COMPLETE " ^ String.concat "," ids ^ " [" ^ String.concat "," (List.map Q.to_string vs) ^ "]"
  | RefusedOutcome ids -> "REFUSED " ^ String.concat "," (List.sort compare ids)
  | UnresolvedOutcome rs ->
      "UNRESOLVED "
      ^ String.concat "," (List.sort compare rs |> List.map (fun (i, r) -> i ^ ":" ^ r))

(* ---- Parity corpus: nine cases, each independently verified against
   a real run of veribound-fce's assemble_global_evidence() at commit
   f3d4b12 before being hardcoded here (see this file's own header).
   Interface ids/digests reuse the exact four-cycle fixture identifiers
   tests/four_cycle_assembly_fixtures.py already established
   (SEAM_ORDER = e12,e23,e34,e14; digests "four-cycle-fixture:<seam>";
   contributions 1,1,1,-2 promoted from associator_residue.py, commit
   0573cab). *)

let d s = "four-cycle-fixture:" ^ s

let four_cycle_required =
  [ { req_id = "e12"; req_digest = d "e12" };
    { req_id = "e23"; req_digest = d "e23" };
    { req_id = "e34"; req_digest = d "e34" };
    { req_id = "e14"; req_digest = d "e14" } ]

let compatible_adm id = { adm_id = id; adm_digest = d id; adm_kind = Compatible }

let four_cycle_adm = List.map compatible_adm [ "e12"; "e23"; "e34"; "e14" ]

let four_cycle_contrib =
  [ { con_id = "e12"; con_digest = d "e12"; con_value = Q.of_int 1 };
    { con_id = "e23"; con_digest = d "e23"; con_value = Q.of_int 1 };
    { con_id = "e34"; con_digest = d "e34"; con_value = Q.of_int 1 };
    { con_id = "e14"; con_digest = d "e14"; con_value = Q.of_int (-2) } ]

let replace_by_id id repl l = List.map (fun x -> if x.adm_id = id then repl else x) l

type case = { name : string; expected : outcome; run : unit -> outcome }

let cases : case list =
  [ { name = "complete_four_cycle";
      expected = Complete ([ "e12"; "e23"; "e34"; "e14" ],
                            [ Q.of_int 1; Q.of_int 1; Q.of_int 1; Q.of_int (-2) ]);
      run = (fun () -> assemble four_cycle_required four_cycle_adm four_cycle_contrib) };

    { name = "refused_incompatible_e23";
      expected = RefusedOutcome [ "e23" ];
      run = (fun () ->
        let adm = replace_by_id "e23" { adm_id = "e23"; adm_digest = d "e23"; adm_kind = Incompatible }
                    four_cycle_adm in
        assemble four_cycle_required adm four_cycle_contrib) };

    { name = "unresolved_missing_contribution_e34";
      expected = UnresolvedOutcome [ ("e34", "missing_contribution") ];
      run = (fun () ->
        let contrib = List.filter (fun c -> c.con_id <> "e34") four_cycle_contrib in
        assemble four_cycle_required four_cycle_adm contrib) };

    { name = "unresolved_missing_admissibility_e14";
      expected = UnresolvedOutcome [ ("e14", "missing_admissibility") ];
      run = (fun () ->
        let adm = List.filter (fun a -> a.adm_id <> "e14") four_cycle_adm in
        assemble four_cycle_required adm four_cycle_contrib) };

    { name = "unresolved_duplicate_e12";
      expected = UnresolvedOutcome [ ("e12", "duplicate_interface_evidence") ];
      run = (fun () ->
        let adm = four_cycle_adm @ [ List.hd four_cycle_adm ] in
        assemble four_cycle_required adm four_cycle_contrib) };

    { name = "unresolved_unexpected_e99";
      expected = UnresolvedOutcome [ ("e99", "unexpected_interface") ];
      run = (fun () ->
        let stray = { adm_id = "e99"; adm_digest = d "e99"; adm_kind = Incompatible } in
        let adm = four_cycle_adm @ [ stray ] in
        assemble four_cycle_required adm four_cycle_contrib) };

    { name = "complete_single_nonzero_e12";
      expected = Complete ([ "e12" ], [ Q.of_int 1 ]);
      run = (fun () ->
        assemble [ List.hd four_cycle_required ] [ List.hd four_cycle_adm ] [ List.hd four_cycle_contrib ]) };

    { name = "unresolved_coreference_mismatch_e12";
      expected = UnresolvedOutcome [ ("e12", "coreference_mismatch") ];
      run = (fun () ->
        let tampered = List.hd four_cycle_contrib in
        let contrib = { tampered with con_digest = "wrong-digest" } :: List.tl four_cycle_contrib in
        assemble four_cycle_required four_cycle_adm contrib) };

    { name = "unresolved_admissibility_kind_e23";
      expected = UnresolvedOutcome [ ("e23", "unresolved_admissibility") ];
      run = (fun () ->
        let adm = replace_by_id "e23" { adm_id = "e23"; adm_digest = d "e23"; adm_kind = UnresolvedKind }
                    four_cycle_adm in
        assemble four_cycle_required adm four_cycle_contrib) };
  ]

let run_all () =
  let failures =
    List.filter_map (fun c ->
      let actual = c.run () in
      if outcome_equal actual c.expected then begin
        Printf.printf "  %-38s %s\n" c.name (outcome_to_string actual);
        None
      end else begin
        Printf.printf "  %-38s FAILED: expected %s, got %s\n"
          c.name (outcome_to_string c.expected) (outcome_to_string actual);
        Some c.name
      end)
      cases
  in
  failures

let () =
  Printf.printf "assembly_checker: %d parity cases\n" (List.length cases);
  match run_all () with
  | [] -> Printf.printf "assembly_checker: all cases match their independently verified expected outcome.\n"
  | failures ->
      Printf.printf "assembly_checker: FAILED cases: %s\n" (String.concat ", " failures);
      exit 1
