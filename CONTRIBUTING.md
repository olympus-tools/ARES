# Contributing to ARES

Thank you for your interest in contributing to ARES! We welcome contributions of all kinds, including bug reports, feature requests, and code improvements.

Before you begin, please read our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive environment for everyone.

## Table of Contents

* [1. Getting Started](#1-getting-started)
    * [1.1 Development Setup](#11-development-setup)
    * [1.2 Running Tests](#12-running-tests)
* [2. How to Contribute](#2-how-to-contribute)
    * [2.1 Bug Reports & Feature Requests](#21-bug-reports--feature-requests)
    * [2.2 Code Contributions](#22-code-contributions)
    * [2.3 Documentation](#23-documentation)
* [3. Understanding the Codebase](#3-understanding-the-codebase)
    * [3.1 Quick Architecture Overview](#31-quick-architecture-overview)
    * [3.2 Where to Make Changes?](#32-where-to-make-changes)
* [4. License Agreement](#4-license-agreement)
* [5. Getting Help](#5-getting-help)

---

## 1. Getting Started

### 1.1 Development Setup

To set up your development environment:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/AndraeCarotta/ares.git
   cd ares
   ```

2. **Set up a Python virtual environment:**
   ```bash
   make setup-venv
   ```
   This command creates a virtual environment in `.venv/` and installs all required dependencies from `pyproject.toml`.

3. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate     # Windows
   ```

4. **Verify the installation:**
   ```bash
   python -m ares --version
   ```

5. **VSCode Debugging (optional):**
   If you use Visual Studio Code, launch configurations for debugging the examples are already set up in `.vscode/launch.json`. You can use these to debug ARES workflows directly from the IDE.

**⚠️ NOTE:** Currently ARES is only supported for Linux.

### 1.2 Running Tests

Before submitting your changes, ensure all tests pass:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=ares --cov-report=html

# Run specific test file
pytest test/utils/test_logger.py
```

**Where to place tests:**
- Unit tests go in `test/` directory, mirroring the structure of `ares/`
- Example: Tests for `ares/utils/logger.py` → `test/utils/test_logger.py`
- Integration tests for examples → `test/examples/`

**Test requirements:**
- All new features must include tests
- Bug fixes should include a test that catches the bug
- Aim for high test coverage on critical code paths

---

## 2. How to Contribute

We encourage you to submit pull requests to fix bugs, add new features, or improve documentation.

### 2.1 Bug Reports & Feature Requests

Before you start coding, please create a new issue for your planned work. This helps us track the problem and coordinate contributions.

* For **Bug Reports**, please use our [Bug Report Template](https://github.com/AndraeCarotta/ares/issues/new?template=bug_report.md).
* For **Feature Requests**, please use our [Feature Request Template](https://github.com/AndraeCarotta/ares/issues/new?template=feature_request.md).

### 2.2 Code Contributions

**Before submitting a pull request:**

1.  **Fork the repository** and create a new branch from `master`. The branch name should be linked to your issue (e.g., `fix-issue-123` or `feature-124`).
2.  **Make your changes.** Ensure your code is well-commented and follows our coding style defined in `.github/instructions/` (e.g., `python.instructions.md` for Python files, `markdown.instructions.md` for Markdown).
3.  **Format your code** using `make format`. Verify formatting compliance with `make format-check` before committing.
4.  **Test your changes.** Verify that your code works as expected and doesn't introduce any new bugs.
5.  **Sign your commits.** All commits must be signed using GPG or SSH keys to verify authorship. See [GitHub's guide on commit signing](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits) for setup instructions.
6.  **Write clear and structured commit messages.** We use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

**In your pull request, please:**

* Reference the related issue by number (e.g., `Closes #123`).
* Provide a detailed description of your changes.
* Explain the motivation behind the change.

### 2.3 Documentation

Improving our documentation is a great way to contribute, especially if you're new to the project. You can help by:

* Correcting typos and grammatical errors.
* Improving the clarity of existing documentation.
* Adding new examples or tutorials.

---

## 3. Understanding the Codebase

Before diving into code contributions, we recommend familiarizing yourself with the ARES architecture:

📖 **[Architecture Documentation](architecture.md)** - Comprehensive technical documentation covering:
- System architecture with layer diagrams
- Class structures for all major components
- Design patterns (Flyweight, Factory, Strategy)
- Key design decisions and rationale

### 3.1 Quick Architecture Overview

ARES is organized in four main layers:

1. **Orchestration Layer** (`ares/core/`) - Pipeline and workflow execution
2. **Plugin Layer** (`ares/plugins/`) - Extensible processing units (SimUnit, custom plugins)
3. **Interface Layer** (`ares/interface/`) - File I/O handlers with caching (MF4, DCM, JSON)
4. **Base Types** (`ares/interface/`) - Core data structures (Signal, Parameter)

### 3.2 Where to Make Changes?

- **Adding a new file format?** → Implement a handler in `ares/interface/data/` or `ares/interface/parameter/`
- **Creating a custom plugin?** → See `ares/plugins/simunit.py` as reference
- **Modifying workflow logic?** → Check `ares/core/pipeline.py` and `ares/core/workflow.py`
- **Adding new base types?** → Extend `ares/interface/data/signal.py` or `ares/interface/parameter/ares_parameter.py`

---

## 4. License Agreement

By contributing to ARES, you agree that your contributions will be licensed under the **Apache License 2.0**.

All contributions must include appropriate copyright headers as defined in `.github/instructions/`. Your submissions are understood to be under the same [Apache 2.0 License](LICENSE) that covers the project.

For more details, see the [License section in the README](README.md#7-license).

---

## 5. Getting Help

If you need help or have questions about contributing:

* **GitHub Issues:** For bug reports, feature requests, or technical questions, create an [issue](https://github.com/AndraeCarotta/ares/issues)
* **Support Requests:** Use our [Support Request Template](https://github.com/AndraeCarotta/ares/issues/new?template=support_request.md)
* **Pull Request Discussions:** Ask questions directly in your PR

**Review Process:**
- Pull requests are typically reviewed within 1-2 weeks
- Maintainers may request changes or ask clarifying questions
- Once approved, your PR will be merged into the main branch

---

Thank you for your valuable contribution!
