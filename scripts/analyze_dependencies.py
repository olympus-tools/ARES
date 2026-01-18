r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$ |  $$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
|              \__|  \__|\__|  \__|\________| \______/                 |
|                                                                      |
|              Automated Rapid Embedded Simulation (c)                 |
|______________________________________________________________________|

Copyright 2025 olympus-tools contributors. Contributors to this project
are listed in the NOTICE file:

    https://github.com/olympus-tools/ARES/blob/master/NOTICE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License:

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""

import argparse
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

from typeguard import typechecked

# Licenses incompatible with Apache 2.0
INCOMPATIBLE_LICENSES = [
    "GPL-2.0",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "AGPL-3.0",
    "AGPL-3.0-only",
    "AGPL-3.0-or-later",
    "CC-BY-NC",
    "CC-BY-NC-SA",
    "CC-BY-NC-ND",
    "Commercial",
    "Proprietary",
]


@typechecked
def check_required_packages() -> bool:
    """Check if pip-licenses and pipdeptree are installed.

    Returns:
        bool: True if both packages are installed, False otherwise.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "piplicenses", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [sys.executable, "-m", "pipdeptree", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


@typechecked
def install_required_packages() -> None:
    """Install pip-licenses and pipdeptree if not already installed."""
    print("Installing required packages: pip-licenses, pipdeptree...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pip-licenses", "pipdeptree"],
            check=True,
        )
        print("✓ Required packages installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing required packages: {e}", file=sys.stderr)
        sys.exit(1)


@typechecked
def get_license_info(output_format: str = "plain") -> str:
    """Retrieve license information for all installed packages.

    Args:
        output_format (str): Output format - 'plain', 'json', 'csv', or 'markdown'.

    Returns:
        str: License information in the specified format.
    """
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "piplicenses",
                f"--format={output_format}",
                "--with-urls",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running pip-licenses: {e}", file=sys.stderr)
        return ""


@typechecked
def get_dependency_tree(output_format: str = "text") -> str:
    """Retrieve dependency tree for all installed packages.

    Args:
        output_format (str): Output format - 'text', 'json', or 'graphviz'.

    Returns:
        str: Dependency tree in the specified format.
    """
    try:
        cmd = [sys.executable, "-m", "pipdeptree"]
        if output_format == "json":
            cmd.append("--json")
        elif output_format == "graphviz":
            cmd.append("--graph-output")
            cmd.append("png")

        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running pipdeptree: {e}", file=sys.stderr)
        return ""


@typechecked
def save_to_file(content: str, filepath: Path) -> None:
    """Save content to a file.

    Args:
        content (str): Content to save.
        filepath (Path): Path to the output file.
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Saved to {filepath}")
    except OSError as e:
        print(f"✗ Error saving to {filepath}: {e}", file=sys.stderr)


@typechecked
def get_parsed_license_info() -> list[dict[str, str]]:
    """Retrieve and enrich license information.

    Returns:
        list[dict[str, str]]: List of package information dictionaries.
    """
    json_str = get_license_info(output_format="json")
    if not json_str:
        return []

    try:
        packages = json.loads(json_str)
        for pkg in packages:
            if pkg.get("License", "UNKNOWN") == "UNKNOWN":
                name = pkg.get("Name")
                if name:
                    try:
                        meta = importlib.metadata.metadata(name)
                        # Try License-Expression first, then fallback to License
                        new_license = meta.get("License-Expression") or meta.get(
                            "License"
                        )
                        if new_license:
                            pkg["License"] = new_license
                    except importlib.metadata.PackageNotFoundError:
                        pass
        return packages
    except json.JSONDecodeError:
        return []


@typechecked
def analyze_license_compliance() -> dict[str, list[str]]:
    """Analyze licenses and categorize them by type.

    Returns:
        dict[str, list[str]]: Dictionary mapping license types to package names.
    """
    packages = get_parsed_license_info()
    if not packages:
        return {}

    license_map: dict[str, list[str]] = {}

    for pkg in packages:
        license_name = pkg.get("License", "UNKNOWN")
        package_name = pkg.get("Name", "UNKNOWN")

        if license_name not in license_map:
            license_map[license_name] = []
        license_map[license_name].append(package_name)

    return license_map


@typechecked
def check_license_compatibility() -> tuple[bool, list[dict[str, str]]]:
    """Check if all dependencies have Apache 2.0 compatible licenses.

    Returns:
        tuple[bool, list[dict[str, str]]]: (is_compatible, list of incompatible packages).
            is_compatible is True if all licenses are compatible.
            Incompatible packages list contains dicts with 'name', 'version', and 'license'.
    """
    packages = get_parsed_license_info()
    if not packages:
        return True, []

    incompatible_packages: list[dict[str, str]] = []

    for pkg in packages:
        license_name = pkg.get("License", "UNKNOWN")
        package_name = pkg.get("Name", "UNKNOWN")
        version = pkg.get("Version", "UNKNOWN")

        # Check if license is in incompatible list
        for incompatible in INCOMPATIBLE_LICENSES:
            if incompatible.lower() in license_name.lower():
                incompatible_packages.append(
                    {
                        "name": package_name,
                        "version": version,
                        "license": license_name,
                    }
                )
                break

        # Warn about unknown licenses
        if license_name == "UNKNOWN":
            print(
                f"⚠️  Warning: Package '{package_name}' has UNKNOWN license - manual review required.",
                file=sys.stderr,
            )

    is_compatible = len(incompatible_packages) == 0
    return is_compatible, incompatible_packages


