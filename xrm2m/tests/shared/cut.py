# -----------------------------------------------------------------------------
# cut.py - Component Unit Tests
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


"""Tests for connections."""


import collections
import os
import unittest

from .. import _cut

# Import different for onbox vs. offbox packages
if _cut.IS_OFFBOX:
    import xrm2m_offbox.xrm2m as xrm2m
else:
    import xrm2m


def _from_exec_prompt():
    """Returns True if tests have been run from exc prompt."""
    return os.environ.get("EXEC_PID") is not None

# Decorator used to mark tests as "exec only"
_exec_only_test = unittest.skipUnless(_from_exec_prompt(), "Not from exec")
_onbox_only_test = unittest.skipUnless(_cut.IS_ONBOX, "On-box only test")
_offbox_only_test = unittest.skipUnless(_cut.IS_OFFBOX, "Off-box only test")


class SyncWrapperTests(_cut.BaseTest):
    """
    Test for the `sync()` function which turns an async connecting into a sync
    connection.

    """
    @_offbox_only_test
    def test_get_version(self):
        """
        Test to create a sync connection from an async connection, make a
        request, and disconnect.

        """
        async_conn_fut = xrm2m.connect_async(loop=self._loop)
        async_conn = self._loop.run_until_complete(async_conn_fut)

        sync_conn = xrm2m.sync(async_conn)
        self.assertEqual(sync_conn.state, xrm2m.ConnectionState.CONNECTED)
        self.assertEqual(async_conn.state, xrm2m.ConnectionState.CONNECTED)

        result = sync_conn.get_version()
        self.assertIsInstance(result, xrm2m.Version)

        sync_conn.disconnect()
        self.assertEqual(sync_conn.state, xrm2m.ConnectionState.DISCONNECTED)
        self.assertEqual(async_conn.state, xrm2m.ConnectionState.DISCONNECTED)


class LocalOtherRequestsTests(_cut.LocalTestsBase):
    """
    Test misc request methods, over a local connection.

    """
    def test_get_version(self):
        result = self.conn.get_version()
        self.assertIsInstance(result, xrm2m.Version)

    def test_normalize_path(self):
        base_path = (xrm2m.RootOper.MPGTest.CUT.Operational.AccessOperations.
                                          BasicTableContainer.Basic)
        p = base_path(["apple"])
        result = self.conn.normalize_path(p)
        expected_result = base_path(OnlyName='apple')
        self.assertEqual(result, expected_result)


