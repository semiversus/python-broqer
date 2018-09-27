# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'broqer'
copyright = u'2018, Günther Jena'
author = u'Günther Jena'
version = '0.6.0-dev'

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

latex_documents = [
    (master_doc, 'python-broqer.tex', 'python-broqer Documentation',
     u'Günther Jena', 'manual'),
]

from sphinx.ext import autodoc

class ClassDocDocumenter(autodoc.ClassDocumenter):
    objtype = "classdoc"

    #do not indent the content
    content_indent = ""

    #do not add a header to the docstring
    def add_directive_header(self, sig):
        pass

def setup(app):
    app.add_autodocumenter(ClassDocDocumenter)