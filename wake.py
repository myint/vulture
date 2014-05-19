# -*- coding: utf-8 -*-
#
# vulture - Find dead code.
#
# Copyright (C) 2012  Jendrik Seipp (jendrikseipp@web.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function

import ast
from fnmatch import fnmatchcase
import io
import os
import re


__version__ = '1.0'


FORMAT_STRING_PATTERN = re.compile(r'\%\((\S+)\)s')
PYTHON_SHEBANG_PATTERN = re.compile(r'^#!.*\bpython[23]?\b\s*$')


class Item(str):

    def __new__(cls, name, typ, filename, lineno, line):
        item = str.__new__(cls, name)
        item.typ = typ
        item.filename = filename
        item.lineno = lineno
        item.line = line
        return item


class Vulture(ast.NodeVisitor):

    """Find dead stuff."""

    def __init__(self, exclude=None, verbose=False, level=2):
        self.exclude = []
        for pattern in exclude or []:
            if not any(char in pattern for char in ['*', '?', '[']):
                pattern = '*%s*' % pattern
            self.exclude.append(pattern)

        self.verbose = verbose
        self.level = level

        self.defined_funcs = []
        self.used_funcs = []
        self.defined_props = []
        self.defined_attrs = []
        self.used_attrs = []
        self.defined_vars = []
        self.used_vars = []
        self.tuple_assign_vars = []

        self.filename = None
        self.code = None

    def scan(self, node_string):
        self.code = node_string.splitlines()
        try:
            node = ast.parse(node_string)
        except SyntaxError:
            print('Error in file:', self.filename)
            return
        self.visit(node)

    def _get_modules(self, paths, toplevel=True):
        """Take files from the command line even if they don't end with .py."""
        modules = []
        for path in paths:
            path = os.path.abspath(path)
            if os.path.isfile(path) and (is_python_file(path) or toplevel):
                modules.append(path)
            elif os.path.isdir(path):
                subpaths = [os.path.join(path, filename)
                            for filename in sorted(os.listdir(path))
                            if not filename.startswith('.')]
                modules.extend(self._get_modules(subpaths, toplevel=False))
        return modules

    def scavenge(self, paths):
        modules = self._get_modules(paths)
        included_modules = []
        for module in modules:
            if any(fnmatchcase(module, pattern) for pattern in self.exclude):
                self.log('Excluded:', module)
                continue
            included_modules.append(module)

        for module in included_modules:
            self.log('Scanning:', module)
            with open_with_encoding(module) as input_file:
                module_string = input_file.read()
            self.filename = module
            self.scan(module_string)

    def report(self):
        """Return True if unused items are found."""
        def file_lineno(item):
            return (item.filename.lower(), item.lineno)
        found = False
        for item in sorted(self.unused_funcs + self.unused_props +
                           self.unused_vars + self.unused_attrs,
                           key=file_lineno):
            relpath = os.path.relpath(item.filename)
            path = relpath if not relpath.startswith('..') else item.filename
            print("%s:%d: Unused %s '%s'" % (path, item.lineno, item.typ,
                                             item))
            found = True
        return found

    def get_unused(self, defined, used):
        return list(sorted(set(defined) - set(used), key=lambda x: x.lower()))

    @property
    def unused_funcs(self):
        return self.get_unused(self.defined_funcs,
                               self.used_funcs + self.used_attrs)

    @property
    def unused_props(self):
        return self.get_unused(self.defined_props, self.used_attrs)

    @property
    def unused_vars(self):
        return self.get_unused(
            self.defined_vars,
            self.used_vars + self.used_attrs + self.tuple_assign_vars)

    @property
    def unused_attrs(self):
        if self.level < 1:
            return []

        return self.get_unused(self.defined_attrs, self.used_attrs)

    def _get_lineno(self, node):
        return getattr(node, 'lineno', 1)

    def _get_line(self, node):
        return self.code[self._get_lineno(node) - 1] if self.code else ''

    def _get_item(self, node, typ):
        name = getattr(node, 'name', None)
        id = getattr(node, 'id', None)
        attr = getattr(node, 'attr', None)
        assert len([x for x in (name, id, attr) if x is not None]) == 1
        return Item(name or id or attr, typ, self.filename, node.lineno,
                    self._get_line(node))

    def log(self, *args):
        if self.verbose:
            print(*args)

    def print_node(self, node):
        self.log(self._get_lineno(node), ast.dump(node), self._get_line(node))

    def _get_func_name(self, func):
        for field in func._fields:
            if field == 'id':
                return func.id
            elif field == 'func':
                return self._get_func_name(func.func)
        return func.attr

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if getattr(decorator, 'id', None) == 'property':
                self.defined_props.append(self._get_item(node, 'property'))
                break
        else:
            if (
                self.level < 2 and
                node.args.args and
                node.args.args[0].arg == 'self'
            ):
                return

            # Only executed if function is not a property.
            if not (node.name.startswith('__') and node.name.endswith('__')):
                self.defined_funcs.append(self._get_item(node, 'function'))

    def visit_Attribute(self, node):
        item = self._get_item(node, 'attribute')
        if isinstance(node.ctx, ast.Store):
            self.log('defined_attrs <-', item)
            self.defined_attrs.append(item)
        elif isinstance(node.ctx, ast.Load):
            self.log('useed_attrs <-', item)
            self.used_attrs.append(item)

    def visit_Name(self, node):
        if node.id != 'object':
            self.used_funcs.append(node.id)
            if isinstance(node.ctx, ast.Load):
                self.log('used_vars <-', node.id)
                self.used_vars.append(node.id)
            elif isinstance(node.ctx, ast.Store):
                # Ignore _x (pylint convention), __x, __x__ (special method).
                if not node.id.startswith('_'):
                    item = self._get_item(node, 'variable')
                    self.log('defined_vars <-', item)
                    self.defined_vars.append(item)

    def _find_tuple_assigns(self, node):
        # Find all tuple assignments. Those have the form
        # Assign->Tuple->Name or For->Tuple->Name or comprehension->Tuple->Name
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, ast.Tuple):
                continue
            for grandchild in ast.walk(child):
                if (isinstance(grandchild, ast.Name) and
                        isinstance(grandchild.ctx, ast.Store)):
                    self.log('tuple_assign_vars <-', grandchild.id)
                    self.tuple_assign_vars.append(grandchild.id)

    def visit_Assign(self, node):
        self._find_tuple_assigns(node)

    def visit_For(self, node):
        self._find_tuple_assigns(node)

    def visit_comprehension(self, node):
        self._find_tuple_assigns(node)

    def visit_ClassDef(self, node):
        self.defined_funcs.append(self._get_item(node, 'class'))

    def visit_Str(self, node):
        """Variables may appear in format strings:

        '%(a)s' % locals()

        """
        self.used_vars.extend(FORMAT_STRING_PATTERN.findall(node.s))

    def visit(self, node):
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is not None:
            if self.verbose:
                self.print_node(node)
            visitor(node)
        return self.generic_visit(node)


def open_with_encoding(filename, encoding=None, mode='r'):
    """Return opened file with a specific encoding."""
    if not encoding:
        encoding = detect_encoding(filename)

    return io.open(filename, mode=mode, encoding=encoding,
                   newline='')  # Preserve line endings


def detect_encoding(filename):
    """Return file encoding."""
    try:
        with open(filename, 'rb') as input_file:
            from lib2to3.pgen2 import tokenize as lib2to3_tokenize
            encoding = lib2to3_tokenize.detect_encoding(input_file.readline)[0]

        # Check for correctness of encoding
        with open_with_encoding(filename, encoding) as test_file:
            test_file.read()

        return encoding
    except (LookupError, SyntaxError, UnicodeDecodeError):
        return 'latin-1'


def is_python_file(filename):
    """Return True if filename is Python file."""
    if filename.endswith('.py'):
        return True

    try:
        with open_with_encoding(filename) as f:
            first_line = f.readlines(1)[0]
    except (IOError, IndexError):
        return False

    if not PYTHON_SHEBANG_PATTERN.match(first_line):
        return False

    return True
