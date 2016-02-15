# -----------------------------------------------------------------------------
# _utils.py - Utilities for writing unit tests
#
# November 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

"""Utilities for writing unit tests."""


__all__ = (
    'BaseTest',
)


import gc
import unittest

from .. import _async

from .._logging import logger


# Attach with PDB when a reference cycle is detected. See
# `BaseTest._find_reference_cycle` for more information.
_DEBUG_REFERENCE_CYCLES = True


class BaseTest(unittest.TestCase):
    """
    Base class for all xrm2m tests.

    Checks that no reference cycles are created, and also that no tasks are
    left running.

    Also provides an event loop attribute `_loop` to be used by inherited
    methods doing async operations. Use of this loop is required for the
    pending tasks check to work properly.

    The class attribute `_gc_checks` can be overridden by subclasses in order
    to disable the garbage collection cycle checks.

    """

    _gc_checks = True

    def setUp(self):
        self._loop = _async.get_test_event_loop()

        if self._gc_checks:
            # Disable the garbage collector, collecting any existing cycles.
            # Enable debug options so that unreachable objects go into
            # `gc.garbage`.
            gc.disable()
            debug = gc.get_debug()
            try:
                gc.set_debug(0)
                gc.collect()
                gc.garbage[:] = []
            finally:
                gc.set_debug(debug)
            gc.set_debug(gc.DEBUG_UNCOLLECTABLE | gc.DEBUG_SAVEALL)

        # Check no tasks are currently running.
        _async.Task.running = []

    def _find_reference_cycle(self):
        # Shorthand variables, useful if attached with PDB.
        # g = "unfetchable objects"
        # i2o = "id to object, for objects in `g`"
        # gr = "get referrers of an object in the unfetchable objects"
        # gri = "get the id of the above referrers"
        g = gc.garbage
        i2o = {id(o): o for o in g}
        gr = lambda o: [r for r in gc.get_referrers(o) if id(r) in i2o]
        gri = lambda o: [id(r) for r in gr(o)]
        
        # Find a loop by walking unfetched objects, stepping to an arbitrary
        # referrer each time. When an object that has already been encountered
        # is encountered again a loop has been found.
        #
        # The loop is described in terms of object ids, to avoid having to
        # invoke objects' __eq__ method.
        def find_loop(start_idx=0):
            path = [id(g[start_idx])]
            while True:
                path.append(gri(i2o[path[-1]])[0])
                # This check could be made more efficient using a set to track
                # elements in `path`.
                if path[-1] in path[:-1]:
                    return path[path.index(path[-1]):]

        loop = find_loop()
        logger.error("Reference cycle of size {} found:".format(len(loop) - 1))
        for obj_id in loop:
            logger.error("    {!r} (id: {})".format(i2o[obj_id], obj_id))

        if _DEBUG_REFERENCE_CYCLES:
            loop = [i2o[o] for o in loop]
            import pdb
            pdb.set_trace()

    def tearDown(self):
        if self._gc_checks:
            # Check no reference cycles were created, and set the garbage
            # collector settings back to normal.
            gc.collect()
            if gc.garbage != []:
                self._find_reference_cycle()
            try:
                self.assertEqual(gc.garbage, [])
            finally:
                gc.garbage[:] = []
                gc.set_debug(0)
                gc.enable()
                gc.collect()

        # Give tasks a chance to complete.
        _async.run_until_callbacks_invoked(loop=self._loop)

        # Check no tasks are currently running.
        self.assertEqual(_async.Task.running, [])

