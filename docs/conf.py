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

Copyright 2025 olympus-tools contributors. Dependencies and licenses
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

import sys
from pathlib import Path

# Add project root to path so autodoc can import the package.
sys.path.insert(0, str(Path(__file__).parent.parent))

# -- Project information -----------------------------------------------------

project = "ARES"
copyright = "2026, Andrä Carotta, Jonas Bleich"
author = "Andrä Carotta, Jonas Bleich"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Suppress warnings caused by myst cross-references that are GitHub-relative
# and not resolvable in Sphinx.
suppress_warnings = ["myst.xref_missing"]

# Both .rst and .md files are supported as source files.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Napoleon (Google-style docstrings) --------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_use_rtype = False
napoleon_use_param = True

# -- Autodoc -----------------------------------------------------------------

autodoc_member_order = "bysource"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "private-members": False,
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- sphinx-autodoc-typehints ------------------------------------------------

always_document_param_types = False
typehints_fully_qualified = False

# -- Intersphinx mapping -----------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- HTML output settings ----------------------------------------------------

html_theme = "furo"
html_title = "ARES"
html_static_path = []

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
}


# -- Autodoc event hooks -----------------------------------------------------


def skip_module_docstrings(app, what, name, obj, options, lines):
    """Clear module-level docstrings.

    All modules carry an ASCII art banner as their docstring which produces
    RST parse errors. Only class, method and function docstrings are relevant
    for the API reference.
    """
    if what == "module":
        del lines[:]


def setup(app):
    """Register Sphinx event hooks."""
    app.connect("autodoc-process-docstring", skip_module_docstrings)
