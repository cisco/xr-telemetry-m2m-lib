# -----------------------------------------------------------------------------
# transport.py - Test for transports
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

"""Tests for transports."""

from . import _utils
from .. import _async
from .. import _transport

from .._async import From, Return

try:
    import unittest.mock as mock
except ImportError:
    # For Python 2, try importing the backport.
    import mock


# Mutable versions of _async._DummyFile and _DummyProc, useful so that their
# attributes can be patched.
class _DummyFile(object):
    def __init__(self, read, write):
        self.read = read
        self.write = write


class _DummyProc(object):
    """
    Wrapper around _TestSubProcess to make `read` and `write` objects appear
    under `stdout` and `stdin` attributes, respectively.

    """
    def __init__(self, proc):
        self.stdin = _DummyFile(read=None, write=proc.write)
        self.stdout = _DummyFile(read=proc.read, write=None)
        self.terminate = proc.terminate
        self.wait = proc.wait
        self._proc = proc

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self._proc)


class _TestSubProcess(object):
    """
    SubProcess work-a-like for testing.

    Each asynchronous method will create a future in its attributes. The test
    routine is expected to complete the future attributes to trigger particular
    callbacks, as appropriate.

    As futures are completed they are removed from the attributes.

    """

    def __init__(self):
        self._loop = None
        self.spawn_future = None
        self.wait_future = None
        self.read_future = None

    def spawn(self, args, loop):
        self._loop = loop
        self.spawn_future = _async.Future(loop=loop)
        self.spawn_future.add_done_callback(self._spawn_future_done)

        return self.spawn_future

    def _spawn_future_done(self, f):
        self.spawn_future = None
        if not f.exception():
            self.wait_future = _async.Future(loop=self._loop)

    def wait(self):
        return self.wait_future

    def terminate(self):
        pass

    def read(self, n):
        # Concurrent reads should not happen.
        assert self.read_future is None
        self.read_future = _async.Future(loop=self._loop)
        self.read_future.add_done_callback(self._read_future_done)
        return self.read_future

    def _read_future_done(self, f):
        self.read_future = None

    def write(self, d):
        pass


class _TestException(Exception):
    pass


class _SubProcessTransportBaseTest(_utils.BaseTest):
    @_async.make_task
    @_async.coroutine
    def _test_spawn_subprocess(self, args, loop=None):
        self._proc = _TestSubProcess()
        yield From(self._proc.spawn(args, loop=loop))
        # Store the dummy proc so that it can be used for attribute patching.
        self._dummy_proc = _DummyProc(self._proc)
        raise Return(self._dummy_proc)

    def setUp(self):
        super(_SubProcessTransportBaseTest, self).setUp()
        self.patcher = mock.patch.object(_async, 'spawn_subprocess',
                                         new=self._test_spawn_subprocess)
        self.patcher.start()

        # If extending this method, ensure `self.patcher` gets stopped.

    def tearDown(self):
        self.patcher.stop()
        super(_SubProcessTransportBaseTest, self).tearDown()


