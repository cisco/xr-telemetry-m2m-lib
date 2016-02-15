# -----------------------------------------------------------------------------
# _util.py - M2M utility functions
#
# December 2015, Ian Kimpton
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


'''Common utilities for M2M.'''


__all__ = (
    'copy_docstring',
    'copy_docstring_from_parent',
)

import functools
import inspect


def copy_docstring(doc_src):
    """
    Copies a docstring from one class or function to another.

    `doc_src` is the class or function whose docstring is to be copied.

    Usage:
        def foo():
            "Doc string"
            pass

        @copy_docstring(foo)
        def bar():
            pass

        After this, bar.__doc__ equals "Doc string"

    This method can also be applied to classes:
        class Foo(object):
            "Doc string"

        @copy_docstring(Foo)
        class Bar(Foo):
            pass

    """
    def cls_methods(cls):
        # Get the methods for a class
        return (
            meth_name
            for meth_name in dir(cls)
            if inspect.isfunction(getattr(cls, meth_name))
        )
    def copy_method_docs(cls):
        # Copy the methods docs for a class
        for meth_name in cls_methods(cls):
            meth = getattr(cls, meth_name)
            # Don't overwrite new docstrings!
            if meth.__doc__ is None:
                try:
                    meth.__doc__ = getattr(doc_src, meth_name).__doc__
                except AttributeError:
                    # The method doesn't exist on the parent!
                    pass
    def wrapper(cls_or_func):
        # Apply the doc source's docstring
        # (if there is not a docstring defined)
        if cls_or_func.__doc__ is None:
            try:
                cls_or_func.__doc__ = doc_src.__doc__
            except AttributeError:
                # On Python 2, the __doc__ attribute of new-style classs are
                # not writable, so the user will have to refer to the parent
                # class documentation instead.
                pass
        # Is this a class?
        if inspect.isclass(cls_or_func):
            # Copy docs for the methods too
            copy_method_docs(cls_or_func)
            return cls_or_func
        # If not a class, assume function
        func = cls_or_func
        @functools.wraps(func)
        def inner(*args, **kwargs):
            return func(*args, **kwargs)
        return inner
    return wrapper


def copy_docstring_from_parent(cls):
    """
    Copies the docstring from a parent class.

    Note that unlike `copy_docstring`, this function takes no arguments and
    only classes are supported.

    """
    return copy_docstring(cls.__bases__[0])(cls)

