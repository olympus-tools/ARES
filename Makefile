# makefile to manage project
# commands:
# 	- make test
# 	- make format
# 	- make clean
# 	- meke venv    | doesn't activate afterwards

.PHONY: venv
venv: 
	./setup_venv.sh

.PHONY: example
example: 
	source ./setup_venv.sh true && ares pipeline -wf examples/workflow/workflow_example_1.json --log-level=20

.PHONY: test
test:
	source ./setup_venv.sh true && pytest test/

.PHONY: format
format:
	source ./setup_venv.sh true && ruff format . --exclude ares/core/version.py --exclude .venv

.PHONY: clean
clean:
	find . -type f -name "*.pyc" | xargs rm -fr
	find . -type d -name __pycache__ | xargs rm -fr
	find . -type d -name log | xargs rm -fr
	find . -type d -name .pytest_cache | xargs rm -fr
	find . -type d -name .ruff_cache | xargs rm -fr

