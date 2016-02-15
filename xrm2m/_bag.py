#------------------------------------------------------------------------------
# _bag.py - M2M bag schema objects.
#
# November 2015, Matthew Earl
#
# Copyright (c) 2015-2016 by Cisco Systems, Inc.
# All rights reserved.
#------------------------------------------------------------------------------

"""Representations of bags in the XR management data schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


__all__ = (
    'BagDatatype',
    'BagEnumElement',
    'BagParam',
    'BagListArgs',
    'BagParamStatus',
    'BagType',
    'bag_types_from_json',
    'BagUnionArgs',
)


from . import _errors
from . import _utils

from . import _shared
from ._shared.bag import (
    BagParamStatus,
    BagDatatype,
)


@_utils.copy_docstring_from_parent
class BagListArgs(_shared.bag.BagListArgs):
    @classmethod
    def _from_json(cls, d):
        """Create from the corresponding JSON object."""
        return cls(fixed_length=d['fixed_length'],
                   max_length=d['max_length'])


@_utils.copy_docstring_from_parent
class BagParam(_shared.bag.BagParam):
    @classmethod
    def _from_json(cls, d):
        """Create from the corresponding JSON object."""
        status = BagParamStatus[d['status']]
        if d['status_args'] is not None:
            if status != BagParamStatus.LIST:
                raise _errors.InternalError('BagParam JSON object contains '
                        'status_args, but status is not BagParamStatus.LIST')
            status_args = [BagListArgs._from_json(json_arg)
                                              for json_arg in d['status_args']]
        else:
            status_args = None
        return cls(name=d['name'],
                   description=d['description'],
                   datatype=BagDatatype[d['datatype']],
                   datatype_name=d['datatype_name'],
                   status=status,
                   status_args=status_args)


@_utils.copy_docstring_from_parent
class BagEnumElement(_shared.bag.BagEnumElement):
    @classmethod
    def _from_json(cls, d):
        """Create from the corresponding JSON object."""
        return cls(name=d['name'],
                   description=d['description'])


@_utils.copy_docstring_from_parent
class BagUnionArgs(_shared.bag.BagUnionArgs):
    @classmethod
    def _from_json(cls, d):
        """Create from the corresponding JSON object."""
        return cls(discriminator=BagParam._from_json(d['discriminator']))


@_utils.copy_docstring_from_parent
class BagType(_shared.bag.BagType):
    @classmethod
    def _from_json(cls, d):
        """Create from the corresponding JSON object."""

        # Determine the datatype and datatype_args fields. Currently only UNION
        # types should have a datatype_args field, so raise an InternalError if
        # this is not the case here.
        datatype = BagDatatype[d['datatype']]
        if not datatype.is_composite():
            raise _errors.InternalError("BagType has non-composite datatype: "
                                                         "{}".format(datatype))
        if d['datatype_args'] is not None:
            if datatype != BagDatatype.UNION:
                raise _errors.InternalError("BagType JSON object contains "
                        "datatype_args, but datatype is not BagDatatype.UNION")
            datatype_args = BagUnionArgs._from_json(d['datatype_args'])
        else:
            datatype_args = None

        # Determine the children field. For structures and unions this is a
        # list of BagParams. For enumerations it is a list of BagEnumElements.
        if datatype is BagDatatype.ENUM:
           children = [BagEnumElement._from_json(json_child)
                                               for json_child in d['children']]
        else:
           children = [BagParam._from_json(json_child)
                                               for json_child in d['children']]

        return cls(name=d['name'],
                   description=d['description'],
                   datatype=datatype,
                   children=children,
                   datatype_args=datatype_args)


def bag_types_from_json(d):
    """
    Convert a JSON `bag_types` field into structured bag info.

    :param d:
        The JSON object to be converted.

    :returns:
        `dict` in the format required by :attribute:`.SchemaClass.bag_types`.

    """

    return {name: BagType._from_json(json_bag_type)
                                          for name, json_bag_type in d.items()}

