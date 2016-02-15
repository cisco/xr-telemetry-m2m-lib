# -----------------------------------------------------------------------------
# cut.py - Component Unit Tests
#
# October 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals


"""Tests for connections."""

import xrm2m_offbox.xrm2m as xrm2m

from . import _utils


from . _utils import BaseTest


# Tests may be skipped depending whether on or off-box code executed
IS_ONBOX = False
IS_OFFBOX = True


class LocalTestsBase(BaseTest):
    def setUp(self):
        super(LocalTestsBase, self).setUp()

        self.conn = xrm2m.connect(loop=self._loop)

        self.conn.set([(xrm2m.RootCfg.MPGTest.Enable, 1)])
        self.conn.commit()

    def tearDown(self):
        self.conn.disconnect()

        super(LocalTestsBase, self).tearDown()

