# makefile to manage project
# commands:
#   - make setup_venv
#   - make examples
#   - make test
#   - make format
#   - make format_check
#   - make clean
#   - make release-checklist
#   - make release-changelog
#   - make release-build
#   - make release-upload
#   - make release

VENV_DIR := .venv

.PHONY: setup_venv
setup_venv:
setup_venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment '$(VENV_DIR)' already exists."; \
	else \
		echo "Creating virtual environment '$(VENV_DIR)'..."; \
		python3 -m venv "$(VENV_DIR)" || { echo "Error: Failed to create virtual environment."; exit 1; }; \
		echo "Installing project dependencies in virtual environment '$(VENV_DIR)'..."; \
		\
		# Check if .git exists to decide on versioning strategy for editable install \
		if [ ! -d ".git" ]; then \
			echo "NOTE: .git directory not found. Setting pretend version for installation."; \
			SETUPTOOLS_SCM_PRETEND_VERSION_FOR_ARES=0.0.1 "$(VENV_DIR)/bin/pip" install -e ".[dev]" || { echo "Error: Failed to install dependencies (no Git)."; exit 1; }; \
		else \
			echo "NOTE: .git directory found. Using setuptools_scm for versioning."; \
			"$(VENV_DIR)/bin/pip" install -e ".[dev]" || { echo "Error: Failed to install dependencies (with Git)."; exit 1; }; \
		fi; \
	fi

.PHONY: examples
examples: setup_venv
	$(MAKE) -C examples

.PHONY: test_examples
test_examples: setup_venv
	$(MAKE) -C examples/sim_unit all
	@"$(VENV_DIR)/bin/python" -m pytest test/examples

.PHONY: test_requirements
test_requirements: setup_venv
	@"$(VENV_DIR)/bin/python" -m pytest test/ --ignore=test/examples

.PHONY: format
format: setup_venv
	@"$(VENV_DIR)/bin/python" -m ruff format . --exclude ares/core/version.py --exclude .venv

.PHONY: format_check
format_check: setup_venv
	@"$(VENV_DIR)/bin/python" -m ruff format --check . --exclude ares/core/version.py --exclude .venv

.PHONY: release-checklist
release-checklist:
	@echo "ARES Release Checklist:"
	@VERSION=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo ""; \
	printf "Are all tests passing? [y/n] "; \
	read -r REPLY; \
	if [ "$$REPLY" != "y" ] && [ "$$REPLY" != "Y" ]; then exit 1; fi; \
	printf "Is the version \"$$VERSION\" in pyproject.toml correct? [y/n] "; \
	read -r REPLY; \
	if [ "$$REPLY" != "y" ] && [ "$$REPLY" != "Y" ]; then exit 1; fi; \
	printf "Are all changes committed and pushed to GitHub? [y/n] "; \
	read -r REPLY; \
	if [ "$$REPLY" != "y" ] && [ "$$REPLY" != "Y" ]; then exit 1; fi; \
	printf "Is git tag \"v$$VERSION\" created and pushed? [y/n] "; \
	read -r REPLY; \
	if [ "$$REPLY" != "y" ] && [ "$$REPLY" != "Y" ]; then exit 1; fi

.PHONY: release-changelog
release-changelog:
	@echo ""
	@echo "Generating CHANGELOG.md from git history..."
	@"$(VENV_DIR)/bin/python" scripts/generate_changelog.py
	@echo "CHANGELOG.md generated."

.PHONY: release-build
release-build:
	@echo ""
	@echo "Building release packages..."
	@rm -rf dist/
	@"$(VENV_DIR)/bin/python" -m build
	@"$(VENV_DIR)/bin/twine" check dist/*
	@echo ""
	@echo "Release build complete."

.PHONY: release-thirdpartycheck
release-thirdpartycheck:
	@echo ""

.PHONY: release-upload
release-upload:
	@echo ""
	@printf "Upload to TestPyPI, PyPI, or skip? [test/pypi/skip] "; \
	read -r REPO; \
	if [ "$$REPO" = "test" ]; then \
		"$(VENV_DIR)/bin/twine" upload --repository testpypi dist/*; \
	elif [ "$$REPO" = "pypi" ]; then \
		"$(VENV_DIR)/bin/twine" upload dist/*; \
	elif [ "$$REPO" = "skip" ]; then \
		echo "Upload skipped."; \
	else \
		echo "Invalid choice. Aborting."; exit 1; \
	fi

.PHONY: release
release: release-checklist release-changelog release-thirdpartycheck release-build release-upload
	@echo ""
	@echo "Release process complete!"

.PHONY: clean
clean:
	@printf "WARNING: This will permanently delete all generated files, caches, and logs. Continue? [y/n] "; \
	read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		echo "Cleaning project in mode full..."; \
		$(MAKE) clean_light; \
		rm -rf logs; \
		rm -rf examples/output; \
		echo "Project cleaned successfully in mode full."; \
	else \
		echo "Clean cancelled."; \
	fi

.PHONY: clean_light
clean_light:
	echo "Cleaning project in mode light..."; \
	find . -type f -name "*.pyc" | xargs rm -fr; \
	find . -type d -name __pycache__ | xargs rm -fr; \
	find . -type d -name log | xargs rm -fr; \
	find . -type d -name .pytest_cache | xargs rm -fr; \
	find . -type d -name .ruff_cache | xargs rm -fr; \
	$(MAKE) -C examples/sim_unit clean; \
	echo "Project cleaned successfully in mode light."; \
