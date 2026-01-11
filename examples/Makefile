# examples/Makefile
# commands:
#   - make example1
#   - make example2

VENV_DIR ?= ../.venv

.PHONY: all
all: example1 example2

.PHONY: example1
example1:
	@echo "Running workflow example 1..."
	@"$(VENV_DIR)/bin/python" -m ares pipeline \
		-wf workflow/workflow_example_1.json \
		--output output/ \
		--log-level=10

.PHONY: example2
example2:
	@echo "Running workflow example 2..."
	$(MAKE) -C sim_unit derivation
	$(MAKE) -C sim_unit lowpassfilterfirstorder
	$(MAKE) -C sim_unit inout-handling
	@"$(VENV_DIR)/bin/python" -m ares pipeline \
		-wf workflow/workflow_example_2.json \
		--output output/ \
		--log-level=10


