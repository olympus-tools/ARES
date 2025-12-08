# Contributing to ARES

Thank you for your interest in contributing to ARES! We welcome contributions of all kinds, including bug reports, feature requests, and code improvements.

Before you begin, please read our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive environment for everyone.

## Table of Contents

* [1. How to Contribute](#1-how-to-contribute)
    * [1.1 Bug Reports & Feature Requests](#11-bug-reports--feature-requests)
    * [1.2 Code Contributions](#12-code-contributions)
    * [1.3 Documentation](#13-documentation)
* [2. Understanding the Codebase](#2-understanding-the-codebase)
    * [2.1 Quick Architecture Overview](#21-quick-architecture-overview)
    * [2.2 Where to Make Changes?](#22-where-to-make-changes)

---

## 1. How to Contribute

We encourage you to submit pull requests to fix bugs, add new features, or improve documentation.

### 1.1 Bug Reports & Feature Requests

Before you start coding, please create a new issue for your planned work. This helps us track the problem and coordinate contributions.

* For **Bug Reports**, please use our [Bug Report Template](https://github.com/AndraeCarotta/ares/issues/new?template=bug_report.md).
* For **Feature Requests**, please use our [Feature Request Template](https://github.com/AndraeCarotta/ares/issues/new?template=feature_request.md).

### 1.2 Code Contributions

**Before submitting a pull request:**

1.  **Fork the repository** and create a new branch from `master`. The branch name should be linked to your issue (e.g., `fix-issue-123` or `feature-124`).
2.  **Make your changes.** Ensure your code is well-commented and follows our coding style.
3.  **Format your code** using the `black` formatter.
4.  **Test your changes.** Verify that your code works as expected and doesn't introduce any new bugs.
5.  **Write clear and structured commit messages.** We use the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

**In your pull request, please:**

* Reference the related issue by number (e.g., `Closes #123`).
* Provide a detailed description of your changes.
* Explain the motivation behind the change.

### 1.3 Documentation

Improving our documentation is a great way to contribute, especially if you're new to the project. You can help by:

* Correcting typos and grammatical errors.
* Improving the clarity of existing documentation.
* Adding new examples or tutorials.

---

## 2. Understanding the Codebase

Before diving into code contributions, we recommend familiarizing yourself with the ARES architecture:

📖 **[Architecture Documentation](architecture.md)** - Comprehensive technical documentation covering:
- System architecture with layer diagrams
- Class structures for all major components
- Design patterns (Flyweight, Factory, Strategy)
- Key design decisions and rationale

### 2.1 Quick Architecture Overview

ARES is organized in four main layers:

1. **Orchestration Layer** (`ares/core/`) - Pipeline and workflow execution
2. **Plugin Layer** (`ares/plugins/`) - Extensible processing units (SimUnit, custom plugins)
3. **Interface Layer** (`ares/interface/`) - File I/O handlers with caching (MF4, DCM, JSON)
4. **Base Types** (`ares/interface/`) - Core data structures (Signal, Parameter)

### 2.2 Where to Make Changes?

- **Adding a new file format?** → Implement a handler in `ares/interface/data/` or `ares/interface/parameter/`
- **Creating a custom plugin?** → See `ares/plugins/simunit.py` as reference
- **Modifying workflow logic?** → Check `ares/core/pipeline.py` and `ares/core/workflow.py`
- **Adding new base types?** → Extend `ares/interface/data/signal.py` or `ares/interface/parameter/ares_parameter.py`

---

Thank you for your valuable contribution!
