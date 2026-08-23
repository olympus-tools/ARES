---
name: ares-review
description: 'Review code for compliance with ares project conventions. Use when: reviewing files, checking python code quality, validating test coverage, auditing code for best practices, pre-merge review.'
---

## ARES Code Review

Systematic review of code for compliance with ares project best practices and olympic tools conventions.

## When to Use

- **Before submitting pull requests** - Review changed files on your branch
- **Pre-commit checks** - Quick scan of staged or modified files
- Checking test coverage and unit test quality

## Review Procedure

### Step 1: Scope the Review

Determine what to review using one of these approaches:

**A. Branch-Based Review (Recommended for PRs)**
1. Check git for changed files on current branch:
   ```bash
   git diff --name-only origin/master...HEAD
   ```
   or
   ```bash
   git diff --name-only --cached  # for staged files
   ```
2. Filter for relevant file types *.py, *.json, *.md, Makefile)
3. Review only the changed files

**Note**: This repository uses `master` as the main branch, not `main`.

**B. Explicit Scope**
Ask the user which folders or files to review:
- Specific package (e.g., `submodules/mati`,`submodules/*`)
- Individual files

**C. Default Fallback**
If not specified, default to reviewing the current file or directory.

### Step 2: Scan Files

Use `file_search` and `grep_search` to locate:
- Python files (`.py`)
- Makefiles (`Makefile`)
- Test files (`*_test.py`, `test_*.py`, `test/*.py`)

### Step 3: Run Compliance Checks

Perform systematic checks based on file type. See **Check Categories** below.

**Important**: Load all available language instructions and testing instruction files: 
- [ARES README](../../../README.md)
- [python](../../instructions/python.instructions.md)
- [markdown](../../instructions/markdown.instructions.md)
- [testing-examples](../../instructions/testing-examples.instructions.md)
- [testing-unit](../../instructions/testing-unit.instructions.md)

### Step 4: Generate Report

Produce a structured report with:
- **Major Findings (Mandatory)**: Violations that must be fixed
- **Minor Findings (Optional)**: Improvements recommended but not blocking
- **Examples**: Specific fix suggestions with before/after code

Format as:
```
## Major Findings

### [Category] File: path/to/file.ext
- **Issue**: Description of the problem
- **Line**: 42 (if applicable)
- **Fix**: Specific remediation steps
- **Example**: Code snippet showing correct pattern

## Minor Findings

### [Category] File: path/to/file.ext
...
```

### Step 5: Create Summary File

**Always create a markdown summary file** documenting the review results. This provides a permanent record for PR reviews and compliance tracking.

**File Naming**: `ares-review-<branch-name>.md`

**Required Content**:

1. **Change Statistics**: Run git commands to gather metrics:
   ```bash
   git diff --stat origin/master...HEAD
   git diff --shortstat origin/master...HEAD
   ```

2. **File Organization**: Group changed files by folder/subfolder - `test/unit`, `test/examples`, `ares/interface`, etc.

3. **Complete Findings**: Include all major and minor findings with file references

See **Review Output Format** section below for the complete template.

## Check Categories

This section maps ares skill conventions to review checks.

### Python File Checks

**References**:
- [Python Best Practices](../../instructions/python.instructions.md)

Check for compliance with both ares-specific conventions and general Python best practices.

#### Major Findings

1. **Missing docstrings** (ARES Documentation rule)
   - Check: Public functions/classes without Google-style docstrings
   - Must include: Args, Returns, Raises sections

2. **Missing type hints** (ARES Typing rule)
   - Check: Function parameters without type annotations
   - Must include: Parameter types and return type

3. **Broad exception handling** (ARES Exceptions rule)
   - Check: `except Exception:` or `except:` without specificity
   - Must use: Specific exceptions like `ValueError`, `TypeError`

4. **Uncommented code** (ARES Code Documentation Requirements)
   - Check: Complex logic without inline comments
   - Must include: Comments explaining non-obvious decisions

#### Minor Findings

1. **Inappropriate .get() usage** (ARES Defensive Programming rule)
   - Check: `.get()` on internal/validated data structures
   - Should use: Direct dict access for internal data

### Test File Checks

Reference: [ARES Unit Tests](../../instructions/testing-unit.instructions.md)

#### Major Findings

1. **Missing tests for public functions**
   - Check: Public functions in module without corresponding tests
   - Must have: Test cases using `pytest` framework

2. **Tests without descriptive names**
   - Check: Test names like `test_1`, `test_case`
   - Must use: Descriptive names like `test_function_returns_expected_value`

#### Minor Findings

1. **Missing test docstrings**
   - Check: Test methods without docstrings
   - Should have: Brief docstring explaining what is being tested

2. **Not using mocks for external dependencies**
   - Check: Tests that import external services without mocking
   - Should use: `@patch` decorator to mock dependencies

### Markdown File Checks

Reference: GitHub-style admonitions for standalone documentation

For **standalone .md files not included in mkdocs**, only these admonitions are valid:

#### Valid Admonitions

1. **NOTE** - Highlights information that users should take into account, even when skimming
   ```markdown
   > [!NOTE]  
   > Highlights information that users should take into account, even when skimming.
   ```

2. **TIP** - Optional information to help a user be more successful
   ```markdown
   > [!TIP]
   > Optional information to help a user be more successful.
   ```

3. **IMPORTANT** - Crucial information necessary for users to succeed
   ```markdown
   > [!IMPORTANT]  
   > Crucial information necessary for users to succeed.
   ```

