# makefile to manage project
# commands:
#   - make setup_venv
#   - make examples
#   - make test
#   - make format
#   - make clean

VENV_DIR := .venv

.PHONY: setup_venv
setup_venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment '$(VENV_DIR)' already exists. Success!"; \
	else \
		echo "Creating virtual environment '$(VENV_DIR)'..."; \
		python3 -m venv "$(VENV_DIR)" || { echo "Error: Failed to create virtual environment."; exit 1; }; \
		echo "Installing ARES dependencies in virtual environment '$(VENV_DIR)'..."; \
		"$(VENV_DIR)/bin/pip" install -e ".[dev]" || { echo "Error: Failed to install dependencies."; exit 1; }; \
	fi
.PHONY: examples_compile
examples_compile: setup_venv
	$(MAKE) -C examples compile

.PHONY: examples_run
examples_run: setup_venv
	$(MAKE) -C examples run

.PHONY: test_all
test_all: setup_venv
	$(MAKE) -C examples/sim_unit all
	@"$(VENV_DIR)/bin/python" -m pytest test/

.PHONY: examples
examples: setup_venv
	$(MAKE) -C examples
	$(MAKE) clean

.PHONY: test
test: setup_venv
	@"$(VENV_DIR)/bin/python" -m pytest test/ --ignore=test/examples/

.PHONY: format
format: setup_venv
	@"$(VENV_DIR)/bin/python" -m ruff format . --exclude ares/core/version.py --exclude .venv

.PHONY: format_check
format_check: setup_venv
	@"$(VENV_DIR)/bin/python" -m ruff format --check . --exclude ares/core/version.py --exclude .venv

.PHONY: clean
clean:
	find . -type f -name "*.pyc" | xargs rm -fr
	find . -type d -name __pycache__ | xargs rm -fr
	find . -type d -name log | xargs rm -fr
	find . -type d -name .pytest_cache | xargs rm -fr
	find . -type d -name .ruff_cache | xargs rm -fr
	$(MAKE) -C examples/sim_unit clean
