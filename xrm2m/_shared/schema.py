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


import collections
import enum


# Maximum positive value of a (signed) 32 bit integer
_INT32_MAX = 2**31-1
# Size of uint32_t range
_UINT32_SIZE = 2**32


class Datatype(enum.Enum):
    """
    Enumeration of datatypes that appear in the schema.

    .. attribute:: INTEGER

        `Unsigned 32-bit integer <types.html#integer>`__

    .. attribute:: HEX_INTEGER

        `Unsigned 32-bit integer <types.html#hex-integer>`__

    .. attribute:: SIGNED_INTEGER

        `Signed 32-bit integer <types.html#signed-integer>`__

    .. attribute:: BOOL

        `Boolean <types.html#bool>`__

    .. attribute:: TRUE_ONLY

        `Boolean restricted to True <types.html#true-only>`__

    .. attribute:: FALSE_ONLY

        `Boolean restricted to False <types.html#false-only>`__

    .. attribute:: RANGE

        `Unsigned 32-bit integer range <types.html#range>`__

    .. attribute:: SIGNED_RANGE

        `Signed 32-bit integer range <types.html#signed-range>`__

    .. attribute:: ENUM

        `Integer-valued enum <types.html#enum>`__

    .. attribute:: RANGE_ENUM

        `Unsigned 32-bit integer range with labels <types.html#range-enum>`__

    .. attribute:: STRING

        `ASCII-compatible string <types.html#string>`__

    .. attribute:: TEXT

        `ASCII-compatible string <types.html#text>`__

    .. attribute:: IDENTIFIER

        `Identifier string <types.html#identifier>`__

    .. attribute:: ENCODED_STRING

        `ASCII-compatible string <types.html#encoded-string>`__

    .. attribute:: BOUNDED_STRING

        `Restricted-length ASCII-compatible string <types.html#bounded-string>`__

    .. attribute:: BOUNDED_IDENTIFIER

        `Restricted-length identifier string <types.html#bounded-identifier>`__

    .. attribute:: ENCODED_BOUNDED_STRING

        `Restricted-length ASCII-compatible string <types.html#encoded-bounded-string>`__

    .. attribute:: STRING_LIST

        `String-valued enum <types.html#string-list>`__

    .. attribute:: BAG

        `Composite data <types.html#bag>`__

    .. attribute:: IPV4ADDRESS

        `IPv4 address <types.html#ipv4address>`__

    .. attribute:: MASK

        `IPv4 address <types.html#mask>`__

    .. attribute:: IPV4ADDRESS_STRING

        `IPv4 address <types.html#ipv4address-string>`__

    .. attribute:: IPV4HOSTNAME

        `IPv4 address <types.html#ipv4hostname>`__

    .. attribute:: IPV6ADDRESS

        `IPv6 address <types.html#ipv6address>`__

    .. attribute:: IPV6ADDRESS_PLUS

        `IPv6 address <types.html#ipv6address-plus>`__

    .. attribute:: IPV6ADDRESS_STRING

        `IPv6 address <types.html#ipv6address-string>`__

    .. attribute:: IPV6ADDRESS_HEXSTRING

        `IPv6 address <types.html#ipv6address-hexstring>`__

    .. attribute:: IPV6HOSTNAME

        `IPv6 address <types.html#ipv6hostname>`__

    .. attribute:: IPADDRESS

        `IP address <types.html#ipaddress>`__

    .. attribute:: IPADDRESS_STRING

        `IP address <types.html#ipaddress-string>`__

    .. attribute:: IPHOSTNAME

        `IP address <types.html#iphostname>`__

    .. attribute:: IPADDRESS_PREFIX

        `IP address and prefix length <types.html#ipaddress-prefix>`__

    .. attribute:: VRF

        `VRF <types.html#vrf>`__

    .. attribute:: MACADDRESS

        `MAC address <types.html#macaddress>`__

    .. attribute:: MACADDRESS_STRING

        `MAC address <types.html#macaddress-string>`__

    .. attribute:: INTERFACE_NAME

        `Interface name <types.html#interface-name>`__

    .. attribute:: INTERFACE_HANDLE

        `Interface name <types.html#interface-handle>`__

    .. attribute:: INTERFACE_FORWARD

        `Interface name <types.html#interface-forward>`__

    .. attribute:: NODEID

        `Node ID <types.html#nodeid>`__

    .. attribute:: SYSDB_NODEID

        `Node ID <types.html#sysdb-nodeid>`__

    .. attribute:: NODEID_STRING

        `Node ID <types.html#nodeid-string>`__

    .. attribute:: PHYSICAL_NODEID

        `Node ID <types.html#physical-nodeid>`__

    .. attribute:: PHYSICAL_NODEID_STRING

        `Node ID <types.html#physical-nodeid-string>`__

    .. attribute:: EXTENDED_NODEID

        `Node ID <types.html#extended-nodeid>`__

    .. attribute:: PQ_NODEID

        `Partially-qualified node ID <types.html#pq-nodeid>`__

    .. attribute:: PQ_NODEID_STRING

        `Partially-qualified node ID <types.html#pq-nodeid-string>`__

    .. attribute:: RACKID

        `Rack ID <types.html#rackid>`__

    .. attribute:: ENCRYPTION_TYPE

        `Enum of cryptographic algorithms <types.html#encryption-type>`__

    .. attribute:: ENCRYPTED_STRING

        `Obfuscated string <types.html#encrypted-string>`__

    .. attribute:: ENCRYPTION_STRING

        `Obfuscated string <types.html#encryption-string>`__

    .. attribute:: MD5_PASSWORD

        `Obfuscated string <types.html#md5-password>`__

    .. attribute:: PROPRIETARY_PASSWORD

        `Obfuscated string <types.html#proprietary-password>`__

    .. attribute:: OSI_SYSTEMID

        `OSI system ID <types.html#osi-systemid>`__

    .. attribute:: OSI_AREA_ADDRESS

        `OSI area address <types.html#osi-area-address>`__

    .. attribute:: ISIS_NODEID

        `IS-IS node ID <types.html#isis-nodeid>`__

    .. attribute:: ISIS_LSPID

        `IS-IS LSP ID <types.html#isis-lspid>`__

    .. attribute:: OSI_NET

        `OSI NET <types.html#osi-net>`__

    .. attribute:: CHARNUM

        `Byte value <types.html#charnum>`__

    .. attribute:: TTY_ESCAPE_CHARNUM

        `Byte value or special value <types.html#tty-escape-charnum>`__

    .. attribute:: TTY_ESCAPE_CHARNUM

        `Byte value or special value <types.html#tty-escape-charnum>`__
    """
    INTEGER = 0
    HEX_INTEGER = 1
    SIGNED_INTEGER = 2
    BOOL = 3
    TRUE_ONLY = 4
    FALSE_ONLY = 5
    RANGE = 6
    SIGNED_RANGE = 7
    ENUM = 8
    RANGE_ENUM = 9
    STRING = 10
    TEXT = 11
    IDENTIFIER = 12
    ENCODED_STRING = 13
    BOUNDED_STRING = 14
    BOUNDED_IDENTIFIER = 15
    ENCODED_BOUNDED_STRING = 16
    STRING_LIST = 17
    BAG = 18
    IPV4ADDRESS = 19
    MASK = 20
    IPV4ADDRESS_STRING = 21
    IPV4HOSTNAME = 22
    IPV6ADDRESS = 23
    IPV6ADDRESS_PLUS = 24
    IPV6ADDRESS_STRING = 25
    IPV6ADDRESS_HEXSTRING = 26
    IPV6HOSTNAME = 27
    IPADDRESS = 28
    IPADDRESS_STRING = 29
    IPHOSTNAME = 30
    IPADDRESS_PREFIX = 31
    VRF = 32
    MACADDRESS = 33
    MACADDRESS_STRING = 34
    INTERFACE_NAME = 35
    INTERFACE_HANDLE = 36
    INTERFACE_FORWARD = 37
    NODEID = 38
    SYSDB_NODEID = 39
    NODEID_STRING = 40
    PHYSICAL_NODEID = 41
    PHYSICAL_NODEID_STRING = 42
    EXTENDED_NODEID = 43
    PQ_NODEID = 44
    PQ_NODEID_STRING = 45
    RACKID = 46
    ENCRYPTION_TYPE = 47
    ENCRYPTED_STRING = 48
    ENCRYPTION_STRING = 49
    MD5_PASSWORD = 50
    PROPRIETARY_PASSWORD = 51
    OSI_SYSTEMID = 52
    OSI_AREA_ADDRESS = 53
    ISIS_NODEID = 54
    ISIS_LSPID = 55
    OSI_NET = 56
    CHARNUM = 57
    TTY_ESCAPE_CHARNUM = 58
    RPLPOLICY = 59
    RPLSET = 60

    @property
    def camelcase_name(self):
        return _DATATYPE_TO_CAMELCASE[self]


