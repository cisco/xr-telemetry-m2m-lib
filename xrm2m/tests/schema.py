# -----------------------------------------------------------------------------
# schema.py - Schema tests
#
# November 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

"""Tests for the schema module."""

from . import _utils
from .. import _path
from .. import _schema
from .. import _bag

{'category': 'CONTAINER',
 'children': ['RootOper.MPGTest.MUT.Instance.Flat.Naming.MultiComplex.MultiComplexLeaf'],
 'description': 'Naming of MultiComplex',
 'hidden': False,
 'key': [{'datatype': 'INTEGER',
          'datatype_args': None,
          'description': 'First integer name',
          'internal_name': None,
          'name': 'FirstInteger',
          'repeat_count': 1,
          'status': 'MANDATORY'},
         {'datatype': 'INTEGER',
          'datatype_args': None,
          'description': 'Second integer name',
          'internal_name': None,
          'name': 'SecondInteger',
          'repeat_count': 1,
          'status': 'OPTIONAL'},
         {'datatype': 'IPV6ADDRESS',
          'datatype_args': None,
          'description': '4 concrete name',
          'internal_name': None,
          'name': 'AnIPv6Address',
          'repeat_count': 1,
          'status': 'MANDATORY'},
         {'datatype': 'MACADDRESS',
          'datatype_args': None,
          'description': '3 concrete name',
          'internal_name': None,
          'name': 'AMacAddress',
          'repeat_count': 1,
          'status': 'OPTIONAL'}],
 'presence': None,
 'table_description': 'Table class for MultiComplex',
 'table_version': None,
 'table_version_compatibility': [None, None],
 'value': [],
 'version': None,
 'version_compatibility': [None, None]}

