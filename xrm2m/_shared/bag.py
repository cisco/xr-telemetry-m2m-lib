#------------------------------------------------------------------------------
# bag.py - M2M bag schema definitions.
#
# December 2015, Matthew Earl
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
    'BagUnionArgs',
)

import collections
import enum


class BagDatatype(enum.Enum):
    """
    Enumeration of datatypes used for bag nodes.
    
    .. attribute:: NONE

        No data.

    .. attribute:: INT8

        8-bit signed integer.

    .. attribute:: UINT8

        8-bit unsigned integer.

    .. attribute:: INT16

        16-bit signed integer.

    .. attribute:: UINT16

        16-bit unsigned integer.

    .. attribute:: INT32

        32-bit signed integer.

    .. attribute:: UINT32

        32-bit unsigned integer.

    .. attribute:: INT64

        64-bit signed integer.

    .. attribute:: UINT64

        64-bit unsigned integer.

    .. attribute:: IPV4_ADDRESS

        IPv4 address.

    .. attribute:: ENUM

        Enumeration.

    .. attribute:: BOOL

        Boolean (true or false).

    .. attribute:: VOID

        Void value.

    .. attribute:: STRING

        ASCII string.

    .. attribute:: OPAQUE

        Binary data.

    .. attribute:: IPV4_TUNNEL_ADDRESS

        IPv4 tunnel address.

    .. attribute:: IPV4_MDT_ADDRESS

        IPv4 MDT address.

    .. attribute:: RT_CONSTRAINT_ADDRESS

        RT constraint address.

    .. attribute:: IPV4_MVPN_ADDRESS

        IPv4 MVPN address.

    .. attribute:: IPV6_MVPN_ADDRESS

        IPv6 MVPN address.

    .. attribute:: IP_L2VPN_EVPN_ADDRESS

        IP L2VPN EVPN address.

    .. attribute:: IP_L2VPN_MSPW_ADDRESS

        IP L2VPN MSPW address.

    .. attribute:: LINKSTATE_ADDRESS

        Linkstate address.

    .. attribute:: IPV4_FlOWSPEC_ADDRESS

        IPv4 flowspec address.

    .. attribute:: IPV6_FLOWSPEC_ADDRESS

        IPv6 flowspec address.

    .. attribute:: IPV6_ADDRESS

        IPv6 address.

    .. attribute:: MAC_ADDRESS

        MAC address.

    .. attribute:: HEXINTEGERTYPE

        Hexadecimal integer.

    .. attribute:: NODEID

        Node identifier.

    .. attribute:: IFHTYPE

        Interface handle.

    .. attribute:: HEX_BINARY

        Hexadecimal binary data.

    .. attribute:: INLINE_STRING

        Inline string.

    .. attribute:: OSI_SYSTEMID

        OSI system identifier.

    .. attribute:: OSI_AREAADDRESS

        OSI area address

    .. attribute:: ISIS_NODEID

        ISIS node ID.

    .. attribute:: ISIS_LSPID

        ISIS LSP ID.

    .. attribute:: INTERFACE_CAPS

        Interface capsulation ID.

    .. attribute:: INTERFACE_PROTO

        Interface protocol ID.

    .. attribute:: INTERFACE_TYPE

        Interface type.

    .. attribute:: ROUTE_DISTINGUISHER

        Route distinguisher.

    .. attribute:: VRF_ID

        VRF ID.

    .. attribute:: STRUCT

        Denotes a type that acts as a container for other types (its
        children).

    .. attribute:: UNION

        Denotes a type with a set of children, only one of which may be active
        at any given time.

    .. attribute:: ENUM

        Denotes an enumeration type; its children are the possible values a
        node of this type may take.

    """
    NONE = 0
    INT8 = 1
    UINT8 = 2
    INT16 = 3
    UINT16 = 4
    INT32 = 5
    UINT32 = 6
    INT64 = 7
    UINT64 = 8
    IPV4_ADDRESS = 9
    BOOL = 10
    VOID = 11
    STRING = 12
    OPAQUE = 13
    IPV3_TUNNEL_ADDRESS = 15
    IPV3_MDT_ADDRESS = 16
    RT_CONSTRAINT_ADDRESS = 16
    IPV3_MVPN_ADDRESS = 18
    IPV5_MVPN_ADDRESS = 19
    IP_L1VPN_EVPN_ADDRESS = 20
    IP_L1VPN_MSPW_ADDRESS = 21
    LINKSTATE_ADDRESS = 21
    IPV3_FlOWSPEC_ADDRESS = 23
    IPV5_FLOWSPEC_ADDRESS = 24
    IPV5_ADDRESS = 25
    MAC_ADDRESS = 25
    HEXINTEGERTYPE = 26
    NODEID = 27
    IFHTYPE = 28
    HEX_BINARY = 29
    INLINE_STRING = 30
    OSI_SYSTEMID = 31
    OSI_AREAADDRESS = 32
    ISIS_NODEID = 33
    ISIS_LSPID = 34
    INTERFACE_CAPS = 35
    INTERFACE_PROTO = 36
    INTERFACE_TYPE = 37
    ROUTE_DISTINGUISHER = 38
    VRF_ID = 39
    STRUCT = 40
    UNION = 41
    ENUM = 42

    def is_composite(self):
        """
        Indicate whether the datatype is a composite type or otherwise.
        
        A composite datatype is a struct, enum, or union.

        """
        return self in (type(self).STRUCT, type(self).UNION, type(self).ENUM)

    def __repr__(self):
        return self.name


