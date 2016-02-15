# -----------------------------------------------------------------------------
# path.py - Instance module management data object representations.
#
# July 2015, Phil Connell
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


"""Representation of paths."""


__all__ = (
    "Path",
    "PathElement",
    "RootAction",
    "RootCfg",
    "RootOper",
)

from ._shared.path import (
    Path,
    PathElement,
    RootAction,
    RootCfg,
    RootOper,
)

