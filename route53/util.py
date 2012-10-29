"""
Various utility functions that are useful across the codebase.
"""

from lxml import etree

def prettyprint_xml(node):
    return etree.tostring(node, pretty_print=True).decode('utf-8')
