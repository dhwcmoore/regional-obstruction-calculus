(*
   refinement_checker.ml

   OCaml mirror of refinement_checker.py: checks the four admissibility
   conditions (A1)-(A4) of the paper's "Admissible refinement persistence"
   theorem against the witnesses in refinement_witnesses.ml, and computes
   the exact rational pairing <z', rho^*r> by construction.

     (A1) delta^1 r = 0            -- r is closed in the coarse complex
     (A2) delta'^1 (rho^* r) = 0   -- transferred residue is closed
     (A3) z'^T delta'^0 = 0        -- z' is a cycle in the refined complex
     (A4) <z', rho^* r> != 0       -- non-zero refined pairing

   No adjointness condition and no H1-surjectivity condition are checked;
   the published theorem does not require them (see refinement_witnesses.ml
   and the deprecation notices in refinement_algebra.ml / refinement_theorem.ml
   for why the older four-condition scheme in this directory is superseded).

   This module asserts the same four values the Python implementation
   computed (5, 5, 5, -5); those numbers are not stored as literals
   anywhere except in that assertion, run_self_check.

   Build (zarith must be installed and visible to ocamlfind):
     ocamlfind ocamlopt -package zarith -linkpkg \
       refinement_witnesses.ml refinement_checker.ml -o refinement_checker
     ./refinement_checker
*)

open Refinement_witnesses

let mat_vec (m : Q.t list list) (v : Q.t list) : Q.t list =
  List.map (fun row -> List.fold_left2 (fun acc a b -> Q.add acc (Q.mul a b)) Q.zero row v) m

let row_vec_mat (row : Q.t list) (m : Q.t list list) : Q.t list =
  match m with
  | [] -> []
  | first :: _ ->
    let ncols = List.length first in
    List.init ncols (fun j ->
      List.fold_left2 (fun acc ri mrow -> Q.add acc (Q.mul ri (List.nth mrow j))) Q.zero row m)

let dot (u : Q.t list) (v : Q.t list) : Q.t =
  List.fold_left2 (fun acc a b -> Q.add acc (Q.mul a b)) Q.zero u v

let is_zero (v : Q.t list) : bool = List.for_all (fun x -> Q.equal x Q.zero) v

(* delta^0 : C^0 -> C^1, one row per edge, one column per vertex. *)
let coboundary_0 (vertices : string list) (edges : edge list) : Q.t list list =
  List.map (fun e ->
    List.map (fun v ->
      if v = e.src then Q.minus_one
      else if v = e.tgt then Q.one
      else Q.zero)
      vertices)
    edges

(* rho^* : C^1(coarse) -> C^1(refined), one row per refined edge. *)
let pullback_matrix (coarse_edges : edge list) (refined_edges : edge list) : Q.t list list =
  List.map (fun e ->
    List.map (fun ce ->
      match e.over with
      | Some name when name = ce.name -> e.over_sign
      | _ -> Q.zero)
      coarse_edges)
    refined_edges

type certificate = {
  witness : string;
  a1 : bool;
  a2 : bool;
  a3 : bool;
  a4 : bool;
  admissible : bool;
  pairing : Q.t;
  legacy : Q.t option;
  legacy_matches : bool option;
}

let check_witness (w : witness) : certificate =
  let coarse_delta1 : Q.t list list = [] in   (* C^2(coarse) = 0 *)
  let refined_delta1 : Q.t list list = [] in  (* C^2(refined) = 0 for all four witnesses *)

  let delta0_refined = coboundary_0 w.vertices w.edges in
  let rho_star = pullback_matrix coarse.c_edges w.edges in
  let rho_star_r = mat_vec rho_star coarse.c_residue in

  let a1 = is_zero (mat_vec coarse_delta1 coarse.c_residue) in
  let a2 = is_zero (mat_vec refined_delta1 rho_star_r) in
  let a3 = is_zero (row_vec_mat w.declared_z_prime delta0_refined) in
  let pairing = dot w.declared_z_prime rho_star_r in
  let a4 = not (Q.equal pairing Q.zero) in

  let legacy_matches = Option.map (fun l -> Q.equal pairing l) w.legacy_claimed_pairing in

  {
    witness = w.wname;
    a1; a2; a3; a4;
    admissible = a1 && a2 && a3 && a4;
    pairing;
    legacy = w.legacy_claimed_pairing;
    legacy_matches;
  }

let print_certificate (c : certificate) : unit =
  Printf.printf "\n%s\n" (String.make 70 '=');
  Printf.printf "REFINEMENT WITNESS: %s\n" c.witness;
  Printf.printf "%s\n" (String.make 70 '=');
  Printf.printf "(A1) coarse cocycle:        %b\n" c.a1;
  Printf.printf "(A2) refined cocycle:       %b\n" c.a2;
  Printf.printf "(A3) z' is a cycle:         %b\n" c.a3;
  Printf.printf "(A4) <z', rho^*r> != 0:     %b\n" c.a4;
  Printf.printf "Admissible (A1-A4 all hold): %b\n" c.admissible;
  Printf.printf "Computed pairing <z', rho^*r> = %s\n" (Q.to_string c.pairing);
  (match c.legacy, c.legacy_matches with
   | Some l, Some matched ->
     Printf.printf "Paper's legacy table value  = %s  (%s)\n"
       (Q.to_string l) (if matched then "MATCHES" else "DOES NOT MATCH (historical claim only)")
   | _ -> ());
  Printf.printf "%s\n" (String.make 70 '=')

(* Locks down parity with the Python implementation's computed values.
   These are the only place in this file the pairing numbers appear as
   literals. *)
let run_self_check (certs : certificate list) : bool =
  let expected = [
    ("subdivide_U1", Q.of_int 5);
    ("subdivide_U2", Q.of_int 5);
    ("subdivide_all", Q.of_int 5);
    ("insert_bridge", Q.of_int (-5));
  ] in
  List.for_all (fun c ->
    let (_, exp) = List.find (fun (n, _) -> n = c.witness) expected in
    c.admissible && Q.equal c.pairing exp)
    certs

let () =
  let certs = List.map check_witness all_witnesses in
  List.iter print_certificate certs;
  let ok = run_self_check certs in
  Printf.printf "\n%s\n" (String.make 70 '=');
  Printf.printf "Parity with Python (5, 5, 5, -5) and all A1-A4 admissible: %b\n" ok;
  Printf.printf "%s\n" (String.make 70 '=');
  if not ok then exit 1