class LocalOperRequestsTests(_cut.LocalTestsBase):
    """
    Test oper request methods, over a local connection.

    """
    def test_single_get(self):
        p = (xrm2m.RootOper.MPGTest.CUT.Operational.AccessOperations.
                                                     BasicTableContainer.Basic)
        result = self.conn.get(p)

        expected_result = \
            [(p(OnlyName='apple'), 4),
             (p(OnlyName='BANANA'), 5),
             (p(OnlyName='Cow'), 7),
             (p(OnlyName='dog'), 0),
             (p(OnlyName='e'), 49)]

        self.assertEqual(result, expected_result)

    @_exec_only_test
    def test_single_cli_get(self):
        p = (xrm2m.RootOper.MPGTest.CUT.Operational.AccessOperations.
                                                     BasicTableContainer.Basic)
        result = self.conn.cli_get("show mpg basic")

        expected_result = \
            [(p(OnlyName='apple'), 4),
             (p(OnlyName='BANANA'), 5),
             (p(OnlyName='Cow'), 7),
             (p(OnlyName='dog'), 0),
             (p(OnlyName='e'), 49)]
        self.assertEqual(result, expected_result)

    def test_single_get_nested(self):
        p = (xrm2m.RootOper.MPGTest.CUT.Operational.AccessOperations.
                                                     BasicTableContainer.Basic)
        result = self.conn.get_nested(p)

        expected_result = \
            {'RootOper': {'MPGTest': {'CUT': {'Operational':
                {'AccessOperations': {'BasicTableContainer': {'Basic':
                    [{'AValue': 4, 'OnlyName': 'apple'},
                     {'AValue': 5, 'OnlyName': 'BANANA'},
                     {'AValue': 7, 'OnlyName': 'Cow'},
                     {'AValue': 0, 'OnlyName': 'dog'},
                     {'AValue': 49, 'OnlyName': 'e'}]}}}}}}}
        self.assertEqual(result, expected_result)

    @_exec_only_test
    def test_cli_describe_oper(self):
        result = self.conn.cli_describe("show int br")

        expected_result = [xrm2m.Request(
            method=xrm2m.Method.GET,
            path=xrm2m.RootOper.Interfaces.InterfaceBrief,
            value=None)]
        self.assertEqual(result, expected_result)

    @_exec_only_test
    def test_cli_describe_config(self):
        result = self.conn.cli_describe("int gig 0/0/0/0 shut", config=True)
        expected_result = [xrm2m.Request(
            method=xrm2m.Method.SET,
            path=xrm2m.RootCfg.InterfaceConfiguration(Active='act',
                              InterfaceName='GigabitEthernet0/0/0/0').Shutdown,
            value=True)]
        self.assertEqual(result, expected_result)

    @_exec_only_test
    def test_single_cli_get_nested(self):
        result = self.conn.cli_get_nested("show mpg basic")

        expected_result = \
            {'RootOper': {'MPGTest': {'CUT': {'Operational':
                {'AccessOperations': {'BasicTableContainer': {'Basic':
                    [{'AValue': 4, 'OnlyName': 'apple'},
                     {'AValue': 5, 'OnlyName': 'BANANA'},
                     {'AValue': 7, 'OnlyName': 'Cow'},
                     {'AValue': 0, 'OnlyName': 'dog'},
                     {'AValue': 49, 'OnlyName': 'e'}]}}}}}}}

        self.assertEqual(result, expected_result)

    def test_single_get_children(self):
        p = (xrm2m.RootOper.MPGTest.CUT.Operational.SchemaStructure.Keys.
                                     MacAddressKeyTableContainer.MacAddressKey)
        result = self.conn.get_children(p)
        expected_result = \
            [p(OnlyName='ab:cd:ef:01:23:45'),
             p(OnlyName='00:00:00:00:ab:00'),
             p(OnlyName='ff:ff:ff:ff:ff:ff'),
             p(OnlyName='01:23:45:67:89:ab')]

        self.assertEqual(result, expected_result)

    def test_single_get_parent(self):
        p = (xrm2m.RootOper.MPGTest)
        result = self.conn.get_parent(p)
        expected_result = xrm2m.RootOper

        self.assertEqual(result, expected_result)

    @_exec_only_test
    def test_single_cli_exec(self):
        result = self.conn.cli_exec("show mpg basic")
        expected_result = """Here is some MPG stuff:

table/apple                  4
table/BANANA                 5
table/Cow                    7
table/dog                    0
table/e                     49
"""

        self.assertEqual(result, expected_result)


