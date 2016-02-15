# -----------------------------------------------------------------------------
# _errors.py - External error definitions and utilities.
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

"""External error definitions and utilities."""


import sys


__all__ = (
    'AmbiguousPathError',
    'CiscoError',
    'ConfigCommitError',
    'ConnectionError',
    'DatatypeNotSupportedError',
    'DisconnectedError',
    'FileExistsError',
    'InternalError',
    'InvalidArgumentError',
    'NotFoundError',
    'OperationNotSupportedError',
    'ParseError',
    'PathHierarchyError',
    'PathKeyContentError',
    'PathKeyStructureError',
    'PathStringFormatError',
    'ValueContentError',
    'ValueStructureError',
)


class ConnectionError(Exception):
    """
    Raised if connecting or reconnecting failed.

    Can be raised by :func:`.connect`, :func:`.connect_async` or
    :meth:`.Connection.reconnect`.

    """


class DisconnectedError(Exception):
    """
    Raised by methods requiring a connection, if one has not been established.

    The exception is raised in the following cases:

    - The connection was not available before the method was called.
    - The connection went away before the method returned.

    A connection is considered to be not available if it is not in `CONNECTED`
    state. See :data:`.Connection.state` for more details.

    """


class AmbiguousPathError(Exception):
    """
    A `get_value` request matched multiple paths.

    .. attribute:: path

        The path passed to `get_value`.

    """
    def __init__(self, msg, path=None):
        super(AmbiguousPathError, self).__init__(msg)
        self.path = path


class RequestError(Exception):
    """
    Base class for (expected) request errors.

    """


class InternalError(Exception):
    """
    Base class for errors which are not expected to be seen.

    These exceptions indicate a bug in either the M2M API, or in the server
    code.

    Note that this class is not intended to cover all such errors, for example
    missing fields in a response's `result` field may raise a `KeyError`.

    """


class CiscoError(RequestError):
    """
    An error not covered by one of the other error types was encountered during
    processing a request. This error is used for errors represented by cerrnos
    - the associated error string is presented as the exception message string.

    """


class ConfigCommitError(RequestError):
    """
    A commit request failed.

    .. attribute:: detail

        Dictionary mapping failed :class:`.Path` objects to
        :class:`.ConfigCommitErrorDetail` objects which give the specific
        failure details.

    """
    detail = None
    def __init__(self, msg, detail):
        self.detail = detail
        super(ConfigCommitError, self).__init__(msg)


class DatatypeNotSupportedError(RequestError):
    """
    The requested operation is not supported for the corresponding data type.

    """


class FileExistsError(RequestError):
    """
    The user provided an invalid filename to the write_file method, for example
    a directory that does not exist. More details are given in the message
    field

    .. attribute:: filename

        The missing file name.

    """
    filename = None
    def __init__(self, msg, filename):
        self.filename = filename
        super(FileExistsError, self).__init__(msg)


class InvalidArgumentError(RequestError):
    """
    An input argument was detected to be invalid by an IOS-XR feature.

    This exception may, in rare circumstances, be raised when working with data
    access functions. In general problems with input data should be detected
    and reported (in a descriptive way!) by MPG.

    .. attribute:: path

        :class:`.Path` recording which data was requested.

    """
    path = None
    def __init__(self, msg, path):
        self.path = path
        super(InvalidArgumentError, self).__init__(msg)


class NotFoundError(RequestError):
    """
    An attempt was made to access data that doesn't exist.

    .. attribute:: path

        :class:`.Path` to which the error is related.

    """
    path = None
    def __init__(self, msg, path):
        self.path = path
        super(NotFoundError, self).__init__(msg)


class OperationNotSupportedError(RequestError):
    """
    The requested operation is not supported.

    .. attribute:: path

        :class:`.Path` to which the error is related.

    """
    path = None
    def __init__(self, msg, path):
        self.path = path
        super(OperationNotSupportedError, self).__init__(msg)


class PathHierarchyError(RequestError):
    """
    An invalid path through the schema hierarchy was specified.

        >>> conn.get_schema(RootOper.Interfaces.Interface)
        PathHierarchyError: 'Interface' is not a child of 'Interfaces'

    .. attribute:: element

        Name of the path element that doesn't match the schema (e.g.
        `'Interface` in the example above).

    .. attribute:: parent

        Name of the last valid element in the path (e.g. `'Interfaces'` in the
        example above).

    """
    element = None
    parent = None
    def __init__(self, msg, element, parent):
        self.element = element
        self.parent = parent
        super(PathHierarchyError, self).__init__(msg)


