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
#   - make docs
#   - make clean
#   - make clean-light
#   - make release-checklist
#   - make release-changelog
#   - make thirdpartycheck
#   - make release-upload
#   - make release

VENV_DIR := .venv

# Platform detection for virtual environment binary path
ifeq ($(OS),Windows_NT)
	PLATFORM := windows
	PATHSEP := ;
else
	PLATFORM := unix
	PATHSEP := :
endif

# Main setup-venv target - uses POSIX shell commands (works with Git Bash on Windows)
.PHONY: setup-venv
setup-venv:
	echo "Syncing project dependencies:"	
	uv sync --all-extras

.PHONY: examples
examples: setup-venv
	$(MAKE) -C examples

.PHONY: test-examples
test-examples: setup-venv
	$(MAKE) -C examples/sim_unit all
	uv run pytest test/examples

.PHONY: test-requirements
test-requirements: setup-venv
	uv run pytest

.PHONY: test-coverage
test-coverage: setup-venv
	uv run pytest --cov --cov-report=html --cov-report=term-missing

.PHONY: format
format: setup-venv
	uv run ruff format .

.PHONY: format-check
format-check: setup-venv
	uv run ruff format --check .

.PHONY: build-executable
build-executable: setup-venv
	@echo "Building executable with PyInstaller..."
	uv run pyinstaller --onefile --name ares --paths . --paths submodules/dcmi --add-data "ares/plugins/simunit.py$(PATHSEP)ares/plugins" --add-data "ares/plugins/merge.py$(PATHSEP)ares/plugins" --hidden-import "ares.pydantic_models.datadictionary_model" --hidden-import "dcmi" --hidden-import "dcmi.dcmi" ares/__main__.py
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
	uv run scripts/generate_changelog.py
	@echo "CHANGELOG.md generated."

.PHONY: thirdpartycheck
thirdpartycheck: setup-venv
	@echo ""
	@echo "Running third-party dependency analysis..."
	uv run scripts/analyze_dependencies.py --format json --generate-notice --check-compatibility
	@echo "Third-party dependency check complete."

.PHONY: release-upload
release-upload:
	@echo ""
	@printf "Upload to TestPyPI, PyPI, or skip? [test/pypi/skip] "; \
	read -r REPO; \
	if [ "$$REPO" = "test" ]; then \
		uv run twine upload --repository testpypi dist/*; \
	elif [ "$$REPO" = "pypi" ]; then \
		uv run twine upload dist/*; \
	elif [ "$$REPO" = "skip" ]; then \
		echo "Upload skipped."; \
	else \
		echo "Invalid choice. Aborting."; exit 1; \
	fi

.PHONY: release
release: release-checklist release-changelog thirdpartycheck build-executable release-upload
	@echo ""
	@echo "Release process complete!"

.PHONY: docs
docs: setup-venv
	uv run sphinx-build -M html docs docs/_build
	@echo ""
	@echo "Open docs/_build/html/index.html in your browser."

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
		rm -rf docs/_build; \
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
	find . -type f -name "*.spec" -delete; \
	rm -f .coverage .coverage.*; \
	rm -rf htmlcov; \
	$(MAKE) -C examples/sim_unit clean; \
	echo "Project cleaned successfully in mode light."; \
