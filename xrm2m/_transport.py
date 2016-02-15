# -----------------------------------------------------------------------------
# _transport.py - Transport layer
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

"""
Transport layer.

"""

__all__ = (
    'EnXRTransport',
    'LoopbackTransport',
    'SubProcessTransport',
    'SSHTransport',
    'State',
    'Transport',
    'TransportConnectionError',
    'TransportNotConnected',
)

import abc
import enum
import shlex

from . import _async
from . import _utils

from ._async import From, Return
from ._logging import logger

from ._shared import transport as _transport
from ._shared.transport import (
    State,
    Transport,
    TransportConnectionError,
    TransportNotConnected,
)

try:
    import paramiko.client
except ImportError:
    paramiko = None
  

# Path to the JSON-RPC server binary.
_JSON_RPC_SERVER_PATH = "json_rpc_server"


# Maximum amount to read in a single Transport.read() call.
_MAX_READ_AMOUNT = 1024


class _BaseTransport(Transport):
    """
    Base class for transports, which provides checks on correct calling
    patterns.

    """

    def __init__(self):
        super(_BaseTransport, self).__init__()
        self._read_in_progress = False

    @_async.coroutine
    def connect(self, loop):
        if self.state is State.CONNECTED:
            raise TransportConnectionError(
                              "Already connected. Connection in-flight.")
        if self.state is State.CONNECTING:
            raise TransportConnectionError(
                              "Connection already in-flight.")

        yield From(self._connect_no_check(loop=loop))

    @_async.coroutine
    def disconnect(self):
        if self.state is State.DISCONNECTED:
            raise TransportNotConnected
        yield From(self._disconnect_no_check())

    def write(self, data):
        if self.state != State.CONNECTED:
            raise TransportNotConnected
        self._write_no_check(data)

    @_async.coroutine
    def read(self):
        if self.state != State.CONNECTED:
            raise TransportNotConnected
        assert not self._read_in_progress, "Concurrent reads detected"
        self._read_in_progress = True
        try:
            d = yield From(self._read_no_check())
        finally:
            self._read_in_progress = False
        raise Return(d)


@_utils.copy_docstring(_transport.SSHTransport)
class SSHTransport(_BaseTransport):
    def __init__(self, hostname, username, key_filename=None, password=None,
                 port=22, look_for_keys=True, allow_agent=True):
        super(SSHTransport, self).__init__()

        # Import here to raise the ImportError if paramiko is not available.
        import paramiko.client

        self._connection_params = {'hostname': hostname,
                                   'username': username,
                                   'key_filename': key_filename,
                                   'password': password,
                                   'look_for_keys': look_for_keys,
                                   'allow_agent': allow_agent,
                                   'port': port}
        
        self._client = paramiko.client.SSHClient()
        self._state = State.DISCONNECTED
        self._read_in_progress = False

    def _connect_thread(self):
        self._client.set_missing_host_key_policy(
                                               paramiko.client.AutoAddPolicy())
        self._client.connect(**self._connection_params)
        (self._stdin,
         self._stdout,
         self._stderr) = self._client.exec_command("run json_rpc_server")

    @_async.coroutine
    def _connect_no_check(self, loop):
        self._loop = loop
        self._state = State.CONNECTING
        try:
            yield From(_async.wrap_external_coro(
                              loop.run_in_executor(None,
                                                   self._connect_thread)))
        except Exception:
            logger.error("{}: Connect failed".format(self), exc_info=True)
            self._state = State.DISCONNECTED
            raise TransportConnectionError

        # After running json_rpc_server, the server should send some blank
        # lines followed by a timestamp. Read those lines here.
        logger.debug("{}: Waiting for date line".format(self))
        line = None
        while line is None or line == b'\n':
            line = yield From(self._read_no_check())
        logger.debug("{}: Read date line {!r}".format(self, line))

        self._state = State.CONNECTED
        
    @_async.coroutine
    def _disconnect_no_check(self):
        logger.debug("{}: Disconnect called".format(self))
        self._client.close()
        self._state = State.DISCONNECTED

    def _write_no_check(self, data):
        self._stdin.write(data)
        self._stdin.flush()

    @_async.coroutine
    def _read_no_check(self):
        """
        Read a single line, fix line endings to "\n".
        
        The fixing of line endings is necessary because somewhere between
        json_rpc_server's stdout and what the SSH client sees UNIX-style line
        endings (\n) get converted to DOS-style (\r\n).
        
        """
        on_data_fut = _async.Future(self._loop)
        def on_data():
            on_data_fut.set_result(None)
        self._loop.add_reader(self._stdout.channel.fileno(), on_data)

        try:
            yield From(on_data_fut)
        finally:
            self._loop.remove_reader(self._stdout.channel.fileno())

        d = self._stdout.readline()
        if d == '':
            logger.debug("{}: Read returned {!r}".format(self, d))
            raise TransportNotConnected

        logger.debug("{}: Read {!r}".format(self, d))
        if d.endswith("\r\n"):
            d = d[:-2] + "\n"
        d = d.encode('ascii')

        raise Return(d)

    @property
    def state(self):
        return self._state

    def __repr__(self):
        return "{}(state={}, _client={!r})".format(
                            type(self).__name__,
                            self._state,
                            self._client)


