# -----------------------------------------------------------------------------
# _shared_conn.py - Connection objects.
#
# September 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


"""
Connection objects.

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


import json

from . import _async
from . import _defs
from . import _errors
from . import _path
from . import _schema
from . import _transport
from . import _utils
from ._shared import utils

from ._async import From, Return
from ._logging import logger

# Import items from the shared connection
from ._shared import conn as _shared_conn
# ConnectionState used unmodified
from ._shared.conn import (
    ConnectionState,
)


# Included in JSON-RPC headers
_JSON_RPC_VERSION = "2.0"


_JSON_ENCODING = "ascii"


@_utils.copy_docstring_from_parent
class Connection(_shared_conn.Connection):
    """
    Connection to a router, with synchronous methods.

    Connections are created with :func:`.connect`. See the corresponding
    documentation for more information.

    Note: `Connection`s are not thread-safe: No two threads should concurrently
    call a single `Connection`'s methods.

    """

    # Methods which should be wrapped with run_until_complete().
    WRAPPED_ASYNC_METHODS = (
        'cli_describe',
        'cli_exec',
        'cli_get',
        'cli_get_nested',
        'cli_set',
        'cli_replace',
        'commit',
        'commit_replace',
        '_connect',
        'delete',
        'discard_changes',
        'disconnect',
        'get',
        'get_children',
        'get_changes',
        'get_nested',
        'get_parent',
        'get_schema',
        'get_value',
        'get_version',
        'normalize_path',
        'reconnect',
        'replace',
        'set',
        'write_file',
    )

    # Other attributes which should be directly mirrored by this class.
    WRAPPED_ATTRS = (
        'state',
    )

    def __init__(self, async_conn):
        """
        Create a new synchronous connection.

        :class:`.Connection`s should be created with :func:`.connect` rather
        than creating the object directly.

        This constructor accepts an asynchronous connection, which this
        (synchronous) connection will wrap.

        """
        self._async_conn = async_conn

    def _make_sync(self, func):
        """Make a given asynchronous function synchronous."""

        @_utils.copy_docstring(func)
        def wrapper(*args, **kwargs):
            future = func(*args, **kwargs)
            self._async_conn._loop.run_until_complete(future)
            return future.result()

        return wrapper

    def __getattribute__(self, name):
        if name in object.__getattribute__(self, "WRAPPED_ASYNC_METHODS"):
            assert hasattr(self._async_conn, name)
            out = self._make_sync(getattr(self._async_conn, name))
        elif name in object.__getattribute__(self, "WRAPPED_ATTRS"):
            assert hasattr(self._async_conn, name)
            out = getattr(self._async_conn, name)
        else:
            out =  object.__getattribute__(self, name)

        return out

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__,
                                 self._async_conn)


@_utils.copy_docstring_from_parent
class AsyncConnection(_shared_conn.AsyncConnection):
    """
    A connection to a router, with asynchronous methods.

    Objects of this type are equivalent to those of :class:`.Connection`,
    except the request methods are synchronous: They return the result directly
    rather than returning a future. See the :class:`.Connection` documentation
    for more details.

    Note: `AsyncConnection`s are not thread-safe: No two threads should
    concurrently call a single `AsyncConnection`'s methods.

    """

    def __init__(self, transport=None, loop=None):
        if loop:
            self._loop = loop
        else:
            self._loop = _async.get_event_loop()

        if transport:
            self._transport = transport
        else:
            # @@@@@@ raise ValueError if not on box?
            self._transport = _transport.LoopbackTransport()

        self._id = None

        # This is the same as the underlying transport's state, except it can
        # be in disconnected state if a connection-wide error condition is hit
        # (eg.  mangled JSON has been received). In which case the user is
        # forced to reconnect.
        #
        # The variable must only be assigned with `_set_state`.
        self._state = ConnectionState.DISCONNECTED

        # Mapping of IDs to futures. Presence of an ID in the dict indicates
        # that the request is in-flight. The corresponding future will be
        # completed when the response with the same ID is received.
        self._request_futures = {}

        # A future which will complete when the connection changes state. Every
        # time the state changes this future is completed, and the variable is
        # assigned a new future.
        self._state_change_future = _async.Future(loop=self._loop)

        # Flag used by `disconnect()` to suppress logging of an error message.
        self._expect_disconnect = False

    # State transition methods
    @property
    def state(self):
        """
        The connection's state.

        :return:

            A :class:`.ConnectionState`.

        """
        return self._state

    def _set_state(self, state, disconnect_msg=None):
        """
        Change the connection state.

        Set the state-change future with the result. In the case of a
        disconnection, a `disconnect_msg` parameter will also be passed. This
        is the exception string that will be raised by any in-flight connection
        attempts.

        """
        if state is ConnectionState.DISCONNECTED:
            assert disconnect_msg is not None
        else:
            assert disconnect_msg is None

        logger.debug("{}: Changing from state {} to {}".format(
                        self, self.state, state))
        self._state = state

        self._state_change_future.set_result(disconnect_msg)
        self._state_change_future = _async.Future(loop=self._loop)

    @_async.make_task
    @_async.coroutine
    def _connect(self):
        """Open the connection."""

        if self.state is ConnectionState.CONNECTED:
            raise _errors.ConnectionError("Already connected")
        if self.state is ConnectionState.CONNECTING:
            raise _errors.ConnectionError("Already connecting")

        # Create a task to connect and perform reads. Because the connection is
        # disconnected we know that such a task does not already exist.
        _async.Task(self._connect_and_read_loop(), loop=self._loop,
                    id="Connect and read loop for {!r}".format(self))

        # Allow the above task to begin executing, after which the connection
        # should have moved into connecting state.
        yield
        assert self.state is ConnectionState.CONNECTING

        # Wait until the connection has connected, or has failed to connect.
        # Raise an exception in the latter case.
        while self.state is ConnectionState.CONNECTING:
            disconnect_msg = yield From(self._state_change_future)

        if disconnect_msg is not None:
            raise _errors.ConnectionError(disconnect_msg)

        assert self.state is ConnectionState.CONNECTED

    @_async.make_task
    @_async.coroutine
    def disconnect(self):
        if self.state is ConnectionState.DISCONNECTED:
            raise _errors.DisconnectedError

        self._expect_disconnect = True
        try:
            yield From(self._transport.disconnect())

            while self.state != ConnectionState.DISCONNECTED:
                yield From(self._state_change_future)
        finally:
            self._expect_disconnect = False

    @_async.make_task
    @_async.coroutine
    def reconnect(self):
        """
        Reconnect to connection.

        Disconnect first if connected or connecting.

        """
        if self.state != ConnectionState.DISCONNECTED:
            yield From(self.disconnect())

        yield From(self._connect())

    # Connect and read-loop methods

    def _on_read_line(self, line):
        """
        Parse the line into a JSON message.

        Also complete the future that was waiting for the message.

        """
        try:
            response = json.loads(line)
        except ValueError:
            raise _errors.MalformedJSONReceived(line)

        if response["id"] not in self._request_futures:
            raise _errors.UnexpectedResponseID(
                    "Received response with unexpected ID {}".format(
                                                               response["id"]))

        self._request_futures[response["id"]].set_result(response)

    @_async.coroutine
    def _connect_and_read_loop_inner(self):
        """
        Business logic for :meth:`._connect_and_read_loop`.

        See :meth:`._connect_and_read_loop` for more details.

        """
        assert self.state is ConnectionState.DISCONNECTED

        self._set_state(ConnectionState.CONNECTING)
        self._id = 1
        if self._transport.state != _transport.State.DISCONNECTED:
            yield From(self._transport.disconnect())
        yield From(self._transport.connect(self._loop))
        self._set_state(ConnectionState.CONNECTED)

        partial_line = ""
        while True:
            d = yield From(self._transport.read())
            s = d.decode(_JSON_ENCODING)
            partial_line += s

            lines = partial_line.split('\n')
            partial_line = lines[-1]

            for line in lines[:-1]:
                self._on_read_line(line)

    @_async.coroutine
    def _connect_and_read_loop(self):
        """
        Main coroutine for this connection.

        Handles:
          - Connecting to the transport.
          - Reading data from the transport.
          - Setting the result of request futures (when the corresponding
            response arrives).
          - Erroring request futures (on connection-wide errors).
          - Changing the connection state.

        This function itself is concerned with error handling, and defers to
        :meth:`._connect_and_read_loop_inner` for the business logic.

        """
        try:
            yield From(self._connect_and_read_loop_inner())
        except _transport.TransportConnectionError:
            logger.error("{}: Transport failed to connect.".format(self),
                         exc_info=True)
            self._set_state(ConnectionState.DISCONNECTED,
                            lambda: _errors.ConnectionError())
        except _transport.TransportNotConnected:
            if not self._expect_disconnect:
                logger.error("{}: Transport not connected.".format(self),
                             exc_info=True)
                self._set_state(ConnectionState.DISCONNECTED,
                                "Transport disconnected")
            else:
                self._set_state(ConnectionState.DISCONNECTED,
                                "Disconnect called")
        except Exception:
            logger.error("{}: Connection-wide error".format(self),
                         exc_info=True)
            self._set_state(ConnectionState.DISCONNECTED,
                            "Connection-wide error")
        else:
            assert False, "The only way _connect_and_read_loop_inner() can " \
                                              "exit is by raising an exception"

        for request_future in self._request_futures.values():
            request_future.set_exception(_errors.DisconnectedError)

    @_async.coroutine
    def _send_request(self, method_name, params):
        """
        Send a RPC request and return the response asynchronously.

        On success, the `result` field is returned.

        On failure, the error is converted into one of the corresponding
        exceptions and raised.

        """
        if self.state != ConnectionState.CONNECTED:
            raise _errors.DisconnectedError

        req = {
                "jsonrpc": _JSON_RPC_VERSION,
                "id": self._id,
                "method": method_name,
                "params": params,
              }

        # Write the data to the transport.
        try:
            self._transport.write(json.dumps(req, default=str).encode(
                                                              _JSON_ENCODING) +
                                  b"\n")
        except _transport.TransportNotConnected:
            assert False, "Should have raised DisconnectedError above."
        except Exception:
            raise

        # Successfully written, so increment the ID for the next request.
        self._id += 1

        # Set up a future to be completed when the corresponding response is
        # received.
        assert req["id"] not in self._request_futures
        response_future = _async.Future(loop=self._loop)
        self._request_futures[req["id"]] = response_future

        # When the response is received map the result, or the exception, into
        # the form expected by the caller.
        try:
            response = yield From(response_future)
        except Exception:
            logger.error("{}: Request {} failed".format(self, req["id"]),
                         exc_info=True)
            raise
        else:
            logger.debug("{}: Request {} succeeded".format(self, req["id"]))
        finally:
            del self._request_futures[req["id"]]

        if "error" in response:
            raise _errors.error_from_error_field(response["error"])

        raise Return(response["result"])

    # Request methods

    @_async.make_task
    @_async.coroutine
    def get(self, path):
        result = yield From(self._send_request("get",
                                       {"path": str(path), "format": "pairs"}))
        raise Return([(_path.Path.from_str(p), v) for p, v in result])

    @_async.make_task
    @_async.coroutine
    def get_nested(self, path):
        result = yield From(self._send_request("get",
                                      {"path": str(path), "format": "nested"}))
        raise Return(result)

    @_async.make_task
    @_async.coroutine
    def get_children(self, path):
        result = yield From(self._send_request("get_children",
                                                          {"path": str(path)}))
        raise Return([_path.Path.from_str(p) for p in result])

    @_async.make_task
    @_async.coroutine
    def set(self, leaf_or_iter, value=None):
        if isinstance(leaf_or_iter, (type(""), _path.Path)):
            leaf_values = [(leaf_or_iter, value)]
        else:
            leaf_values = list(leaf_or_iter)

        def convert_val(val):
            if isinstance(val, (type(""), type(b""))):
                out = utils.sanitize_input_string(val)
            elif isinstance(val, _defs.Password):
                out = {"encrypted": False, "password": val}
            else:
                out = val
            return out
        paths = [str(path) for path, val in leaf_values]
        values = [convert_val(val) for path, val in leaf_values]
        yield From(self._send_request("set", {"path": paths, "value": values}))

    @_async.make_task
    @_async.coroutine
    def delete(self, path_or_iter):
        if isinstance(path_or_iter, (type(""), _path.Path)):
            paths = [path_or_iter]
        else:
            paths = path_or_iter
        paths = [str(p) for p in paths]
        yield From(self._send_request("delete", {"path": paths}))

    @_async.make_task
    @_async.coroutine
    def replace(self, subtree_or_iter):
        if isinstance(subtree_or_iter, (type(""), _path.Path)):
            subtrees = [subtree_or_iter]
        else:
            subtrees = subtree_or_iter
        subtrees = [str(p) for p in subtrees]
        yield From(self._send_request("replace", {"path": subtrees}))

    @_async.make_task
    @_async.coroutine
    def commit(self):
        commit_id = yield From(self._send_request("commit", {}))
        logger.info("Commit succeeded. Commit ID: {}".format(commit_id))

    @_async.make_task
    @_async.coroutine
    def commit_replace(self):
        commit_id = yield From(self._send_request("commit_replace", {}))
        logger.info("Commit replace succeeded. Commit ID: {}".format(
                                                                    commit_id))

    @_async.make_task
    @_async.coroutine
    def discard_changes(self):
        yield From(self._send_request("discard_changes", {}))

    @_async.make_task
    @_async.coroutine
    def get_changes(self):
        changes = yield From(self._send_request("get_changes", {}))
        raise Return(
            [
                _defs.ChangeDetails(
                      path=_path.Path.from_str(change["path"]),
                      op=_defs.Change[change["operation"]],
                      value=change["value"])
                for change in changes
            ])

    @_async.make_task
    @_async.coroutine
    def get_version(self):
        ver = yield From(self._send_request("get_version", {}))
        raise Return(_schema.Version(major=ver["major"],
                                     minor=ver["minor"]))

    @_async.make_task
    @_async.coroutine
    def get_parent(self, path):
        path_str = yield From(self._send_request("get_parent",
                                                          {"path": str(path)}))
        raise Return(_path.Path.from_str(path_str))

    @_async.make_task
    @_async.coroutine
    def cli_describe(self, command, config=False):
        result = yield From(self._send_request("cli_describe",
                                      {"command": command,
                                       "configuration": config}))
        raise Return([_defs.Request(
                        method=_defs.Method[d["method"].upper()],
                        path=_path.Path.from_str(d["path"]),
                        value=d.get("value")) for d in result])

    @_async.make_task
    @_async.coroutine
    def cli_get(self, command):
        result = yield From(self._send_request("cli_get",
                                      {"command": command, "format": "pairs"}))
        raise Return([(_path.Path.from_str(p), v) for p, v in result])

    @_async.make_task
    @_async.coroutine
    def cli_set(self, command):
        yield From(self._send_request("cli_set", {"command": command}))

    @_async.make_task
    @_async.coroutine
    def cli_get_nested(self, command):
        result = yield From(self._send_request("cli_get",
                                     {"command": command, "format": "nested"}))

        raise Return(result)

    @_async.make_task
    @_async.coroutine
    def cli_exec(self, command):
        result = yield From(self._send_request("cli_exec",
                                               {"command": command}))
        raise Return(result)

    @_async.make_task
    @_async.coroutine
    def write_file(self, data, filename):
        yield From(self._send_request("write_file",
                                      {"data": data, "filename": filename}))

    @_async.make_task
    @_async.coroutine
    def get_schema(self, path):
        if isinstance(path, _path.Path):
            path_str = str(path)
        else:
            path_str = path
            path = _path.Path.from_str(path_str)
        info_dict = yield From(self._send_request("get_schema",
                                                           {"path": path_str}))

        raise Return(_schema.SchemaClass.from_dict(path, info_dict))

    @_async.make_task
    @_async.coroutine
    def normalize_path(self, path):
        norm_path_str = yield From(self._send_request("normalize_path",
                                                      {"path": str(path)}))
        raise Return(_path.Path.from_str(norm_path_str))

    @_async.make_task
    @_async.coroutine
    def get_value(self, path):
        if isinstance(path, _path.Path):
            path_str = str(path)
        else:
            path_str = path
            path = _path.Path.from_str(path_str)
        get_result = yield From(self.get(path_str))
        if len(get_result) > 1:
            raise _errors.AmbiguousPathError("Multiple paths match {}".format(
                                                    path),
                                             path=path)
        if len(get_result) == 0:
            raise _errors.NotFoundError("No paths match {}".format(path),
                                        path=path)
        raise Return(get_result[0][1])

    def __repr__(self):
        return ("{}(state={}, _transport={!r}, "
                    "len(_request_futures)={!r})".format(
                                                   type(self).__name__,
                                                   self.state,
                                                   self._transport,
                                                   len(self._request_futures)))


@_utils.copy_docstring(_shared_conn.connect_async)
def connect_async(transport=None, loop=None):
    conn = AsyncConnection(transport, loop=loop)

    @_async.coroutine
    def coro():
        yield From(conn._connect())
        raise Return(conn)

    return _async.Task(coro(), loop=loop, id="connect_async() call")


@_utils.copy_docstring(_shared_conn.connect)
def connect(transport=None, loop=None):
    conn = Connection(AsyncConnection(transport, loop=loop))

    conn._connect()

    return conn


@_utils.copy_docstring(_shared_conn.sync)
def sync(async_conn):
    # Docstring copied from "_shared"
    return Connection(async_conn)


@_utils.copy_docstring(_shared_conn.async)
def async(sync_conn):
    # Docstring copied from "_shared"
    return sync_conn._async_conn

