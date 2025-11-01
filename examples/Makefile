# examples/Makefile
# commands:
#   - make example1

VENV_DIR ?= ../.venv

.PHONY: example1
example1:
	$(MAKE) -C sim_unit derivation
	$(MAKE) -C sim_unit lowpassfilterfirstorder
	$(MAKE) -C sim_unit inout_handling
	@echo "Running workflow example 1..."
	@"$(VENV_DIR)/bin/python" -m ares pipeline \
		-wf workflow/workflow_example_1.json \
		--output output/ \
		--log-level=10