# Used by Datatype.camelcase_name. Defined in the global scope as class
# attributes of `Datatype` are consumed by the `Enum` logic.
_DATATYPE_TO_CAMELCASE = {
    Datatype.BAG:                    'Bag',
    Datatype.INTEGER:                'Integer',
    Datatype.HEX_INTEGER:            'HexInteger',
    Datatype.SIGNED_INTEGER:         'SignedInteger',
    Datatype.BOOL:                   'Boolean',
    Datatype.TRUE_ONLY:              'TrueOnly',
    Datatype.FALSE_ONLY:             'FalseOnly',
    Datatype.RANGE:                  'Range',
    Datatype.SIGNED_RANGE:           'SignedRange',
    Datatype.ENUM:                   'Enum',
    Datatype.RANGE_ENUM:             'RangeEnum',
    Datatype.STRING:                 'String',
    Datatype.TEXT:                   'Text',
    Datatype.IDENTIFIER:             'StringIdentifier',
    Datatype.ENCODED_STRING:         'EncodedString',
    Datatype.BOUNDED_STRING:         'BoundedString',
    Datatype.BOUNDED_IDENTIFIER:     'BoundedIdentifier',
    Datatype.ENCODED_BOUNDED_STRING: 'EncodedBoundedString',
    Datatype.STRING_LIST:            'StringList',
    Datatype.IPV4ADDRESS:            'IPV4Address',
    Datatype.MASK:                   'IPV4Mask',
    Datatype.IPV4ADDRESS_STRING:     'IPV4AddressString',
    Datatype.IPV4HOSTNAME:           'IPV4Hostname',
    Datatype.IPV6ADDRESS:            'IPV6Address',
    Datatype.IPV6ADDRESS_PLUS:       'IPV6AddressPlus',
    Datatype.IPV6ADDRESS_STRING:     'IPV6AddressString',
    Datatype.IPV6ADDRESS_HEXSTRING:  'IPV6AddressHexString',
    Datatype.IPV6HOSTNAME:           'IPV6Hostname',
    Datatype.IPADDRESS:              'IPAddress',
    Datatype.IPADDRESS_STRING:       'IPAddressString',
    Datatype.IPHOSTNAME:             'IPAddressHostname',
    Datatype.IPADDRESS_PREFIX:       'IPAddressPrefix',
    Datatype.VRF:                    'VRF_ID',
    Datatype.MACADDRESS:             'MACAddress',
    Datatype.MACADDRESS_STRING:      'MACAddressString',
    Datatype.INTERFACE_NAME:         'InterfaceName',
    Datatype.INTERFACE_HANDLE:       'InterfaceHandle',
    Datatype.INTERFACE_FORWARD:      'InterfaceForward',
    Datatype.NODEID:                 'NodeID',
    Datatype.SYSDB_NODEID:           'SysDBNodeID',
    Datatype.NODEID_STRING:          'StringNodeID',
    Datatype.PHYSICAL_NODEID:        'PhysicalAllowedNodeID',
    Datatype.PHYSICAL_NODEID_STRING: 'PhysicalAllowedNodeIDString',
    Datatype.EXTENDED_NODEID:        'ExtendedNodeID',
    Datatype.PQ_NODEID:              'PQNodeID',
    Datatype.PQ_NODEID_STRING:       'PQNodeIDString',
    Datatype.RACKID:                 'RackID',
    Datatype.ENCRYPTION_TYPE:        'EncryptionType',
    Datatype.ENCRYPTED_STRING:       'EncryptedString',
    Datatype.ENCRYPTION_STRING:      'EncryptionString',
    Datatype.MD5_PASSWORD:           'MD5Password',
    Datatype.PROPRIETARY_PASSWORD:   'ProprietaryPassword',
    Datatype.OSI_SYSTEMID:           'OSISystemID',
    Datatype.OSI_AREA_ADDRESS:       'OSIAreaAddress',
    Datatype.ISIS_NODEID:            'ISISNodeID',
    Datatype.ISIS_LSPID:             'ISIS_LSP_ID',
    Datatype.OSI_NET:                'OSI_NET',
    Datatype.CHARNUM:                'CharNum',
    Datatype.TTY_ESCAPE_CHARNUM:     'TTYEscapeCharNum',
    Datatype.RPLPOLICY:              'RPLPolicy',
    Datatype.RPLSET:                 'RPLSet',
}


