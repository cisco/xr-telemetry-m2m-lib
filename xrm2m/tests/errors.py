# -----------------------------------------------------------------------------
# errors.py - Test for the errors module.
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

"""Tests for the errors module."""

from .. import _defs
from .. import _errors
from .. import _path

from . import _utils

class ErrorDetailTests(_utils.BaseTest):
    """
    Test that the class and attributes for _error module errors are correct.

    """
    def _assertDetails(self, exception, expected_msg, expected_cls,
                       expected_attrs):
        self.assertEqual(type(exception), expected_cls)
        for name, val in expected_attrs.items():
            self.assertTrue(hasattr(exception, name))
            self.assertEqual(getattr(exception, name), val)

    def test_path_string_format_error(self):
        error_field = {'code': -32000,
                       'data': {'path': 'BadRoot',
                                 'type': 'path_string_format_error'},
                       'message': "Path BadRoot doesn't start at a root node."}
        expected_msg = "Path BadRoot doesn't start at a root node."
        expected_attrs = {
            'pathstr': 'BadRoot'
        }
        expected_cls = _errors.PathStringFormatError 
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_cisco_error(self):
        error_field = {'code': -32000,
                       'data': {'type': 'cisco_error'},
                       'message': 'Cisco error message goes here'}
        expected_msg = 'Cisco error message goes here'
        expected_attrs = {
        }
        expected_cls = _errors.CiscoError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_config_commit_error(self):
        error_field = {'code': -32000,
                       'data': [{'category': 'APPLY',
                                 'error': "Apply error message",
                                 'operation': 'SET',
                                 'path': 'RootCfg.Path1',
                                 'type': 'config_commit_error',
                                 'value': 601},
                                {'category': 'VERIFY',
                                 'error': "Verify error message",
                                 'operation': 'SET',
                                 'path': 'RootCfg.Path2',
                                 'type': 'config_commit_error',
                                 'value': 601},
                                {'category': 'VERIFY',
                                 'error': "Delete error message",
                                 'operation': 'DELETE',
                                 'path': 'RootCfg.Path3',
                                 'type': 'config_commit_error',
                                 'value': None}],
                       'message': 'One or more config changes failed'}

        expected_msg = 'One or more config changes failed'
        expected_attrs = {
            'detail': [
                     _defs.ConfigCommitErrorDetail(
                        op=_defs.Change.SET,
                        path=_path.RootCfg.Path1,
                        value=601,
                        error_category=_defs.ErrorCategory.APPLY,
                        error="Apply error message"),
                     _defs.ConfigCommitErrorDetail(
                        op=_defs.Change.SET,
                        path=_path.RootCfg.Path2,
                        value=601,
                        error_category=_defs.ErrorCategory.VERIFY,
                        error="Verify error message"),
                     _defs.ConfigCommitErrorDetail(
                        op=_defs.Change.DELETE,
                        path=_path.RootCfg.Path3,
                        value=None,
                        error_category=_defs.ErrorCategory.VERIFY,
                        error="Delete error message"),
                    ]
            }
        expected_cls = _errors.ConfigCommitError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_path_key_structure_error(self):
        error_field = {'code': -32000,
                       'data': {'class': 'BasicItem',
                                'type': 'path_key_structure_error',
                                'value_seq': []},
                       'message': 'Name-value mappings refer to non-existent '
                                  'names: Foo'}
        expected_msg = 'Name-value mappings refer to non-existent names: Foo'
        expected_attrs = {
            "value_seq": [],
            "class_name": "BasicItem"
        }
        expected_cls = _errors.PathKeyStructureError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_permissions_error(self):
        error_field = {'code': -32000,
                       'data': {'msg': 'File /tmp/foo.txt is read-only',
                                'type': 'permissions_error'},
                       'message': 'Permission denied when writing file '
                                                                '/tmp/foo.txt'}

        expected_msg = None
        expected_msg = 'Permission denied when writing file /tmp/foo.txt'
        expected_attrs = {
        }
        expected_cls = PermissionError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_value_structure_error(self):
        error_field = {"message":
                        "Too many values specified. Expected at most 1, got 2",
                        "code": -32000,
                        "data": {"value_seq": [5, 6],
                                 "type": "value_structure_error",
                                 "class": "BasicItem"}}
        expected_msg = 'Too many values specified. Expected at most 1, got 2'
        expected_attrs = {
            "value_seq": [5, 6],
            "class_name": "BasicItem"
        }
        expected_cls = _errors.ValueStructureError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_datatype_not_supported_error(self):
        error_field = {'code': -32000,
                       'data': {'type': 'datatype_not_supported_error'},
                       'message': 'Datatype is not supported'}
        expected_msg = 'Datatype is not supported'
        expected_attrs = {
        }
        expected_cls = _errors.DatatypeNotSupportedError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_file_exists_error(self):
        error_field = {'code': -32000,
                       'data': {'filename': '/tmp2/foo.txt',
                                'type': 'file_exists_error'},
                       'message': "Specified directory doesn't exist"}
        expected_msg = "Specified directory doesn't exist"
        expected_attrs = {
            'filename': '/tmp2/foo.txt'
        }
        expected_cls = _errors.FileExistsError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_not_found_error(self):
        error_field = {'code': -32000,
                       'data': {'path': 'RootOper.SomePath',
                                'type': 'not_found_error'},
                       'message': "Specified directory doesn't exist"}
        expected_msg = "Specified directory doesn't exist"
        expected_attrs = {
            'path': _path.RootOper.SomePath
        }
        expected_cls = _errors.NotFoundError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_operation_not_supported_error(self):
        error_field = {'code': -32000,
                         'data': {'path': 'RootOper.SomePath',
                                  'type': 'operation_not_supported_error'},
                         'message': "Operation not supported"}
        expected_msg = 'Operation not supported'
        expected_attrs = {
            'path': _path.RootOper.SomePath
        }
        expected_cls = _errors.OperationNotSupportedError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_path_hierarchy_error(self):
        error_field = {'code': -32000,
                       'data': {'element': 'Basicable',
                                'parent': 'Write',
                                'type': 'path_hierarchy_error'},
                       'message': "'Basicable' is not a child of 'Write'"}
        expected_msg = "'Basicable' is not a child of 'Write'"
        expected_attrs = {
            'parent': 'Write',
            'element': 'Basicable'
        }
        expected_cls = _errors.PathHierarchyError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_path_key_content_error(self):
        error_field = {'code': -32000,
                       'data': {'param': 'String OnlyName',
                                'type': 'path_key_content_error',
                                'value': 42},
                       'message': '42 is not a valid String value'}
        expected_msg = '42 is not a valid String value'
        expected_attrs = {
            'value': 42,
            'param': 'String OnlyName'
        }
        expected_cls = _errors.PathKeyContentError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_value_content_error(self):
        error_field = {'code': -32000,
                       'data': {'param': 'Integer Value',
                                'type': 'value_content_error',
                                'value': 'Foo'},
                       'message': "'Foo' is not a valid Integer value"}
        expected_msg = "'Foo' is not a valid Integer value"
        expected_attrs = {
            'value': 'Foo',
            'param': 'Integer Value'
        }
        expected_cls = _errors.ValueContentError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

    def test_invalid_argument_error(self):
        error_field = {'code': -32000,
                       'data': {'path': 'RootOper.SomePath',
                                'type': 'invalid_argument_error'},
                       'message': 'Invalid argument'}
        expected_msg = 'Invalid argument'
        expected_attrs = {
            'path': _path.RootOper.SomePath
        }
        expected_cls = _errors.InvalidArgumentError
        self._assertDetails(
                _errors.error_from_error_field(error_field),
                expected_msg,
                expected_cls,
                expected_attrs
        )

