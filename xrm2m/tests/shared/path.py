# -----------------------------------------------------------------------------
# path.py - Test for the path module.
#
# October 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

"""Tests for the path module."""
# These tests are shared between on & off-box

import collections
import contextlib
import re
import unittest

from ... import _defs
from ... import _errors
from ... import _path
from ..._shared import _pathstr

from .. import _utils
from .. import _cut

_offbox_only_test = unittest.skipUnless(_cut.IS_OFFBOX, "Off-box only test")

class _LoopbackIP():
    def __str__(self):
        return "127.0.0.1"

    def __repr__(self):
        return "IP(127.0.0.1)"


class _PathSubclass(_path.Path):
    # Used for equality testing
    pass


class PathToStrTests(_utils.BaseTest):
    """
    Test Path.__str__ and Path.__repr_ (and PathElement).

    In doing so basic path functionality is also tested (eg. path
    construction). Validating the string form also verifies the internal state
    is valid.

    """

    def test_root_items(self):
        self.assertEqual(str(_path.RootCfg), "RootCfg")
        self.assertEqual(repr(_path.RootCfg), "Path(RootCfg)")
        self.assertEqual(repr(_path.RootCfg.elems()[0]),
                         "PathElement(RootCfg)")
        self.assertEqual(str(_path.RootOper), "RootOper")
        self.assertEqual(repr(_path.RootOper), "Path(RootOper)")
        self.assertEqual(str(_path.RootAction), "RootAction")
        self.assertEqual(repr(_path.RootAction), "Path(RootAction)")

    def test_child(self):
        p = _path.RootCfg.ChildElement
        self.assertEqual(str(p), "RootCfg.ChildElement")
        self.assertEqual(repr(p), "Path(RootCfg.ChildElement)")
        p = _path.RootOper.ChildElement
        self.assertEqual(str(p), "RootOper.ChildElement")
        self.assertEqual(repr(p), "Path(RootOper.ChildElement)")
        p = _path.RootAction.ChildElement
        self.assertEqual(str(p), "RootAction.ChildElement")
        self.assertEqual(repr(p), "Path(RootAction.ChildElement)")

    def test_wildcard_all(self):
        p = _path.RootCfg(_defs.WILDCARD_ALL)
        self.assertEqual(str(p), "RootCfg(*)")
        self.assertEqual(repr(p), "Path(RootCfg(WILDCARD_ALL))")

    def test_unnamed_single_keys(self):
        p = _path.RootCfg(5)
        self.assertEqual(str(p), "RootCfg([5])")
        self.assertEqual(repr(p), "Path(RootCfg(5))")

    def test_multiple_unnamed_keys(self):
        ps = [_path.RootCfg(5, 6), _path.RootCfg([5, 6])]
        for p in ps:
            self.assertEqual(str(p), "RootCfg([5, 6])")
            self.assertEqual(repr(p), "Path(RootCfg(5, 6))")

    def test_multiple_named_keys(self):
        ps = [_path.RootCfg(a=5, b=6), _path.RootCfg({'a': 5, 'b': 6})]
        for p in ps:
            self.assertIn(str(p),
                          [
                              'RootCfg({"a": 5, "b": 6})',
                              'RootCfg({"b": 6, "a": 5})',
                          ])
            self.assertIn(repr(p),
                          [
                              "Path(RootCfg(a=5, b=6))",
                              "Path(RootCfg(b=6, a=5))",
                          ])

    def test_keys_with_different_types(self):
        p = _path.RootCfg(None, True, 42, "Foo", _LoopbackIP(), _defs.WILDCARD)
        self.assertEqual(str(p),
                         'RootCfg([null, true, 42, "Foo", "127.0.0.1", *])')
        self.assertEqual(
            repr(p),
            "Path(RootCfg(None, True, 42, 'Foo', IP(127.0.0.1), WILDCARD))")
        self.assertEqual(
            repr(p.elems()[0]),
            "PathElement(RootCfg(None, True,"
            " 42, 'Foo', IP(127.0.0.1), WILDCARD))")

    def test_keys_with_escape_chars(self):
        p = _path.RootCfg("\"\\\a\b\f\n\r\t\v\x7f")
        self.assertEqual(str(p), r'RootCfg(["\"\\\a\b\f\n\r\t\v\x7f"])')
        self.assertEqual(repr(p),
                              r"Path(RootCfg('" '"'
                              r"\\\x07\x08\x0c\n\r\t\x0b\x7f'))")

    @_offbox_only_test
    def test_keys_as_bytes(self):
        p = _path.RootCfg(b"Foo")
        self.assertEqual(str(p), 'RootCfg(["Foo"])')

        with self.assertRaises(ValueError):
            _path.RootCfg(b"Foo\x80")