class SchemaClassCategory(enum.Enum):
    """
    Enumeration of classifications of schema classes.

    .. attribute:: CONTAINER

        Denotes a class that acts as a container for other classes (its
        children) and has no value.

    .. attribute:: LEAF

        Denotes a class whose instances have a value. Leaf classes have no
        child classes.

    """
    CONTAINER = 0
    LEAF = 1


class SchemaParamStatus(enum.Enum):
    """
    Enumeration of schema parameter statuses.

    .. attribute:: MANDATORY

        Value must be specified for this parameter.

    .. attribute:: OPTIONAL

        Value may be specified for this parameter.

    .. attribute:: IGNORED

        Value may be specified for this parameter, but any value given will
        have no effect on the system.

        This status is typically used to denote a parameter that no longer has
        a meaning after an update to the schema, while preserving backwards
        compatibility.

    """
    MANDATORY = 0
    OPTIONAL = 1
    IGNORED = 2


class _UnversionedType:
    """Singleton class representing absence of version information."""

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_UnversionedType, cls).__new__(cls)
        return cls._instance

    def __repr__(self):
        return "UNVERSIONED"

UNVERSIONED = _UnversionedType()


class Version(collections.namedtuple("_Version", ["major", "minor"])):
    """
    Named tuple describing the version of an object in the schema.

    If version information is requested for an object that's not versioned, the
    :data:`.UNVERSIONED` singleton is returned rather than an instance of this
    class.

    The :data:`.MAX_VERSION` singleton represents an 'infinitely high' version.

    .. attribute:: major

        Major version number.

    .. attribute:: minor

        Minor version number.

    """

    def __str__(self):
        return "{}.{}".format(self.major, self.minor)

    def __repr__(self):
        return "{}({}.{})".format(type(self).__name__,
                                  self.major,
                                  self.minor)