class PathKeyContentError(RequestError):
    """
    A path key value is not compatible with its schema data type.

    This exception may be raised when a request is made on a path which has
    invalid key types. For example::

        >>> intf_cfg_path = RootCfg.InterfaceConfiguration
        >>> intf_cfg_path = intf_cfg_path("act", "HundredGigE0/0")
        >>> conn.get_value(intf_cfg_path)
        PathKeyContentError: 'HundredGigE0/0' is not a valid InterfaceName value

    .. attribute:: param

        Instance of :class:`.SchemaParam` containing the schema meta-data
        that the value failed to conform with.

    .. attribute:: value

        Invalid value specified.

    """
    param = None
    value = None
    def __init__(self, msg, param, value):
        self.param = param
        self.value = value
        super(PathKeyContentError, self).__init__(msg)


class PathKeyStructureError(RequestError):
    """
    A collection of path key values doesn't have the correct structure.

    This exception may be raised, for example, when adding key values to a
    path the values don't conform with union constraints::

        >>> nbr
        Path(RootOper.EIGRP.Process(1).Neighbour)
        >>> nbr = nbr("foovrf", "IPv4", 3)
        >>> conn.get_value(nbr)
        PathKeyStructureError: Invalid union combination: VRFName, AFName, ASN

    .. attribute:: class_name

        Name of the the schema class that the values fail to conform with.

    .. attribute:: value_seq

        Sequence of values passed as the path key (e.g.
        `['foovrf', 'IPv4', 3]` in the example above).

    """
    class_name = None
    value_seq = None
    def __init__(self, msg, class_name, value_seq):
        self.class_name = class_name
        self.value_seq = value_seq
        super(PathKeyStructureError, self).__init__(msg)


class PathStringFormatError(RequestError):
    """
    A string representation of a path is badly formatted.

    This exception may be raised when attempting to create a
    :class:`.Path` from a string representation::

        >>> Path.from_str(conn, 'RootOper.Abc.Def(10.0.0.1)')
        PathStringFormatError: Unquoted string '10.0.0.1' not recognised as a literal value (e.g. 'null')

    .. attribute:: pathstr

        Path string that this exception relates to.

    """
    pathstr = None
    def __init__(self, msg, pathstr):
        self.pathstr = pathstr
        super(PathStringFormatError, self).__init__(msg)


class ParseError(PathStringFormatError):
    """
    Path parsing failed.

    Parse error that can be returned by :meth:`.Path.fromstr`.

    .. attribute:: idx

        The index into the string where the error occurred.

    .. attribute:: pathstr

        The string that was being parsed.

    .. attribute:: msg

        Description of the error message.

    """

    def __init__(self, idx, pathstr, msg):
        super(ParseError, self).__init__(
                "Error parsing path {!r} at index {}: {}".format(pathstr,
                                                                 idx, msg),
                pathstr)
        self.idx = idx
        self.pathstr = pathstr
        self.msg = msg

    def print(self, file=sys.stdout):
        """
        Print the error message.

        :param file:
            File-like object to which the message will be written.

        """
        print("Parse error at index {}:".format(self.idx), file=file)
        print("    {}".format(self.pathstr), file=file)
        print(" " * (4 + self.idx) + "^", file=file)
        print("    {}".format(self.msg), file=file)


class ValueContentError(RequestError):
    """
    An element in a value sequence is not compatible with its schema data type.

    This exception may be raised when attempting to set a value. For example::

        >>> ipv4_addr = intf_ipv4_config.Addresses.Primary
        >>> conn.set([ipv4_addr, ["10.0.0.", "255.0.0.0"]])
        ValueContentError: '10.0.0.' is not a valid IPv4Address value

    .. attribute:: param

        Instance of :class:`.SchemaParam` containing the schema meta-data that
        the value failed to conform with.

    .. attribute:: value

        Invalid value specified.

    """
    param = None
    value = None
    def __init__(self, msg, param, value):
        self.param = param
        self.value = value
        super(ValueContentError, self).__init__(msg)


class ValueStructureError(RequestError):
    """
    A collection of values doesn't have the correct structure.

    This exception may be raised when attempting to write values if, for
    example, some mandatory elements of the value sequence have been omitted::

        >>> intf_ipv4
        Path(RootCfg.InterfaceConfiguration('act', 'Loopback0').IPV4Network)
        >>> conn.set([intf_ipv4.Addresses.Primary, ["203.0.0.1"]])
        ValueStructureError: Too few values: need 2, have 1

    .. attribute:: class_name

        Name of the the schema class containing the schema meta-data that the
        values fail to conform with.

    .. attribute:: value_seq

        Sequence of values passed (e.g. `['203.0.0.1']` in the example above).

    """
    class_name = None
    value_seq = None
    def __init__(self, msg, class_name, value_seq):
        self.class_name = class_name
        self.value_seq = value_seq
        super(ValueStructureError, self).__init__(msg)