class FromDictTests(_utils.BaseTest):

    def test_version_compatibilities(self):
        expected_repr_fmt = (
            "SchemaClass(name='DummyPath', "
            "category=<SchemaClassCategory.LEAF: 1>, "
            "description='Test description', "
            "table_description=None, key=[], value=[], presence=None, "
            "version=UNVERSIONED, table_version=None, hidden=False, "
            "version_compatibility={}, "
            "table_version_compatibility=None, children=[], bag_types=None)")
        p = _path.RootOper.DummyPath
        d = {'category': 'LEAF',
             'children': [],
             'description': 'Test description',
             'hidden': False,
             'key': [],
             'presence': None,
             'table_description': None,
             'table_version': None,
             'table_version_compatibility': None,
             'value': [],
             'version': None,
             'version_compatibility': [None, None],
             'bag_types': None}

        result = _schema.SchemaClass.from_dict(p, d)
        self.assertEqual(result.version_compatibility,
                         (_schema.UNVERSIONED, _schema.UNVERSIONED))
        self.assertEqual(result.table_version_compatibility, None)
        self.assertEqual(repr(result), expected_repr_fmt.format(
                         "(UNVERSIONED, UNVERSIONED)"))

        d['version_compatibility'] = ({'major': 1, 'minor': 2}, None)
        result = _schema.SchemaClass.from_dict(p, d)
        self.assertEqual(result.version_compatibility,
                         (_schema.Version(1, 2), _schema.MAX_VERSION))
        self.assertEqual(repr(result), expected_repr_fmt.format(
                         "(Version(1.2), MAX_VERSION)"))

        d['version_compatibility'] = ({'major': 1, 'minor': 2},
                                      {'major': 3, 'minor': 4})
        result = _schema.SchemaClass.from_dict(p, d)
        self.assertEqual(result.version_compatibility,
                         (_schema.Version(1, 2), _schema.Version(3, 4)))
        self.assertEqual(repr(result), expected_repr_fmt.format(
                         "(Version(1.2), Version(3.4))"))

    def test_datatypes(self):
        p = _path.RootOper.DummyPath
        d = {'category': 'LEAF',
             'children': [],
             'description': 'Test description',
             'hidden': False,
             'key': [{'datatype': 'RANGE',
                      'datatype_args': {'min': 1, 'max': 100},
                      'description': 'Range test',
                      'internal_name': None,
                      'name': 'RangeTest',
                      'repeat_count': 1,
                      'status': 'MANDATORY'},
                     {'datatype': 'BOUNDED_STRING',
                      'datatype_args': {'minlen': 7, 'maxlen': 16},
                      'description': 'Bounded string test',
                      'internal_name': None,
                      'name': 'BoundedStringTest',
                      'repeat_count': 1,
                      'status': 'MANDATORY'},
                     {'datatype': 'BOOL',
                      'datatype_args': None,
                      'description': 'Bool test',
                      'internal_name': None,
                      'name': 'BoolTest',
                      'repeat_count': 1,
                      'status': 'MANDATORY'}],
             'presence': None,
             'table_description': None,
             'table_version': None,
             'table_version_compatibility': None,
             'value': [],
             'version': None,
             'version_compatibility': [None, None],
             'bag_types': None}
        expected_repr = (
                "SchemaClass(name='DummyPath', "
                "category=<SchemaClassCategory.LEAF: 1>, "
                "description='Test description', "
                "table_description=None, "
                "key=[SchemaParam(Range(1, 100) RangeTest), "
                "SchemaParam(BoundedString(7, 16) BoundedStringTest), "
                "SchemaParam(Boolean BoolTest)], value=[], "
                "presence=None, version=UNVERSIONED, table_version=None, "
                "hidden=False, "
                "version_compatibility=(UNVERSIONED, UNVERSIONED), "
                "table_version_compatibility=None, children=[], "
                "bag_types=None)")

        result = _schema.SchemaClass.from_dict(p, d)
        self.assertEqual(repr(result), expected_repr)

    def test_bag_types(self):
        p = _path.RootOper.DummyPath
        d = {'category': 'LEAF',
             'children': [],
             'description': 'Test description',
             'hidden': False,
             'key': [],
             'presence': None,
             'table_description': None,
             'table_version': None,
             'table_version_compatibility': None,
             'value': [{'datatype': 'BAG',
                        'datatype_args': None,
                        'description': 'An example bag',
                        'internal_name': 'example_bag',
                        'name': 'example_bag',
                        'repeat_count': 1,
                        'status': 'MANDATORY'}],
             'version': None,
             'version_compatibility': [None, None],
             'bag_types':
                 {'bag_1': {'children': [{'datatype': 'UINT8',
                      'datatype_name': None,
                                          'description': 'The first bag param',
                                          'name': 'param1',
                                          'status': 'MANDATORY',
                                          'status_args': None},
                                         {'datatype': 'STRUCT',
                                          'datatype_name': 'InterfaceList',
                                          'description': 
                                                        'The second bag param',
                                          'name': 'param2',
                                          'status': 'LIST',
                                          'status_args': [{'fixed_length':
                                                                         False,
                                                           'max_length': 4}]}],
                            'datatype': 'STRUCT',
                            'datatype_args': None,
                            'description': 'A bag structure',
                            'name': 'bag_1'},
                  'bag_2': {'children': [{'datatype': 'UINT8',
                                          'datatype_name': None,
                                          'description': 'The first bag param',
                                          'name': 'param1',
                                          'status': 'MANDATORY',
                                          'status_args': None},
                                         {'datatype': 'STRUCT',
                                          'datatype_name': 'InterfaceList',
                                          'description': 'The second bag param',
                                          'name': 'param2',
                                          'status': 'LIST',
                                          'status_args': [{'fixed_length':
                                                                         False,
                                                           'max_length': 4}]}],
                            'datatype': 'UNION',
                            'datatype_args': {'discriminator':
                                {'datatype': 'STRUCT',
                                 'datatype_name': 'InterfaceList',
                                 'description': 'The second bag param',
                                 'name': 'param2',
                                 'status': 'LIST',
                                 'status_args': [{'fixed_length': False,
                                                  'max_length': 4}]}},
                            'description': 'A bag union',
                            'name': 'bag_2'},
                  'bag_3': {'children': [{'description': 'An enum param',
                                          'name': 'enum_param1'}],
                            'datatype': 'ENUM',
                            'datatype_args': None,
                            'description': 'A bag enum',
                            'name': 'bag_3'}}}

        result = _schema.SchemaClass.from_dict(p, d)

        expected_bag_types = {
            'bag_1': _bag.BagType(
                name='bag_1',
                description='A bag structure',
                datatype=_bag.BagDatatype.STRUCT,
                datatype_args=None,
                children=[
                    _bag.BagParam(name='param1',
                                  description='The first bag param',
                                  datatype=_bag.BagDatatype.UINT8,
                                  datatype_name=None,
                                  status=_bag.BagParamStatus.MANDATORY,
                                  status_args=None),
                    _bag.BagParam(name='param2',
                                  description='The second bag param',
                                  datatype=_bag.BagDatatype.STRUCT,
                                  datatype_name='InterfaceList',
                                  status=_bag.BagParamStatus.LIST,
                                  status_args=[_bag.BagListArgs(
                                                            fixed_length=False,
                                                            max_length=4)]),
                             ]),
            'bag_2': _bag.BagType(
                name='bag_2',
                description='A bag union',
                datatype=_bag.BagDatatype.UNION,
                datatype_args=_bag.BagUnionArgs(
                        discriminator=_bag.BagParam(
                            name='param2',
                            description='The second bag param',
                            datatype=_bag.BagDatatype.STRUCT,
                            datatype_name='InterfaceList',
                            status=_bag.BagParamStatus.LIST,
                            status_args=[_bag.BagListArgs(
                                                      fixed_length=False,
                                                      max_length=4)])),
                children=[
                    _bag.BagParam(name='param1',
                                  description='The first bag param',
                                  datatype=_bag.BagDatatype.UINT8,
                                  datatype_name=None,
                                  status=_bag.BagParamStatus.MANDATORY,
                                  status_args=None),
                    _bag.BagParam(name='param2',
                                  description='The second bag param',
                                  datatype=_bag.BagDatatype.STRUCT,
                                  datatype_name='InterfaceList',
                                  status=_bag.BagParamStatus.LIST,
                                  status_args=[_bag.BagListArgs(
                                                          fixed_length=False,
                                                          max_length=4)]),
                    ]),
            'bag_3': _bag.BagType(
                name='bag_3',
                description='A bag enum',
                datatype=_bag.BagDatatype.ENUM,
                datatype_args=None,
                children=[_bag.BagEnumElement(description='An enum param',
                                              name='enum_param1')]),
        }

        self.assertEqual(set(result.bag_types.keys()),
                    set(expected_bag_types.keys()))
        self.assertEqual(result.bag_types['bag_1'],
                         expected_bag_types['bag_1'])
        self.assertEqual(result.bag_types['bag_2'],
                         expected_bag_types['bag_2'])
        self.assertEqual(result.bag_types['bag_3'],
                         expected_bag_types['bag_3'])

        expected_bag_types_repr1 = (
            "BagType(name='bag_1', description='A bag structure', datatype=STR"
            'UCT, children=[uint8 param1, struct InterfaceList param2[0..4]], '
            'datatype_args=None)'
        )
        expected_bag_types_repr2 = (
            "BagType(name='bag_2', description='A bag union', datatype=UNION, "
            'children=[uint8 param1, struct InterfaceList param2[0..4]], datat'
            'ype_args=BagUnionArgs(discriminator=struct InterfaceList param2[0'
            '..4]))'
        )
        expected_bag_types_repr3 = (
            "BagType(name='bag_3', description='A bag enum', datatype=ENUM, ch"
            'ildren=[enum_param1], datatype_args=None)'
        )
        expected_bag_types_str1 = (
            'struct bag_1:\n'
            '  uint8 param1\n'
            '  struct InterfaceList param2[0..4]'
        )
        expected_bag_types_str2 = (
            'union bag_2(struct InterfaceList param2[0..4]):\n'
            '  uint8 param1\n'
            '  struct InterfaceList param2[0..4]'
        )
        expected_bag_types_str3 = (
            'enum bag_3:\n'
            '  enum_param1'
        )

        self.assertEqual(repr(result.bag_types['bag_1']),
                         expected_bag_types_repr1)
        self.assertEqual(repr(result.bag_types['bag_2']),
                         expected_bag_types_repr2)
        self.assertEqual(repr(result.bag_types['bag_3']),
                         expected_bag_types_repr3)

        self.assertEqual(str(result.bag_types['bag_1']),
                         expected_bag_types_str1)
        self.assertEqual(str(result.bag_types['bag_2']),
                         expected_bag_types_str2)
        self.assertEqual(str(result.bag_types['bag_3']),
                         expected_bag_types_str3)

