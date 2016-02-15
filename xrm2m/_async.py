# -----------------------------------------------------------------------------
# _async.py - Abstraction layer for various async libraries
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
Abstraction layer for asyncio, Trollius and xos.async.

Modules within xrm2m should not use asyncio/trollius/xos.async directly,
instead they should use functions and classes from this module.

Coroutines should be implemented in the Trollius style (ie. "yield From()"
instead of "yield from", and "raise Return(x)" instead of "return x".

Furthermore, external async APIs should return futures (eg. tasks) instead of
coroutines.

"""

__all__ = (
    'coroutine',
    'From',
    'Future',
    'get_event_loop',
    'get_test_event_loop',
    'InvalidStateError',
    'iscoroutine',
    'iscoroutinefunction',
    'LOGGER_NAME',
    'make_task',
    'Return',
    'run_until_callbacks_invoked',
    'Task',
    'wrap_external_coro',
)


# Import an available async library as `_asynclib`. Trollius and asyncio are
# compatible, however xos.async is not. The `_IS_XOS_ASYNC` flag is used later
# on to fix up these incompatibilities.   
#
# Try xos.async first, as in some EnXR test setups asyncio can appear in the
# sys.path, but isn't usable.
_IS_XOS_ASYNC = False
try:
    import xos.async as _asynclib
    _IS_XOS_ASYNC = True
    LOGGER_NAME = None # No logging for xos.async
except ImportError:
    try:
        import asyncio as _asynclib
        LOGGER_NAME = "asyncio"
    except ImportError:
        import trollius as _asynclib
        LOGGER_NAME = "trollius"

import collections
import functools
import inspect
import os
import sys

from ._logging import logger


# Functions and classes which are just pass-throughs or thin wrappers to the
# underlying async library equivalent.

class Future(_asynclib.Future):
    def __init__(self, loop=None):
        # The xos.async.Future class expects an `event_loop` arg, whereas
        # asyncio/Trollius expects a `loop` arg.
        if not _IS_XOS_ASYNC:
            super(Future, self).__init__(loop=loop)
        else:
            super(Future, self).__init__(event_loop=loop)


def get_event_loop():
    # xos.async has no default event loop; callers must explicitly provide one
    # to functions/classes with a loop argument.
    if not _IS_XOS_ASYNC:
        return _asynclib.get_event_loop()
    else:
        raise NotImplementedError("Event loop must be explicitly passed")


# Compatible coroutine functions and classes

def coroutine(func):
    """
    Mark a function as a compatible coroutine.

    A compatible coroutine can be used on both Python 2 and Python 3. The
    corresponding coroutine object can be turned into a future using
    :class:`.Task`.

    Compatible coroutines are written using :func:`.Return` and :func:`.From`,
    in a similar way to Trollius.

    """
    if inspect.isgeneratorfunction(func):
        coro = func
    else:
        @functools.wraps(func)
        def coro(*args, **kw):
            res = func(*args, **kw)
            if False:
                yield
            raise Return(res)

    # We could potentially add a flag to the returned coroutine object here, to
    # be checked by `Task` however for now this decorator just serves as
    # documentation.
    coro._is_compat_coroutine = True
    return coro


def iscoroutinefunction(func):
    """Check if a function is a compatible coroutine function."""
    return getattr(func, "_is_compat_coroutine", False)


def iscoroutine(obj):
    """Return True if obj is a coroutine object."""
    return inspect.isgenerator(obj)


def Return(*args):
    if not args:
        value = None
    elif len(args) == 1:
        value = args[0]
    else:
        value = args
    return StopIteration(value)


def From(coro_or_future):
    return coro_or_future


class Task(Future):
    """
    Schedule a compatible coroutine object for execution.

    Returns a future which completes when the coroutine is complete (or has
    failed).

    """
    running = []

    def __init__(self, coro_or_future, loop=None, id=None):
        super(Task, self).__init__(loop)
        if isinstance(coro_or_future, _asynclib.Future):
            raise ValueError("Future passed to Task().")

        if loop is None:
            loop = get_event_loop()

        self._coro = self._flatten_coro(coro_or_future)
        self._loop = loop
        self._loop.call_soon(self._step)
        self._id = id

        Task.running.append(self)
        self.add_done_callback(self._remove_from_running)

    def _remove_from_running(self, fut):
        assert self is fut
        Task.running.remove(self)

    def __repr__(self):
        return "{}(id={!r})".format(type(self).__name__, self._id)
        
    @staticmethod
    def _flatten_coro(coro):
        """
        Take a Trollius style coroutine and return an asyncio style coroutine.

        To elaborate, this coroutine steps through a compatible coroutine,
        yielding each Future encountered, stepping through sub-coroutines as
        required. 

        Results of previously executed Futures are sent back in. When the
        compatible coroutine terminates (either because it has returned or
        thrown an exception) this coroutine similarly raises or returns.

        """
        # `coros` represents the current stack of coroutines.
        coros = [coro]

        # exc, val is the exception info or value that will be passed into the
        # top-most coroutine next.
        exc, val = None, None

        while True:
            # Send the current value/exception into the currently executing
            # co-routine.
            #
            # If it exits then pop the coroutine off the stack, and
            # pass the result into the calling coroutine. If it is the
            # top-level coroutine (ie. the coroutine passed in) then
            # raise/return.
            #
            # If a coroutine is yielded add it onto the stack. It
            # will begin execution on the next iteration of the loop.
            #
            # If a future is yielded then suspend execution until it
            # completes. The result will then be sent into the coroutine on the
            # next iteration.
            try:
                if not exc:
                    coro_or_future = coros[-1].send(val)
                else:
                    coro_or_future = coros[-1].throw(*exc)
            except Exception as e:
                val, exc = None, None
                if len(coros) == 1:
                    raise
                if isinstance(e, StopIteration):
                    val = e.args[0] if e.args else None
                else:
                    exc = sys.exc_info()
                coros = coros[:-1]
            else:
                val, exc = None, None
                if (coro_or_future is None or
                                 isinstance(coro_or_future, _asynclib.Future)):
                    try:
                        val = yield coro_or_future
                    except Exception:
                        exc = sys.exc_info()
                elif iscoroutine(coro_or_future):
                    coros += [coro_or_future]
                else:
                    assert False, "Non-generator/future yielded by coroutine"
                coro_or_future = None

    def _step(self, value=None, exc=None):
        try:
            # Send the result of the previously yielded Future (or None if this
            # is the first time entering the coroutine).
            if not exc:
                coro_or_future = self._coro.send(value)
            else:
                coro_or_future = self._coro.throw(exc)
        except StopIteration as e:
            # Handle the coroutine returning (ie. raising Return(), calling
            # return, or just exiting naturally) by setting the result of this
            # task.
            if e.args:
                self.set_result(e.args[0])
            else:
                self.set_result(None)
        except Exception as e:
            # Handle the coroutine raising an exception (either directly or
            # through an exception not being caught by calling `.throw()` in
            # the previous step) by setting the exception on this task
            logger.debug("Exception thrown executing {}".format(self),
                         exc_info=True)
            self.set_exception(e)
        else:
            # No exceptions were raised: This means the coroutine yielded an
            # object. At this point the object is turned into a future
            # (`sub_future`). When it is complete `_step` is called again with
            # the result.
            #
            # The mapping of the yielded object to a future depends on the
            # object type:
            #  - If a future is yielded nothing needs to be done.
            #  - If a coroutine is yielded, then it is (recursively) turned
            #    into a task.
            #  - If None was yielded (eg. a bare `yield`) then this is used by
            #    the caller to indicate that the coroutine should be resumed
            #    once all pending callbacks have been made. Creating and
            #    immediately completing a new future acheives this.
            if isinstance(coro_or_future, _asynclib.Future):
                sub_future = coro_or_future
            elif coro_or_future is None:
                sub_future = Future(self._loop)
                sub_future.set_result(None)
            else:
                assert False

            sub_future.add_done_callback(self._sub_future_done)
        finally:
            # Avoid cyclic references from tracebacks.
            self = None
            exc = None

    def _sub_future_done(self, f):
        """Callback for when a sub-future completes."""

        # If this function were a nested function inside `_step` then `_step`
        # frames would never be freed until completion of the task.  This is
        # because each `_sub_future_done` frame would keep a reference to its
        # enclosing `_step` frame, while the  next `_step` frame would keep a
        # reference to the `_sub_future_done` frame.
        if f.exception():
            self._step(exc=f.exception())
        else:
            self._step(value=f.result())

        # Avoid cyclic references from tracebacks.
        self = None
        f = None


def make_task(meth):
    """
    Decorator for coroutine methods which makes them return a :class:`.Task`.

    `self._loop` is used as the event loop for the task.

    """
    @functools.wraps(meth)
    def decorated(self, *args, **kwargs):
        assert iscoroutinefunction(meth), "make_task can only be used on " \
                                                        "compatible coroutines"
        coro = meth(self, *args, **kwargs)
        return Task(coro, self._loop, id="Call to {!r}".format(meth))

    return decorated


# ensure_future doesn't exist in old versions of Python. Also ensure_future on
# xos.async accepts an `event_loop` argument rather than `loop`. Fix these
# issues here by making a consistent `_asynclib_ensure_future` function which
# accepts an optional loop argument on all platforms.
if _IS_XOS_ASYNC:
    def _asynclib_ensure_future(coro_or_future, loop=None):
        if not loop:
            loop = get_event_loop()
        return _asynclib.async(coro_or_future, event_loop=loop)
elif not hasattr(_asynclib, "ensure_future"):
    _asynclib_ensure_future = _asynclib.async
else:
    _asynclib_ensure_future = _asynclib.ensure_future

def wrap_external_coro(external_coro, loop=None):
    """
    Turn an external coroutine object into a Future.

    An external coroutine is either a asyncio coroutine, a trollius coroutine,
    or an xos.async coroutine, depending on which async library is being used.

    """
    return _asynclib_ensure_future(external_coro, loop=loop)


# Subprocess functionality

import subprocess

class _SubProcess(object):
    """
    This class is a stand-in for asyncio.subprocess.

    It provides asynchronous (but not concurrent) reads. Writes are entirely
    synchronous. This is considered acceptable as long as client usage of
    `xrm2m` is synchronous only (as it is expected to be in the initial
    release). This is because `write` calls will effectively block anyway as
    nothing will be received until the request has been sent.

    In subsequent releases on-box `xrm2m` will either be implemented directly
    on top of MPG, or `asyncio` will be available. Off-box `xrm2m` will always
    be able to use 

    """

    def __init__(self, args, loop=None):
        assert loop is not None

        self._proc = subprocess.Popen(args,
                                      stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE)

        self._loop = loop
        
        # A `read` is always in progress, such that if an EOF is hit then the
        # wait future can be completed. This adds some complexity in that data
        # that is read while no `read` call is in progress must be buffered.
        # Similarly special handling is required to ensure an EOF read is sent.
        self._unread_bytes = b''
        self._eof_recvd = False
        loop.add_reader(self._proc.stdout, self._on_read_cb)
        self._wait_future = Future(loop)
        self._read_future = None

    def _cleanup_proc(self):
        """
        Close file descriptors and wait for the process to exit.

        This is called after receiving EOF from the process's stdout, so the
        wait is expected to be immediate.

        """
        logger.debug("{}: Cleaning up and waiting for process to exit".format(
                                                                         self))
        try:
            self._loop.remove_reader(self._proc.stdout)
            self._proc.stdout.close()
            self._proc.stdin.close()
        except Exception:
            # Log errors, but otherwise ignore.
            logger.error("{}: Failed cleaning up process".format(self),
                         exc_info=True)
        finally:
            # If the wait fails, the sub-process will appear in the process
            # tree (labelled defunct). This is mostly harmless so just log a
            # warning.
            try:
                self._proc.wait(0)
            except subprocess.TimeoutExpired:
                logger.warning("{}: Wait failed".format(self),
                         exc_info=True)

    def _on_read_cb(self, f):
        d = self._proc.stdout.read1(1024)
        logger.debug("{}: Read {} bytes".format(self, len(d)))
        self._unread_bytes += d

        if d == b'':
            self._wait_future.set_result(None)
            self._eof_recvd = True
            self._cleanup_proc()

        if self._read_future is not None and not self._read_future.done():
            self._read_future.set_result(self._unread_bytes)
            logger.debug("{}: {} unread bytes sent to {}".format(
                            self, len(self._unread_bytes), self._read_future))
            self._unread_bytes = b''
        else:
            logger.debug("{}: {} unread bytes".format(self,
                                                  len(self._unread_bytes)))

    def write(self, d):
        self._proc.stdin.write(d)
        self._proc.stdin.flush()

    def read(self, n):
        """
        Return a future which will complete when there is data available.

        If data was already available before the call was made then the future
        will complete immediately with the data that was available. Otherwise
        the future will complete once data is available.

        The future will complete with the result `b''` if the process
        terminates, or otherwise closes `stdout`.

        Note the `n` argument is currently ignored. As much data as is
        available at the time of calling will be returned.

        """
        assert self._read_future is None, "Concurrent reads detected"

        read_future = Future(self._loop)

        if self._unread_bytes or self._eof_recvd:
            read_future.set_result(self._unread_bytes)
            self._unread_bytes = b''
        else:
            self._read_future = read_future
            def read_future_done(_):
                self._read_future = None
            read_future.add_done_callback(read_future_done)

        return read_future

    def terminate(self):
        """Send the term signal to the process."""
        self._proc.terminate()

    def wait(self):
        return self._wait_future

    def __repr__(self):
        return "{}(pid={}, eof={}, rc={})".format(
                                type(self).__name__,
                                self._proc.pid,
                                self._eof_recvd,
                                self._proc.returncode)


_DummyFile = collections.namedtuple('_DummyFile', ['read', 'write'])


class _DummyProc(collections.namedtuple('_DummyProcBase',
                                ['stdin', 'stdout', 'terminate', 'wait'])):
    """
    Wrapper around _SubProcess to make `read` and `write` objects appear
    under `stdout` and `stdin` attributes, respectively.

    """
    def __new__(cls, proc):
        self = super(_DummyProc, cls).__new__(
            cls,
            stdin=_DummyFile(read=None, write=proc.write),
            stdout=_DummyFile(read=proc.read, write=None),
            terminate=proc.terminate,
            wait=proc.wait)

        return self

    def __init__(self, proc):
        self._proc = proc

    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self._proc)


def spawn_subprocess(args, loop=None):
    """
    Spawn a subprocess.

    This function returns a coroutine object which returns a `Proc` object.
    This is equivalent to that returned by `asyncio.create_subprocess_exec`.

    Note this function returns an external coroutine object, and the
    asynchronous methods of the `Proc` object themselves return external
    coroutine objects. As such they should be wrapped with
    `wrap_external_coro`.

    """
    if not _IS_XOS_ASYNC:
        return spawn_subprocess_not_xos(args, loop=loop)
    else:
        return spawn_subprocess_xos(args, loop=loop)


if not _IS_XOS_ASYNC:
    def spawn_subprocess_not_xos(args, loop=None):
        return _asynclib.create_subprocess_exec(*args, loop=loop,
                                                stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE,
                                                preexec_fn=os.setpgrp)
else:
    @_asynclib.coroutine
    def spawn_subprocess_xos(args, loop=None):
        proc = _SubProcess(args, loop=loop)
        return _DummyProc(proc)


# Test utilities

# Passed to .assertRaises() when testing.
InvalidStateError = _asynclib.InvalidStateError

def _run_until_callbacks_invoked_once(loop):
    future = Future(loop)
    def callback():
        future.set_result(None)
    loop.call_soon(callback)
    loop.run_until_complete(future)


def run_until_callbacks_invoked(n=10, loop=None):
    """
    Run the event loop until all pending callbacks have been made.

    This function is only intended to be used for testing. Pass `n > 1` to do
    this multiple times. This is useful to be sure any chains of futures are
    correctly propagated.

    """

    if loop is None:
        loop = get_event_loop()

    for i in range(n):
        _run_until_callbacks_invoked_once(loop=loop)

_xos_async_loop = None
def _get_xos_async_test_event_loop():
    global _xos_async_loop

    # event_create_manager() seems to break if EVMs are created in quick
    # succession (as would happen when running unit test). Work around this by
    # just use a single EVM for running UT. 
    if _xos_async_loop is None:
        import cisco.sdk
        app_ctx = cisco.sdk.get_application_context()
        name = "xrm2m-test-process"
        if not app_ctx:
            app_ctx = cisco.sdk.ApplicationContext(name)
        assert app_ctx.name == name, "Non test app ctx exists: {}".format(
                                                                       app_ctx)
        _xos_async_loop = cisco.sdk.EventContext(app_ctx)

    return _xos_async_loop

def get_test_event_loop():
    """Get an event loop suitable for use doing unit tests."""
    if not _IS_XOS_ASYNC:
        loop = _asynclib.get_event_loop()
    else:
        loop = _get_xos_async_test_event_loop()
    return loop


