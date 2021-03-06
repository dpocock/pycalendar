# Copyright (C) 2013 W. Trevor King <wking@tremily.us>
#
# This file is part of pycalender.
#
# pycalender is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pycalender is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# pycalender.  If not, see <http://www.gnu.org/licenses/>.

"""Functions for processing text

As defined in :RFC:`5545`, section 3.3.11 (Text).
"""

import logging as _logging
import re as _re

from . import base as _base


_LOG = _logging.getLogger(__name__)

_ESCAPES = {
    '\\': [r'\\'],
    '\n': [r'\n', r'\N'],
    ';': [r'\;'],
    ',': [r'\,'],
    }

_UNESCAPES = None
_ESCAPE_REGEXP = None
_UNESCAPE_REGEXP = None


def _backslash_escape(text):
    r"""Escape backslashes, but nothing else

    This is used in ``_setup_escapes`` to build regular
    expressions.

    >>> _backslash_escape('\\')
    '\\\\'
    >>> _backslash_escape('stuff')
    'stuff'
    """
    if text == '\\':
        return r'\\'
    return text


def _setup_escapes():
    global _UNESCAPES
    global _ESCAPE_REGEXP
    global _UNESCAPE_REGEXP
    _UNESCAPES = {}
    for key,values in _ESCAPES.items():
        for value in values:
            if len(value) != 2:
                raise NotImplementedError(
                    '{!r} escape value too long ({})'.format(
                        value, len(value)))
            if value[0] != '\\':
                raise NotImplementedError(
                    '{!r} escape does not begin with a backslash'.format(
                        value))
            _UNESCAPES[value] = key
    escape_regexp = '({})'.format('|'.join(
            _backslash_escape(char) for char in _ESCAPES.keys()))
    _LOG.debug('text-escape regexp: {!r}'.format(escape_regexp))
    _ESCAPE_REGEXP = _re.compile(escape_regexp)
    unescape_regexp =  r'(\\({}))'.format('|'.join(
            _backslash_escape(escape[1]) for escape in _UNESCAPES.keys()))
    _LOG.debug('text-unescape regexp: {!r}'.format(unescape_regexp))
    _UNESCAPE_REGEXP = _re.compile(unescape_regexp)
_setup_escapes()


def _escape_replacer(match):
    return _ESCAPES[match.group(1)][0]


def _unescape_replacer(match):
    return _UNESCAPES[match.group(1)][0]


def escape(text):
    r"""Convert a Python string to :RFC:`5545`-compliant text

    Conforming to section 3.3.11 (text)

    >>> print(escape(text='Hello!\nLook: newlines!'))
    Hello!\nLook: newlines!
    >>> print(escape(text='Single backslashes \\ may be tricky\n'))
    Single backslashes \\ may be tricky\n
    """
    return _ESCAPE_REGEXP.subn(
        repl=_escape_replacer, string=text)[0]


def unescape(text):
    r"""Convert :RFC:`5545`-compliant text to a Python string

    Conforming to section 3.3.11 (text)

    >>> for text in [
    ...         'Hello!\nLook: newlines!',
    ...         ]:
    ...     escaped = escape(text=text)
    ...     unescaped = unescape(text=escaped)
    ...     if unescaped != text:
    ...         raise ValueError(unescaped)
    """
    return _UNESCAPE_REGEXP.subn(
        repl=_unescape_replacer, string=text)[0]


class Text (_base.DataType):
    name = 'TEXT'

    @classmethod
    def decode(cls, property, value):
        return unescape(text=value)

    @classmethod
    def encode(cls, property, value):
        return escape(text=value)


class UniversalResourceLocator (Text):
    name = 'URI'