class _MaxVersionType(Version):
    """Singleton class representing an 'infinitely high' version."""

    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(_MaxVersionType, cls).__new__(
                                               cls, float("inf"), float("inf"))
        return cls._instance

    def __repr__(self):
        return "MAX_VERSION"

MAX_VERSION = _MaxVersionType()


class SchemaClass(collections.namedtuple(
                    "_SchemaClass",
                    [
                        "name",
                        "category",
                        "description",
                        "table_description",
                        "key",
                        "value",
                        "presence",
                        "version",
                        "table_version",
                        "hidden",
                        "version_compatibility",
                        "table_version_compatibility",
                        "children",
                        "bag_types",
                    ])):
    """
    Meta-data for a node in the schema hierarchy.

    Schema classes describe a type of management data that *may* exist and
    the properties of any such data.

    For example::

        # To navigate to a particular point in the schema, create a Path
        # without filling in key values.
        >>> path = RootCfg.InterfaceConfiguration.VRF
        >>> cls_info = conn.get_schema(path)
        >>> cls_info.name
        'VRF'
        >>> cls_info.category
        <SchemaClassCategory.LEAF: 2>
        >>> cls_info.description
        'Assign the interface to a VRF'
        >>> for param in cls_info.value()
        ...     print(param)
        SchemaParam(BoundedString(1, 32) VRFName)

    .. attribute:: name

        Name of this class in the schema.

    .. attribute:: category

        :class:`Category <.SchemaClassCategory>` of this class.

        A class' category denotes what data it describes e.g. whether it's a
        container for other classes, or has an associated value.

    .. attribute:: description

        String giving a verbose description of the semantics of data described
        by the class.

    .. attribute:: table_description

        Same as :attr:`description`, for the table described by this class, if
        any.

    .. attribute:: key

        Data type information for this class' key parameters. This is a list of
        :class:`SchemaParam` objects, each describing a single key parameter.

        The 'key' of a class is the collection of parameters whose values
        distinguish different instances of the class in data described by the
        schema. This attribute describes the format and meaning of those
        values. For example::

            >>> print(route_cls)
            SchemaClass(IP_RIBRoute)
            >>> for param in route_cls.key():
            ...     print(param)
            SchemaParam(String RouteTableName)

    .. attribute:: value

        Data type information for this class' value parameters. This is a list
        of :class:`SchemaParam` objects, each describing a single value
        parameters.

        This attribute describes the format and meaning of the data contained
        in instances of this class. An example from the BGP config schema::

            >>> print(bufsizes)
            SchemaClass(ReceiveSocketBufferSizes)
            >>> for param in bufsizes.value():
            ...     print(param)
            SchemaParam(Range(512, 13107) SocketReceiveSize)
            SchemaParam(Range(512, 13107) BGPReceiveSize)

        Note that if the leaf represents a bag, then `value` will be a
        singleton list containing a :class:`SchemaParam` of type
        `Datatype.BAG`.

        Note that if the leaf represents a bag, then `value` will be a
        singleton list containing a :class:`SchemaParam` of type
        `Datatype.BAG`.

    .. attribute:: presence

        A :class:`.Path` identifying the leaf class that gives this class
        'presence', or `None` if there is no such leaf class.

        Container classes may have a nominated leaf class that defines whether
        the container exists or not, a similar concept to 'containers with
        presence' in YANG. This method returns a path to the nominated class,
        if any.

    .. attribute:: version

        Current :class:`.Version` of this class or :data:`.UNVERSIONED` if this
        class has the same version as its parent.

        For example::

            >>> print(cls)
            SchemaClass(InterfaceProperties)
            >>> cls.version()
            Version(major=3, minor=2)

    .. attribute:: table_version

        Same as :attr:`version`, for the table described by this class, if any.
        None if the class does not describe a table.

    .. attribute:: hidden

        `True` if this class is hidden, `False` otherwise.

        Classes are typically hidden to mark them as deprecated. See
        :attr:`version_compatibility`.

    .. attribute:: version_compatibility

        Minimum and maximum schema versions this class is compatible with.

        This is a `(min version, max version)` tuple of :class:`.Version`
        instances. It can be used to determine whether a class is deprecated
        (in which case it's also likely to be marked as hidden)::

            >>> print(cls)
            SchemaClass(DefaultVRF)
            >>> current = cls.version()
            >>> min_supported, max_supported = cls.version_compatibility()
            >>> max_supported < current
            True
            >>> current
            Version(major=10, minor=0)
            >>> max_supported
            Version(major=8, minor=0)
            >>> cls.hidden()
            True

        A deprecated class is still a valid representation of management data,
        but represents an outdated or incomplete view of that data.

        If a class is compatible with known versions after a certain point, the
        :data:`MAX_VERSION` singleton is used to represent the maximum
        compatible version::

            >>> print(cls)
            SchemaClass(Node)
            >>> cls.version_compatibility()
            (Version(major=2, minor=0), MAX_VERSION)
            >>> Version(major=100, minor=20) < MAX_VERSION
            True

        If a class contains no compatibility information, then
        :data:`UNVERSIONED` is returned for both the min and max versions.

    .. attribute:: table_version_compatibility

        Same as :attr:'version_compatibility`, for the table described by this
        class, if any. None if the class does not describe a table.

    .. attribute:: children

        List of paths to children of this class in the schema::

            >>> cls = conn.get_schema(RootCfg.InterfaceConfiguration)
            >>> for child in cls.children[:5]:
            ...     print(child)
            Path(RootCfg.InterfaceConfiguration.PseudowireEther)
            Path(RootCfg.InterfaceConfiguration.IPv6Neighbor)
            Path(RootCfg.InterfaceConfiguration.MACAccounting)
            Path(RootCfg.InterfaceConfiguration.IPV6PacketFilter)
            Path(RootCfg.InterfaceConfiguration.PTP)

    .. attribute:: bag_types

        Bag types relevant to this schema node, or `None` if `value` does not
        contain (a single) :class:`.SchemaParam` of type `Datatype.BAG`.

        `bag_types` contains schema information for structures (equivalently
        bags), unions, and enums that are directly or indirectly referenced by
        this node's schema parameter. It is structured as a dict in the
        following form:

        .. sourcecode:: python

            >>> schema_info = conn.get_schema(intf_config))
            >>> pprint(schema_info.bag_types)
            {
                'im_if_type_summary_st': BagType(
                    name='im_if_type_summary_st',
                    description='', datatype=<BagDatatype.STRUCT: 2>,
                    children=[
                         string InterfaceTypeName,
                         string InterfaceTypeDescription,
                         struct im_if_group_counts_st InterfaceCounts
                    ],
                    datatype_args=None
                ),
                'im_if_group_counts_st': BagType(
                    name='im_if_group_counts_st',
                    description='',
                    datatype=<Datatype.STRUCT: 2>,
                    children=[
                        uint32 InterfaceCount,
                        uint32 UpInterfaceCount,
                        uint32 DownInterfaceCount,
                        uint32 AdminDownInterfaceCount
                    ],
                    datatype_args=None
                ),
                'im_if_summary_info': BagType(
                    name='im_if_summary_info',
                    description='Interface summary bag',
                    datatype=<Datatype.STRUCT: 2>,
                    children=[
                        struct im_if_type_summary_st InterfaceTypeList[],
                        struct im_if_group_counts_st InterfaceCounts
                    ],
                    datatype_args=None
                )
            }

        Keys of the dict correspond with this node's schema parameter's
        `name` field:

        .. sourcecode python

            >>> assert len(schema_info.value) == 1
            >>> assert schema_info.value[0].name in schema_info.bag_types
            >>> bag_info = schema_info.bag_types[schema_info.value[0].name]

        In the case that the bag corresponding with this node contains a
        structure, enum, or union as one of its parameters, then the structure,
        enum, or union is referenced by the `datatype_name` attribute of the
        corresponding :class:`BagParam`. For example, if the third bag
        parameter is a struct, and the fourth a union:

        .. sourcecode python

            >>> struct_info = bag_info.children[2].datatype_name
            >>> union_info = bag_info.children[4].datatype_name

        Such nested structs and unions may themselves refer to further nested
        structs, unions and enums in a similar way.

    """

    __slots__ = ()

    def __str__(self):
        return "{}({})".format(type(self).__name__, self.name)


