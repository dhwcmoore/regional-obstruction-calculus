open Batteries
open Printf

(*
  OCaml implementation of an exact linear algebra solver over rationals (Big_int).
  This is the core dependency for verifying admissibility conditions.
*)

module Rational = struct
  type t = Big_int.big_int * Big_int.big_int

  let zero = (Big_int.zero_big_int, Big_int.unit_big_int)
  let one = (Big_int.unit_big_int, Big_int.unit_big_int)

  let rec gcd a b =
    if Big_int.compare_big_int b Big_int.zero_big_int = 0 then a
    else gcd b (Big_int.mod_big_int a b)

  let simplify (n, d) =
    if Big_int.compare_big_int d Big_int.zero_big_int = 0 then
      failwith "Division by zero in Rational.simplify";
    let common = gcd (Big_int.abs_big_int n) (Big_int.abs_big_int d) in
    let n' = Big_int.div_big_int n common in
    let d' = Big_int.div_big_int d common in
    if Big_int.sign_big_int d' < 0 then
      (Big_int.minus_big_int n', Big_int.minus_big_int d')
    else
      (n', d')

  let of_string s =
    match String.split_on_char '/' s with
    | [num] -> (Big_int.big_int_of_string num, Big_int.unit_big_int)
    | [num; den] -> simplify (Big_int.big_int_of_string num, Big_int.big_int_of_string den)
    | _ -> failwith ("Invalid rational string: " ^ s)

  let to_string (n, d) =
    if Big_int.eq_big_int d Big_int.unit_big_int then Big_int.string_of_big_int n
    else (Big_int.string_of_big_int n) ^ "/" ^ (Big_int.string_of_big_int d)

  let add (n1, d1) (n2, d2) =
    simplify (Big_int.add_big_int (Big_int.mult_big_int n1 d2) (Big_int.mult_big_int n2 d1), Big_int.mult_big_int d1 d2)

  let sub (n1, d1) (n2, d2) =
    simplify (Big_int.sub_big_int (Big_int.mult_big_int n1 d2) (Big_int.mult_big_int n2 d1), Big_int.mult_big_int d1 d2)

  let mul (n1, d1) (n2, d2) =
    simplify (Big_int.mult_big_int n1 n2, Big_int.mult_big_int d1 d2)

  let div (n1, d1) (n2, d2) =
    if Big_int.eq_big_int n2 Big_int.zero_big_int then failwith "Division by zero";
    simplify (Big_int.mult_big_int n1 d2, Big_int.mult_big_int d1 n2)

  let is_zero (n, _) = Big_int.eq_big_int n Big_int.zero_big_int
end

type rational_matrix = Rational.t array array
type rational_vector = Rational.t array

(** Converts a matrix of strings to a rational_matrix *)
let matrix_from_strings (m: string list list) : rational_matrix =
  Array.of_list (List.map (fun row -> Array.of_list (List.map Rational.of_string row)) m)

(** Converts a vector of strings to a rational_vector *)
let vector_from_strings (v: string list) : rational_vector =
  Array.of_list (List.map Rational.of_string v)

(** Pretty print a rational matrix *)
let print_matrix m =
  Array.iter (fun row ->
    Array.iter (fun x -> printf "%8s" (Rational.to_string x)) row;
    print_newline ()
  ) m

(** Augmented matrix for solving Ax = b *)
let augmented_matrix (a: rational_matrix) (b: rational_vector) : rational_matrix =
  let rows = Array.length a in
  let cols = Array.length a.(0) in
  if rows <> Array.length b then failwith "Matrix and vector dimensions do not match";
  Array.init rows (fun i ->
    Array.append a.(i) [|b.(i)|]
  )

(** Reduced Row Echelon Form using Gaussian elimination *)
let to_rref (m: rational_matrix) : rational_matrix * int =
  let m' = Array.map Array.copy m in
  let rows = Array.length m' in
  let cols = if rows > 0 then Array.length m'.(0) else 0 in
  let rank = ref 0 in
  let pivot_row = ref 0 in

  for j = 0 to cols - 1 do
    if !pivot_row < rows then
      let i = ref !pivot_row in
      while !i < rows && Rational.is_zero m'.(!i).(j) do
        incr i
      done;

      if !i < rows then
        let tmp = m'.(!pivot_row) in
        m'.(!pivot_row) <- m'.(!i);
        m'.(!i) <- tmp;

        let pivot_val = m'.(!pivot_row).(j) in
        for k = j to cols - 1 do
          m'.(!pivot_row).(k) <- Rational.div m'.(!pivot_row).(k) pivot_val
        done;

        for i' = 0 to rows - 1 do
          if i' <> !pivot_row then
            let factor = m'.(i').(j) in
            for k = j to cols - 1 do
              m'.(i').(k) <- Rational.sub m'.(i').(k) (Rational.mul factor m'.(!pivot_row).(k))
            done
        done;
        incr pivot_row;
  done;
  done;
  rank := !pivot_row;
  (m', !rank)

(** Solves Ax = b using Gaussian elimination. *)
let solve (a: rational_matrix) (b: rational_vector) : rational_vector option =
  let aug = augmented_matrix a b in
  let rref, rank = to_rref aug in
  let rows = Array.length rref in
  let cols = Array.length rref.(0) in

  (* Check for inconsistency: a row like [0 0 ... | 1] *)
  for i = rank to rows - 1 do
    if not (Rational.is_zero rref.(i).(cols - 1)) then
      (* Inconsistent system, b is not in the image of A *)
      None
  done;

  (* System is consistent, find one solution *)
  let solution = Array.make (cols - 1) Rational.zero in
  let pivot_cols = Array.make rank (-1) in
  let p = ref 0 in
  for i = 0 to rows - 1 do
    for j = 0 to cols - 2 do
      if !p < rank && i = !p && not (Rational.is_zero rref.(i).(j)) then
        begin
          pivot_cols.(!p) <- j;
          solution.(j) <- rref.(i).(cols - 1);
          incr p;
        end
    done
  done;
  Some solution

(** Computes the rank of a matrix. *)
let rank (a: rational_matrix) : int =
  let _, r = to_rref a in
  r

(** Checks if a vector b is in the image of matrix A. *)
let in_image (a: rational_matrix) (b: rational_vector) : bool =
  let aug = augmented_matrix a b in
  let rank_A = rank a in
  let rank_aug = rank aug in
  rank_A = rank_aug

(** Computes a basis for the kernel (null space) of A. *)
let kernel_basis (a: rational_matrix) : rational_vector list =
  let rref, rank = to_rref a in
  let rows = Array.length rref in
  let cols = if rows > 0 then Array.length rref.(0) else 0 in
  let pivot_cols = ref [] in
  let free_cols = ref [] in

  let r = ref 0 in
  for j = 0 to cols - 1 do
    if !r < rows && not (Rational.is_zero rref.(!r).(j)) then
      begin
        pivot_cols := j :: !pivot_cols;
        incr r;
      end
    else
      free_cols := j :: !free_cols
  done;
  let free_cols = List.rev !free_cols in

  List.map (fun free_col_idx ->
    let v = Array.make cols Rational.zero in
    v.(free_col_idx) <- Rational.one;
    let r = ref 0 in
    for j = 0 to cols - 1 do
      if !r < rows && not (Rational.is_zero rref.(!r).(j)) then
        begin
          v.(j) <- Rational.sub Rational.zero rref.(!r).(free_col_idx);
          incr r;
        end
    done;
    v
  ) free_cols

let () =
  printf "OCaml rational linear algebra solver loaded.\n"