# -----------------------------------------------------------------------------
# conn.py - Test for connections
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

import json

from . import _utils
from .. import _conn
from .. import _async
from .. import _errors
from .. import _path
from .. import _transport


class _TestTransport(_transport.Transport):
    """
    Transport work-a-like for testing.

    Each asynchronous method will create a future in its attributes. The test
    routine is expected to complete the future attributes to trigger particular
    callbacks, as appropriate.

    As futures are completed they are removed from the attributes.

    """

    def __init__(self):
        self._loop = None
        self.connect_future = None
        self.wait_future = None
        self.read_future = None
        self.write_buffer = b""

    def connect(self, loop):
        assert self.state == _transport.State.DISCONNECTED
        self._loop = loop
        self.connect_future = _async.Future(loop=loop)
        self.connect_future.add_done_callback(self._connect_future_done)

        return self.connect_future

    def _connect_future_done(self, f):
        self.connect_future = None
        if not f.exception():
            self.wait_future = _async.Future(loop=self._loop)
            self.wait_future.add_done_callback(self._wait_complete)

    def _wait_complete(self, f):
        self.wait_future = None

    @property
    def state(self):
        if self.connect_future:
            return _transport.State.CONNECTING
        elif self.wait_future:
            return _transport.State.CONNECTED
        else:
            return _transport.State.DISCONNECTED

    def disconnect(self):
        assert self.state == _transport.State.CONNECTED
        return self.wait_future

    def read(self):
        assert self.state == _transport.State.CONNECTED
        # Concurrent reads should not happen.
        assert self.read_future is None
        self.read_future = _async.Future(loop=self._loop)
        self.read_future.add_done_callback(self._read_future_done)
        return self.read_future

    def _read_future_done(self, f):
        self.read_future = None

    def write(self, d):
        assert self.state == _transport.State.CONNECTED

        # The write buffer should be a byte sequence. The second parameter is
        # for compatibility with both Python 2 (where type(b"") is str) and
        # Python 3 (where type(b"") is bytes.
        assert isinstance(d, type(b""))

        self.write_buffer += d


class _TestException(Exception):
    pass


