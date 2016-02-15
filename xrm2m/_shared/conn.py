# -----------------------------------------------------------------------------
# conn.py - M2M Connections
#
# December 2015, Ian Kimpton
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


"""
M2M connection objects.

"""


__all__ = (
    'async',
    'AsyncConnection',
    'connect',
    'connect_async',
    'Connection',
    'ConnectionState',
    'sync',
)


import enum


class ConnectionState(enum.Enum):
    """
    Representation of a :class:`.Connection`'s state.

    .. attribute:: CONNECTED

        Connected to the router. This is the only state in which request
        methods can be made.

    .. attribute:: CONNECTING

        In the process of connecting to the router, ie. :func:`connect_async`,
        :func:`connect`, or :meth:`.Connection.reconnect` has been called but
        has not yet returned.

    .. attribute:: DISCONNECTED

        Not connected to the router, and not connecting.

        A :class:`.Connection` may move into this state from `CONNECTED` if:

        - The transport fails, or

        - A connection-wide error condition is hit.

        A :class:`.Connection` may move into this state from `CONNECTING` if:

        - The in-flight :func:`.connect_async` call fails, or
        - The in-flight :meth:`.Connection.reconnect` call fails.

    """
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class _ConnectionBase(object): # pragma: no cover
    @property
    def state(self):
        """
        The connection's state.

        :return:

            A :class:`.ConnectionState`.

        """

    def disconnect(self):
        """
        Disconnect the connection.

        """

    def reconnect(self):
        """
        Reconnect to the router.

        If already connected, disconnect first and then connect. If connecting,
        wait for connection to complete, return when connected.

        Note that if reconnect has already been called from another thread,
        this function will return once a reconnection has happened, rather than
        disconnecting and then reconnecting.

        See :data:`.state` for the current connection state.

        """

    def get_nested(self, path):
        """
        Read paths and values under a given path, returning structured data.

        Example::

            >>> c.get_nested(RootOper.Foo.Interface)
            ... {
            ...     "RootOper": {
            ...         "Foo": {
            ...             "Interface": [{
            ...                 "IntfName": "GigE0",
            ...                 "a": 1,
            ...                 "b": 2
            ...             }, {
            ...                 "IntfName": "GigE1",
            ...                 "a": 6,
            ...                 "b": 7
            ...             }]
            ...         }
            ...     }
            ... }


        :param path:
            :class:`.Path` identifying which paths and values should be
            returned.

        :returns:
            Return a nested dict/list containing the retreived values. The
            information retrieved is equivalent to that returned by
            :meth:`.get`. Leaves in the structures correspond with the values
            returned by `get`. See example for how the dict is formatted.

        :raises:
            - :exc:`.OperationNotSupportedError`
            - :exc:`.InvalidArgumentError`
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get(self, path):
        """
        Read paths and values under a given path.

        Example::

            >>> c.get(RootOper.Foo.Interface)
            ... [[RootOper.Foo.Interface({'IntfName': 'GigE0'}), {"a": 1, "b": 2}],
            ...  [RootOper.Foo.Interface({'IntfName': 'GigE1'}), {"a": 5, "b": 6}]]

        :param path:
            :class:`.Path` identifying which paths and values should be
            returned.

        :returns:
            Iterable of :class:`.Path`, value pairs.

        :raises:
            - :exc:`.OperationNotSupportedError`
            - :exc:`.InvalidArgumentError`
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get_children(self, path):
        """
        Read key/index information (in the form of paths) under a given path.

        Example::

            >>> vrfs = RootCfg.VRF
            >>> for path in get_children(vrfs):
            ...     print(path)
            ...
            Path(RootCfg.VRF('bar'))
            Path(RootCfg.VRF('foo'))

        :param path:
            :class:`.Path` for which key/index information is being sought.

        :returns:
            Iterable of :class:`.Path`.

        :raises:
            - :exc:`.OperationNotSupportedError`
            - :exc:`.InvalidArgumentError`
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def set(self, leaf_or_iter, value=None):
        """
        Set the value of one or more leaves.

        Example::

            >>> intf = RootCfg.InterfaceConfiguration
            >>> set(intf("act", "HundredGigE0/0/0/0").VRF, "barvrf")
            >>> set(intf("act", "HundredGigE0/0/0/1").VRF, "bazvrf")

        Or equivalently::

            >>> intf = RootCfg.InterfaceConfiguration
            >>> set([(intf("act", "HundredGigE0/0/0/0").VRF, "barvrf"),
            ...      (intf("act", "HundredGigE0/0/0/1").VRF, "bazvrf")])

        :param leaf_or_iter:
            A :class:`.Path` indicating the leaf being set, or a sequence of
            `path`, `value` pairs, each of which will be set accordingly.

        :param value:
            The `value` to be set. This should only be provided when
            `leaf_or_iter` is a :class:`.Path`.

        :raises:
            - :exc:`.OperationNotSupportedError`
            - :exc:`.InvalidArgumentError`
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.NotFoundError`
            - :exc:`.DatatypeNotSupportedError`
            - :exc:`.ValueContentError`
            - :exc:`.ValueStructureError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def delete(self, path_or_iter):
        """
        Delete the contents of one or more leaves/subtrees.

        :param path_or_iter:
            Either a :class:`.Path` or an iterable of :class:`.Path` to be
            deleted.

        :raises:
            - :exc:`.OperationNotSupportedError`
            - :exc:`.InvalidArgumentError`
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.NotFoundError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def replace(self, subtree_or_iter):
        """
        Mark one or more subtrees for atomic replacement.

        :param subtree_or_iter:
            Either a :class:`.Path` or an iterable of :class:`.Path` to be
            marked for replacement.

        :raises:
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.NotFoundError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def commit(self):
        """
        Commit the config changes made using this connection.

        :raises:
            - :exc:`.ConfigCommitError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def commit_replace(self):
        """
        Commit the config changes made using this connection, replacing all
        existing config.

        :raises:
            - :exc:`.ConfigCommitError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def discard_changes(self):
        """
        Discard any uncommitted config changes made using this connection.

        :raises:
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get_changes(self):
        """
        Return the changes in running config built up (but not yet commited) on
        this connection.

        This method can be used to examine the changes that would be made if
        :meth:`.commit` were called::

            >>> for change in conn.get_changes():
            ...     print(change.path)
            ...     print(change.op.name, change.value)
            ...     print("--")
            ...
            Path(RootCfg.Hostname)
            SET R1-BOS
            --
            Path(RootCfg.InterfaceConfiguration("act", "HundredGigE0/0/0/0").Shutdown)
            DELETE None
            --

        :returns:
            Sequence of :class:`.ChangeDetails` for every change that would be
            made if the config changes on this connection were committed.

        :raises:
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get_version(self):
        """
        Return the current M2M API version number.

        :returns:
            A `major`,`minor` pair of ints, representing the API major and
            minor version number, respectively.

        :raises:
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get_parent(self, path):
        """
        Get the parent of a data path.

        :param path:
            A :class:`.Path` whose parent is to be found.

        :returns:
            A :class:`.Path` which is the parent of the path being found.

        :raises:
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def cli_describe(self, command, config=False):
        """
        Find underlying requests associated with a given command.

        :param command:
            The command whose underlying requests are being sought. The command
            is a single line.

        :param configuration:
            Indicates whether or not the command is a configuration command, or
            an exec command.

        :returns:
            A sequence of :class:`.Request` objects.

        :raises:
            - :class:`.DisconnectedError` if the connection was lost.
            - :class:`.InvalidArg` if the command is invalid.

        """
        raise NotImplementedError

    def cli_get(self, command):
        """
        Retrieve data given a CLI command.

        The command is equivalent to doing a :meth:`.get` call for each path
        that the command fetches, and concatenating the results.

        Example::

            >>> c.cli_get("show foo interfaces")
            ... [["RootOper.Foo.Interface({'IntfName': 'GigE0'})", {"a": 1, "b": 2}],
            ...  ["RootOper.Foo.Interface({'IntfName': 'GigE1'})", {"a": 5, "b": 6}]]

        :param command:
            CLI command to fetch data for.

        :returns:
            Iterable of :class:`.Path`, value pairs.

        :raises:
            - :exc:`.InvalidArgumentError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def cli_get_nested(self, command):
        """
        Retrieve structured data given a CLI command.

        The command is equivalent to doing a :meth:`.get_nested` call for
        each path that the command fetches, and combining the results.

        Example::

            >>> c.cli_get_nested("show foo interfaces")
            ... {
            ...     "RootOper": {
            ...         "Foo": {
            ...             "Interface": [{
            ...                 "IntfName": "GigE0",
            ...                 "a": 1,
            ...                 "b": 2
            ...             }, {
            ...                 "IntfName": "GigE1",
            ...                 "a": 6,
            ...                 "b": 7
            ...             }]
            ...         }
            ...     }
            ... }


        :param command:
            CLI command to fetch data for.

        :returns:
            Return a nested dict/list containing the retreived values. The
            information retrieved is equivalent to that returned by
            :meth:`.get`. Leaves in the structures correspond with the values
            returned by `get_nested`. See example for how the dict is
            formatted.

        :raises:
            - :exc:`.InvalidArgumentError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def cli_set(self, command):
        """
        Set/delete data corresponding with a config CLI command.

        Example::

            >>> c.cli_set("int GE/0/0/0 shut")

        :param command:
            Config CLI command.

        :raises:
            - :exc:`.InvalidArgumentError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def cli_exec(self, command):
        """
        Execute a CLI comand and return the resulting string.

        :param command:
            CLI command to fetch data for.

        :returns:
            The string returned when the command was executed.

        :raises:
            - :exc:`.InvalidArgumentError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def write_file(self, data, filename):
        """
        Writes the given string to the router's filesystem.

        :param data:
            A string which will be written to a file on the router's
            filesystem.

        :param filename:
            Path of the file on the router to which the file is to be written.

        :raises:
            - :exc:`.FileExistsError`
            - :exc:`PermissionError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get_value(self, path):
        """
        Retrieve the value of a given path.

        The functionality is equivalent to that of :meth:`get` where the path
        identifies a single leaf, except only the value is returned.

        A :class:`.AmbiguousPathError` is raised if the path matches multiple
        leaves. Note that the request may still succeed even if the path is not
        inherently unambiguous (ie. it contains wildcards or missing keys), in
        the case that the query

        :param path:
            A :class:`.Path` to be fetched.
        :returns:
            Scalar value of the leaf.

        :raises:
            - :exc:`.AmbiguousPathError`
            - :exc:`.OperationNotSupportedError`
            - :exc:`.InvalidArgumentError`
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.NotFoundError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def get_schema(self, path):
        """
        Return the schema meta-data for a path.

        This method returns a :class:`.SchemaClass` describing the last element
        of the path::

            >>> schema = conn.get_schema(RootCfg.InterfaceConfiguration)
            >>> print(schema)
            SchemaClass(InterfaceConfiguration)
            >>> schema.description
            'The configuration for an interface'
            >>> for child in schema.children[:5]:
            ...     print(child)
            Path(RootCfg.InterfaceConfiguration.PseudowireEther)
            Path(RootCfg.InterfaceConfiguration.IPv6Neighbor)
            Path(RootCfg.InterfaceConfiguration.MACAccounting)
            Path(RootCfg.InterfaceConfiguration.IPV6PacketFilter)
            Path(RootCfg.InterfaceConfiguration.PTP)

        The input :class:`.Path` identifies the point of interest in the schema
        hierarchy.

        Any key values in the path are ignored. In particular, it's ok to
        omit key values even where they'd usually be mandatory::

            >>> cls = conn.get_schema(RootCfg.InterfaceConfiguration.VRF)
            >>> print(cls)
            SchemaClass(VRF)

        If the path doesn't identify a valid sequence of classes in the schema,
        :exc:`.PathHierarchyError` is raised::

            >>> conn.get_schema(RootOper.Missing.Interface)
            PathHierarchyError: 'Missing' is not a child of 'RootOper'

        :param path:
            :class:`.Path` identifying the point in the hierarchy of interest.

        :returns:
            A :class:`.SchemaClass` object, as above.

        :raises:
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """
        raise NotImplementedError

    def normalize_path(self, path):
        """
        Return a validated copy of a path in the canonical format.

        :param path:
            :class:`.Path` to be normalized.

        :returns:
            Copy of this path, in the standard format returned from the M2M
            API. The returned path is compatible with all standard path
            functions, e.g. :meth:`.Path.key`.

        This method validates the contents of the path against the schema.

        It raises :exc:`.PathHierarchyError` if the sequence of element names
        in this path doesn't match the schema::

            >>> path = RootOper.Missing.Interface
            >>> conn.normalize_path(path)
            PathHierarchyError: 'Missing' is not a child of 'RootOper'

        It raises :exc:`.PathKeyStructureError` if (for example) the key values
        in this path don't include a value for a mandatory key::

            >>> path = RootCfg.InterfaceConfiguration("TenGigE0/2/0/0").VRF
            >>> conn.normalize_path(path)
            PathKeyStructureError: Too few key values for 'InterfaceConfiguration': need 2, have 1

        It raises :exc:`.PathKeyContentError` if one of the key values is
        incompatible with the data type defined by the schema.

        :raises:
            - :exc:`.PathHierarchyError`
            - :exc:`.PathStringFormatError`
            - :exc:`.PathKeyContentError`
            - :exc:`.PathKeyStructureError`
            - :exc:`.CiscoError`
            - :exc:`.DisconnectedError`

        """


