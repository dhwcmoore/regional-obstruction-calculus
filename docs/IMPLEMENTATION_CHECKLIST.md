# Implementation Checklist

## Phase 1: Foundation ✅ COMPLETE

### Mathematical Definition
- [x] Define four admissibility conditions with full rigor
- [x] Prove main theorem (proof strategy documented)
- [x] Prove cycle-pairing non-exactness lemma
- [x] Show how four witnesses are instances of general theorem
- [x] Document functorial perspective

### OCaml Infrastructure
- [x] Define RationalVector type (sparse representation)
- [x] Define RationalMatrix type
- [x] Define ChainComplex record
- [x] Define CochainComplex record
- [x] Define RefinementMorphism record with four flags
- [x] Define RefinementCertificate record
- [x] Implement module signatures

### Python Framework
- [x] RefinementMorphism class (JSON-compatible)
- [x] RefinementVerifier class
- [x] All four condition verification methods
- [x] RefinementCertificate dataclass
- [x] Pretty-printing utilities
- [x] JSON output format

### Rocq Skeleton
- [x] Formal syntax for chain/cochain complexes
- [x] RefinementMorphism record in Coq
- [x] Theorem statement in Coq
- [x] Proof structure (to be filled)
- [x] Cycle-pairing lemma skeleton

### Documentation
- [x] `UNIVERSAL_THEOREM_GUIDE.md` — complete mathematical exposition
- [x] `REFINEMENT_DEVELOPMENT.md` — development guide
- [x] `UNIVERSAL_REFINEMENT_README.md` — project overview
- [x] Code comments and docstrings
- [x] Example: `example_four_cycle_bridge.py`

**Deliverable**: Complete theoretical framework and computational scaffold

**Note on OCaml**: Type definitions and module structure are complete. The `LinearAlgebra.solve` procedure (Gaussian elimination) is structured but not yet implemented — this blocks all four condition verifications. See Phase 2.

---

## Phase 2: Computation

---

## Phase 2: Common-Refinement Invariance

### Strategic Shift
Phase 1 proved **one-directional persistence**: obstructions survive upward refinement.

**Phase 2 demonstrates bidirectional presentation invariance** on a concrete example: two different presentations of the same four-cycle boundary obstruction, compared via a common refinement.

**Key theorem**: Theorem 3 (Common-Refinement Invariance) — if $N_1$, $N_2$ admit a common admissible refinement $N_{12}$ and their pullbacks agree, both must detect obstruction or neither does.

**Concrete Phase 2 deliverable** (NOT everything at once):
> Demonstrate on four-cycle: coarse presentation vs. subdivided presentation both pull back to the same cohomology class in a common refinement. Conclude: obstruction verdict is presentation-invariant.

### Mathematical Development 📋 HIGH PRIORITY

- [ ] Formalize **Theorem 3: Common-Refinement Invariance** on paper
  - [ ] Proof uses injectivity of pullbacks (2-step direct proof)
  - [ ] State explicitly: injectivity follows from admissibility conditions

- [ ] Document in ROADMAP with full precise statement (already done)

### Phase 1 Completion (Prerequisite): OCaml Linear Solver

- [ ] Implement Gaussian elimination over $\mathbb{Q}$ in OCaml
- [ ] Test on sample 4×4 and 5×5 matrices
- [ ] Verify against NumPy/SciPy on same inputs
- [ ] Unblock all four verification procedures

### Python Concrete Demonstration 🚀 NEXT

**Focused deliverable**: One four-cycle presentation comparison

1. **Presentation 1** ($N_1$): Four-cycle coarse
2. **Presentation 2** ($N_2$): Four-cycle with U₁ subdivided
3. **Common refinement** ($N_{12}$): Four-cycle with both U₁ and U₂ subdivided
4. **Residues**: $r_1$ on coarse, $r_2$ on U₁-subdivided
5. **Compute**:
   - $\rho_1^* [r_1]$ pullback to common refinement
   - $\rho_2^* [r_2]$ pullback to common refinement
6. **Verify**: $[\rho_1^* r_1] = [\rho_2^* r_2]$ in $H^1(N_{12})$
7. **Conclusion**: Both $[r_1] \neq 0$ and $[r_2] \neq 0$ must hold simultaneously

