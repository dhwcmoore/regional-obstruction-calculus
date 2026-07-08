(*
   refinement_witnesses.ml

   OCaml mirror of refinement_witnesses.py: explicit refined-complex
   constructions for the four refinement witnesses of the paper's
   "Admissible refinement persistence" section (subdivide U1, subdivide
   U2, subdivide all regions, insert bridge). Field-for-field the same
   data as the Python module -- see its docstring for the mathematical
   content and derivations; this file does not re-derive anything, it
   mirrors an already-frozen construction.

   Depends only on the OCaml standard library and a local exact rational module Q implemented over ordinary OCaml ints. Does not depend on the deprecated Core/Batteries-based
   modules in this directory (refinement_types.ml, refinement_algebra.ml,
   refinement_theorem.ml, refinement_verification.ml).
*)

module Q = struct
  type t = {
    n : int;
    d : int;
  }

  let rec gcd a b =
    let a = abs a in
    let b = abs b in
    if b = 0 then a else gcd b (a mod b)

  let normalize n d =
    if d = 0 then invalid_arg "Q.normalize: zero denominator";
    let g = gcd n d in
    let n' = n / g in
    let d' = d / g in
    if d' < 0 then { n = -n'; d = -d' }
    else { n = n'; d = d' }

  let zero =
    { n = 0; d = 1 }

  let one =
    { n = 1; d = 1 }

  let minus_one =
    { n = -1; d = 1 }

  let of_int n =
    { n; d = 1 }

  let of_ints n d =
    normalize n d

  let neg a =
    { n = -a.n; d = a.d }

  let add a b =
    normalize
      ((a.n * b.d) + (b.n * a.d))
      (a.d * b.d)

  let sub a b =
    add a (neg b)

  let mul a b =
    normalize
      (a.n * b.n)
      (a.d * b.d)

  let equal a b =
    a.n = b.n && a.d = b.d

  let is_zero a =
    a.n = 0

  let to_string q =
    if q.d = 1 then string_of_int q.n
    else string_of_int q.n ^ "/" ^ string_of_int q.d
end

type edge = {
  name : string;
  src : string;
  tgt : string;
  (* Name of the coarse edge this refined edge lies over under rho^*,
     or None if it is genuinely new (an internal split edge or a
     bridge). *)
  over : string option;
  over_sign : Q.t;
}

