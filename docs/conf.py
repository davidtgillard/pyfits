"""Sphinx configuration for pyfits documentation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

project = "pyfits"
copyright = "2026, David Gillard"
author = "David Gillard"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinx_copybutton",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path: list[str] = []
exclude_patterns: list[str] = ["_build"]

html_theme = "furo"
html_static_path: list[str] = []
html_baseurl = "https://davidtgillard.github.io/pyfits/"

html_theme_options = {
    "source_repository": "https://github.com/davidtgillard/pyfits",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "#3f51b5",
        "color-brand-content": "#3f51b5",
    },
    "dark_css_variables": {
        "color-brand-primary": "#7986cb",
        "color-brand-content": "#7986cb",
    },
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}

autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_include_init_with_doc = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable/", None),
}

nitpick_ignore = [
    ("py:class", "Id"),
    ("py:class", "TargetId"),
    ("py:class", "ValidateResult"),
    ("py:class", "Result"),
    ("py:class", "CDLL"),
    ("py:meth", "open"),
    ("py:meth", "close"),
    ("py:meth", "init"),
    ("py:func", "status_from_int"),
    ("py:func", "last_error"),
]

nitpick_ignore_regex = [
    (r"py:class", r"result\.result\.\w+"),
    (r"py:obj", r"result\.result\.\w+"),
]

viewcode_follow_imported_members = False


def setup(app):
    """Register Sphinx extension hooks for this documentation build."""

    def autodoc_skip_member(app, what, name, obj, skip, options):
        if what == "function" and name in ("is_err", "is_ok"):
            return True
        return skip

    app.connect("autodoc-skip-member", autodoc_skip_member)