class ValidationTests(_utils.BaseTest):
    """
    Tests that invalid inputs result in an exception

    """
    def test_mixed_named_and_unnamed_keys(self):
        with self.assertRaisesRegex(ValueError, "Mixture.*"):
            _path.RootCfg(5, b=6)

    def test_none_string_keys(self):
        with self.assertRaisesRegex(ValueError, ".*not a string.*"):
            _path.RootCfg({1: 2})


class PathEqualityTests(_utils.BaseTest):
    """
    Test Path.__eq__ and __hash__

    """
    # Assert equal/not equal can also test hash equality
    def _assertEqual(self, item1, item2):
        self.assertEqual(item1, item2)
        self.assertEqual(hash(item1), hash(item2))
    def _assertNotEqual(self, item1, item2):
        self.assertNotEqual(item1, item2)
        # Both types not necessarily hashable!
        try:
            hash1 = hash(item1)
        except TypeError:
            self.assertNotIsInstance(item1, _path.Path)
            hash1 = None
        try:
            hash2 = hash(item2)
        except TypeError:
            self.assertNotIsInstance(item2, _path.Path)
            hash2 = None
        self.assertNotEqual(hash1, hash2)

    def test_child_equality(self):
        self._assertEqual(_path.RootCfg.Foo, _path.RootCfg.Foo)
        self._assertNotEqual(_path.RootOper.Foo, _path.RootCfg.Foo)
        self._assertNotEqual(_path.RootCfg.Foo, _path.RootCfg.Bar)

    def test_key_equality(self):
        self._assertEqual(_path.RootCfg(a=1, b=2), _path.RootCfg(a=1, b=2))
        self._assertEqual(_path.RootCfg(a=1, b=2),
                         _path.RootCfg(collections.OrderedDict(
                                                        [('a', 1), ('b', 2)])))
        self._assertNotEqual(
                         _path.RootCfg(collections.OrderedDict(
                                                        [('b', 2), ('a', 1)])),
                         _path.RootCfg(collections.OrderedDict(
                                                        [('a', 1), ('b', 2)])))
        self._assertNotEqual(_path.RootOper(a=1, b=2), _path.RootCfg(a=1, b=2))
        self._assertEqual(
                _path.Path.from_str('RootOper({"a": 1, "b": 2})'),
                _path.Path.from_str('RootOper({"a": 1, "b": 2})'))
        self._assertNotEqual(
                _path.Path.from_str('RootOper({"a": 1, "b": 2})'),
                _path.Path.from_str('RootOper({"b": 2, "a": 1})'))

    def test_type_equality(self):
        pathstr = "RootOper.Foo.Bar"
        path = _path.Path.from_str(pathstr)
        self._assertNotEqual(path, pathstr)
        self._assertNotEqual(path, path.elems())
        self._assertNotEqual(path, None)
        # But subclasses should be equal
        self._assertEqual(path, _PathSubclass.from_str(pathstr))


class PathGetItemtests(_utils.BaseTest):
    """
    Test Path.__getitem__

    """
    PATH = _path.RootCfg.Foo(A=1, B=2).Bar.Baz(A=3, C=4)

    def test_int(self):
        self.assertEqual(self.PATH[0], 1)
        self.assertEqual(self.PATH[-1], 4)
        self.assertEqual(self.PATH[-2], 3)
        with self.assertRaises(IndexError):
            _ = self.PATH[4]
        with self.assertRaises(IndexError):
            _ = self.PATH[-5]

    def test_slice(self):
        self.assertEqual(self.PATH[:], [1, 2, 3, 4])
        self.assertEqual(self.PATH[-1:], [4])
        self.assertEqual(self.PATH[1:], [2, 3, 4])
        self.assertEqual(self.PATH[:-1], [1, 2, 3])
        self.assertEqual(self.PATH[1:3], [2, 3])
        self.assertEqual(self.PATH[4:], [])

    def test_str(self):
        self.assertEqual(self.PATH['A'], 1)
        self.assertEqual(self.PATH['B'], 2)
        self.assertEqual(self.PATH['C'], 4)
        with self.assertRaises(KeyError):
            _ = self.PATH['D']

    def test_invalid_value(self):
        with self.assertRaises(TypeError):
            _ = self.PATH[{1: 2}]