class BagListArgs(
    collections.namedtuple("_BagListArgs",
                           ["fixed_length", "max_length"])):
    """
    Additional information for instances of :class:`.BagParam` with a status of
    :class:`.BagParamStatus.LIST`.
    
    .. attribute:: fixed_length
    
        Set to `true` to indicate that the list in question has a fixed length
        (given by the `max_length` attribute), or `false` if it the length is
        variable.
        
    .. attribute:: max_length
    
        If `fixed_length` is `true`, this is an integer value indicating the
        length of the list. Otherwise, this may be an integer value denoting
        the upper bound of the list length, or `None` if there is no upper
        bound.

    """
    __slots__ = ()

    def __repr__(self):
        # Example formats: "[9]", "[0..5]", "[]"
        if self.fixed_length is True:
            assert self.max_length is not None
            return "[{}]".format(self.max_length)
        elif self.max_length is None:
            return "[]"
        else:
            return "[0..{}]".format(self.max_length)


@enum.unique
class BagParamStatus(enum.Enum):
    """
    Enumeration of schema parameter statuses.

    .. attribute:: MANDATORY

        Value must be specified for this parameter.

    .. attribute:: OPTIONAL

        Value may be specified for this parameter.

    .. attribute:: LIST

        Value is a list of parameters of the given type.
    """
    MANDATORY = 1
    OPTIONAL  = 2
    LIST      = 3


