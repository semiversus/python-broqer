# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'broqer'
copyright = u'2018, Günther Jena'
author = u'Günther Jena'
version = '0.4.2-dev'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.doctest',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
]

master_doc = 'index'
source_suffix = '.rst'

html_theme = 'sphinx_rtd_theme'
htmlhelp_basename = 'broqer'

latex_documents = [
    (master_doc, 'python-broqer.tex', 'python-broqer Documentation',
     u'Günther Jena', 'manual'),
]