class ParserTests(_utils.BaseTest):

     def setUp(self):
         super(ParserTests, self).setUp()
         self._parser = _pathstr.PathParser()
         self._parse_val = self._parser._parse_val
         self._parse_re = self._parser._parse_re
         self._parse = _path.Path.from_str

     def _assertRegex(self, text, regex):
         if not re.search(regex, text):
             self.fail("Text {!r} does not match regex {!r}".format(text,
                                                                    regex))

     @contextlib.contextmanager
     def _assertRaisesParseError(self, error_idx, msg_re=None):
         try:
             yield
         except _errors.ParseError as e:
             e.print()
             self.assertEqual(e.idx, error_idx)
             if msg_re:
                 self._assertRegex(e.msg, msg_re)
         else:
             self.fail("Parse error was not raised")

     def test_parse_val(self):
         self.assertEqual(self._parse_val("*  "),
                          (_defs.WILDCARD, 3))
         self.assertEqual(self._parse_val(" 42 ", start_idx=1),
                          (42, 4))
         self.assertEqual(self._parse_val("'\"'")[0], '"')
         self.assertEqual(self._parse_val('"\'"')[0], "'")
         self.assertEqual(self._parse_val(r'"\x0F"')[0], "\x0F")
         self.assertEqual(self._parse_val(r'"\0"')[0], "\0")
         self.assertEqual(self._parse_val(r'"\777"')[0], "\777")
         self.assertEqual(self._parse_val(r'"\a\b\f\n\r\t\v"')[0],
                                          "\a\b\f\n\r\t\v")
         self.assertEqual(self._parse_val(r"'\/'")[0], '\/')
         self.assertEqual(self._parse_val(r"'\@'")[0], '\@')

         with self._assertRaisesParseError(error_idx=0):
             self._parse_val(r"'\u1234'")

         with self._assertRaisesParseError(error_idx=1):
             self._parse_val(" @", start_idx=1)

     def test_parse_quotes(self):
         # Double quotes
         self.assertEqual(
             self._parse('RootOper(["cow"])'),
             _path.RootOper("cow"))
         with self._assertRaisesParseError(10, "scalar, asterisk, or string"):
             self._parse('RootOper(["cow])')
         # Single quotes
         self.assertEqual(
             self._parse("RootOper(['cow'])"),
             _path.RootOper("cow"))
         with self._assertRaisesParseError(10, "scalar, asterisk, or string"):
             self._parse('RootOper(["cow])')
         # Mismatched
         with self._assertRaisesParseError(10, "scalar, asterisk, or string"):
             self._parse("RootOper(['cow\"])")
         with self._assertRaisesParseError(10, "scalar, asterisk, or string"):
             self._parse("RootOper([\"cow'])")

     def test_parse_re(self):
         self.assertEqual(self._parse_re("{", self._parser._DICT_START_TOK),
                          ("{", 1))
         self.assertEqual(self._parse_re("{ ", self._parser._DICT_START_TOK),
                          ("{", 2))
         self.assertEqual(self._parse_re("{ x", self._parser._DICT_START_TOK),
                          ("{", 2))
         with self._assertRaisesParseError(error_idx=0):
             self._parse_re("}", self._parser._DICT_START_TOK)
         with self._assertRaisesParseError(error_idx=0):
             self._parse_re("", self._parser._DICT_START_TOK)

     def test_parse_list(self):
         self.assertEqual(self._parser._parse_list("[]"),
                          ([], 2))
         self.assertEqual(self._parser._parse_list("[ ] "),
                          ([], 4))
         self.assertEqual(self._parser._parse_list("[5]"),
                          ([5], 3))
         self.assertEqual(self._parser._parse_list("[*]"),
                          ([_defs.WILDCARD], 3))
         self.assertEqual(self._parser._parse_list("[5, *]"),
                          ([5, _defs.WILDCARD], 6))
         with self._assertRaisesParseError(1,
                                  "Expected JSON scalar, asterisk, or string"):
             self._parser._parse_list("[,]")
         with self._assertRaisesParseError(3,
                                           "Expected comma"):
             self._parser._parse_list("[5 5]")

     def test_parse_dict(self):
         self.assertEqual(self._parser._parse_dict("{}"),
                          ({}, 2))
         self.assertEqual(self._parser._parse_dict("{ } "),
                          ({}, 4))
         self.assertEqual(self._parser._parse_dict("{1:2}"),
                          ({1: 2}, 5))
         self.assertEqual(self._parser._parse_dict("{1:*}"),
                          ({1: _defs.WILDCARD}, 5))
         with self._assertRaisesParseError(1,
                                  "Expected JSON scalar, asterisk, or string"):
             self._parser._parse_dict("{,}")
         with self._assertRaisesParseError(2,
                                           "Expected colon"):
             self._parser._parse_dict("{1}")
         with self._assertRaisesParseError(3,
                                  "Expected JSON scalar, asterisk, or string"):
             self._parser._parse_dict("{1:}")
         with self._assertRaisesParseError(5,
                                           "Expected comma"):
             self._parser._parse_dict("{1:2 3}")

     def test_parse_key_info(self):
         self.assertEqual(self._parser._parse_key_info("(*)"),
                          (_defs.WILDCARD_ALL, 3))
         self.assertEqual(self._parser._parse_key_info("([*])"),
                          ([_defs.WILDCARD], 5))
         self.assertEqual(self._parser._parse_key_info("({1:2})"),
                          ({1: 2}, 7))

         with self._assertRaisesParseError(0,
                                           "Expected key info start"):
             self._parser._parse_key_info("")
         with self._assertRaisesParseError(1,
                                       "Expected wildcard, JSON dict, or list"):
             self._parser._parse_key_info("()")
         with self._assertRaisesParseError(1,
                                       "Expected wildcard, JSON dict, or list"):
             self._parser._parse_key_info("(:)")
         with self._assertRaisesParseError(2, "Expected key info end"):
             self._parser._parse_key_info("(**")

     def test_parse_path(self):
         self.assertEqual(self._parse("  RootCfg"),
                          _path.RootCfg)
         self.assertEqual(self._parse("RootOper"),
                          _path.RootOper)
         self.assertEqual(self._parse("RootCfg(*)"),
                          _path.RootCfg(_defs.WILDCARD_ALL))
         self.assertEqual(self._parse("RootOper.Foo"),
                          _path.RootOper.Foo)
         self.assertEqual(self._parse("RootOper([1]).Foo"),
                          _path.RootOper([1]).Foo)
         self.assertEqual(self._parse('RootOper.Foo({"a": *})'),
                          _path.RootOper.Foo({'a': _defs.WILDCARD}))

         with self._assertRaisesParseError(0,
                                           "Expected path element name"):
             self._parse("")
         with self._assertRaisesParseError(0,
                                           "Root element must be one of"):
             self._parse("InvalidRoot")
         with self._assertRaisesParseError(9, "Expected path separator"):
             self._parse("RootOper x")
         with self._assertRaisesParseError(
                 12, "Expected wildcard, JSON dict, or list"):
             self._parse("RootOper.A (")
         with self.assertRaisesRegex(ValueError, r"Key name.*is not a string"):
             self._parse("RootOper({*: 2})")
         with self._assertRaisesParseError(
                 8, "Expected path element name or end of input"):
             self._parse("RootCfg..Foo")
         with self._assertRaisesParseError(
                 12, "Input must not end with path separator (.)"):
             self._parse("RootCfg.Foo.")


