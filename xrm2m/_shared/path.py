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


import collections
import json
import string

from . import defs
from . import _pathstr
from . import utils

class Path(object):
    """
    Path objects encode references to management data items.

    For example::

        >>> hostname = RootCfg.Hostname
        >>> hostname
        Path(RootCfg.Hostname)
        >>> conn.get_value(hostname)
        'R1-SFO'
        >>>
        >>> intf = RootCfg.InterfaceConfiguration("act", "HundredGigE0/0/0/0")
        >>> conn.get_value(intf.Description)
        'To BOS'

    Paths encode two types of information:

    - A point in the schema hierarchy.

    - 'Key' values, identifying specific data described by that point in the
      schema.

    The path objects :data:`.RootCfg`, :data:`.RootOper` and
    :data:`.RootAction` provide access to the root of the configuration and
    operational data hierarchies, respectively:

        >>> RootCfg
        Path(RootCfg)
        >>> RootOper
        Path(RootOper)
        >>> RootAction
        Path(RootAction)

    Attribute access on a path returns a new path with additional schema
    hierarchy levels::

        >>> RootOper
        Path(RootOper)
        >>> RootOper.BGP.Instance
        Path(RootOper.BGP.Instance)

    Calling a path returns a new path with additional key values::

        >>> bgp_inst
        Path(RootOper.BGP.Instance)
        >>> bgp_inst("foo").InstanceActive
        Path(RootOper.BGP.Instance('foo').InstanceActive)

    Key values can be identified by name using keyword arguments::

        >>> te_announce("ISIS", Area=0, IGP_ID=0)
        Path(RootOper.MPLS_TE.Announce('ISIS', 0, 0))

    Additionally, key values can be supplied in a sequence or mapping (matching
    the format used by other interfaces e.g. JSON-RPC)::

        >>> RootOper.MPLS_TE.Announce(["ISIS", 0, 0])
        Path(RootOper.MPLS_TE.Announce('ISIS', 0, 0))
        >>> RootOper.MPLS_TE.Announce({"Protocol": "ISIS", "Area": 0, "IGP_ID": 0})
        Path(RootOper.MPLS_TE.Announce('ISIS', 0, 0))

    `Wildcards <dataobj.html#wildcards>`__ can be used when specifying keys::

        >>> intf_cfg
        Path(RootCfg.InterfaceConfiguration)
        >>> te_tunnels = intf_cfg("act", "te-tunnel*")

    Schema meta-data for a path can be obtained using the
    :meth:`~.Connection.get_schema` method of connection objects.

    Paths are hashable. Two paths are considered equal if they encode the same
    schema hierarchy and key information.

    """
    def __init__(self, elements):
        self._elements = list(elements)

    def elems(self):
        """
        Return a sequence of :class:`.PathElement` objects for this path.

            >>> path
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0').VRF)
            >>> elems = path.elems()
            >>> elems[2]
            PathElement(InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
            >>> elems[2].name
            'InterfaceConfiguration'
            >>> elems[2].key
            {'Active': 'act', 'InterfaceName': 'HundredGigE0/0/0/0'}

        Path element sequences have limited support for slicing to obtain a
        prefix, as a new :class:`.Path` object::

            >>> path
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0').VRF)
            >>> elems = path.elems()
            >>> elems[:3]
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
            >>> elems[::2]
            ValueError: Path slices must not specify step
            >>> elems[1:]
            ValueError: Path slices must include the start of the path

        """
        return self._elements

    def __getitem__(self, name_or_idx):
        """
        Return the value of a key with a particular name or index.

        :param name_or_idx:
            String name or integer index of the key to return.

        .. sourcecode:: python

            >>> path
            Path(RootOper.Interfaces.Interface('HundredGigE0/0/0/0'))
            >>> path["InterfaceName"]
            'HundredGigE0/0/0/0'
            >>> path[0]
            'HundredGigE0/0/0/0'

        If the path includes multiple keys with the same name, the first key
        with the given name is returned.

        If there's no key with the given name or index, :exc:`KeyError` is
        raise for name lookups, and :exc:`IndexError` for index lookups.

        If the path was constructed without key names, this method can't be
        used::

            >>> path = RootCfg.InterfaceConfiguration("act", "Loopback0")
            >>> path["InterfaceName"]
            KeyError: No key named 'InterfaceName'
            >>> path[1]
            'Loopback0'

        Paths output from the M2M API *always* have key names available
        (including :meth:`.Connection.normalize_path`).

        """
        all_keys = [(name, val) for el in self.elems()
                                               for name, val in el._key_info]

        if isinstance(name_or_idx, str):
            out = collections.OrderedDict(reversed(all_keys))[name_or_idx]
        elif isinstance(name_or_idx, (int, slice)):
            out = [val for (name, val) in all_keys][name_or_idx]
        else:
            raise TypeError

        return out

    @classmethod
    def from_str(cls, pathstr):
        r"""
        Create a new path from a string representation.

        .. sourcecode:: python

            >>> Path.from_str('RootCfg.Abc')
            Path(RootCfg.Abc)
            >>> Path.from_str('RootCfg.Abc.Def(["10.0.0.1", "(xyz|abc)*", null])')
            Path(RootCfg.Abc.Def('10.0.0.1', '(xyz|abc)*', None)
            >>> Path.from_str('RootCfg.Abc.Def({IPAddress: "10.0.0.1", Name: "(xyz|abc)*"})')
            Path(RootCfg.Abc.Def('10.0.0.1', '(xyz|abc)*', None)

        As seen in the example above, the format expected on input is very
        similar to the string representation of path objects:

        - Hierarchy element names are separated by `.`
        - Key values are specified inside `()` - either inside `[]` as a sequence of values, or `{}` as a mapping of name-value pairs (i.e. using JSON array or object notation).
        - Key values are separated by `,`
        - Key name-value pairs separate the name and value by `:`

        Additionally:

        - Whitespace between key values is ignored.
        - It's possible to wildcard *all* key values, using `(*)`. This is equivalent to :data:`.WILDCARD_ALL`.

        Each key value should be one of the following:

        - A string literal, using any literal notation with `''` or `""`
          delimiters that's supported by Python.

          The string is evaluated using `ast.literal_eval`. For example
          `RootCfg.Xyz(['abc"\\\\z'])` gives the path
          `Path(RootCfg.Xyz('abc"\\z'))`.

          Strings may include `globbing <dataobj.html#wildcards>`__
          meta-characters (e.g. `'abc*'`).

          Triple-quoted strings and prefixed strings (e.g. `'''abc'''` or
          `r"abc"`) are not supported.

        - An integer literal, using decimal notation or hex notation with a
          `0x` or `0X` prefix, e.g. `123`, `0x7B` or `0X7b`.

        - One of the literals `true` or `false` to indicate the corresponding
          bool value.

        - The literal `null` to explicitly indicate 'no value'.

        - The literal `*` to indicate a :data:`.WILDCARD`.

        Each key name should be a string literal.

        :exc:`.PathStringFormatError` is raised if:

        - The input string is badly formatted and can't be parsed.

        :param pathstr:
            String representation of a path to be parsed.

        :returns:
            A new :class:`.Path`.

        """
        pathstr = utils.sanitize_input_string(pathstr)
        elems = _pathstr.PathParser().parse(pathstr)
        assert elems
        assert elems[0].name in {"RootOper", "RootCfg", "RootAction"}

        path = cls([])
        for name, key_info in elems:
            path = getattr(path, name)(key_info)
        return path

    def __eq__(self, other):
        # Type checks, then compare underlying elements.
        #
        # N.B. that this check is purely syntactic, vs. the MPG version that
        # attempts to canonicalise first. e.g. if one path uses named keys and
        # another uses positional keys, we can never decide that they're equal
        # (it would require a schema lookup).
        if not isinstance(other, Path):
            return NotImplemented
        return self.elems() == other.elems()

    def __hash__(self):
        return hash(tuple(self.elems()))

    def __repr__(self):
        """See :meth:`.Path.__str__`."""
        return "{}({})".format(type(self).__name__,
                          ".".join(el._repr_no_class() for el in self.elems()))

    def __str__(self):
        """
        Return the string representation of this path.

        The format returned is (as far as possible) the same that's supported
        as input by :meth:`from_str`::

            >>> print(repr(path))
            Path(RootCfg.Abc.Def('10.0.0.1', 'xyz*').Ghi(42, True, WILDCARD))
            >>> print(str(path))
            RootCfg.Abc.Def({"address": "10.0.0.1", "name": "xyz*"}).Ghi({"j": 42, "k": true, "l": *})

        For paths constructed by users of this API, it's possible that key
        names aren't available. In this case, they're ommitted::

            >>> path = RootCfg.InterfaceConfiguration("act", "Loopback0")
            >>> print(str(path))
            RootCfg.InterfaceConfiguration(["act", "Loopback0"])

        """
        return ".".join(str(el) for el in self.elems())

    @staticmethod
    def _make_path_element(elem_name):
        """Create path element, given its name."""
        # This is a separate function to allow onbox to use its own path
        # element.
        return PathElement(elem_name)

    def __getattr__(self, elem_name):
        """
        Return a copy of this path with an extra hierarchy element appended.

        :param elem_name:
            Name of the additional element.

        """
        return type(self)(self._elements +
                          [self._make_path_element(elem_name)])

    def __call__(self, *key_seq, **key_map):
        """
        Return a copy of this path with key information added.

        Values for optional keys 'omitted' by passing `None`. For example
        `path(123, None, 456)` returns a new path with values for the first and
        third key elements, but no value for the second element.

        Keys may be specified using:

            - positional arguments, or
            - keyword arguments, or
            - a single sequence, or
            - a single mapping

        The following expressions create equivalent paths::

            >>> intf_cfg("act", "HundredGigE0/0/0/0")
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
            >>> intf_cfg(Active="act", InterfaceName="HundredGigE0/0/0/0")
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
            >>> intf_cfg(["act", "HundredGigE0/0/0/0"])
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
            >>> intf_cfg({"Active": "act", "InterfaceName": "HundredGigE0/0/0/0"})
            Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))

        `Wildcard <dataobj.html#wildcards>`__ key values can be used to
        match multiple values. For example `intf_cfg("tunnel-te*")` returns a
        new path matching all TE tunnel interface config.

        """

        # Reduce the cases where a single sequence or mapping is passed to the
        # argument and keyword argument case.
        if (len(key_seq) == 1 and len(key_map) == 0 and
                           isinstance(key_seq[0], collections.Sequence) and
                           not isinstance(key_seq[0], str) and
                           not isinstance(key_seq[0], bytes)):
            # Handle list case.
            key_seq = list(key_seq[0])
            key_map = {}
        elif (len(key_seq) == 1 and len(key_map) == 0 and
                                 isinstance(key_seq[0], collections.Mapping)):
            # Handle dict case.
            key_map = collections.OrderedDict(key_seq[0])
            key_seq = []

        # Construct the key information that should be added to the last
        # element. The format is identical to that taken by
        # `PathElement._key_info`.
        #
        # Note after this step `key_info` may contain a mix of named and
        # unnamed keys. If so the final step (constructing the new path
        # element) will raise an exception.
        key_info = []

        for val in key_seq:
            key_info.append((None, val))

        for name, val in key_map.items():
            key_info.append((name, val))

        # Return a new path identical to this path, but with the last element
        # updated to have key information.
        elems = self.elems()
        return type(self)(elems[:-1] + [elems[-1]._add_key_info(key_info)])


