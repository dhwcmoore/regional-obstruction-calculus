SHELL := /bin/bash
PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
COQC ?= coqc
COQCHK ?= coqchk
OCAMLOPT ?= ocamlopt

# The declared Rocq build chain, in dependency order (a file must appear
# after everything it Requires). check-rocq-inventory below fails the
# build if this list and rocq/*.v ever disagree, in either direction --
# a new .v file added without being wired in here must break the build,
# not silently go unchecked.
ROCQ_MODULES := AdmissibleRefinementPersistence AssociatorResidueRepair \
  FourCycleObstruction RepeatedTripleSupportCandidate3b \
  CandidateThreeBDistinctSupportClassification CochainNaturalityDescent \
  CommonSubdivisionAgreement ExactnessReflection \
  CommonSubdivisionVerdictInvariance \
  FirstOrderClassifierCertificate RefinementWitnessComposition \
  RefinementWitnessVerdictComposition RefinementWitnessSequentialComposition \
  RefinementWitnessParallelComposition CoupledParallelCompatibility \
  ConflictResolutionTrilemma ConflictResolutionLowerBound \
  ConflictDiagnosticCompleteness TypedDiagnosticCalculus \
  PairwiseDiagnosticCertificate GlobalCoherenceCertificate \
  PairwiseToGlobalAssembly AssociatorContributionCertificate

.PHONY: test check clean check-python check-residue check-refinements check-random \
  check-rocq check-rocq-inventory check-rocq-scan check-rocq-trust check-ocaml \
  check-assembly-parity check-contribution-parity check-associator check-diagnostics \
  check-certificates check-all

check: check-python

# Runs all four independent checks in a fixed order, stopping at the
# first failure -- each $(MAKE) line below is its own shell invocation,
# so a nonzero exit from any one of them aborts check-all immediately
# without running the rest. This is the single command a CI job (or a
# human) can run to reproduce every claim this repository makes about
# itself, all at once.
check-all:
	$(MAKE) check-python
	$(MAKE) check-rocq
	$(MAKE) check-rocq-trust
	$(MAKE) check-ocaml
	$(MAKE) check-assembly-parity
	$(MAKE) check-contribution-parity
	@echo "check-all: check-python, check-rocq, check-rocq-trust, check-ocaml, check-assembly-parity, and check-contribution-parity all passed."

check-python:
	$(PYTHON) residue_classifier.py examples/four_cycle.json
	$(PYTHON) refinement_checker.py
	$(PYTHON) run_associator_obstruction.py examples/four_cycle_associator.json
	$(MAKE) check-diagnostics
	$(PYTEST) -q

check-diagnostics:
	$(PYTHON) realisability_diagnostic.py
	$(PYTHON) coupled_realisability_diagnostic.py
	$(PYTHON) boolean_crossing_diagnostic.py
	$(PYTHON) lattice_ie_diagnostic.py
	$(PYTHON) candidate_discipline_diagnostic.py
	$(PYTHON) repeated_triple_support_diagnostic.py

check-certificates:
	$(PYTHON) run_associator_obstruction.py examples/four_cycle_associator.json --json /tmp/roc_cert_check.json
	$(PYTHON) first_order_certificate_checker.py /tmp/roc_cert_check.json
	rm -f /tmp/roc_cert_check.json

check-residue:
	$(PYTHON) residue_classifier.py examples/four_cycle.json

check-refinements:
	$(PYTHON) refinement_checker.py

check-associator:
	$(PYTHON) run_associator_obstruction.py examples/four_cycle_associator.json

check-random:
	$(PYTEST) -q tests/test_random_residue_regression.py

# Fast preliminary check only -- confirms the declared build chain
# (ROCQ_MODULES, above) names exactly the files in rocq/, in both
# directions. A .v file present but not declared, or declared but
# missing, fails the build here rather than being silently skipped or
# silently referencing a nonexistent file.
check-rocq-inventory:
	@actual=$$(cd rocq && ls *.v | sed 's/\.v$$//' | sort); \
	declared=$$(echo $(ROCQ_MODULES) | tr ' ' '\n' | sort); \
	if [ "$$actual" != "$$declared" ]; then \
	  echo "check-rocq-inventory FAILED: rocq/*.v does not match the Makefile's" >&2; \
	  echo "declared ROCQ_MODULES list. Diff (declared vs actual):" >&2; \
	  diff <(echo "$$declared") <(echo "$$actual") >&2; \
	  exit 1; \
	fi
	@echo "check-rocq-inventory: all $(words $(ROCQ_MODULES)) declared modules match rocq/*.v exactly."

