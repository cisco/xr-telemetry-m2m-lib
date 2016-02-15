#------------------------------------------------------------------------------
# _schema.py - M2M schema objects.
#
# July 2015, Phil Connell
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
#------------------------------------------------------------------------------

"""Representations of objects in the XR management data schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__all__ = (
    "Datatype",
    "Version",
    "MAX_VERSION",
    "UNVERSIONED",
    "SchemaClass",
    "SchemaClassCategory",
    "SchemaParam",
    "SchemaParamStatus",
)

from . import _bag
from . import _path
from . import _utils

# Import shared objects, either to export direct or subclass
from ._shared import schema
from ._shared.schema import(
    Datatype,
    Version,
    MAX_VERSION,
    UNVERSIONED,
    SchemaClassCategory,
    SchemaParamStatus,
)


@_utils.copy_docstring_from_parent
class SchemaClass(schema.SchemaClass):
    # Docstring in parent
    @classmethod
    def from_dict(cls, path, d):
        """
        Construct a schema class from a `dict`, as returned by JSON.

        This method should not be called directly by external users.

        """
        def convert_version_compatibility(v):
            if v[0] is None and v[1] is None:
                out = UNVERSIONED, UNVERSIONED
            elif v[1] is None:
                out = Version(**v[0]), MAX_VERSION
            else:
                out = Version(**v[0]), Version(**v[1])
            return out

        # An incoming table_version value of None indicates either UNVERSIONED
        # or None, depending on whether table information is present. The
        # table_version_compatibility field is used to determine this (it will
        # be None if table information is not present, or a pair otherwise).
        if d["table_version_compatibility"] is None:
            table_version = None
            table_version_compatibility = None
        else:
            table_version = (Version(**d["table_version"])
                                        if d["table_version"] else UNVERSIONED)
            table_version_compatibility = convert_version_compatibility(
                                              d["table_version_compatibility"])

        # Build the `bag_types` field.
        if d['bag_types'] is not None:
            bag_types = _bag.bag_types_from_json(d['bag_types'])
        else:
            bag_types = None

        # Make a SchemaClass with the converted schema information.
        return cls(
            name=path.elems()[-1].name,
            category=SchemaClassCategory[d["category"]],
            description=d["description"],
            table_description=d["table_description"],
            key=[SchemaParam._from_dict(p) for p in d["key"]],
            value=[SchemaParam._from_dict(p) for p in d["value"]],
            presence=_path.Path.from_str(d["presence"]) if d["presence"]
                     else None,
            version=Version(**d["version"]) if d["version"] else UNVERSIONED,
            table_version=table_version,
            hidden=d["hidden"],
            version_compatibility=convert_version_compatibility(
                                                   d["version_compatibility"]),
            table_version_compatibility=table_version_compatibility,
            children=[_path.Path.from_str(p) for p in d["children"]],
            bag_types=bag_types) 


@_utils.copy_docstring_from_parent
class SchemaParam(schema.SchemaParam):
    # Docstring in parent
    @classmethod
    def _from_dict(cls, d):
        """
        Construct a schema param from a `dict`, as returned by JSON.

        This method should not be called directly by external users.

        """
        return cls(
            datatype=Datatype[d["datatype"]],
            name=d["name"],
            description=d["description"],
            datatype_args=d["datatype_args"],
            repeat_count=d["repeat_count"],
            status=SchemaParamStatus[d["status"]],
            internal_name=d["internal_name"])