class LocalConfigRequestsTests(_cut.LocalTestsBase):
    """
    Test config request methods, over a local connection.

    """

    COMMON_ANCESTOR = xrm2m.RootCfg.MPGTest.CUT
    LEAF1 = xrm2m.RootCfg.MPGTest.CUT.Write.Basic.BasicLeaf
    LEAF2 = xrm2m.RootCfg.MPGTest.CUT.SubtreeReplace.Basic.BasicLeaf
    UINT32_TABLE = xrm2m.RootCfg.MPGTest.CUT.DataTypes.TestUInt32
    PASSWORD_LEAF = xrm2m.RootCfg.MPGTest.CUT.DataTypes.ProprietaryPasswordLeaf
    STRING_TABLE = xrm2m.RootCfg.MPGTest.CUT.DataTypes.TestString

    MULTIVALUE_LEAF = (xrm2m.RootCfg.MPGTest.CUT.Write.Schema.Values.MultiValue)
    MULTIVALUE_LEAF_VALUE = (1, 2, 'aa:aa:aa:aa:aa:aa', 'bb:aa:aa:aa:aa:aa')

    # Path to trigger a PathHierarchyError.
    BAD_PATH = xrm2m.RootCfg.NotAChildOfRootCfg

    def test_set(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set(self.LEAF1, 111)
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.SET,
                                                       value=111)])
        self.assertEqual(self.conn.get_value(self.LEAF1), 111)
        self.conn.commit()
        changes = self.conn.get_changes()
        self.assertEqual(changes, [])
        self.assertEqual(self.conn.get_value(self.LEAF1), 111)

    @_offbox_only_test
    def test_set_bytes(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()
        
        # Set a leaf, and commit.
        self.conn.set([(self.STRING_TABLE(Name=b"Foo"), b"Bar")])
        results = self.conn.get(self.STRING_TABLE)
        self.assertEqual(results,
                         [(self.STRING_TABLE(Name="Foo"), "Bar")])

    def test_set_many(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set([(self.LEAF1, 111),
                       (self.LEAF2, 222)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.SET,
                                                       value=111),
                                   xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.SET,
                                                       value=222)
                                                       ])

    @unittest.skip('Password leaf not in schem.')
    def test_set_password(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        cleartext = "Secret!"

        ciphertext_re = r"^[A-F0-9]{16}$"

        # Set a leaf, and commit.
        self.conn.set([(self.PASSWORD_LEAF, xrm2m.Password(cleartext))])
        changes = self.conn.get_changes()

        self.assertEqual(len(changes), 1)
        self.assertRegex(changes[0].value, ciphertext_re)
        self.assertRegex(self.conn.get_value(self.PASSWORD_LEAF),
                         ciphertext_re)
        self.conn.commit()
        changes = self.conn.get_changes()
        self.assertEqual(changes, [])
        self.assertRegex(self.conn.get_value(self.PASSWORD_LEAF),
                         ciphertext_re)

    def test_set_multivalue(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        self.conn.set([(self.MULTIVALUE_LEAF, self.MULTIVALUE_LEAF_VALUE)])
        expected_value = {'FirstValue': 1,
                          'SecondValue': 2,
                          'ThirdValue': 'aa:aa:aa:aa:aa:aa',
                          'FourthValue': 'bb:aa:aa:aa:aa:aa'}
        self.assertEqual(
                self.conn.get_value(self.MULTIVALUE_LEAF),
                expected_value)

    def test_set_invalid(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Try to perform a set with an iterable supplied, plus a value
        with self.assertRaises(ValueError):
            self.conn.set([self.LEAF1, 111], 10)

    @_exec_only_test
    def test_single_cli_set(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        self.conn.cli_set("int gig 0/0/0/0 ipv4 addr 10.0.0.1/24")
        path = xrm2m.RootCfg.\
                InterfaceConfiguration(collections.OrderedDict([
                    ("Active", "act"),
                    ("InterfaceName", "GigabitEthernet0/0/0/0")])).\
                IPV4Network.Addresses.Primary
        value = collections.OrderedDict([("Address", "10.0.0.1"),
                                         ("Netmask", "255.255.255.0"),
                                         ("RouteTag", None)])
        changes = self.conn.get_changes()
        self.assertEqual(changes,
                         [xrm2m.ChangeDetails(path=path,
                                              op=xrm2m.Change.SET,
                                              value=value)])
        self.conn.discard_changes()

    def test_discard_changes(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and discard the changes.
        self.conn.set([(self.LEAF1, 111)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.SET,
                                                       value=111)])
        self.conn.discard_changes()
        changes = self.conn.get_changes()
        self.assertEqual(changes, [])

    def test_commit_replace(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set([(self.LEAF1, 111)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.SET,
                                                       value=111)])
        self.conn.commit()
        changes = self.conn.get_changes()
        self.assertEqual(changes, [])

        # Set another leaf, commit-replace the changes
        self.conn.set([(self.LEAF2, 222)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.SET,
                                                       value=222)])
        self.conn.commit_replace()

        # Check only the second leaf is set.
        self.assertEqual(self.conn.get(self.LEAF1), [])
        self.assertEqual(self.conn.get_value(self.LEAF2), 222)

    def test_delete(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set(self.LEAF1, 111)
        self.conn.commit()
        self.assertEqual(self.conn.get_value(self.LEAF1), 111)

        # Delete the leaf, then commit.
        self.conn.delete(self.LEAF1)
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.DELETE,
                                                       value=None)])
        self.conn.commit()

    def test_delete_many(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set([(self.LEAF1, 111),
                       (self.LEAF2, 222)])
        self.conn.commit()
        self.assertEqual(self.conn.get_value(self.LEAF1), 111)
        self.assertEqual(self.conn.get_value(self.LEAF2), 222)

        # Delete the leaf, then commit.
        self.conn.delete([self.LEAF1, self.LEAF2])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.DELETE,
                                                       value=None),
                                   xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.DELETE,
                                                       value=None)])
        self.conn.commit()

    def test_replace(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set([(self.LEAF1, 111),
                       (self.LEAF2, 222)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.SET,
                                                       value=111),
                                   xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.SET,
                                                       value=222)])
        self.conn.commit()
        cfg = self.conn.get(self.COMMON_ANCESTOR)
        self.assertEqual(cfg, [(self.LEAF1, 111), (self.LEAF2, 222)])

        # Mark the whole sub-tree for replacement, set a single leaf, then
        # commit.
        self.conn.replace(self.COMMON_ANCESTOR)
        self.conn.set([(self.LEAF2, 333)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.DELETE,
                                                       value=None),
                                   xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.SET,
                                                       value=333)])
        self.conn.commit()

        cfg = self.conn.get(self.COMMON_ANCESTOR)
        self.assertEqual(cfg, [(self.LEAF2, 333)])

    def test_replace_many(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Set a leaf, and commit.
        self.conn.set([(self.LEAF1, 111),
                       (self.LEAF2, 222)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.SET,
                                                       value=111),
                                   xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.SET,
                                                       value=222)])
        self.conn.commit()
        cfg = self.conn.get(self.COMMON_ANCESTOR)
        self.assertEqual(cfg, [(self.LEAF1, 111), (self.LEAF2, 222)])

        # Mark the whole sub-tree for replacement, set a single leaf, then
        # commit.
        self.conn.replace([self.COMMON_ANCESTOR])
        self.conn.set([(self.LEAF2, 333)])
        changes = self.conn.get_changes()
        self.assertEqual(changes, [xrm2m.ChangeDetails(path=self.LEAF1,
                                                       op=xrm2m.Change.DELETE,
                                                       value=None),
                                   xrm2m.ChangeDetails(path=self.LEAF2,
                                                       op=xrm2m.Change.SET,
                                                       value=333)])
        self.conn.commit()

        cfg = self.conn.get(self.COMMON_ANCESTOR)
        self.assertEqual(cfg, [(self.LEAF2, 333)])

    def test_get_value(self):
        # Remove all existing config.
        self.conn.discard_changes()
        self.conn.commit_replace()

        # Getting a path which maps to nothing should raise not found.
        with self.assertRaises(xrm2m.NotFoundError):
            self.conn.get_value(self.UINT32_TABLE)

        # Set a single value, and verify the item is found.
        self.conn.set([(self.UINT32_TABLE(Name=3), 9)])
        val = self.conn.get_value(self.UINT32_TABLE)
        self.assertEqual(val, 9)

        # Try a get on a path which does not exist in the schema.
        with self.assertRaises(xrm2m.PathHierarchyError):
            self.conn.get_value(self.BAD_PATH)

        # Set a second value, and verify that an ambiguous path error is
        # raised.
        self.conn.set([(self.UINT32_TABLE(Name=4), 16)])
        with self.assertRaises(xrm2m.AmbiguousPathError):
            self.conn.get_value(self.UINT32_TABLE)


