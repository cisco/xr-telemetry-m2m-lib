# -----------------------------------------------------------------------------
# defs.py - M2M common definitions
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


"""Common M2M definitions."""


__all__ = (
    'Change',
    'ChangeDetails',
    'ConfigCommitErrorDetail',
    'ErrorCategory',
    'Method',
    'Password',
    'Request',
    'WILDCARD',
    'WILDCARD_ALL',
)


import collections
import enum


class Password(str):
    """
    Wrapper for password data.

    This is a subclass of `str` that is used to indicate that a string should
    be encrypted before it is stored. The algorithm used depends on the schema
    type of the node being set.

    For example::

        conn.set([password_path, Password("very secret")])

    """

    def __new__(cls, value):
        """
        Create a new password.

        :param value:
            String value to be obfuscated. It's assumed that this is a
            cleartext value! If this value is already obfuscated, it should be
            set directly without wrapping it an instance of this class.

        """
        return super(Password, cls).__new__(cls, value)


class _WildcardType(object):
    """Singleton class representing key wildcards."""

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_WildcardType, cls).__new__(cls)
        return cls._instance

    def __repr__(self):
        return "WILDCARD"

    def __str__(self):
        return "*"


WILDCARD = _WildcardType()


class _WildcardAllType(object):
    """Singleton class representing a wildcard for all key parameters."""

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_WildcardAllType, cls).__new__(cls)
        return cls._instance

    def __repr__(self):
        return "WILDCARD_ALL"


WILDCARD_ALL = _WildcardAllType()


class ErrorCategory(enum.Enum):
    """
    Enumeration identifying the high-level reasons for operation failures.

    .. attribute:: VERIFY

        A change was rejected by an IOS-XR feature as semantically invalid,
        e.g. since it would move the system to an inconsistent state.

    """
    VERIFY = 1
    APPLY = 2


class ConfigCommitErrorDetail(
        collections.namedtuple('_ConfigCommitErrorDetailBase',
            ['op',
             'path',
             'value',
             'error_category',
             'error'
            ])):
    """
    Detail for a particular path within a failed config commit operation.

    .. attribute:: op

        Element of :class:`.Change` recording the operation that failed.

    .. attribute:: path

        Element of :class:`.Path` recording the path path of the failed
        operation.

    .. attribute:: value

        For non-delete operations, the (new) value for the leaf to which the
        error applies. This is represented in the standard `output format
        <types.html>`_ (and so may not exactly match the input representation).

        For delete operations, this is `None`.

    .. attribute:: error

        String describing the error.

    .. attribute:: error_category

        Describes the circumstances of the error, one of the
        :class:`.ErrorCategory` values.

    """


class Change(enum.Enum):
    """
    Enumeration of data-modifying operations.

    .. attribute:: SET

        Value set for a leaf (that may or may not have already existed).

    .. attribute:: DELETE

        Existing value for a leaf deleted.

    """
    SET = 1
    DELETE = 2


class ChangeDetails(collections.namedtuple("_ChangeDetails",
                                                     ["path", "op", "value"])):
    """
    Description of a data-modifying operation.

    .. attribute:: path

        :class:`.Path` identifying the leaf whose value is altered.

    .. attribute:: op

        Element of :class:`.Change` recording the operation performed on the
        leaf.

    .. attribute:: value

        For non-delete operations, the (new) value for the leaf. This is
        represented in the standard `output format <types.html>`_ (and so may
        not exactly match the input representation).

        For delete operations, this is `None`.

    """


class Method(enum.Enum):
    """
    An enumeration of methods of :meth:`.Connection`.

    Currently this enumeration is only in :meth:`.Connection.cli_describe`
    responses, hence the restricted subset of methods described.

    .. attribute:: GET

        Corresponds with the method :meth:`.Connection.get`.

    .. attribute:: GET_CHILDREN

        Corresponds with the method :meth:`.Connection.get_children`.

    .. attribute:: SET

        Corresponds with the method :meth:`.Connection.set`.

    .. attribute:: DELETE

        Corresponds with the method :meth:`.Connection.delete`.

    """
    GET = 0
    GET_CHILDREN = 1
    SET = 2
    DELETE = 3


class Request(collections.namedtuple("_Request", ["method", "path", "value"])):
    """
    Describes a :class:`.Connection` request.

    A list of these are returned by :meth:`.Connection.cli_describe`.

    .. attribute:: method

        A :class:`.Method` identifying the :class:`.Connection` method.

    .. attribute:: path

        A :class:`.Path` to be passed as the `path` parameter to the above
        method.

    .. attribute:: value

        The value parameter to be passed to the method. This is always `None`
        for methods that don't accept a value.

    """