# The Connection and AsyncConnection objects shoudl be used as parent clasess,
# to ensure that isintance(conn, AsyncConnection) works for both on-box and
# off-box!

class Connection(_ConnectionBase):
    """
    Connection to a router, with synchronous methods.

    Connections are created with :func:`.connect`, or :func:`.sync`. See the
    corresponding documentation for more information.

    """



class AsyncConnection(_ConnectionBase):
    """
    A connection to a router, with asynchronous methods.

    Async connections are created with :func:`.connect_async`, or
    :func:`.async`. See the corresponding documentation for more information.

    Objects of this type are equivalent to those of :class:`.Connection`,
    except the request methods are synchronous: They return the result directly
    rather than returning a future. See the :class:`.Connection` documentation
    for more details.

    """


def connect_async(transport=None, loop=None): # pragma: no cover
    """
    Asynchronously connect to a router, via the given transport.

    See :func:`.connect` for details on when a transport can be re-used.

    :param transport:
        The :class:`.Transport` to connect to the router with. If running on an
        IOS-XR router this argument may be omitted, in which case the
        connection will be made locally.

    :param loop:
        The event loop with which the future returned by this function will be
        associated. It is also the event loop that will be associated with
        the futures returned by the methods of the resulting
        :class:`.AsyncConnection` object. See `Event Loops
        <conn.html#event-loops>`__ for more details.

    :returns:
        A :class:`.AsyncConnection` representing the new connection.

    :raises:
        :class:`.ConnectionError` if the connection could not be made.

    """
    raise NotImplementedError