class PathNegativeTests(_utils.BaseTest):
    """Negative path testcases."""
    def test_add_keys_multiple_times(self):
        """Keys can only be added once to a given path element."""
        path = _path.Path.from_str("RootOper.Foo(*)")
        with self.assertRaisesRegex(
                ValueError, "Path element already has key information"):
            path(4)

    def test_wildcard_all(self):
        """Wildcard all with extra key information is not permitted."""
        with self.assertRaisesRegex(
                ValueError, "WILDCARD_ALL passed with other key information"):
            _path.RootOper.Foo(_defs.WILDCARD_ALL, 4)


class PathElementKeyTests(_utils.BaseTest):
    """PathElement key tests."""
    def _get_pe_key(self, pathstr):
        """Gets the key of the last path element."""
        path = _path.Path.from_str(pathstr)
        return path.elems()[-1].key

    def _generic_test(self, pathstr, expected):
        """
        Compare the output of .key to an expected result.

        :param pathstr:
            The path string to be converted. (The key of the final element
            will be used in the test.)

        :param expected:
            The expected .key value.

        """
        self.assertEqual(self._get_pe_key(pathstr), expected)

    def test_no_keys(self):
        self._generic_test("RootOper", None)

    def test_wildcard_all(self):
        self._generic_test("RootOper(*)", _defs.WILDCARD_ALL)

    def test_named_keys(self):
        self._generic_test(
            'RootOper({"foo": 4, "bar": false})',
            collections.OrderedDict((
                ("foo", 4),
                ("bar", False),
            )))

    def test_unnamed_keys(self):
        self._generic_test(
            'RootOper([4, "foo", false])',
            [4, "foo", False])

