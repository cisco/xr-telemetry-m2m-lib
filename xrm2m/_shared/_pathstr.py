# -----------------------------------------------------------------------------
# _pathstr.py - Conversion to Paths from strings
#
# October 2015, Matt Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


"""Conversion to Paths from strings."""


__all__ = (
    "PathParser",
)


import ast
import collections
import json
import re

from . import defs
from . import errors


_ParseResult = collections.namedtuple('_ParseResult', ['val', 'idx'])
_Token = collections.namedtuple('_Token', ['name', 'regex'])

ParsedElement = collections.namedtuple("ParsedElement", ['name', 'key_info'])


class PathParser(object):
    """
    Routines for parsing paths.

    """

    _LIST_START_TOK = _Token('list start ([)', r"^\[")
    _LIST_END_TOK = _Token('list end (])', r"^\]")
    _DICT_START_TOK = _Token('dict start ({)', r"^\{")
    _DICT_END_TOK = _Token('dict end (})', r"^\}")
    _COMMA_TOK = _Token('comma (,)', r"^,")
    _COLON_TOK = _Token('colon (:)', r"^:")
    _WILDCARD_TOK = _Token('wildcard (*)', r"^\*")

    _KEY_INFO_START_TOK = _Token('key info start (()', r"^\(")
    _KEY_INFO_END_TOK = _Token('key info end ())', r"^\)")

    _PATH_ELEMENT_NAME_TOK = _Token('path element name',
                                    r"^[A-Za-z_][-A-Za-z0-9_]*")
    _PATH_SEPARATOR_TOK = _Token('path separator (.)', r"^\.")

    _ESCAPE_SEQS = r"\\[^NuU]|\\[0-7]{1,3}|\\x[0-9a-fA-F]{2}"
    _SINGLE_QUOTE_STRING = r"^'([^'\\]|" + _ESCAPE_SEQS + r")*'"
    _DOUBLE_QUOTE_STRING = r'^"([^"\\]|' + _ESCAPE_SEQS + r')*"'
    _STRING_TOK = _Token('string', "({})|({})".format(_SINGLE_QUOTE_STRING,
                                                      _DOUBLE_QUOTE_STRING))

    _VALID_ROOT_NAMES = {"RootAction", "RootOper", "RootCfg"}

    def _lookahead(self, s, tok, start_idx=0):
        """
        Test if a string matches a given token.

        """
        return bool(re.search(tok.regex, s[start_idx:]))

    def _consume_whitespace(self, s, start_idx):
        m = re.search(r"^\s*", s[start_idx:])
        return start_idx + len(m.group(0))

    def _parse_val(self, s, start_idx=0):
        """
        Parse a string with an object value at the start of it.

        Returns a pair `val, idx` of the parsed value and the index in `s`
        where the value ended.

        """
        assert len(s) >= start_idx

        idx = start_idx

        # Look to see if there is an asterisk. Consume it and return if so.
        if self._lookahead(s, self._WILDCARD_TOK, start_idx=idx):
            _, idx = self._parse_re(s, self._WILDCARD_TOK, start_idx=idx)
            return defs.WILDCARD, idx

        # Look to see if there is a string. These are not parsed as JSON as
        # strings in paths are to be interpreted as Python strings. (This
        # allows single quote strings, as well as having slightly different
        # escape semantics.)
        if self._lookahead(s, self._STRING_TOK, start_idx=idx):
            unparsed_str, idx = self._parse_re(s,
                                               self._STRING_TOK,
                                               start_idx=idx)
            return ast.literal_eval(unparsed_str), idx

        # Otherwise fall back to the default JSON parser to decode a value.
        try:
            val, idx_inc = json.JSONDecoder().raw_decode(s[idx:])
            idx += idx_inc
        except ValueError:
            raise errors.ParseError(idx, s,
                "Expected JSON scalar, asterisk, or string")

        idx = self._consume_whitespace(s, start_idx=idx)

        return _ParseResult(val, idx)

    def _parse_re(self, s, tok, start_idx=0):
        """
        Parse a token, and any following whitespace.

        Returns a pair `val, idx` of the parsed value and the index in `s`
        where the value ended.

        """
        assert len(s) >= start_idx

        idx = start_idx
        m = re.match(tok.regex, s[idx:])
        if not m:
            raise errors.ParseError(idx, s, "Expected {}".format(tok.name))
        out = m.group(0)

        idx += len(m.group(0))

        idx = self._consume_whitespace(s, start_idx=idx)

        return _ParseResult(out, idx)

    def _parse_list(self, s, start_idx=0):
        """
        Parse a list of object values.

        Returns a pair `val, idx` of the parsed value and the index in `s`
        where the list ended.

        """
        out = []
        idx = start_idx

        # Consume the opening square bracket, and exit with the empty list if
        # there's immediately a closing bracket.
        _, idx = self._parse_re(s, self._LIST_START_TOK, start_idx=idx)
        if self._lookahead(s, self._LIST_END_TOK, start_idx=idx):
            _, idx = self._parse_re(s, self._LIST_END_TOK, start_idx=idx)
            return _ParseResult(out, idx)

        # Repeatedly consume values, bailing out if followed by a closing
        # bracket, continuing if followed by a comma.
        while True:
            val, idx = self._parse_val(s, start_idx=idx)
            out.append(val)

            if self._lookahead(s, self._LIST_END_TOK, start_idx=idx):
                _, idx = self._parse_re(s, self._LIST_END_TOK, start_idx=idx)
                return _ParseResult(out, idx)

            _, idx = self._parse_re(s, self._COMMA_TOK, start_idx=idx)

    def _parse_dict(self, s, start_idx=0):
        """
        Parse a dict of object values.

        Returns a pair `val, idx` of the parsed value and the index in `s`
        where the list ended.

        """
        out = collections.OrderedDict()
        idx = start_idx

        # Consume the opening curly bracket, and exit with the empty dict if
        # there's immediately a closing bracket.
        _, idx = self._parse_re(s, self._DICT_START_TOK, start_idx=idx)
        if self._lookahead(s, self._DICT_END_TOK, start_idx=idx):
            _, idx = self._parse_re(s, self._DICT_END_TOK, start_idx=idx)
            return _ParseResult(out, idx)

        # Otherwise repeatedly consume "<key>: <val>" pairs, bailing out if
        # followed by a closing bracket, continuing if followed by a comma.
        while True:
            key, idx = self._parse_val(s, start_idx=idx)
            _, idx = self._parse_re(s, self._COLON_TOK, start_idx=idx)
            val, idx = self._parse_val(s, start_idx=idx)

            out[key] = val

            if self._lookahead(s, self._DICT_END_TOK, start_idx=idx):
                _, idx = self._parse_re(s, self._DICT_END_TOK, start_idx=idx)
                return _ParseResult(out, idx)

            _, idx = self._parse_re(s, self._COMMA_TOK, start_idx=idx)

    def _parse_key_info(self, s, start_idx=0):
        """
        Parse key information from a path.

        Returns a pair `val, idx` of the parsed value and the index in `s`
        where the list ended.

        The value returned is either a dict or a list, as may be passed into
        :meth:`.Path.__call__`.

        """

        idx = start_idx

        # Consume the opening bracket.
        _, idx = self._parse_re(s, self._KEY_INFO_START_TOK, start_idx=idx)

        # Lookahead for a wildcard, dict or list and consume as appropriate.
        if self._lookahead(s, self._WILDCARD_TOK, start_idx=idx):
            _, idx = self._parse_re(s, self._WILDCARD_TOK, start_idx=idx)
            out = defs.WILDCARD_ALL
        elif self._lookahead(s, self._DICT_START_TOK, start_idx=idx):
            out, idx = self._parse_dict(s, start_idx=idx)
        elif self._lookahead(s, self._LIST_START_TOK, start_idx=idx):
            out, idx = self._parse_list(s, start_idx=idx)
        else:
            raise errors.ParseError(idx, s,
                                    "Expected wildcard, JSON dict, or list")

        # Consume the closing bracket.
        _, idx = self._parse_re(s, self._KEY_INFO_END_TOK, start_idx=idx)

        return _ParseResult(out, idx)

    def parse(self, path_str):
        """
        Parse a path.

        :param path_str:
            The string to be parsed.

        See :meth:`.Path.from_str` for more information.

        """
        idx = 0
        idx = self._consume_whitespace(path_str, start_idx=idx)

        # Read the first path element. This must be either RootOper or RootCfg.
        path_start_idx = idx
        el_name, idx = self._parse_re(path_str, self._PATH_ELEMENT_NAME_TOK,
                                      start_idx=idx)
        if el_name not in self._VALID_ROOT_NAMES:
            raise errors.ParseError(
                path_start_idx, path_str,
                "Root element must be one of {}, not {}".format(
                    " or ".join(self._VALID_ROOT_NAMES), el_name))

        # Repeatedly:
        #  - Check for key info, and add it to the current path if found.
        #  - Check for a path separating dot, and return the current path if
        #    not found.
        #  - Consume the next path element name and add the element to the
        #    current path.
        elems = []
        key_info = ()
        while idx < len(path_str):
            if self._lookahead(path_str, self._KEY_INFO_START_TOK,
                               start_idx=idx):
                key_info, idx = self._parse_key_info(path_str, start_idx=idx)

            if self._lookahead(path_str, self._PATH_SEPARATOR_TOK,
                               start_idx=idx):
                elems.append(ParsedElement(el_name, key_info))
                el_name = None
                key_info = ()
                _, idx = self._parse_re(path_str, self._PATH_SEPARATOR_TOK,
                        start_idx=idx)
            elif idx < len(path_str):
                raise errors.ParseError(
                    idx, path_str,
                    "Expected path separator (.) or end of input")

            if self._lookahead(path_str, self._PATH_ELEMENT_NAME_TOK,
                               start_idx=idx):
                el_name, idx = self._parse_re(path_str,
                                              self._PATH_ELEMENT_NAME_TOK,
                                              start_idx=idx)

            elif idx < len(path_str):
                raise errors.ParseError(
                    idx, path_str,
                    "Expected path element name or end of input")

        assert idx == len(path_str)
        if el_name is None:
            assert path_str[-1] == ".", path_str
            raise errors.ParseError(
                idx, path_str, "Input must not end with path separator (.)")
        elems.append(ParsedElement(el_name, key_info))

        return elems