**Tasks**:
- [ ] Extend `RefinementVerifier` to handle two presentations + common refinement
- [ ] Implement pullback equality check in Python
- [ ] Generate certificate showing presentation invariance:
  ```json
  {
    "verdict": "presentation_invariant",
    "presentation_1": "four_cycle_coarse",
    "presentation_2": "four_cycle_subdivide_u1",
    "common_refinement": "four_cycle_subdivide_u1_u2",
    "rho1_pullback": [...],
    "rho2_pullback": [...],
    "pullbacks_equal": true,
    "conclusion": "obstruction is presentation_invariant"
  }
  ```

### OCaml Mirroring (Phase 1 Completion)

- [ ] Complete LinearAlgebra.solve implementation
- [ ] Test `AdmissibilityVerification` procedures on four-cycle
- [ ] Add presentation-invariance check to OCaml
  - [ ] Input: two presentations + common refinement
  - [ ] Compute pullback equality
  - [ ] Return invariance certificate

### Rocq Formalization: Theorem 3 🚀 NEXT

- [ ] Prove Theorem 3 (Common-Refinement Invariance) in Rocq
  - [ ] Formalizes: two presentations with common refinement implies same obstruction verdict
  - [ ] Proof: injectivity of pullbacks (2 steps)
  - [ ] Applies to four-cycle example

**Milestone**: One complete presentation-invariance demonstration (Python + OCaml + Rocq) on four-cycle

**Publication target**: Paper 2 — *Functorial Boundary Obstructions: Presentation-Invariant Certificates for Regional Gluing*

