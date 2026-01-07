# makefile to manage project
# commands:
#   - make setup-venv
#   - make examples
#   - make test-examples
#   - make test-requirements
#   - make test-coverage
#   - make format
#   - make format-check
#   - make build-executable
#   - make clean
#   - make clean-light
#   - make release-checklist
#   - make release-changelog
#   - make thirdpartycheck
#   - make release-upload
#   - make release

VENV_DIR := .venv
VENV_RECREATE := false

.PHONY: setup-venv
setup-venv:
	@if [ -d "$(VENV_DIR)" ]; then \
		echo "Virtual environment '$(VENV_DIR)' already exists. For recreation add 'VENV_RECREATE=true to cli.'"; \
		if [ "$(VENV_RECREATE)" = "true" ] || [ "$(VENV_RECREATE)" = "TRUE" ]; then \
			echo "Removing existing virtual environment '$(VENV_DIR)'..."; \
			rm -rf "$(VENV_DIR)"; \
		else \
			exit 0; \
		fi; \
	fi; \
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
	fi

.PHONY: examples
examples: setup-venv
	$(MAKE) -C examples

.PHONY: test-examples
test-examples: setup-venv
	$(MAKE) -C examples/sim_unit all
	@"$(VENV_DIR)/bin/python" -m pytest test/examples

.PHONY: test-requirements
test-requirements: setup-venv
	@"$(VENV_DIR)/bin/python" -m pytest

.PHONY: test-coverage
test-coverage: setup-venv
	@"$(VENV_DIR)/bin/python" -m pytest --cov --cov-report=html --cov-report=term-missing

.PHONY: format
format: setup-venv
	@"$(VENV_DIR)/bin/python" -m ruff format . --exclude ares/core/version.py --exclude .venv

.PHONY: format-check
format-check: setup-venv
	@"$(VENV_DIR)/bin/python" -m ruff format --check . --exclude ares/core/version.py --exclude .venv

.PHONY: build-executable
build-executable: setup-venv
	@echo "Building executable with PyInstaller..."
	@"$(VENV_DIR)/bin/pyinstaller" --onefile --name ares --paths . --paths packages/param_dcm --add-data "ares/plugins/simunit.py:ares/plugins" --hidden-import "ares.pydantic_models.datadictionary_model" --hidden-import "param_dcm" --hidden-import "param_dcm.param_dcm" ares/__main__.py
	@echo ""
	@echo "Executable created in dist/ares"

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

.PHONY: thirdpartycheck
thirdpartycheck: setup-venv
	@echo ""
	@echo "Running third-party dependency analysis..."
	@"$(VENV_DIR)/bin/python" scripts/analyze_dependencies.py --format json --generate-notice --check-compatibility
	@echo "Third-party dependency check complete."

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
release: release-checklist release-changelog thirdpartycheck build-executable release-upload
	@echo ""
	@echo "Release process complete!"

.PHONY: clean
clean:
	@printf "WARNING: This will permanently delete all generated files, caches, and logs. Continue? [y/n] "; \
	read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		echo "Cleaning project in mode full..."; \
		$(MAKE) clean-light; \
		rm -rf logs; \
		rm -rf build; \
		rm -rf dist; \
		rm -rf examples/output; \
		echo "Project cleaned successfully in mode full."; \
	else \
		echo "Clean cancelled."; \
	fi

.PHONY: clean-light
clean-light:
	echo "Cleaning project in mode light..."; \
	find . -type f -name "*.pyc" -delete; \
	find . -type d -name "__pycache__" -exec rm -rf {} +; \
	find . -type d -name "log" -exec rm -rf {} +; \
	find . -type d -name ".pytest_cache" -exec rm -rf {} +; \
	find . -type d -name ".ruff_cache" -exec rm -rf {} +; \
	rm -f .coverage .coverage.*; \
	rm -rf htmlcov; \
	$(MAKE) -C examples/sim_unit clean; \
	echo "Project cleaned successfully in mode light."; \