4. **WARNING** - Critical content demanding immediate user attention due to potential risks
   ```markdown
   > [!WARNING]  
   > Critical content demanding immediate user attention due to potential risks.
   ```

5. **CAUTION** - Negative potential consequences of an action
   ```markdown
   > [!CAUTION]
   > Negative potential consequences of an action.
   ```

#### Major Findings

1. **Invalid admonition types**
   - Check: Use of non-standard admonitions (e.g., `DANGER`, `INFO`, `RECOMMENDATION`, `HINT`)
   - Pattern: `> \[!((?!NOTE|TIP|IMPORTANT|WARNING|CAUTION)\w+)\]`
   - Must use: Only the 5 valid admonitions listed above

2. **Incorrect admonition syntax**
   - Check: Missing `!` or incorrect bracket format
   - Pattern: `> \[(?!!).*\]` or malformed syntax
   - Must use: Proper GitHub-flavored markdown format `> [!TYPE]`

#### Minor Findings

1. **Inconsistent admonition usage**
   - Check: Same type of information using different admonition types
   - Should use: Consistent admonition types for similar contexts

## Review Output Format

**IMPORTANT**: Always create a markdown file with the review summary. Use the template below.

### Summary File Template

Save the review results to a file named `ares-review-<branch-name>.md`:

```markdown
# ARES Compliance Review

**Date**: YYYY-MM-DD  
**Reviewer**: GitHub Copilot  
**Scope**: [branch-based | package | file-based]  
**Branch**: [current-branch-name] (if applicable)

## Change Statistics

**Files Changed**: N files  
**Lines Added**: +XXX  
**Lines Removed**: -YYY  

```bash
# Git diff statistics
<output from: git diff --stat origin/master...HEAD>
```

## Files by Folder

Group files by ares/<folder> and test/<folder>:

### `folder1/` (X files)
- file1.py
- file2.bzl
- BUILD.bazel

### `folder2/` (Y files)
- file3.py
- file4.py

## Review Summary

**Total Files Reviewed**: N  
- Python files: X
- Make files: Y
- Test files: W
- Other: M

**Compliance Status**:
- ✅ **Compliant**: N files
- ⚠️  **Minor Issues**: M files
- ❌ **Major Issues**: K files

**Finding Summary**:
- **Major Findings**: N (mandatory fixes)
- **Minor Findings**: M (optional improvements)

---

## Major Findings

### [Category] File: path/to/file.ext
- **Issue**: Description of the problem
- **Line**: 42 (if applicable)
- **Rule**: Reference to ares skill/instruction section (e.g., "ARES rule #3")
- **Fix**: Specific remediation steps
- **Example**: 
  ```python
  # Correct pattern
  ```

## Minor Findings

### [Category] File: path/to/file.ext
- **Issue**: Description
- **Rule**: Reference to ARES skill/instruction section
- **Fix**: Brief remediation guidance

---

## Next Steps

1. [ ] Fix all major findings (mandatory)
2. [ ] Consider addressing minor findings
3. [ ] Re-run review after fixes
4. [ ] Update this document with resolution status

## Review Metadata

- **ares-review Skill Version**: [link to commit]
- **Best Practices Referenced**:
  - [ARES README](../../../README.md)
  - [ARES python instructions](../../instructions/python.instructions.md)
  - [ARES markdown instructions](../../instructions/markdown.instructions.md)
```

## Quick Usage Guide

### Review Changed Files on Branch (Recommended for PRs)
```
Review my branch changes for ares compliance
```
or
```
Check all files I changed for ares violations
```

### Pre-Merge Review
```
I'm about to submit a PR - review my changes for compliance
```

### Current File
```
Review this file for ares standards
```

## Tips for Effective Reviews

1. **Consult language best practices**: Always review the relevant best practices documentation:
  - [ARES README](../../../README.md)
  - [ARES python instructions](../../instructions/python.instructions.md)
  - [ARES markdown instructions](../../instructions/markdown.instructions.md)

2. **Always create a summary file**: Document every review in a markdown file using the template from the "Review Output Format" section. This provides a permanent record for compliance tracking and PR reviews.

3. **Gather change statistics first**: Run `git diff --stat` and `git diff --shortstat` at the beginning to understand the scope of changes

4. **Start broad, then focus**: Scan entire directory structure first, then deep-dive into specific files

5. **Prioritize major findings**: Fix mandatory issues before optional improvements

6. **Show examples from documentation**: Point to the correct code examples in the ares insturctions,readme's or best practices for fixes

7. **Check related files**: Review tests alongside implementation

8. **Batch similar issues**: Group repeated violations (e.g., "5 functions missing docstrings")

## Tools to Use

### Git Commands for Branch Reviews
```bash
# Get files changed on current branch vs master
git diff --name-only origin/master...HEAD

# Get staged files
git diff --name-only --cached

# Get change statistics (for summary file)
git diff --stat origin/master...HEAD
git diff --shortstat origin/master...HEAD

# Get detailed line-by-line statistics per file
git diff --numstat origin/master...HEAD

# Get all changed files including untracked
git status --short

# Get files changed in last N commits
git diff --name-only HEAD~N..HEAD

# Get current branch name
git branch --show-current
```

**Note**: This repository uses `master` as the default branch and `origin` as the remote.

### ARES Search Tools
- `file_search` - Find Python files by pattern
- `grep_search` - Search for specific patterns (e.g., commented commands, broad exceptions)
- `read_file` - Inspect files for violations
- `semantic_search` - Find similar code patterns
