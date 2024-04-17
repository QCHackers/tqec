# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Updating sys.path to let autodoc find the tqec package ------------------
import sys
from pathlib import Path
import typing as ty

DOCUMENTATION_DIRECTORY = Path(__file__).parent
PROJECT_DIRECTORY = DOCUMENTATION_DIRECTORY.parent
SOURCE_DIRECTORY = PROJECT_DIRECTORY / "src"

sys.path.append(str(SOURCE_DIRECTORY))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "TQEC"
copyright = "2024, TQEC Community"
author = "TQEC Community"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    # Include documentation from docstrings
    # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
    "sphinx.ext.autodoc",
    # Generate autodoc summaries
    # https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html
    "sphinx.ext.autosummary",
    # Publish HTML docs in GitHub Pages
    # https://www.sphinx-doc.org/en/master/usage/extensions/githubpages.html
    "sphinx.ext.githubpages",
    # Support for NumPy and Google style docstrings
    # https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
    "sphinx.ext.napoleon",
    # Add links to highlighted source code
    # https://www.sphinx-doc.org/en/master/usage/extensions/viewcode.html
    "sphinx.ext.viewcode",
    # A Markdown parser for Sphinx
    # https://myst-parser.readthedocs.io/en/latest/index.html
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-maximum_signature_line_length
# maximum_signature_line_length = 150
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-add_module_names
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# See https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html
html_theme_options = {
    "style_external_links": True,
    "navigation_depth": 4,
}


# -- Options for Napoleon extension ------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html#configuration
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Options for autodoc extension -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html


# Do not document tests.
def autodoc_skip_member_handler(
    app,
    what: ty.Literal["module", "class", "exception", "function", "method", "attribute"],
    name: str,
    obj,
    skip: bool,
    options,
) -> bool | None:
    # Skips test files
    if name.startswith("test_"):
        return True
    # Any non-test file is left to other filters.
    return None


# Automatically called by sphinx at startup
# From https://stackoverflow.com/a/53888481
def setup(app):
    # Connect the autodoc-skip-member event from apidoc to the callback
    app.connect("autodoc-skip-member", autodoc_skip_member_handler)
