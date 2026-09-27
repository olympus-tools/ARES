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
#   - make release-checklist
#   - make release-changelog
#   - make thirdpartycheck
#   - make release-upload
#   - make release

# Release metadata is maintained in pyproject.toml and checked against the tag.
RELEASE_TAG := $(shell git describe --tags --exact-match --match 'v[0-9]*' 2>/dev/null)
VERSION := $(shell sed -n 's/^version = "\([^"]*\)"/\1/p' pyproject.toml)
RELEASE_ARCHIVE := dist/ares-$(VERSION)-release.zip

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
	NUMBA_DISABLE_JIT=1 uv run pytest --cov --cov-report=html --cov-report=term-missing

.PHONY: format
format: setup-venv
	uv run ruff format .

.PHONY: format-check
format-check: setup-venv
	uv run ruff format --check .

.PHONY: build-executable
build-executable: setup-venv
	@echo "Building executable with PyInstaller..."
	uv run pyinstaller --onefile --name ares --paths . --paths submodules/dcmi --copy-metadata ares --add-data "ares/plugins/simunit.py$(PATHSEP)ares/plugins" --add-data "ares/plugins/merge.py$(PATHSEP)ares/plugins" --hidden-import "ares.pydantic_models.datadictionary_model" --hidden-import "dcmi" --hidden-import "dcmi.dcmi" ares/__main__.py
	@echo ""
	@echo "Executable created in dist/ares"

.PHONY: build-package
build-package: setup-venv
	@echo "Building Python packages..."
	uv build
	uv run twine check dist/*.whl dist/*.tar.gz

.PHONY: release-checklist
release-checklist:
	@echo "ARES Release Checklist:"
	@test -n "$(VERSION)" || (echo "Error: no version found in pyproject.toml."; exit 1)
	@test "$(RELEASE_TAG)" = "v$(VERSION)" || (echo "Error: current commit must have tag v$(VERSION)."; exit 1)
	@test -z "$$(git status --porcelain)" || (echo "Error: working tree must be clean."; git status --short; exit 1)
	@grep -q '^## \[$(VERSION)\]' CHANGELOG.md || (echo "Error: CHANGELOG.md has no section for $(VERSION)."; exit 1)
	@echo "Release $(VERSION) is tagged on the current commit."

.PHONY: release-changelog
release-changelog:
	@test -n "$(VERSION)" || (echo "Error: run this target on a tagged commit."; exit 1)
	@grep -q '^## \[$(VERSION)\]' CHANGELOG.md || (echo "Error: add ## [$(VERSION)] to CHANGELOG.md before releasing."; exit 1)
	@echo "CHANGELOG.md contains release $(VERSION)."

.PHONY: thirdpartycheck
thirdpartycheck: setup-venv
	@echo ""
	@echo "Running third-party dependency analysis..."
	uv run scripts/analyze_dependencies.py --format json --generate-notice --check-compatibility
	@echo "Third-party dependency check complete."

.PHONY: release-thirdpartycheck
release-thirdpartycheck: thirdpartycheck
	@test -n "$$(git rev-parse --verify --quiet origin/master)" || (echo "Error: origin/master is not available. Fetch origin/master before releasing."; exit 1)
	@git diff --quiet origin/master -- NOTICE || (echo "Error: NOTICE differs from origin/master."; echo "Update NOTICE on master before releasing."; git diff -- NOTICE; exit 1)
	@echo "NOTICE matches origin/master."

.PHONY: release-upload
release-upload:
	@echo ""
	@printf "Upload Python packages to TestPyPI, PyPI, or skip? [test/pypi/skip] "; \
	read -r REPO; \
	if [ "$$REPO" = "test" ]; then \
		uv run twine upload --repository testpypi dist/*.whl dist/*.tar.gz; \
	elif [ "$$REPO" = "pypi" ]; then \
		uv run twine upload dist/*.whl dist/*.tar.gz; \
	elif [ "$$REPO" = "skip" ]; then \
		echo "Upload skipped."; \
	else \
		echo "Invalid choice. Aborting."; exit 1; \
	fi

.PHONY: release
release: release-checklist release-changelog test-requirements test-examples format-check docs release-thirdpartycheck build-package build-executable release-artefacts release-upload
	@echo ""
	@echo "Release process complete!"

.PHONY: release-artefacts
release-artefacts: docs
	@echo "Creating release archive $(RELEASE_ARCHIVE)..."
	uv run python scripts/create_release_archive.py --version "$(VERSION)" --docs-dir docs/sphinx/_build/html

.PHONY: docs
docs: setup-venv
	uv run sphinx-build -M html docs/sphinx docs/sphinx/_build
	@echo ""
	@echo "Open docs/sphinx/_build/html/index.html in your browser."

.PHONY: clean
clean:
	uv run python scripts/clean.py