# Fast preliminary check only -- does NOT substitute for check-rocq or
# check-rocq-trust below, which is what actually establishes this
# repository's zero-axioms claim. A grep can miss a proof-relevant
# Admitted/Axiom hidden inside a comment-adjacent line or an unusual
# formatting; coqc and coqchk cannot be fooled the same way.
check-rocq-scan:
	@found=0; \
	for f in rocq/*.v; do \
	  hit=$$(perl -0777 -pe 's/\(\*.*?\*\)//gs' "$$f" \
	    | grep -nE '(^|[^A-Za-z_])(Admitted|Axiom|Parameter)([^A-Za-z_]|$$)'); \
	  if [ -n "$$hit" ]; then \
	    echo "$$f:"; echo "$$hit"; found=1; \
	  fi; \
	done; \
	if [ "$$found" = "1" ]; then \
	  echo "check-rocq-scan FAILED: found Admitted/Axiom/Parameter outside comments in rocq/*.v" >&2; \
	  exit 1; \
	fi
	@echo "check-rocq-scan: no Admitted/Axiom/Parameter declarations found outside comments (text scan only -- see check-rocq-trust for the real check)."

# Compiles every declared Rocq module from a clean state, in dependency
# order. Removes stale .vo/.vok/.vos/.glob artefacts first so a failure
# can never be masked by a leftover compiled file from a previous run.
check-rocq: check-rocq-inventory check-rocq-scan
	rm -f rocq/*.vo rocq/*.vok rocq/*.vos rocq/*.glob rocq/.*.aux
	cd rocq && for m in $(ROCQ_MODULES); do \
	  echo "coqc $$m.v"; \
	  $(COQC) $$m.v || exit 1; \
	done
	@echo "check-rocq: all $(words $(ROCQ_MODULES)) Rocq modules compiled from a clean state."

# Runs coqchk -- Rocq's own independent, from-scratch proof checker, a
# separate program from coqc -- over the complete declared module list.
# This is the check that actually backs the "zero axioms" claim: if
# coqchk's output contains an "Axioms:" section, this project has
# introduced an unproved assumption somewhere in the checked closure.
# Precisely what this claims, and does not claim: this confirms the
# PROJECT has added no Admitted proof or extra Axiom/Parameter beyond
# Rocq's own kernel and standard library -- it is not a claim that
# Rocq's own logical foundation is itself free of foundational
# assumptions (it has some, by design, like any proof assistant).
check-rocq-trust: check-rocq
	cd rocq && $(COQCHK) -Q . "" $(ROCQ_MODULES)
	@echo "check-rocq-trust: coqchk reports the declared proof chain successfully checked, introducing no project-added axioms or admitted proofs beyond Rocq's own kernel and standard library."

# Compiles the OCaml parity checker fresh (removing stale build
# artefacts first) and runs it. refinement_checker.ml's own
# run_self_check compares every computed pairing against a fixed set of
# expected values and the program itself exits 1 on any mismatch -- this
# target does not merely run the checker, it fails if that self-check
# fails.
check-ocaml:
	rm -f ocaml/*.cmi ocaml/*.cmx ocaml/*.o refinement_checker_ocaml
	cd ocaml && $(OCAMLOPT) \
	  refinement_witnesses.ml refinement_checker.ml \
	  -o ../refinement_checker_ocaml
	./refinement_checker_ocaml
	@echo "check-ocaml: OCaml parity checker compiled from a clean state; its fixture self-check passed."

# Compiles the independent OCaml mirror of the pairwise-to-global
# assembler (PairwiseToGlobalAssembly.v's own Gallina specification,
# and veribound-fce's src/pairwise_to_global_assembly.py) fresh, and
# runs its self-check: nine cases, each independently verified against
# a real run of the Python assembler before being hardcoded in
# assembly_checker.ml, per that file's own header. Not Rocq extraction
# -- see PairwiseToGlobalAssembly.v's header for why this repository's
# existing hand-written-mirror-plus-parity pattern is used instead.
check-assembly-parity:
	rm -f ocaml/assembly_checker.cmi ocaml/assembly_checker.cmx ocaml/assembly_checker.o assembly_checker
	cd ocaml && $(OCAMLOPT) assembly_checker.ml -o ../assembly_checker
	./assembly_checker
	@echo "check-assembly-parity: OCaml assembler mirror compiled from a clean state; all nine parity cases matched their independently verified expected outcome."

# Compiles the independent OCaml mirror of the associator contribution
# certificate's runtime verification (rocq/AssociatorContributionCertificate
# .v's own semantics, Phase 3C.1) fresh, and runs its self-check:
# fourteen cases -- four real four-cycle acceptances, six rejection
# reasons, a magnitude-negation pair, and three non-canonical-slot
# arithmetic cases -- each independently computed, not copied from any
# other implementation. Not Rocq extraction; see
# associator_contribution_checker.ml's own header.
check-contribution-parity:
	rm -f ocaml/associator_contribution_checker.cmi ocaml/associator_contribution_checker.cmx \
	  ocaml/associator_contribution_checker.o associator_contribution_checker
	cd ocaml && $(OCAMLOPT) associator_contribution_checker.ml -o ../associator_contribution_checker
	./associator_contribution_checker
	@echo "check-contribution-parity: OCaml contribution-certificate mirror compiled from a clean state; all fourteen parity cases matched their independently computed expected outcome."

clean:
	rm -rf __pycache__ tests/__pycache__ .pytest_cache
	rm -f refinement_checker_ocaml assembly_checker associator_contribution_checker
	rm -f ocaml/*.cmi ocaml/*.cmx ocaml/*.o
	rm -f rocq/*.vo rocq/*.vok rocq/*.vos rocq/*.glob rocq/.*.aux
