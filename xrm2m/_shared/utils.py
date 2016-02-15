# -----------------------------------------------------------------------------
# util.py - M2M shared utility functions
#
# January 2016, Matthew Earl
#
# Copyright (c) 2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


__all__ = (
    'sanitize_input_string',
)

def sanitize_input_string(s):
    if isinstance(s, type(b"")):
        s = s.decode('ascii')

    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        raise ValueError("Input string contains non-ASCII chars {}".format(s))

    return s

