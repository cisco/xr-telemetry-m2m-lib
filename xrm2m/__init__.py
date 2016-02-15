# -----------------------------------------------------------------------------
# __init__.py - M2M Python API package root.
#
# July 2015, Phil Connell
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
# -----------------------------------------------------------------------------

'''Machine-to-Machine Python API.'''

__all__ = (
    # _path
    'Path',
    'PathElement',
    'RootAction',
    'RootCfg',
    'RootOper',

    # _schema
    'Datatype',
    'Version',
    'MAX_VERSION',
    'UNVERSIONED',
    'SchemaClass',
    'SchemaClassCategory',
    'SchemaParam',
    'SchemaParamStatus',

    # _conn
    'async',
    'AsyncConnection',
    'connect',
    'connect_async',
    'Connection',
    'ConnectionState',
    'sync',

    #_defs
    'Change',
    'ChangeDetails',
    'ConfigCommitErrorDetail',
    'ErrorCategory',
    'Method',
    'Password',
    'Request',
    'WILDCARD',
    'WILDCARD_ALL',

    # _transport
    'Transport',
    'SSHTransport',
    'SubProcessTransport',
    'LoopbackTransport',
    'EnXRTransport',

    # _errors
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
    'ValueContentError',
    'ValueStructureError',

    # _bag
    'BagDatatype',
    'BagEnumElement',
    'BagParam',
    'BagListArgs',
    'BagParamStatus',
    'BagType',
    'BagUnionArgs',
)

from ._conn import (
    async,
    AsyncConnection,
    connect,
    connect_async,
    Connection,
    ConnectionState,
    sync,
)

from ._defs import (
    Change,
    ChangeDetails,
    ConfigCommitErrorDetail,
    ErrorCategory,
    Method,
    Password,
    Request,
    WILDCARD,
    WILDCARD_ALL,
)

from ._path import (
    Path,
    PathElement,
    RootAction,
    RootCfg,
    RootOper,
)

from ._schema import (
    Datatype,
    Version,
    MAX_VERSION,
    UNVERSIONED,
    SchemaClass,
    SchemaClassCategory,
    SchemaParam,
    SchemaParamStatus,
)

from ._transport import (
    Transport,
    SSHTransport,
    SubProcessTransport,
    LoopbackTransport,
    EnXRTransport
)

from ._errors import (
    AmbiguousPathError,
    CiscoError,
    ConfigCommitError,
    ConnectionError,
    DatatypeNotSupportedError,
    DisconnectedError,
    FileExistsError,
    InternalError,
    InvalidArgumentError,
    MalformedJSONReceived,
    NotFoundError,
    OperationNotSupportedError,
    ParseError,
    PathHierarchyError,
    PathKeyContentError,
    PathKeyStructureError,
    PathStringFormatError,
    UnexpectedJSONError,
    ValueContentError,
    ValueStructureError,
)

from ._bag import (
    BagDatatype,
    BagEnumElement,
    BagParam,
    BagListArgs,
    BagParamStatus,
    BagType,
    BagUnionArgs,
)