def connect(transport=None, loop=None): # pragma: no cover
    """
    Connect to a router, via the given transport.

    :param transport:
        The :class:`.Transport` to connect to the router with. If running on an
        IOS-XR router this argument may be omitted, in which case the
        connection will be made locally.

    :param loop:
        Optional event loop to use for any internal async calls that may be
        made. If not provided the default event loop will be used. See `Event
        Loops <conn.html#event-loops>`__ for more details.

    :returns:
        A :class:`.Connection` object representing the new connection.

    :raises:
        :class:`.ConnectionError` if the connection could not be made.

    """
    raise NotImplementedError


def sync(async_conn): # pragma: no cover
    """
    Return a :class:`.Connection` given a :class:`.AsyncConnection`.

    The returned object uses the same underlying connection as the input
    connection.

    :param conn:
        The :class:`.AsyncConnection` connection whose synchronous equivalent
        is to be sought.

    :returns:
        A :class:`.Connection` representing the synchronous version of `conn`.

    """
    raise NotImplementedError


def async(sync_conn): # pragma: no cover
    """
    Return a :class:`.AsyncConnection` given a :class:`.Connection`.

    The returned object uses the same underlying connection as the input
    connection.

    :param conn:
        The :class:`.Connection` connection whose asynchronous equivalent
        is to be sought.

    :returns:
        A :class:`.AsyncConnection` representing the asynchronous version of
        `conn`.

    """
    raise NotImplementedError