class SubProcessTransport(_BaseTransport):
    """
    Transport that interacts with a subprocess via stdin/stdout.

    """
    def __init__(self, args):
        """
        Initialize a new SubProcessTransport instance.

        :param args:
            A list containing the subprocess name and its arguments.

        """
        super(SubProcessTransport, self).__init__()

        self._args = args

        # The value of `._connect_future` and `._proc` determine the state of
        # the connection:
        #  - If `_connect_future` is None and `_proc` is None the transport is
        #  not connected, and a connection attempt is not in-flight.
        #  - If `_connect_future` is not None and `_proc` is None then a
        #    connection attempt is in process.
        #  - If `_connect_future is None` and `_proc` is not None then a
        #    connection is established.
        #  - It is invalid for both `_connect_future` and `_proc` to be not
        #    None, or for _connect_future to be done (except transiently within
        #    callbacks).
        self._connect_future = None
        self._proc = None

        # `_wait_future` is not None if and only if `_proc` is not None. It is
        # used to reset `_proc` to None when the process terminates.
        self._wait_future = None

    def _get_state(self, do_assert=True):
        if do_assert:
            assert self._connect_future is None or self._proc is None
    
        if self._proc is not None:
            out = State.CONNECTED
        elif self._connect_future is not None:
            out = State.CONNECTING
        else:
            out = State.DISCONNECTED

        return out

    @property
    def state(self):
        return self._get_state()

    @_async.coroutine
    def _connect_no_check(self, loop):
        self._loop = loop
        self._connect_future = _async.wrap_external_coro(
                                _async.spawn_subprocess(
                                                     self._args,
                                                     loop=self._loop),
                                loop=self._loop)
        logger.debug("{}: Starting server process".format(self))

        try:
            self._proc = yield From(self._connect_future)

            logger.debug("{}: Process started".format(self))

            self._wait_future = _async.wrap_external_coro(self._proc.wait(),
                                                          loop=self._loop)
            self._wait_future.add_done_callback(self._wait_future_done)
        except Exception:
            logger.error("{}: Connecting failed".format(self), exc_info=True)
            raise TransportConnectionError
        finally:
            self._connect_future = None

    def _wait_future_done(self, _):
        assert _ == self._wait_future
        logger.debug("{}: Process exited".format(self))
        self._wait_future = None
        self._proc = None

    @_async.coroutine
    def _read_no_check(self):
        logger.debug("{}: Read called".format(self))

        d = yield From(_async.wrap_external_coro(self._proc.stdout.read(
                                                            _MAX_READ_AMOUNT),
                                                 loop=self._loop))
        if d == b'':
            logger.debug("{}: Read returned {!r}".format(self, d))
            raise TransportNotConnected

        logger.debug("{}: Read {!r}".format(self, d))

        raise Return(d)

    def _write_no_check(self, d):
        logger.debug("{}: Writing {!r}".format(self, d))
        try:
            self._proc.stdin.write(d)
        except Exception:
            # Handle errors by logging and then attempting to terminate the
            # process. Most likely the process has terminated anyway (hence the
            # write error) in which case terminating will do nothing. If the
            # process has terminated then restarting it seems like a reasonable
            # approach; the process is acting strangely
            #
            # The error will be reported to the caller in the form of a
            # `TransportNotConnected` error on any read() coroutines.
            logger.error("{}: Write call failed".format(self), exc_info=True)

            try:
                self._proc.terminate()
            except Exception:
                logger.error("Terminate call failed", exc_info=True)

    @_async.coroutine
    def _disconnect_no_check(self):
        """
        Disconnect the transport.

        :raises:
            :exc:`.TransportNotConnected` if the transport is already
            disconnected.
            
        """
        logger.debug("{}: Disconnect called".format(self))
        while self.state is State.CONNECTING:
            logger.debug("{}: Waiting for connect to complete".format(self))
            try:
                yield From(self._connect_future)
            except Exception:
                logger.debug("{}: Ignored connect failure during "
                             "disconnect".format(self))

        if self.state is State.CONNECTED:
            logger.debug("{}: Sending term signal".format(self))
            self._proc.terminate()

        while self.state is State.CONNECTED:
            yield From(self._wait_future)
            logger.debug("{}: Wait complete".format(self))

        assert self.state is State.DISCONNECTED, "Transitioned to invalid " \
                                 "state {!r} from CONNECTED".format(self.state)

    def __repr__(self):
        return "{}(state={}, _proc={!r})".format(
                            type(self).__name__,
                            self._get_state(do_assert=False),
                            self._proc)


class LoopbackTransport(SubProcessTransport):
    """
    Transport that defines a direct connection to the local router.

    Objects of this type may only be created on an IOS-XR router.

    """
    def __init__(self):
        """Initialize a new LoopbackTransport instance."""
        super(LoopbackTransport, self).__init__([_JSON_RPC_SERVER_PATH])


class EnXRTransport(SubProcessTransport):
    """
    Transport that defines a connection to an EnXR session.

    """
    def __init__(self, session_name="ios.0/0/CPU0"):
        """
        Initialize a new EnXRTransport instance.

        :param session_name:
            The name of the EnXR session to connect to, e.g. 'ios.0/0/CPU0'.

        """
        args = shlex.split(
            'script -c "lboot -cqm {} -- {}" /dev/null'.format(
                session_name,
                _JSON_RPC_SERVER_PATH))
        super(EnXRTransport, self).__init__(args)
