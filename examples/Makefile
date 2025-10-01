# examples/Makefile
# commands:
#   - make example1

VENV_DIR ?= ../.venv

.PHONY: example1_compile
example1_compile:
	$(MAKE) -C sim_unit derivation
	$(MAKE) -C sim_unit lowpassfilterfirstorder

.PHONY: example1_run
example1_run: example1_compile
	@echo "Running workflow example 1..."
	@"$(VENV_DIR)/bin/python" -m ares pipeline \
		-wf workflow/workflow_example_1.json \
		--output output/ \
		--log-level=10

.PHONY: compile
compile: example1_compile

.PHONY: run
run : example1_run