class LocalMiscRequestTests(_cut.LocalTestsBase):
    """
    Test miscellaneous request methods, over a local connection.

    """
    def _test_get_schema_internal(self):
        path_in = xrm2m.RootOper.MPGTest.MUT.Instance.Flat.Naming.MultiComplex
        result = self.conn.get_schema(path_in)
        expected_result = xrm2m.SchemaClass(
            name='MultiComplex',
            category=xrm2m.SchemaClassCategory.CONTAINER,
            description='Naming of MultiComplex',
            table_description='Table class for MultiComplex',
            key=[
                xrm2m.SchemaParam(datatype=xrm2m.Datatype.INTEGER,
                                  datatype_args=None,
                                  description='First integer name',
                                  internal_name=None,
                                  name='FirstInteger',
                                  repeat_count=1,
                                  status=xrm2m.SchemaParamStatus.MANDATORY),
                xrm2m.SchemaParam(datatype=xrm2m.Datatype.INTEGER,
                                  datatype_args=None,
                                  description='Second integer name',
                                  internal_name=None,
                                  name='SecondInteger',
                                  repeat_count=1,
                                  status=xrm2m.SchemaParamStatus.OPTIONAL),
                xrm2m.SchemaParam(datatype=xrm2m.Datatype.IPV6ADDRESS,
                                  datatype_args=None,
                                  description='4 concrete name',
                                  internal_name=None,
                                  name='AnIPv6Address',
                                  repeat_count=1,
                                  status=xrm2m.SchemaParamStatus.MANDATORY),
                xrm2m.SchemaParam(datatype=xrm2m.Datatype.MACADDRESS,
                                  datatype_args=None,
                                  description='3 concrete name',
                                  internal_name=None,
                                  name='AMacAddress',
                                  repeat_count=1,
                                  status=xrm2m.SchemaParamStatus.OPTIONAL),
            ],
            value=[],
            presence=None,
            version=xrm2m.UNVERSIONED,
            table_version=xrm2m.UNVERSIONED,
            hidden=False,
            version_compatibility=(xrm2m.UNVERSIONED, xrm2m.UNVERSIONED),
            table_version_compatibility=(xrm2m.UNVERSIONED, xrm2m.UNVERSIONED),
            children=[path_in.MultiComplexLeaf],
            bag_types=None)

        self.assertEqual(result, expected_result)

    def test_get_schema(self):
        self._test_get_schema_internal()

    def test_get_schema_bag(self):
        path = xrm2m.RootOper.MPGTest.MUT.Schema.Bags.SimpleBag
        result = self.conn.get_schema(path)
        expected_result = xrm2m.SchemaClass(
            name='SimpleBag',
            category=xrm2m.SchemaClassCategory.LEAF,
            description='A simple bag',
            table_description=None,
            key=[],
            value=[
                xrm2m.SchemaParam(
                    name='schema_layer_test',
                    description='A simple bag',
                    datatype=xrm2m.Datatype.BAG,
                    datatype_args=None,
                    repeat_count=1,
                    status=xrm2m.SchemaParamStatus.MANDATORY,
                    internal_name='schema_layer_test')
            ],
            presence=None,
            version=xrm2m.UNVERSIONED,
            table_version=None,
            hidden=False,
            version_compatibility=(xrm2m.UNVERSIONED, xrm2m.UNVERSIONED),
            table_version_compatibility=None,
            children=[],
            bag_types={'schema_layer_test':
                xrm2m.BagType(
                    name='schema_layer_test',
                    description='Schema layer test bag',
                    datatype=xrm2m.BagDatatype.STRUCT,
                    datatype_args=None,
                    children=[
                        xrm2m.BagParam(name='Item',
                                      description='Bag item',
                                      datatype=xrm2m.BagDatatype.STRING,
                                      datatype_name=None,
                                      status=xrm2m.BagParamStatus.MANDATORY,
                                      status_args=None),
                                 ])})
        self.assertEqual(result, expected_result)

    def test_write_file(self):
        filename = "/tmp/xrm2m_cut.txt"

        data = "A new file written by the JSON-RPC CUT"
        self.conn.write_file(data, filename)
        with open(filename, 'r') as f:
            self.assertEqual(data, f.read())

        os.remove(filename)


