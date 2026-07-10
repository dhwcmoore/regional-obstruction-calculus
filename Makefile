PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest

.PHONY: test check clean check-python check-residue check-refinements check-random check-rocq check-ocaml check-associator check-diagnostics check-certificates

check: check-python

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

check-rocq:
	coqc rocq/AdmissibleRefinementPersistence.v
	cd rocq && coqc AssociatorResidueRepair.v && coqc FourCycleObstruction.v && coqc RepeatedTripleSupportCandidate3b.v && coqc CandidateThreeBDistinctSupportClassification.v && coqc CochainNaturalityDescent.v && coqc CommonSubdivisionAgreement.v && coqc ExactnessReflection.v && coqc FirstOrderClassifierCertificate.v && coqc RefinementWitnessComposition.v && coqc RefinementWitnessVerdictComposition.v && coqc RefinementWitnessSequentialComposition.v && coqc RefinementWitnessParallelComposition.v && coqc CoupledParallelCompatibility.v && coqc ConflictResolutionTrilemma.v && coqc ConflictResolutionLowerBound.v && coqc ConflictDiagnosticCompleteness.v && coqc TypedDiagnosticCalculus.v && coqc PairwiseDiagnosticCertificate.v && coqc GlobalCoherenceCertificate.v

check-ocaml:
	cd ocaml && ocamlopt \
	  refinement_witnesses.ml refinement_checker.ml \
	  -o ../refinement_checker_ocaml
	./refinement_checker_ocaml

clean:
	rm -rf __pycache__ tests/__pycache__ .pytest_cache
	rm -f refinement_checker_ocaml
	rm -f ocaml/*.cmi ocaml/*.cmx ocaml/*.o
	rm -f rocq/*.vo rocq/*.vok rocq/*.vos rocq/*.glob rocq/.*.aux
