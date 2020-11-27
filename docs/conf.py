# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'broqer'
copyright = u'2018, Günther Jena'
author = u'Günther Jena'
from broqer import __version__ as version
github_url = 'https://github.com/semiversus/python-broqer'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
]

master_doc = 'index'
source_suffix = '.rst'

html_theme = 'sphinx_rtd_theme'
htmlhelp_basename = 'broqer'

html_context = {
  'display_github': True, # Add 'Edit on Github' link instead of 'View page source'
  'github_user': 'semiversus',
  'github_repo': project,
  'github_version': 'master',
  'conf_py_path': '/docs/',
  'source_suffix': source_suffix,
}

latex_documents = [
    (master_doc, 'python-broqer.tex', 'python-broqer Documentation',
     u'Günther Jena', 'manual'),
]

from sphinx.ext import autodoc

class ClassDocDocumenter(autodoc.ClassDocumenter):
    objtype = 'classdoc'

    #do not indent the content
    content_indent = ""

    #do not add a header to the docstring
    def add_directive_header(self, sig):
        pass

def setup(app):
    app.add_autodocumenter(ClassDocDocumenter)
