#------------------------------------------------------------------------------
#  file: refactor_doc.py
#  License: LICENSE.TXT
#
#  Copyright (c) 2011, Enthought, Inc.
#  All rights reserved.
#------------------------------------------------------------------------------
import re
import collections

#------------------------------------------------------------------------------
#  Precompiled regexes
#------------------------------------------------------------------------------
indent_regex = re.compile(r'\s+')

#------------------------------------------------------------------------------
#  Functions to manage indention
#------------------------------------------------------------------------------

def add_indent(lines, indent=4):
    """ Add spaces to indent a list of lines.

    Arguments
    ---------
    lines : list
        The list of strings to indent.

    indent : int
        The number of spaces to add.

    Returns
    -------
    lines : list
        The indented strings (lines).

    .. note:: Empty strings are not changed

    """
    indent_str = ' ' * indent
    output = []
    for line in lines:
        if is_empty(line):
            output.append(line)
        else:
            output.append(indent_str + line)
    return output

def remove_indent(lines):
    """ Remove all indentation from the lines.

    """
    return [line.lstrip() for line in lines]

def get_indent(line):
    """ Return the indent portion of the line.

    """
    indent = indent_regex.match(line)
    if indent is None:
        return ''
    else:
        return indent.group()

#------------------------------------------------------------------------------
#  Functions to detect line type
#------------------------------------------------------------------------------

def is_variable_field(line, indent=''):
    regex = indent + r'\*?\*?\w+\s:(\s+|$)'
    match = re.match(regex, line)
    return match

def is_method_field(line, indent=''):
    regex = indent + r'\w+\(.*\)\s*'
    match = re.match(regex, line)
    return match

def is_empty(line):
    return not line.strip()

#------------------------------------------------------------------------------
#  Functions to adjust strings
#------------------------------------------------------------------------------

def fix_star(name):
    return name.replace('*','\*')

def fix_backspace(name):
    pass

def replace_at(word, line, index):
    """ Replace the text in-line.

    The text in line is replaced with the word without changing the
    size of the line (in most cases). The replacement starts at the
    provided index.

    Arguments
    ---------
    word : str
        The text to copy into the line.

    line : str
        The line where the copy takes place.

    index : int
        The index to start coping.

    Returns
    -------
    result : str
        line of text with the text replaced.

    """
    word_length = len(word)
    line_list = list(line)
    line_list[index: (index + word_length)] = list(word)
    return ''.join(line_list)

#------------------------------------------------------------------------------
#  Functions to work with fields
#------------------------------------------------------------------------------


def max_header_length(fields):
    """ Find the max length of the header in a list of fields.

    Arguments
    ---------
    fields : list
        The list of the parsed fields.

    """
    return max([len(field[0]) for field in fields])

def max_desc_length(fields):
    """ Find the max length of the description in a list of fields.

    Arguments
    ---------
    fields : list
        The list of the parsed fields.

    """
    return max([len(' '.join([line.strip() for line in field[2]]))
                for field in fields])