type witness = {
  wname : string;
  description : string;
  vertices : string list;
  edges : edge list;
  (* Declared refined cycle z', aligned index-for-index with `edges`. *)
  declared_z_prime : Q.t list;
  (* The paper's currently-printed table value, kept only for
     comparison -- not assumed or reproduced by construction. *)
  legacy_claimed_pairing : Q.t option;
}

type coarse_complex = {
  c_vertices : string list;
  c_edges : edge list;
  c_residue : Q.t list;
  c_cycle : Q.t list;
}

let qi n = Q.of_int n
let qs n d = Q.of_ints n d
let qlist ints = List.map qi ints

let plain_edge name src tgt = { name; src; tgt; over = None; over_sign = Q.one }
let over_edge name src tgt ~over ~over_sign = { name; src; tgt; over = Some over; over_sign }

let coarse : coarse_complex = {
  c_vertices = ["U1"; "U2"; "U3"; "U4"];
  c_edges = [
    plain_edge "e12" "U1" "U2";
    plain_edge "e23" "U2" "U3";
    plain_edge "e34" "U3" "U4";
    plain_edge "e14" "U1" "U4";
  ];
  c_residue = qlist [1; 1; 1; -2];
  c_cycle = qlist [-1; -1; -1; 1];
}

(* Witness 1: subdivide U1 into U1a (incoming half) / U1b (outgoing half).
   Walk: U1b -e12'-> U2 -e23-> U3 -e34-> U4 -e14r-> U1a -s1-> U1b.
   e14r runs opposite to coarse e14 (U1->U4), hence over_sign = -1. *)
let subdivide_u1 : witness = {
  wname = "subdivide_U1";
  description = "Split U1 into U1a (incoming half) and U1b (outgoing half), " ^
                "joined by an internal edge s1.";
  vertices = ["U1a"; "U1b"; "U2"; "U3"; "U4"];
  edges = [
    over_edge "e12p" "U1b" "U2" ~over:"e12" ~over_sign:Q.one;
    over_edge "e23" "U2" "U3" ~over:"e23" ~over_sign:Q.one;
    over_edge "e34" "U3" "U4" ~over:"e34" ~over_sign:Q.one;
    over_edge "e14r" "U4" "U1a" ~over:"e14" ~over_sign:Q.minus_one;
    plain_edge "s1" "U1a" "U1b";
  ];
  declared_z_prime = qlist [1; 1; 1; 1; 1];
  legacy_claimed_pairing = Some (qs (-7) 2);
}

(* Witness 2: subdivide U2 into U2a (incoming half) / U2b (outgoing half).
   Walk: U1 -e12'-> U2a -s2-> U2b -e23'-> U3 -e34-> U4 -e14r-> U1. *)
let subdivide_u2 : witness = {
  wname = "subdivide_U2";
  description = "Split U2 into U2a (incoming half) and U2b (outgoing half), " ^
                "joined by an internal edge s2.";
  vertices = ["U1"; "U2a"; "U2b"; "U3"; "U4"];
  edges = [
    over_edge "e12p" "U1" "U2a" ~over:"e12" ~over_sign:Q.one;
    plain_edge "s2" "U2a" "U2b";
    over_edge "e23p" "U2b" "U3" ~over:"e23" ~over_sign:Q.one;
    over_edge "e34" "U3" "U4" ~over:"e34" ~over_sign:Q.one;
    over_edge "e14r" "U4" "U1" ~over:"e14" ~over_sign:Q.minus_one;
  ];
  declared_z_prime = qlist [1; 1; 1; 1; 1];
  legacy_claimed_pairing = Some (qi (-4));
}

(* Witness 3: subdivide all four regions the same way.
   Walk: U1b->U2a->U2b->U3a->U3b->U4a->U4b->U1a->U1b. *)
let subdivide_all : witness = {
  wname = "subdivide_all";
  description = "Split all four vertices into incoming/outgoing halves, " ^
                "each joined by an internal edge.";
  vertices = ["U1a"; "U1b"; "U2a"; "U2b"; "U3a"; "U3b"; "U4a"; "U4b"];
  edges = [
    over_edge "e12p" "U1b" "U2a" ~over:"e12" ~over_sign:Q.one;
    plain_edge "s2" "U2a" "U2b";
    over_edge "e23p" "U2b" "U3a" ~over:"e23" ~over_sign:Q.one;
    plain_edge "s3" "U3a" "U3b";
    over_edge "e34p" "U3b" "U4a" ~over:"e34" ~over_sign:Q.one;
    plain_edge "s4" "U4a" "U4b";
    over_edge "e14r" "U4b" "U1a" ~over:"e14" ~over_sign:Q.minus_one;
    plain_edge "s1" "U1a" "U1b";
  ];
  declared_z_prime = qlist [1; 1; 1; 1; 1; 1; 1; 1];
  legacy_claimed_pairing = Some (qs (-5) 4);
}

(* Witness 4: insert a bridge edge directly between U1 and U2, with no
   new vertex. The bridge is genuinely new (over = None); the original
   four coarse edges are unchanged and pull back to themselves via the
   identity. *)
let insert_bridge : witness = {
  wname = "insert_bridge";
  description = "Add a new edge b12 directly between U1 and U2, " ^
                "alongside the unchanged original four-cycle.";
  vertices = ["U1"; "U2"; "U3"; "U4"];
  edges = [
    over_edge "e12" "U1" "U2" ~over:"e12" ~over_sign:Q.one;
    over_edge "e23" "U2" "U3" ~over:"e23" ~over_sign:Q.one;
    over_edge "e34" "U3" "U4" ~over:"e34" ~over_sign:Q.one;
    over_edge "e14" "U1" "U4" ~over:"e14" ~over_sign:Q.one;
    plain_edge "b12" "U1" "U2";
  ];
  declared_z_prime = qlist [-1; -1; -1; 1; 0];
  legacy_claimed_pairing = Some (qi (-5));
}

let all_witnesses : witness list =
  [subdivide_u1; subdivide_u2; subdivide_all; insert_bridge]