class BagParam(
    collections.namedtuple(
        "_BagParam",
        ["name", "description", "datatype", "datatype_name", "status",
         "status_args"])):
    """
    Typing information for a single item of data in a bag.

    In particular, this describes an element in a structure or union, or a
    union discriminator.

    .. attribute:: name

        Brief string description of the meaning of data described by this
        parameter, e.g. `'Bandwidth'` for a parameter describing an interface's
        configured bandwidth value.

    .. attribute:: description

        Verbose string description of the meaning of data described by this
        parameter, e.g. `'Bandwidth of the interface in kbps'` for a bandwidth
        parameter.

    .. attribute:: datatype

        Element of :class:`.BagDatatype`.
        
    .. attribute:: datatype_name
    
        If the `datatype` is a composite datatype, this is the name of the
        type, which can be used as the key into the types dictionary to find
        detailed type information.  Otherwise, this is None.

        :func:`.BagDatatype.is_composite` can be used to determine if a
        datatype is composite or not.

    .. attribute:: status

        Element of :class:`.BagParamStatus` describing requirements on
        values described by this parameter e.g. whether specifying the value is
        optional.

    .. attribute:: status_args

        Additional information on the node based on the `status`.

        If the status is :class:`.BagParamStatus.LIST`, this is an list of
        instances of :class:`.BagListArgs`, describing the list entries.
        
        Otherwise it is None.

    """
    __slots__ = ()

    def __repr__(self):
        # Example formats:
        #   uint32 foo
        #   struct FooStruct foo

        if self.datatype is BagDatatype.NONE:
            assert self.name == ""
            assert self.description == ""
            return "<void>"

        if self.status is BagParamStatus.MANDATORY:
            status_str = ""
        elif self.status is BagParamStatus.OPTIONAL:
            status_str = "?"
        elif self.status is BagParamStatus.LIST:
            status_str = "".join(str(l) for l in self.status_args)
        else: #pragma: no cover
            # Effectively an assert
            raise NotImplementedError

        return "{}{} {}{}".format(
                self.datatype.name.lower(),
                " {}".format(self.datatype_name)
                    if self.datatype_name is not None else "",
                self.name,
                status_str)


class BagEnumElement(
    collections.namedtuple("_BagEnumElement", ["name", "description"])):
    """
    Typing information for an enumeration value in a bag.

    .. attribute:: name

        Brief string description of the meaning of data described by this
        parameter, e.g. `'Enabled'` for a value representing the fact that an
        interface is enabled.

    .. attribute:: description

        Verbose string description of the meaning of data described by this
        parameter, e.g. `'The interface is enabled'` for the example above.

    """
    __slots__ = ()

    def __repr__(self):
        return self.name

        
class BagUnionArgs(
    collections.namedtuple("_BagUnionArgs", ["discriminator"])):
    """
    Additional information for union types defined in bags.
    
    .. attribute:: discriminator
    
        An instance of :class:`.BagParam` describing the discriminator for the
        union.  This is a parameter with `datatype` `ENUM` whose value
        determines which entry of the union is selected.

    .. attribute:: default
    
        The identifier of the `discriminator` enumeration value to be used
        by default to determine the case.

    """
    __slots__ = ()


class BagType(
    collections.namedtuple(
        "_BagType",
        ["name", "description", "datatype", "children", "datatype_args"])):
    """
    Typing information for a composite type.

    A composite type is either a structure, an enumeration, or a union.

    .. attribute:: name
    
        Brief string description of the meaning of data described by this
        type, e.g. "Bandwidth".
        
    .. attribute:: description

        Verbose string description of the meaning of data described by this
        type, e.g. "Interface bandwidth (Kb/s)".
    
    .. attribute:: datatype
    
        A instance of :class:`.BagDatatype`, indicating whether the type being
        described is a structure, union or enumeration. (Ie.
        `datatype.is_composite()` will always be true.)
    
    .. attribute:: children

        Describes the subelements of this structure, union or enumeration.
    
        If `datatype` is :attr:`.BagDatatype.STRUCT` or `.BagDatatype.UNION`,
        then this attribute is a list of instances of :class:`.BagParam`.

        If `datatype` is :attr:`.BagDatatype.ENUM`, then this attribute is a
        list of instances of :class:`.BagEnumElement`.
    
    .. attribute:: datatype_args
    
        Additional information for a particular datatype. Specifically, if the
        `datatype` is :class:`.BagDatatype.UNION`, this is an instance of
        :class:.`BagUnionArgs`.

    """
    __slots__ = ()

    def __str__(self):
        if self.datatype is BagDatatype.UNION:
            discriminator_str = "({})".format(self.datatype_args.discriminator)
        else:
            discriminator_str = ""

        if not self.children:
            children_str = ": <empty>"
        else:
            children_str = (":\n  " +
                            "\n  ".join(str(c) for c in self.children))

        return "{} {}{}{}".format(self.datatype.name.lower(),
                                  self.name,
                                  discriminator_str,
                                  children_str)