class PathElement(object):
    """
    Represents a single element of a path.

    Path elements encode:

    - A schema class, defining the semantics of the element.

    - 'Key' information, identifying a specific instance of the schema class.

    For example::

        >>> intf
        Path(RootCfg.InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
        >>> elem = intf.elems()[-1]
        >>> elem.name
        'InterfaceConfiguration'
        >>> elem.key
        OrderedDict([('Active', 'act'), ('InterfaceName', 'HundredGigE0/0/0/0')])

    .. attribute:: name

        Name of the schema class that this element represents an instance of.

    .. attribute:: key

        Key values associated with this element:

        - This is `None` if no key is specified.

        - This is a single value if the key has only a single value, e.g. a
          single IP address.

        - This is an ordered mapping of key names to values if the key
          consists of multiple values.

        For example,

           >>> vrf
           PathElement(VRF('foo'))
           >>> vrf.key
           'foo'
           >>> intf
           PathElement(InterfaceConfiguration('act', 'HundredGigE0/0/0/0'))
           >>> intf.key
           OrderedDict([('Active', 'act'), ('InterfaceName', 'HundredGigE0/0/0/0')])

    """

    def __init__(self, name, key_info=()):
        """
        Create a path element instance.

        :class:`.PathElement`s should only be accessed via :meth:`.Path.elems`
        and should be not be created directly.

        :param name:
            Name attribute.

        :param key_info:
            Key information in the form of a list of `(name, value)` pairs.
            `name` can be `None` in the case that the key name is not known. If
            the path's key info is `WILDCARD_ALL` then this argument should be
            a single pair `(None, WILDCARD_ALL)`.

        """

        self._name = name
        self._key_info = key_info

        # Sanitize and validate key names and values.
        def sanitize_key_name(name):
            if isinstance(name, (type(b""), type(""))):
                name = utils.sanitize_input_string(name)
            elif name is not None:
                raise ValueError("Key name {!r} is not a string".format(name))
            return name
        def sanitize_key_value(val):
            if isinstance(val, (type(b""), type(""))):
                return utils.sanitize_input_string(val)
            return val
        self._key_info = [(sanitize_key_name(name), sanitize_key_value(val))
                                               for name, val in self._key_info]

        name_counts = collections.Counter(name for name, val in key_info)
        # Check that there are no duplicate keys in the key information.
        # The assert below should be impossible to hit (and reflects an M2M
        # bug, rather than error in client input)
        assert not any(name is not None and count > 1
                       for name, count in name_counts.items()), name_counts
        # Check that either all names are None, or none are None.
        if 0 < name_counts[None] < len(key_info):
            raise ValueError("Mixture of named keys and unnamed keys.")

        # Check that if `WILDCARD_ALL` appears then it is the only item of key
        # information (and no name is provided).
        if (defs.WILDCARD_ALL in (val for name, val in key_info) and
                                   key_info != [(None, defs.WILDCARD_ALL)]):
            raise ValueError("WILDCARD_ALL passed with other key information.")

    @property
    def name(self):
        return self._name

    @property
    def key(self):
        """
        Return key information.

        The value returned is either `None`, a sequence, a mapping or
        :data:`.WILDCARD_ALL`. If `None` then the element has no key
        information. Otherwise the value is the same format accepted by
        :meth:`.Path.__call__`::

            >>> p = RootCfg.Interfaces
            >>> p.elems()[-1].key
            >>> p = RootCfg.Interfaces(['act', 'GE/0/0/0'])
            >>> p.elems()[-1].key
            ['act', 'GE/0/0/0']
            >>> p = RootCfg.Interfaces({'Active': 'act', 'Interface': 'GE/0/0/0'})
            >>> p.elems()[-1].key
            OrderedDict([('Active', 'act'), ('Interface', 'GE/0/0/0')])
            >>> p = RootCfg.Interfaces(WILDCARD_ALL)
            >>> p.elems()[-1].key
            WILDCARD_ALL

        :returns:
            Key information in the format described above.

        """
        if not self._has_key_info():
            out = None
        elif self._is_wildcard_all():
            out = defs.WILDCARD_ALL
        elif self._has_names():
            out = collections.OrderedDict(self._key_info)
        else:
            out = [val for name, val in self._key_info]

        return out

    def __eq__(self, other):
        return (isinstance(other, PathElement) and
                self._name == other._name and
                self._key_info == other._key_info)

    def __hash__(self):
        return hash((type(self), self._name, tuple(self._key_info)))

    def _has_names(self):
        """
        Utility to determine whether this element's key info includes names.

        Returns False if there is no key information for this path element.

        """
        # All names should be None; or no names should be None
        assert (all(name is not None for name, val in self._key_info) or
                all(name is None for name, val in self._key_info)), \
                        self._key_info
        return self._key_info[0][0] is not None

    def _has_key_info(self):
        """Utility to determine whether this element has key information."""
        return len(self._key_info) > 0

    def _is_wildcard_all(self):
        """Utility to determine if the key info WILDCARD_ALL."""
        assert self._has_key_info()
        assert ((self._key_info[0][1] is not defs.WILDCARD_ALL) ^
                (self._key_info == [(None, defs.WILDCARD_ALL)]))
        return self._key_info[0][1] is defs.WILDCARD_ALL

    _LITERAL_CHARS = set(string.ascii_letters +
                         string.digits +
                         string.punctuation + ' ')
    _ESCAPED_CHARS = {
        '"': '\\"',
        '\\': '\\\\',
        '\a': '\\a',
        '\b': '\\b',
        '\f': '\\f',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\v': '\\v',
    }
    _LITERAL_CHARS = set(string.ascii_letters +
                         string.digits +
                         string.punctuation + ' ') - set(_ESCAPED_CHARS.keys())
    @staticmethod
    def _encode_char(c):
        if c in PathElement._LITERAL_CHARS:
            out = c
        elif c in PathElement._ESCAPED_CHARS:
            out = PathElement._ESCAPED_CHARS[c]
        else:
            out = "\\x{:02x}".format(ord(c))
        return  out

    @staticmethod
    def _encode_string(s):
        """Encode a string, as it would appear in a path string."""
        return '"{}"'.format(''.join(PathElement._encode_char(c) for c in s))

    @staticmethod
    def _encode_scalar(val):
        """
        Encode a scalar, as it would appear in a path string.

        For all but strings (and unknown types that are implicitly converted to
        strings) this is equivalent to JSON. Strings (and unknown types) are
        encoded as Python string literals.

        """
        # Arrays / objects are converted in self.__str__
        assert (isinstance(val, type('')) or
                not isinstance(val, (collections.Mapping,
                                     collections.Sequence)))

        if isinstance(val, type('')):
            out = PathElement._encode_string(val)
        elif val is None or isinstance(val, (int, float, bool)):
            out = json.dumps(val)
        else:
            out = PathElement._encode_string(str(val))
        return out

    def _encode_key_val(self, val):
        """
        Encode a key value as it would appear in a path string.

        This is equivalent to a JSON encoding but with the following
        exceptions:

        - WILDCARD is encoded as an asterisk (with no quotes).

        - Objects which aren't JSON serializable are mapped through `str()`
          and then serialized.

        """
        assert val is not defs.WILDCARD_ALL
        if val is defs.WILDCARD:
            return str(val)
        return self._encode_scalar(val)

    def _repr_no_class(self):
        """Equivalent of repr, but not wrapped with "PathElement()"."""

        if self._has_key_info():
            if self._is_wildcard_all():
                key_info_str = repr(defs.WILDCARD_ALL)
            elif self._has_names():
                key_info_str = ", ".join(
                        "{}={}".format(name, repr(val))
                                               for name, val in self._key_info)
            else:
                key_info_str = ", ".join(repr(val)
                                               for name, val in self._key_info)

            out = "{}({})".format(self._name, key_info_str)
        else:
            out = self._name

        return out

    def __repr__(self):
        """See :meth:`.Path.__str__`."""
        return "{}({})".format(type(self).__name__, self._repr_no_class())

    def __str__(self):
        """See :meth:`.Path.__str__`."""
        if self._has_key_info():
            if self._is_wildcard_all():
                key_info_str = "*"
            elif self._has_names():
                key_info_str = "{{{}}}".format(
                        ", ".join("{}: {}".format(self._encode_scalar(name),
                                                  self._encode_key_val(val))
                                  for name, val in self._key_info))
            else:
                key_info_str = "[{}]".format(
                        ", ".join(self._encode_key_val(val)
                                  for name, val in self._key_info))

            out = "{}({})".format(self._name, key_info_str)
        else:
            out = self._name

        return out

    def _add_key_info(self, key_info):
        """Return a new path element with the given key information."""
        if self._has_key_info():
            raise ValueError("Path element already has key information")

        return type(self)(self.name, key_info)


RootAction = Path([PathElement("RootAction")])
RootCfg = Path([PathElement("RootCfg")])
RootOper = Path([PathElement("RootOper")])

