# -----------------------------------------------------------------------------
# __init__.py - xrm2m.test package
#
# October 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

"""
Tests for the Machine-to-Machine Python API.

"""

from .conn import *
from .errors import *
from .schema import *
from .transport import *
from .shared.cut import *
from .shared.path import *

# Output test results to stdout
DO_LOGGING = True

if DO_LOGGING:
    import logging, sys
    logger = logging.getLogger()
    logger.level = logging.ERROR
    logger.addHandler(logging.StreamHandler(sys.stdout))