class SubProcessTransportTests(_SubProcessTransportBaseTest):
    """
    SubProcessTransport tests

    """

    def test_connect(self):
        """Basic connect / disconnect test."""

        transport = _transport.SubProcessTransport(['test_prog'])
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)
        connect_fut = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertNotEqual(self._proc.spawn_future, None)
        self.assertFalse(connect_fut.done())
        self.assertEqual(transport.state, _transport.State.CONNECTING)

        self._proc.spawn_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(connect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.CONNECTED)

        disconnect_fut = _async.Task(transport.disconnect(),
                                     loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertFalse(disconnect_fut.done())
        self.assertEqual(transport.state, _transport.State.CONNECTED)

        self._proc.wait_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(disconnect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)
        
    def test_connect_error(self):
        """Connection failure."""

        transport = _transport.SubProcessTransport(['test_prog'])
        connect_fut = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertNotEqual(self._proc.spawn_future, None)
        self.assertFalse(connect_fut.done())
        self.assertEqual(transport.state, _transport.State.CONNECTING)

        self._proc.spawn_future.set_exception(_TestException)
        _async.run_until_callbacks_invoked(loop=self._loop)
        with self.assertRaises(_transport.TransportConnectionError):
            self.assertEqual(connect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)

        connect_fut = None

    def test_connect_while_connecting_or_connected(self):
        # Start the first connection.
        transport = _transport.SubProcessTransport(['test_prog'])
        connect_fut = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(transport.state, _transport.State.CONNECTING)

        # Try and connect again while the first is in progress. Check it fails.
        connect_fut2 = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(connect_fut2.done())
        with self.assertRaises(_transport.TransportConnectionError):
            connect_fut2.result()
        del connect_fut2
        self.assertEqual(transport.state, _transport.State.CONNECTING)

        # Complete the first connection (succesfully).
        self._proc.spawn_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(connect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.CONNECTED)

        # Try and connect again. Check it fails.
        connect_fut2 = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(connect_fut2.done())
        with self.assertRaises(_transport.TransportConnectionError):
            connect_fut2.result()
        del connect_fut2
        self.assertEqual(transport.state, _transport.State.CONNECTED)

        # Disconnect.
        disconnect_fut = _async.Task(transport.disconnect(),
                                     loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self._proc.wait_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(disconnect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)

    def test_disconnect_when_disconnected(self):
        transport = _transport.SubProcessTransport(['test_prog'])
        disconnect_fut = _async.Task(transport.disconnect(),
                                     loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        with self.assertRaises(_transport.TransportNotConnected):
            disconnect_fut.result()
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)

    def test_disconnect_when_connecting(self):
        # Start the first connection.
        transport = _transport.SubProcessTransport(['test_prog'])
        connect_fut = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(transport.state, _transport.State.CONNECTING)

        # Start a disconnection.
        disconnect_fut = _async.Task(transport.disconnect(),
                                     loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(transport.state, _transport.State.CONNECTING)

        # Complete the connection, and check that afterwards disconnection has
        # completed.
        self._proc.spawn_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self._proc.wait_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(connect_fut.result(), None)
        self.assertEqual(disconnect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)

    def test_read_when_disconnected(self):
        transport = _transport.SubProcessTransport(['test_prog'])
        read_fut = _async.Task(transport.read(), self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        with self.assertRaises(_transport.TransportNotConnected):
            read_fut.result()

    def test_write_when_disconnected(self):
        transport = _transport.SubProcessTransport(['test_prog'])
        with self.assertRaises(_transport.TransportNotConnected):
            transport.write(b'')

    def test_concurrent_reads(self):
        # Connect.
        transport = _transport.SubProcessTransport(['test_prog'])
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)
        _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertNotEqual(self._proc.spawn_future, None)
        self._proc.spawn_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(transport.state, _transport.State.CONNECTED)

        # Start two concurrent reads.
        read_fut1 = _async.Task(transport.read(), loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        read_fut2 = _async.Task(transport.read(), loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)

        # Check the first is still pending, but the second has asserted.
        self.assertFalse(read_fut1.done())
        with self.assertRaises(AssertionError):
            read_fut2.result()

        # Complete the first read.
        self._proc.read_future.set_result(b'Data')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(read_fut1.result(), b'Data')

        # Disconnect.
        disconnect_fut = _async.Task(transport.disconnect(),
                                     loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self._proc.wait_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(disconnect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)


class SubProcessTransportTestsNoGCCheck(_SubProcessTransportBaseTest):
    """
    SubProcessTransport tests which result in cycles due to `MagicMock`.

    """

    _gc_checks = False

    def test_write_error(self):
        # Set up a connection.
        transport = _transport.SubProcessTransport(['test_prog'])
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)
        connect_fut = _async.Task(transport.connect(loop=self._loop),
                                  loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertNotEqual(self._proc.spawn_future, None)
        self._proc.spawn_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(connect_fut.result(), None)
        self.assertEqual(transport.state, _transport.State.CONNECTED)

        # Attempt a write, but inject an error.
        with mock.patch.object(self._dummy_proc.stdin, 'write',
                                                   side_effect=_TestException):
            with mock.patch.object(self._dummy_proc,
                                   'terminate') as mock_terminate:
                transport.write(b'')
            mock_terminate.assert_called_once_with()
    
        # Expect the transport to disconnect.
        self._proc.wait_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(transport.state, _transport.State.DISCONNECTED)
        