@typechecked
def generate_notice_file() -> str:
    """Generate NOTICE file content for Apache 2.0 compliance.

    Returns:
        str: Content of the NOTICE file with third-party license information.
    """
    packages = get_parsed_license_info()
    if not packages:
        return ""

    notice_content = [
        "ARES (Automated Rapid Embedded Simulation)",
        "Copyright 2025 olympus-tools contributors.",
        "",
        "This file is automatically generated.",
        "For complete license texts, please visit the respective project URLs.",
        "",
        "=" * 78,
        "",
        "This product contains dependencies with the following licenses:",
        "",
    ]

    # Group packages by license
    license_groups: dict[str, list[dict]] = {}
    for pkg in packages:
        license_name = pkg.get("License", "UNKNOWN")
        if license_name not in license_groups:
            license_groups[license_name] = []
        license_groups[license_name].append(pkg)

    # Sort by license type
    for license_type in sorted(license_groups.keys()):
        pkgs = license_groups[license_type]
        notice_content.append(f"{license_type} License:")
        notice_content.append("-" * 78)

        for pkg in sorted(pkgs, key=lambda x: x.get("Name", "")):
            name = pkg.get("Name", "UNKNOWN")
            version = pkg.get("Version", "UNKNOWN")
            author = pkg.get("Author", "N/A")
            url = pkg.get("URL", "N/A")

            notice_content.append(f"  * {name} {version}")
            if author != "N/A":
                notice_content.append(f"    Author: {author}")
            if url != "N/A":
                notice_content.append(f"    URL: {url}")
            notice_content.append("")

        notice_content.append("")

    # Add warning for unknown licenses
    if "UNKNOWN" in license_groups:
        notice_content.extend(
            [
                "!" * 78,
                "WARNING: The following packages have UNKNOWN licenses.",
                "Please verify their license terms manually:",
                "",
            ]
        )
        for pkg in license_groups["UNKNOWN"]:
            name = pkg.get("Name", "UNKNOWN")
            notice_content.append(f"  * {name}")
        notice_content.append("!" * 78)
        notice_content.append("")

    return "\n".join(notice_content)


@typechecked
def main() -> None:
    """Main function to analyze project dependencies."""
    parser = argparse.ArgumentParser(
        description="Analyze project dependencies using pip-licenses and pipdeptree"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("logs/dependencies"),
        help="Output directory for dependency reports (default: logs/dependencies)",
    )
    parser.add_argument(
        "--format",
        choices=["plain", "json", "markdown"],
        default="plain",
        help="Output format for license information (default: plain)",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip automatic installation of required packages",
    )
    parser.add_argument(
        "--generate-notice",
        action="store_true",
        help="Generate NOTICE file in repository root for Apache 2.0 compliance",
    )
    parser.add_argument(
        "--check-compatibility",
        action="store_true",
        help="Check if all dependencies have Apache 2.0 compatible licenses (exits with error code 1 if incompatible licenses found)",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("ARES Dependency Analysis")
    print("=" * 70)

    # Check and install required packages
    if not check_required_packages():
        if args.skip_install:
            print(
                "✗ Required packages not installed. Run without --skip-install to install them.",
                file=sys.stderr,
            )
            sys.exit(1)
        install_required_packages()

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate license information
    print("\n1. Generating license information...")
    license_info = get_license_info(output_format=args.format)
    if license_info:
        ext = "txt" if args.format == "plain" else args.format
        license_file = output_dir / f"licenses.{ext}"
        save_to_file(license_info, license_file)

    # Generate dependency tree
    print("\n2. Generating dependency tree...")
    dep_tree = get_dependency_tree(output_format="text")
    if dep_tree:
        dep_file = output_dir / "dependency_tree.txt"
        save_to_file(dep_tree, dep_file)

    # Generate dependency tree JSON
    print("\n3. Generating dependency tree (JSON)...")
    dep_tree_json = get_dependency_tree(output_format="json")
    if dep_tree_json:
        dep_json_file = output_dir / "dependency_tree.json"
        save_to_file(dep_tree_json, dep_json_file)

    # Analyze license compliance
    print("\n4. Analyzing license compliance...")
    license_map = analyze_license_compliance()
    if license_map:
        print("\nLicense Summary:")
        print("-" * 70)
        for license_type, packages in sorted(license_map.items()):
            print(f"{license_type}: {len(packages)} package(s)")
            if license_type == "UNKNOWN":
                print(f"  Packages: {', '.join(packages)}")
        print("-" * 70)

        # Save license summary
        summary_file = output_dir / "license_summary.json"
        save_to_file(json.dumps(license_map, indent=2), summary_file)

    # Generate NOTICE file if requested
    if args.generate_notice:
        print("\n5. Generating NOTICE file...")
        notice_content = generate_notice_file()
        if notice_content:
            notice_file = Path("NOTICE")
            save_to_file(notice_content, notice_file)
            print("✓ NOTICE file generated in repository root.")

    # Check license compatibility if requested
    if args.check_compatibility:
        print("\n6. Checking Apache 2.0 license compatibility...")
        is_compatible, incompatible_packages = check_license_compatibility()

        if not is_compatible:
            print("\n" + "!" * 70)
            print("✗ ERROR: Incompatible licenses detected!")
            print("!" * 70)
            print(
                "\nThe following packages have licenses incompatible with Apache 2.0:"
            )
            print("")
            for pkg in incompatible_packages:
                print(f"  ✗ {pkg['name']} {pkg['version']}")
                print(f"    License: {pkg['license']}")
                print("")
            print("!" * 70)
            print("\nAction required:")
            print("  1. Remove or replace these dependencies")
            print("  2. Seek legal advice for alternative licensing")
            print("  3. Consider dual-licensing if applicable")
            print("!" * 70)
            sys.exit(1)
        else:
            print("✓ All dependencies have Apache 2.0 compatible licenses.")

    print("\n" + "=" * 70)
    print(f"✓ Dependency analysis complete. Results saved to: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