class SchemaParam(collections.namedtuple(
                    "_SchemaParam",
                    [
                        "name",
                        "description",
                        "datatype",
                        "datatype_args",
                        "repeat_count",
                        "status",
                        "internal_name",
                    ])):
    """
    Typing information for a single key or value parameter.

    .. attribute:: datatype

        Element of :class:`.Datatype`.

    .. attribute:: name

        Brief string description of the meaning of data described by this
        parameter, e.g. `'Bandwidth'` for a parameter describing an interface's
        configured bandwidth value.

    .. attribute:: description

        Verbose string description of the meaning of data described by this
        parameter, e.g. `'Bandwidth of the interface in kbps'` for a bandwidth
        parameter.

    .. attribute:: datatype_args

        If :attr:`datatype` is a parameterised type, a dict containing the
        parameter values for this instance of the type. For unparameterised
        types, this is `None`.

        For integer range types::

            >>> param
            SchemaParam(Range(5, 16) MaxRecursionDepth)
            >>> param.description
            'Maximum depth for route recursion check'
            >>> pprint(param.datatype_args)
            {
                "min": 5,
                "max": 16,
            }

        For restricted-length string types::

            >>> param
            SchemaParam(BoundedString(0, 244) Description)
            >>> param.description
            'VRF description'
            >>> pprint(param.datatype_args)
            {
                "minlen": 0,
                "maxlen": 244,
            }

        For instances of the `enum <types.html#enum>`__ type::

            >>> param
            SchemaParam(Enum Mode)
            >>> pprint(param.datatype_args)
            {
                "Default": {
                    "value": 0,
                    "description": "Default interface mode",
                },
                "PointToPoint": {
                    "value": 1,
                    "description": "Point-to-point interface mode",
                },
                "Multipoint": {
                    "value": 2,
                    "description": "Multipoint interface mode",
                },
                "L2Transport": {
                    "value": 3,
                    "description": "L2 transport interface mode",
                },
            }

        For instances of the `range enum <types.html#range-enum>`__ type::

            >>> param
            SchemaParam(RangeEnum(0, 4294967295) MeshGroup)
            >>> pprint(param.datatype_args)
            {
                "min": 0,
                "max": 4294967295,
                "enum": {
                    "Blocked": {
                        "value": 0,
                        "description": "Blocked mesh group. Changed LSPs are "
                                       "not flooded over blocked interfaces",
                    },
                },
            }

        For instances of the `string list <types.html#string-list>`__ type::

            >>> param
            SchemaParam(StringList Active)
            >>> pprint(param.datatype_args)
            {
                "act": {
                    "description": "Interface is active",
                },
                "pre": {
                    "description": "Interface is preconfigured",
                },
            }

    .. attribute:: repeat_count

        Number of times this parameter is repeated in data described by the
        schema. This is `1` unless this parameter is an array.

    .. attribute:: status

        Element of :class:`.SchemaParamStatus` describing requirements on
        values described by this parameter e.g. whether specifying the value is
        optional.

    .. attribute:: internal_name

        Name used to refer to this parameter internally within the IOS-XR 
        system.  It is set only if this data is of type `BAG`.
        Otherwise it is None.

        If set it is usually the same as `name`.

        This information is intended for use by IOS-XR tools built on top of 
        MPG. It's unlikely to be useful in other scenarios.

    """

    def __repr__(self):
        if self.datatype in (Datatype.RANGE, Datatype.SIGNED_RANGE):
            # Range types
            args_str = "({min}, {max})".format(**self.datatype_args)
        elif self.datatype in (Datatype.BOUNDED_STRING,
                               Datatype.BOUNDED_IDENTIFIER,
                               Datatype.ENCODED_BOUNDED_STRING):
            # Bounded string types
            args_str = "({minlen}, {maxlen})".format(**self.datatype_args)
        else:
            args_str = ""
        return "{}({}{} {})".format(type(self).__name__,
                                    self.datatype.camelcase_name,
                                    args_str,
                                    self.name)