#------------------------------------------------------------------------------
#  Classes
#------------------------------------------------------------------------------
class BaseDoc(object):
    """Base abstract docstring refactoring class.

    The class' main purpose is to parse the dosctring and find the
    sections that need to be refactored. It also provides a number of
    methods to help with the refactoring. Subclasses should provide
    the methods responsible for refactoring the sections.

    Attributes
    ----------
    docstring : list
        A list of strings (lines) that holds docstrings

    index : int
        The current zero-based line number of the docstring that is
        proccessed.

    verbose : bool
        When set the class prints a lot of info about the proccess
        during runtime.

    headers : dict
        The sections that the class refactors. Each entry in the
        dictionary should have as key the name of the section in the
        form that it appears in the docstrings. The value should be
        the postfix of the method, in the subclasses, that is
        responsible for refactoring (e.g. {'Methods': 'method'}).

    Methods
    -------
    extract_fields(indent='', field_check=None)
        Extract the fields from the docstring

    get_field()
        Get the field description.

    get_next_paragraph()
        Get the next paragraph designated by an empty line.

    is_section()
        Check if the line defines a section.

    parse_field(lines)
        Parse a field description.

    peek(count=0)
        Peek ahead

    read()
        Return the next line and advance the index.

    insert_lines(lines, index)
        Insert refactored lines

    remove_lines(index, count=1)
        Removes the lines for the docstring

    seek_to_next_non_empty_line()
        Goto the next non_empty line

    """

    def __init__(self, lines, headers = None, verbose=False):
        """ Initialize the class

        The method setups the class attributes and starts parsing the
        docstring to find and refactor the sections.

        Arguments
        ---------
        lines : list of strings
            The docstring to refactor

        headers : dict
            The sections for which the class has custom refactor methods.
            Each entry in the dictionary should have as key the name of
            the section in the form that it appears in the docstrings.
            The value should be the postfix of the method, in the
            subclasses, that is responsible for refactoring (e.g.
            {'Methods': 'method'}).

        verbose : bool
            When set the class prints a lot of info about the proccess
            during runtime.

        """
        try:
            self._docstring = lines.splitlines()
        except AttributeError:
            self._docstring = lines
        self.verbose = verbose
        if headers is None:
            self.headers = {}
        else:
            self.headers = headers
        self.index = 0
        if self.verbose:
            print 'INPUT DOCSTRING'
            print '\n'.join(self.docstring)
        self.parse()
        if self.verbose:
            print 'OUTPUT DOCSTRING'
            print '\n'.join(self.docstring)

    def parse(self):
        """ Parse the docstring.

        The docstring is parsed for sections. If a section is found then
        the corresponding refactoring method is called.

        """
        self.index = 0
        self.seek_to_next_non_empty_line()
        while not self.eol:
            if self.verbose:
                print 'current index is', self.index
            header = self.is_section()
            if header:
                if is_empty(self.peek(2)):  # Remove space after header
                    self.remove_lines(self.index + 2)
                self._refactor(header)
            else:
                self.index += 1
                self.seek_to_next_non_empty_line()

    def _refactor(self, header):
        """Call the heading refactor method.

        The name of the refctoring method is constructed using the form
        _refactor_<header>. Where <header> is the value corresponding to
        ``self.headers[header]``. If there is no custom method for the
        section then the self._refactor_header() is called with the
        found header name as input.

        """
        if self.verbose:
            print 'Header is', header
            print 'Line is', self.index

        refactor_postfix = self.headers.get(header, 'header')
        method_name = ''.join(('_refactor_', refactor_postfix))
        method = getattr(self, method_name)
        method(header)

    def _refactor_header(self, header):
        """ Refactor the header section using the rubric directive.

        The method has been tested and supports refactoring single word
        headers, two word headers and headers that include a backslash
        ''\''.

        Arguments
        ---------
        header : string
            The header string to use with the rubric directive.

        """
        if self.verbose:
            print 'Refactoring {0}'.format(header)
        index = self.index
        indent = get_indent(self.peek())
        self.remove_lines(index, 2)
        descriptions = []
        if self.verbose:
            print 'header representation is: {}'.format(repr(header))
        header = repr(header).strip("'")
        descriptions.append(indent + '.. rubric:: {0}'.format(header))
        descriptions.append('')
        self.insert_lines(descriptions, index)
        self.index += len(descriptions)
        return descriptions


    def extract_fields(self, indent='', field_check=None):
        """Extract the fields from the docstring

        Parse the fields in the description of a section into tuples of
        name, type and description in a list of strings. The parsed lines
        are also removed from original list.

        Arguments
        ---------
        indent : str, optional
            the indent argument is used to make sure that only the lines
            with the same indent are considered when checking for a
            field header line. The value is used to define the field
            checking function.

        field_check : function
            Optional function to use for checking if the next line is a
            field. The signature of the function is ``foo(line)`` and it
            should return ``True`` if the line contains a valid field
            The default function is checking for fields of the following
            formats::

                <name> : <type>

            or::

                <name> :

            Where the name has to be one word.

        Returns
        -------
        parameters : list of tuples
            list of parsed parameter tuples as returned from the
            :meth:`~BaseDocstring.parse_field` method.

        """

        #TODO raise error when there is no parameter

        if self.verbose:
            print "PARSING PARAMETERS"

        if field_check:
            is_field = field_check
        else:
            is_field = is_variable_field

        parameters = []

        while (not self.eol) and (is_field(self.peek(), indent) or
                                  is_field(self.peek(1), indent)):
            if is_empty(self.peek()):  # Remove space petween fields
                self.remove_lines(self.index)
            field = self.get_next_block()
            if self.verbose:
                print "next field is: ", field
            parameters.append(self.parse_field(field))

        if self.verbose:
            print "Fields parsed"
        return parameters

    def get_next_block(self):
        """ Get the next field block from the docstring.

        The method reads the next block in the docstring. The first line
        assumed to be the field header and the following lines to belong to
        the description::

            <header line>
                <descrition>

        The end of the field is designated by a line with the same indent
        as the field header or two empty lines are found in sequence. Thus,
        there are two valid field layouts:

        1. No lines between fields::

            <field1>
                <description1>
            <fieldd2>
                <description2>

        2. One line between fields::

            <field1>
                <description1>

            <field2>
                <description2>

        """
        start = self.index
        field_header = self.read()
        indent = get_indent(field_header) + ' '
        field = [field_header]
        if self.verbose:
            print "Get next field"
            print "Field header is {}".format(field_header)
        while (not self.eol):
            peek_0 = self.peek()
            peek_1 = self.peek(1)
            if is_empty(peek_0) and (not peek_1.startswith(indent)):
                break
            elif (not is_empty(peek_0)) and (not peek_0.startswith(indent)):
                break
            else:
                line = self.read()
                field.append(line.rstrip())
                if self.verbose:
                    print 'add "{}" to the field'.format(line)

        self.remove_lines(start, len(field))
        self.index = start
        return field



    def parse_field(self, lines):
        """Parse a field description.

        The field is assumed to be in one of the following formats::

            <name> : <type>
                <description>

        or::

            <name> :
                <description>

        or::

            <name>
                <description>

        Arguments
        ---------
        lines :
            docstring lines of the field.

        Returns
        -------
        arg_name : str
            The name of the parameter.

        arg_type : str
            The type of the parameter (if defined).

        desc : list
            A list of the strings that make up the description.

        """
        header = lines[0].strip()
        if ' :' in header:
            arg_name, arg_type = re.split('\s\:\s?', header, maxsplit=1)
        else:
            arg_name, arg_type = header, ''
        if self.verbose:
            print "name is:", arg_name, " type is:", arg_type
        if len(lines) > 1:
            lines = [line.rstrip() for line in lines]
            return arg_name.strip(), arg_type.strip(), lines[1:]
        else:
            return arg_name.strip(), arg_type.strip(), ['']

    def is_section(self):
        """Check if the line defines a section.

        """
        if self.eol:
            return False

        header = self.peek()
        line2 = self.peek(1)
        if self.verbose:
            print 'current line is: {0} at index {1}'.format(header, self.index)

        # check for underline type format
        underline = re.match(r'\s*\S+\s*\Z', line2)
        if underline is None:
            return False
        # is the nextline an rst underline?
        striped_header = header.rstrip()
        expected_underline1 = re.sub(r'[A-Za-z\\]|\b\s', '-', striped_header)
        expected_underline2 = re.sub(r'[A-Za-z\\]|\b\s', '=', striped_header)
        if ((underline.group().rstrip() == expected_underline1) or
            (underline.group().rstrip() == expected_underline2)):
            return header.strip()
        else:
            return False

    def insert_lines(self, lines, index):
        """ Insert refactored lines

        Arguments
        ---------
        new_lines : list
            The list of lines to insert

        index : int
            Index to start the insertion
        """
        docstring = self.docstring
        for line in reversed(lines):
            docstring.insert(index, line)

    def seek_to_next_non_empty_line(self):
        """ Goto the next non_empty line

        """
        docstring = self.docstring
        for line in docstring[self.index:]:
            if not is_empty(line):
                break
            self.index += 1


    def get_next_paragraph(self):
        """ Get the next paragraph designated by an empty line.

        """
        docstring = self.docstring
        lines = []
        start = self.index
        while (not self.eol) and (not is_empty(self.peek())):
            line = self.read()
            lines.append(line)
        del docstring[start:self.index]
        return lines

    def read(self):
        """ Return the next line and advance the index.

        """
        index = self.index
        line = self._docstring[index]
        self.index += 1
        return line

    def remove_lines(self, index, count=1):
        """ Removes the lines for the docstring

        """
        docstring = self.docstring
        del docstring[index:(index + count)]

    def peek(self, ahead=0):
        """ Peek ahead a number of lines

        The function retrieves the line that is ahead of the current
        index. If the index is at the end of the list then it returns an
        empty string.

        Arguments
        ---------
        ahead : int
            The number of lines to look ahead.


        """
        position = self.index + ahead
        try:
            line = self.docstring[position]
        except IndexError:
            line = ''
        return line

    @property
    def eol(self):
        return self.index >= len(self.docstring)

    @property
    def docstring(self):
        """ Get the docstring lines.

        """
        return self._docstring

