# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from datetime import datetime

# Add project root and src to sys.path so autodoc can import the packages
sys.path.insert(0, os.path.abspath(os.path.join('..', 'src')))

# -- Project information -----------------------------------------------------
project = 'Logikus'
author = 'Heiko Sippel'
copyright = f"{datetime.now().year}, {author}"

# The full version, including alpha/beta/rc tags
release = '0.1.1'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # <-- enable Google/NumPy style docstrings
    'sphinx.ext.viewcode',
]

# Allow Markdown files (README.md) to be used as Sphinx source files by
# enabling the MyST parser extension and adding .md to source suffixes.
extensions.append('myst_parser')

# Recognize both reStructuredText and Markdown source files
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}
# Napoleon settings: keep defaults but allow both NumPy and Google styles
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True

# Templates path
templates_path = ['_templates']

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Use the Read the Docs theme.
html_theme = 'sphinx_rtd_theme'
html_logo = 'images/Logo_200.png'
html_favicon = 'images/Logo_200.png'
html_theme_options = {
    'logo_only': True,
    'style_nav_header_background': '#000000',
}
html_static_path = ['_static']
html_css_files = ['custom.css']

autodoc_typehints = 'description'
autodoc_mock_imports = ['pygame']
