# -----------------------------------------------------------------------------
# _errors.py - External error definitions and utilities.
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
    'AmbiguousPathError',
    'CiscoError',
    'ConfigCommitError',
    'ConnectionError',
    'DatatypeNotSupportedError',
    'DisconnectedError',
    'FileExistsError',
    'InternalError',
    'InvalidArgumentError',
    'MalformedJSONReceived',
    'NotFoundError',
    'OperationNotSupportedError',
    'ParseError',
    'PathHierarchyError',
    'PathKeyContentError',
    'PathKeyStructureError',
    'PathStringFormatError',
    'UnexpectedJSONError',
    'UnexpectedResponseIDError',
    'ValueContentError',
    'ValueStructureError',
)


import re

from . import _defs
from . import _path


# Bring shared errors into this namespace
from ._shared.errors import (
    AmbiguousPathError,
    CiscoError,
    ConfigCommitError,
    ConnectionError,
    DatatypeNotSupportedError,
    DisconnectedError,
    FileExistsError,
    InternalError,
    InvalidArgumentError,
    NotFoundError,
    OperationNotSupportedError,
    ParseError,
    PathHierarchyError,
    PathKeyContentError,
    PathKeyStructureError,
    PathStringFormatError,
    ValueContentError,
    ValueStructureError,
)


def _parse_path(pathstr):
    """Wrapper around :meth:`._path.Path.from_str`."""
    return _path.Path.from_str(pathstr)


class UnexpectedResponseIDError(InternalError):
    """
    Raised when a JSON response is received for an unknown request ID.

    """


class UnexpectedJSONError(InternalError):
    """
    A JSON-RPC error indicating an API bug was received. 

    For example, an error indicating that a malformed path was provided in a
    request. Such an error should be impossible as the path module will only
    generate valid paths.

    The `error_field` attribute is the `error` attribute from the JSON
    response.

    """
    def __init__(self, error_field):
        super(UnexpectedJSONError, self).__init__(error_field["message"])
        self.error_field = error_field


class MalformedJSONReceived(InternalError):
    """
    A maformed JSON message was received.

    The `msg` attribute is the message which could not be decoded.

    """
    def __init__(self, json_msg):
        super(MalformedJSONReceived, self).__init__(
                "Malformed JSON received: {!r}".format(json_msg))
        self.msg = json_msg


_ERROR_FIELDS_MAP = {
    "cisco_error": lambda msg, d: CiscoError(msg),
    "datatype_not_supported_error":
        lambda msg, d: DatatypeNotSupportedError(msg),
    "file_exists_error":
        lambda msg, d: FileExistsError(msg, filename=d["filename"]),
    "invalid_argument_error":
        lambda msg, d: InvalidArgumentError(msg, path=_parse_path(d["path"])),
    "not_found_error":
        lambda msg, d: NotFoundError(msg, path=_parse_path(d["path"])),
    "operation_not_supported_error":
        lambda msg, d: OperationNotSupportedError(msg,
                                                  path=_parse_path(d["path"])),
    "path_hierarchy_error":
        lambda msg, d: PathHierarchyError(msg,
                                          element=d["element"],
                                          parent=d["parent"]),
    "path_key_content_error":
        lambda msg, d: PathKeyContentError(msg,
                                           value=d["value"],
                                           param=d["param"]),
    "path_key_structure_error":
        lambda msg, d: PathKeyStructureError(
            msg,
            value_seq=d["value_seq"],
            class_name=d["class"]),
    "path_string_format_error":
        lambda msg, d: PathStringFormatError(msg, pathstr=d["path"]),
    "permissions_error": lambda msg, d: PermissionError(msg),
    "value_structure_error":
        lambda msg, d: ValueStructureError(
            msg,
            value_seq=d["value_seq"],
            class_name=d["class"]),
    "value_content_error":
        lambda msg, d: ValueContentError(msg,
                                         value=d["value"],
                                         param=d["param"]),
}


def _make_config_commit_error(msg, data):
    def _convert_dict(d):
        return _defs.ConfigCommitErrorDetail(
            op=_defs.Change[d["operation"]],
            path=_path.Path.from_str(d["path"]),
            value=d["value"],
            error=d["error"],
            error_category=_defs.ErrorCategory[d["category"]])
    return ConfigCommitError(msg, detail=[_convert_dict(d) for d in data])


def error_from_error_field(error_field):
    """Create an exception from a JSON error field."""

    if error_field["code"] != -32000:
        return UnexpectedJSONError(error_field)
    elif isinstance(error_field["data"], list):
        # Special handling for config commit errors, as the data field is a
        # list.
        if not all(d["type"] == "config_commit_error"
                   for d in error_field["data"]):
            # Config commit errors are the only errors that we expect to
            # have a list for a data field.
            return UnexpectedJSONError(error_field)
        mk_error_fn = _make_config_commit_error
    else:
        # Otherwise, just use each exception's mapping.
        try:
            mk_error_fn = _ERROR_FIELDS_MAP[error_field["data"]["type"]]
        except KeyError:
            return UnexpectedJSONError(error_field)

    return mk_error_fn(error_field["message"], error_field["data"])