class ReprStrTests(_utils.BaseTest):
    """Get coverage of remaining str/repr branches."""

    def test_bag_type_no_children(self):
        b = _bag.BagType(
                name='bag_1',
                description='A bag structure',
                datatype=_bag.BagDatatype.STRUCT,
                datatype_args=None,
                children=[])
        self.assertEqual(str(b), 'struct bag_1: <empty>')

    def test_bag_param_none_type(self):
        p = _bag.BagParam(name='',
                          description='',
                          datatype=_bag.BagDatatype.NONE,
                          datatype_name=None,
                          status=_bag.BagParamStatus.MANDATORY,
                          status_args=None)
        self.assertEqual(str(p), '<void>')

    def test_bag_param_optional_status(self):
        p = _bag.BagParam(name='param1',
                          description='The first bag param',
                          datatype=_bag.BagDatatype.UINT8,
                          datatype_name=None,
                          status=_bag.BagParamStatus.OPTIONAL,
                          status_args=None)
        self.assertEqual(str(p), 'uint8 param1?')

    def test_bag_list_args_fixed_length(self):
        l = _bag.BagListArgs(fixed_length=True,
                             max_length=5)
        self.assertEqual(str(l), '[5]')

    def test_bag_list_args_no_max_length(self):
        l = _bag.BagListArgs(fixed_length=False,
                             max_length=None)
        self.assertEqual(str(l), '[]')


class MiscTests(_utils.BaseTest):
    def test_datatype_camelcase(self):
        """
        Ensure there's an entry in `_schema._DATATYPE_TO_CAMELCASE` for each
        `Datatype`.

        """
        for d in _schema.Datatype:
            d.camelcase_name