class LocalActionRequestsTests(_cut.LocalTestsBase):
    """
    Test action request methods, over a local connection.

    """
    def test_get_positive(self):
        p = xrm2m.RootAction.MPGTest.CUT.Action.ReadLeaf
        result = self.conn.get_value(p)
        self.assertEqual(result, 1)

    def test_get_negative(self):
        p = xrm2m.RootAction.MPGTest.CUT.Action.WriteLeaf
        with self.assertRaises(xrm2m.OperationNotSupportedError):
            _ = self.conn.get_value(p)

    def test_set_positive(self):
        p = xrm2m.RootAction.MPGTest.CUT.Action.ReadWriteLeaf
        self.conn.set(p, 4)
        self.assertEqual(self.conn.get_value(p), 4)
        # Do two sets to ensure that there will definitely be a change!
        self.conn.set(p, 6)
        self.assertEqual(self.conn.get_value(p), 6)

    def test_set_negative(self):
        p = xrm2m.RootAction.MPGTest.CUT.Action.ReadLeaf
        with self.assertRaises(xrm2m.OperationNotSupportedError):
            self.conn.set(p, 6)


class LocalErrorRequestsTests(_cut.LocalTestsBase):
    """
    Test request methods, over a local connection wihch return an error.

    """
    # Not tested:
    # AmbiguousPathError
    # CiscoError
    # ConfigCommitError
    # ConnectionError
    # DatatypeNotSupportedError
    # DisconnectedError
    # FileExistsError
    # InternalError
    # PathStringFormatError
    # PermissionsError
    def test_cisco_error(self):
        p = (xrm2m.RootOper.MPGTest.CUT.
                Operational.Errors.UnexpectedTableContainer)
        with self.assertRaises(xrm2m.CiscoError):
            self.conn.get(p)

    def test_invalid_arg_error(self):
        p = (xrm2m.RootOper.MPGTest.CUT.
                Operational.Errors.InvalidArgTableContainer)
        with self.assertRaises(xrm2m.InvalidArgumentError):
            self.conn.get(p)

    def test_op_not_supported_read_error(self):
        p = (xrm2m.RootOper.MPGTest.CUT.
                Operational.Errors.NotSupportedTableContainer)
        with self.assertRaises(xrm2m.OperationNotSupportedError):
            self.conn.get(p)

    def test_op_not_supported_write_error(self):
        p = (xrm2m.RootOper.MPGTest.CUT.
                Operational.Errors.NotSupportedTableContainer)
        with self.assertRaises(xrm2m.OperationNotSupportedError):
            self.conn.set(p)

    def test_path_hierarchy_error(self):
        p = xrm2m.RootOper.MPGTest.XYZ
        with self.assertRaises(xrm2m.PathHierarchyError):
            self.conn.get(p)

    def test_path_key_content_error(self):
        p = (xrm2m.RootOper.MPGTest.CUT.Operational.SchemaStructure.Keys.
                MacAddressKeyTableContainer.MacAddressKey)
        with self.assertRaises(xrm2m.PathKeyContentError):
            self.conn.get(p("15"))

    def test_path_key_structure_error(self):
        p = xrm2m.RootOper.MPGTest.CUT.Operational.SchemaStructure.Keys
        with self.assertRaises(xrm2m.PathKeyStructureError):
            self.conn.get(p("15"))
        with self.assertRaises(xrm2m.PathKeyStructureError):
            self.conn.get(p(pig="15"))

    def test_value_content_error(self):
        p = xrm2m.RootCfg.MPGTest.CUT.Write.Basic.BasicLeaf
        with self.assertRaises(xrm2m.ValueContentError):
            self.conn.set(p, "cow")

    def test_value_structure_error(self):
        p = xrm2m.RootCfg.MPGTest.CUT.Write.Basic
        with self.assertRaises(xrm2m.ValueStructureError):
            self.conn.set(p, "cow")

