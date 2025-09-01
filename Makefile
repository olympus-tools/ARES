# makefile to manage project
# commands:
# 	- make test
# 	- make format
# 	- make clean
.PHONY: test
test: 
	pytest test/

.PHONY: format
format:
	ruff format . --exclude ares/core/version.py --exclude .venv

.PHONY: clean
clean: 
	find . -type f -name "*.pyc" | xargs rm -fr
	find . -type d -name __pycache__ | xargs rm -fr
	find . -type d -name log | xargs rm -fr
	find . -type d -name .pytest_cache | xargs rm -fr
	find . -type d -name .ruff_cache | xargs rm -fr

