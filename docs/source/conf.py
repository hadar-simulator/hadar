# Configuration file for the Sphinx reference builder.
#
# This file only contains a selection of the most common options. For a full
# list see the reference:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# reference root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))


import hadar

# -- Project information -----------------------------------------------------
master_doc = "index"
project = "hadar-simulator"
copyright = "Except where otherwise noted, this content is Copyright (c) 2020, RTE (https://www.rte-france.com) and licensed under a CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/) license."
author = "RTE"

# The full version, including alpha/beta/rc tags
release = hadar.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "nbsphinx",
    "IPython.sphinxext.ipython_console_highlighting",
    "sphinx.ext.mathjax",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "**.ipynb_checkpoints"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the reference for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
html_logo = "_static/logo.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

nbsphinx_execute = "never"
