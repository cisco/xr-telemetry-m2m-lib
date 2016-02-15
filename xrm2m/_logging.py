# -----------------------------------------------------------------------------
# _logging.py - Logger definitions
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


__all__ = (
    'LOGGER_NAME',
    'logger',
)

import logging

LOGGER_NAME = "xrm2m"
logger = logging.getLogger(LOGGER_NAME)