class AsyncConnectTests(_utils.BaseTest):
    """
    Asynchronous connection tests.

    """

    def test_connect(self):
        """Basic connect / disconnect test."""

        transport = _TestTransport()

        # Connect, check that the resulting future does not complete until the
        # transport has connected.
        connect_fut = _conn.connect_async(transport, loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertFalse(connect_fut.done())

        transport.connect_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)

        self.assertTrue(connect_fut.done())
        connect_fut.exception()

        # Disconnect, check that the resulting future does not complete until
        # the transport has disconnected.
        conn = connect_fut.result()
        disconnect_fut = conn.disconnect()
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertFalse(disconnect_fut.done())

        transport.wait_future.set_result(None)
        transport.read_future.set_exception(_transport.TransportNotConnected)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(disconnect_fut.done())
        disconnect_fut.exception()

    def test_connect_misc_error(self):
        transport = _TestTransport()

        connect_fut = _conn.connect_async(transport, loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertFalse(connect_fut.done())

        transport.connect_future.set_exception(_TestException)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(connect_fut.done())
        with self.assertRaises(_errors.ConnectionError):
            connect_fut.result()

    def test_connect_connection_error(self):
        transport = _TestTransport()

        connect_fut = _conn.connect_async(transport, loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertFalse(connect_fut.done())

        transport.connect_future.set_exception(
                                           _transport.TransportConnectionError)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(connect_fut.done())
        with self.assertRaises(_errors.ConnectionError):
            connect_fut.result()


class AsyncReadWriteTests(_utils.BaseTest):
    """

    """

    def setUp(self):
        super(AsyncReadWriteTests, self).setUp()

        self._transport = _TestTransport()

        connect_fut = _conn.connect_async(self._transport, loop=self._loop)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self._transport.connect_future.set_result(None)
        self._loop.run_until_complete(connect_fut)
        self._conn = connect_fut.result()

    def tearDown(self):
        disconnect_fut = self._conn.disconnect()
        self._transport.read_future.set_exception(
                                              _transport.TransportNotConnected)
        self._transport.wait_future.set_result(None)
        self._loop.run_until_complete(disconnect_fut)

        super(AsyncReadWriteTests, self).tearDown()

    def test_basic_get(self):
        get_fut = self._conn.get("RootCfg")
        _async.run_until_callbacks_invoked(loop=self._loop)
        with self.assertRaises(_async.InvalidStateError):
            get_fut.result()
        self.assertGreater(len(self._transport.write_buffer), 10)
        self.assertEqual(self._transport.write_buffer[-1], b'\n'[0])

        # Check the output is a valid JSON object, encoded as ASCII.
        s = self._transport.write_buffer[:-1].decode(_conn._JSON_ENCODING)
        parsed = json.loads(s)

        # Do some basic checks on the request object
        self.assertEqual(parsed["jsonrpc"], "2.0")
        self.assertEqual(parsed["params"]["path"], "RootCfg")
        self.assertEqual(parsed["id"], 1)

        # Post a reply (in 10 byte chunks). Check at each step that the data is
        # being read and a new future has been created.
        reply = (br'{"jsonrpc": "2.0", "id": 1, "result": '
                 br'[["RootCfg.Foo({\"ID\": 1}).Alive", true]]}' b'\n')
        while reply:
            chunk, reply = reply[:10], reply[10:]

            self._transport.read_future.set_result(chunk)
            old_read_future = self._transport.read_future
            _async.run_until_callbacks_invoked(loop=self._loop)
            self.assertNotEqual(old_read_future, self._transport.read_future)
            self.assertNotEqual(self._transport.read_future, None)
            if reply:
                with self.assertRaises(_async.InvalidStateError):
                    get_fut.result()

        self.assertTrue(get_fut.done())
        r = get_fut.result()
        self.assertEqual(r, [(_path.RootCfg.Foo(ID=1).Alive, True)])

    def _send_concurrent_gets(self):
        """
        Helper function which makes 2 concurrent get requests, and verifies the
        request was sent.

        The correct replies and expected results of the `get()`s are also
        returned.

        """
        paths = ["RootCfg.A", "RootCfg.B"]
        get_fut1 = self._conn.get(paths[0])
        get_fut2 = self._conn.get(paths[1])
        _async.run_until_callbacks_invoked(loop=self._loop)
        with self.assertRaises(_async.InvalidStateError):
            get_fut1.result()
        with self.assertRaises(_async.InvalidStateError):
            get_fut2.result()
        self.assertGreater(len(self._transport.write_buffer), 10)
        self.assertEqual(self._transport.write_buffer[-1], b'\n'[0])

        # Check the output is a valid JSON object, encoded as ASCII.
        decoded = self._transport.write_buffer.decode(_conn._JSON_ENCODING)
        self._transport.write_buffer = b""
        lines = decoded.split('\n')
        self.assertEqual(lines[-1], "")
        parseds = [json.loads(line) for line in lines[:-1]]
        self.assertEqual(len(parseds), 2)
        
        # Do some basic checks on the request object
        for idx, parsed in enumerate(parseds):
            self.assertEqual(parsed["jsonrpc"], "2.0")
            self.assertEqual(parsed["params"]["path"], paths[idx])
            self.assertEqual(parsed["id"], idx + 1)

        # Also return the replies that should be posted, and the corresponding
        # expected results.
        replies = [
                br'{"jsonrpc": "2.0", "id": 1, "result": [["RootCfg.A", 42]]}',
                br'{"jsonrpc": "2.0", "id": 2, "result": [["RootCfg.B", 43]]}',
                ]

        expected_results = [
                [(_path.RootCfg.A, 42)],
                [(_path.RootCfg.B, 43)],
        ]

        return [get_fut1, get_fut2], replies, expected_results

    def test_concurrent_gets_in_order_delay(self):
        """
        Test 2 concurrent gets, where the first get() completes before the
        second reply is received.

        The replies are sent in the same order as the corresponding requests.

        """
        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Post the reply for the first get(), and verify it completes, but the
        # second doesn't. Also verify the result is as expected.
        self._transport.read_future.set_result(replies[0] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[0].done())
        with self.assertRaises(_async.InvalidStateError):
            get_futs[1].result()
        self.assertEqual(get_futs[0].result(), expected_results[0])

        # Post the reply for the second get(), and verify it is now completed,
        # with the correct result.
        self._transport.read_future.set_result(replies[1] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[1].done())
        self.assertEqual(get_futs[1].result(), expected_results[1])

    def test_concurrent_gets_reverse_delay(self):
        """
        Test 2 concurrent gets, where the first get() completes before the
        second reply is received.

        The replies are sent in the reverse order as the corresponding
        requests.

        """
        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Post the reply for the second get(), and verify it completes, but the
        # first doesn't. Also verify the result is as expected.
        self._transport.read_future.set_result(replies[1] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        with self.assertRaises(_async.InvalidStateError):
            get_futs[0].result()
        self.assertTrue(get_futs[1].done())
        self.assertEqual(get_futs[1].result(), expected_results[1])

        # Post the reply for the first get(), and verify it is now completed,
        # with the correct result.
        self._transport.read_future.set_result(replies[0] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[0].done())
        self.assertEqual(get_futs[0].result(), expected_results[0])

    def test_concurrent_gets_in_order_simultaneous(self):
        """
        Test 2 concurrent gets, where both replies are sent at the same time.

        The replies are sent in the same order as the corresponding requests.

        """
        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Post both replies. Verify both gets() are complete and the results
        # are as expected.
        self._transport.read_future.set_result(replies[0] + b'\n' +
                                               replies[1] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[0].done())
        self.assertTrue(get_futs[1].done())
        self.assertEqual(get_futs[0].result(), expected_results[0])
        self.assertEqual(get_futs[1].result(), expected_results[1])

    def test_concurrent_gets_reverse_simultaneous(self):
        """
        Test 2 concurrent gets, where both replies are sent at the same time.

        The replies are sent in the reverse order as the corresponding
        requests.

        """
        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Post both replies. Verify both gets() are complete and the results
        # are as expected.
        self._transport.read_future.set_result(replies[1] + b'\n' +
                                               replies[0] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[0].done())
        self.assertTrue(get_futs[1].done())
        self.assertEqual(get_futs[0].result(), expected_results[0])
        self.assertEqual(get_futs[1].result(), expected_results[1])

    def test_get_request_error(self):
        """
        Test an error during a get operation, where the error is specific to
        the request.

        The expected behaviour in this case is for the request to fail (with an
        appropriate exception), but for the connection to continue working.

        """

        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Post the first reply, but with a badly formatted path. Check that the
        # request fails.
        bad_reply = (br'{"jsonrpc": "2.0", "id": 1, '
                     br'"result": [["BadRoot", 42]]}')
        self._transport.read_future.set_result(bad_reply + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[0].done())
        with self.assertRaises(_errors.PathStringFormatError):
            get_futs[0].result()
        with self.assertRaises(_async.InvalidStateError):
            get_futs[1].result()

        # Post the second reply, verify that it succeeds.
        self._transport.read_future.set_result(replies[1] + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[1].done())
        self.assertEqual(get_futs[1].result(), expected_results[1])

    def test_get_global_error(self):
        """
        Test an error during a get operation, where the error affects the
        entire connection.

        The expected behaviour is for all pending requests to be errored, and
        the connection to be disconnected.

        """

        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Send a line with some invalid JSON.
        bad_line = br'@@@ bad line @@@'
        self._transport.read_future.set_result(bad_line + b'\n')
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(get_futs[0].done())
        self.assertTrue(get_futs[1].done())
        with self.assertRaises(_errors.DisconnectedError):
            get_futs[0].result()
        with self.assertRaises(_errors.DisconnectedError):
            get_futs[1].result()

        # Make a new request from the connection. Verify that the request
        # fails.
        new_get_fut = self._conn.get("RootCfg")
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(new_get_fut.done())
        with self.assertRaises(_errors.DisconnectedError):
            new_get_fut.result()

        # Reconnect and verify that a get works.
        reconnect_fut = self._conn.reconnect()
        _async.run_until_callbacks_invoked(loop=self._loop)
        self._transport.wait_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self._transport.connect_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertTrue(reconnect_fut.done())
        self.assertEqual(reconnect_fut.result(), None)

        self.test_basic_get()

    def test_unexpected_disconnect(self):
        get_futs, replies, expected_results = self._send_concurrent_gets()

        # Cause the transport to disconnect, verify that the connection state
        # is disconnected, and that the in-flight requests fail.
        self._transport.wait_future.set_result(None)
        self._transport.read_future.set_exception(
                                              _transport.TransportNotConnected)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(self._conn.state, _conn.ConnectionState.DISCONNECTED)
        self.assertTrue(get_futs[0].done())
        self.assertTrue(get_futs[1].done())
        with self.assertRaises(_errors.DisconnectedError):
            get_futs[0].result()
        with self.assertRaises(_errors.DisconnectedError):
            get_futs[1].result()

        # Reconnect and verify that a get works.
        reconnect_fut = self._conn.reconnect()
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(self._conn.state, _conn.ConnectionState.CONNECTING)
        self._transport.connect_future.set_result(None)
        _async.run_until_callbacks_invoked(loop=self._loop)
        self.assertEqual(self._conn.state, _conn.ConnectionState.CONNECTED)
        self.assertTrue(reconnect_fut.done())
        self.assertEqual(reconnect_fut.result(), None)

        self.test_basic_get()

