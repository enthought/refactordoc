from sectiondoc.sections import (
    attributes, methods_table, notes_paragraph, item_list, arguments)
from sectiondoc.renderers import Attribute, Method, Argument, ListItem
from sectiondoc.items import DefinitionItem, MethodItem
from sectiondoc.styles.base_doc import BaseDoc
from sectiondoc.styles.style import Style


def class_section(lines):
    return BaseDoc(
        lines,
        sections={
            'Attributes': (attributes, Attribute, DefinitionItem),
            'Methods': (methods_table, Method, MethodItem),
            'Notes': (notes_paragraph, None, None)})


def function_section(lines):
    return BaseDoc(
        lines,
        sections={
            'Returns': (item_list, ListItem, DefinitionItem),
            'Arguments': (arguments, Argument, DefinitionItem),
            'Parameters': (arguments, Argument, DefinitionItem),
            'Raises': (item_list, ListItem, DefinitionItem),
            'Yields': (item_list, ListItem, DefinitionItem),
            'Notes': (notes_paragraph, None, None)})


def setup(app):
    style = Style({
        'class': class_section,
        'function': function_section,
        'method': function_section})
    app.setup_extension('sphinx.ext.autodoc')
    app.connect('autodoc-process-docstring', style.section_docstring)