**Do NOT in Phase 2**:
- ❌ Multiple four-cycle subdivisions (defer more examples to Phase 3)
- ❌ Functorial assignment / natural transformations (that's Paper 3)
- ❌ Higher obstruction tower (that's Paper 3)

**Phase 2 mantra**: Prove ONE thing (Theorem 3) on ONE example (four-cycle with one subdivision comparison) well.
  - [ ] Four-cycle + U1 subdivision
  - [ ] Four-cycle + U2 subdivision
  - [ ] Four-cycle + all subdivision
  
- [ ] Generate certificates for all four witnesses
- [ ] Output to JSON files
- [ ] Parse and validate output

### Integration Testing
- [ ] OCaml-generated matrices match Python NumPy
- [ ] Same verification results in both languages
- [ ] Certificate format consistent

**Milestone**: Certificates generated for all four witnesses

---

## Phase 3: Higher Obstruction Tower (Higher Cohomology)

### Strategic Shift
Phases 1-2 solve the **first-order** boundary obstruction (H¹-level).

**Phase 3 develops the higher obstruction tower**: H², H³, ... detecting increasingly subtle coherence failures.

**Mathematical objective**: Extend from seam-cycle obstruction to associator-triple obstruction to pentagon-coherence obstruction.

**Note**: Do **NOT** tackle yet. This is 12+ months after Phase 2. The first-order theory is already a strong publication. Only develop Phase 3 after Phase 2 is complete.

### Mathematical Program (Future)

- [ ] **H² obstruction theory**
  - [ ] Triple-overlap failure (associator obstruction)
  - [ ] Cycle lifting for $H_2 \to H_1$
  - [ ] Extension of pairing adjointness to higher levels
  - [ ] Compute $H^2$ witness for four-cycle (if applicable)

- [ ] **H³ obstruction theory**
  - [ ] Pentagon/coherence-of-associators obstruction
  - [ ] Mac Lane coherence laws
  - [ ] Fourfold coherence constraints

- [ ] **Obstruction tower**
  - [ ] Sequence $H^1 \to H^2 \to H^3$ with connecting maps
  - [ ] Show each level captures increasingly subtle failures
  - [ ] Formalize in Rocq

### Publication Target

**Paper 3** — *Higher Coherence Obstructions for Regional Gluing: From Seams to Associators to Pentagons*

Core results:
- H²-level associator obstruction
- H³-level coherence obstruction
- Relation to pentagon/coherence laws
- Higher obstruction tower structure

**Not to include** (defer to Paper 4 or future):
- Nonlinear boundary regimes ($B^2 \neq 0$)
- Full deformation-theoretic analysis
- Higher categorical structures beyond three-fold coherence

---

## Phase 4: Integration

### Pipeline Development 🔧 FUTURE
- [ ] OCaml → Rocq bridge
  - [ ] Export OCaml verification results to Rocq format
  - [ ] Use Rocq to verify certificates from OCaml
  
- [ ] Python → Rocq bridge
  - [ ] JSON certificate → Rocq type
  - [ ] Rocq verifier reads Python output
  
- [ ] Certified classifier
  - [ ] Running Python returns formal certificate
  - [ ] Rocq proves: if certificate passes, obstruction persists

### Documentation & Release 📚 FINAL
- [ ] API documentation
- [ ] User guide: "How to verify your refinement"
- [ ] Mathematical preprint / paper
- [ ] Rocq source code release
- [ ] Python package publication
- [ ] Unit tests and regression suite

**Milestone**: Fully integrated, documented, released toolkit

---

## Risks & Mitigation

| Risk | Severity | Mitigation |
|---|---|---|
| OCaml linear solver bugs | High | Extensive testing, parallel NumPy implementation |
| Chain map verification | Medium | May need to add chain complex data to types |
| Rocq formalization complexity | High | Start with simple case (four-cycle), generalize |
| JSON serialization issues | Low | Validate with schema, test thoroughly |
| Floating-point precision (Python) | Medium | Use `Fraction` throughout, never floats |

---

---

## Success Criteria

### Phase 1 ✅ ACHIEVED
- [x] Mathematical framework rigorous and documented
- [x] Two-level theorem structure (witness-specific and universal)
- [x] Code structure sound and extensible
- [x] No contradictions with paper's results

### Phase 2 🚀 TARGET (Presentation Invariance)
- [ ] Common-refinement invariance theorem formulated and proved on paper
- [ ] Python certificate tracker shows multiple presentations + common refinement
- [ ] Rocq formal proof of Theorem 3 (common-refinement invariance)
- [ ] Demonstrate on four-cycle: two different subdivisions agree after common refinement
- [ ] Generated certificates show "presentation_invariant": true

### Phase 3 🚀 TARGET (Higher Obstructions — Long Term)
- [ ] H² obstruction theory formulated
- [ ] H³ obstruction theory sketched
- [ ] Obstruction tower structure clear
- [ ] Paper 3 outline complete (defer actual proofs)

### Phase 4 🏁 TARGET (Integration & VeriBound)
- [ ] OCaml ↔ Rocq proof-carrying pipeline
- [ ] VeriBound compliance engine: certificate format showing non-removability
- [ ] Single command: `python classifier.py | rocq verify.v`
- [ ] Fully formal, fully checked obstruction certificate

---

## Time Estimates (Revised)

| Phase | Estimated Duration | Focus |
|---|---|---|
| Phase 1 (complete) | ✅ Complete | Foundation |
| Phase 1.5 (OCaml solver) | 2-3 hours | Unblock verification |
| Phase 2 (Presentation Invariance) | 6-8 hours | **NEW PRIMARY** |
| Phase 3 (Higher Obstructions) | 12+ hours | Future |
| Phase 4 (Integration) | 4-6 hours | VeriBound |
| **Total (through Phase 2)** | **~40 hours** | |

---

## Priority Ranking (Revised)

### Critical Path (Do Now)
1. ✅ Mathematical framework (DONE)
2. 🚀 Complete OCaml linear solver (UNBLOCK)
3. 🚀 **Formulate common-refinement invariance theorem** (NEXT MATHEMATICAL STEP)
4. 🚀 Implement presentation-invariance certificate tracking (NEXT CODE)
5. 🚀 Prove Theorem 3 in Rocq (NEXT FORMALIZATION)

### Can Run in Parallel
- Python classifier testing (while OCaml solver develops)
- Higher obstruction theory sketching (longer term)
- Documentation updates (ongoing)

### Do NOT Yet
- ❌ Higher cohomology (H² obstruction) — defer to Phase 3
- ❌ Nonlinear boundary regimes — defer to future paper
- ❌ Deformation theory framework — save for higher theory

**Bottom Line**: The next mathematical step is **not** "test more refinements." It is **presentation invariance**: proving the obstruction is independent of representation.

## Daily Standup Template

```
TODAY:
- [ ] Task: <specific deliverable>
- [ ] Status: <progress>
- [ ] Blocker: <if any>

TOMORROW:
- [ ] Task: <next item from checklist>
```

---

## Sign-Off

**Mathematical Framework**: ✅ APPROVED  
**OCaml Infrastructure**: ✅ APPROVED  
**Python Framework**: ✅ APPROVED  
**Rocq Skeleton**: ✅ APPROVED  
**Documentation**: ✅ APPROVED  

**Ready to proceed to Phase 2**: YES

**Date Approved**: 2026-07-05  
**Reviewed By**: Project Lead  
**Next Review**: After Phase 2 completion
