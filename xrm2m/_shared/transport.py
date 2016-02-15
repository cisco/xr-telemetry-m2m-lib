# -----------------------------------------------------------------------------
# transport.py - Transport layer
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

"""
Transport layer.

"""

__all__ = (
    'SSHTransport',
    'State',
    'Transport',
    'TransportConnectionError',
    'TransportNotConnected',
)

import abc
import enum

  

class TransportNotConnected(Exception):
    """
    Raised if an operation was attempted on a transport when not connected.

    """


class TransportConnectionError(Exception):
    """
    Raised if a :class:`.Transport`'s connect method failed.

    """


class State(enum.Enum):
    """
    Enumeration of transport connection states.

    .. attribute:: DISCONNECTED

        The transport is not connected, and no connection is in progress.

    .. attribute:: CONNECTING
        
        The transport is connecting, but has not yet connected.

    .. attribute:: CONNECTED

        The transport is connected, and is ready for I/O operations.

    """
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2


class Transport(object):
    """
    Abstract transport definition.

    """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self._loop = None

    @abc.abstractmethod
    def connect(self, loop):
        """
        Asynchronously connect to the transport.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self):
        """
        Asynchronously disconnect from the transport.

        This method can be called from any :class:`.State`:

        - `DISCONNECTED`: Nothing is done.

        - `CONNECTING`: Wait for the connection to be established, or fail to
          be established. In the former case tear down the connection as well.

        - `CONNECTED`:  Tear down the connection.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data):
        """
        Write a sequence of bytes to the transport. This method is
        synchronous, but in general non-blocking (data is added to a buffer).

        :param data:
            Bytes to be written to the transport.

        """
        raise NotImplementedError

    @abc.abstractmethod
    def read(self):
        """
        Asynchronously read bytes from the transport.

        :return:
            Bytes read from the transport.

        """
        raise NotImplementedError

    @abc.abstractproperty
    def state(self):
        """
        Indicate the transport's connection state.

        :return:
            A :class:`.State`.

        """


class SSHTransport(Transport):
    """
    Transport that defines a connection to a router over SSH.

    """
    def __init__(self, hostname, username, key_filename=None, password=None,
                 port=22, look_for_keys=True, allow_agent=True):
        """
        Initialize the SSHTransport.

        The transport authenticates using the following steps:

        .. Using the private key file provided by the `key_filename` argument,
           if present.  If the key file is passphrase protected then `password`
           is used to decrypt it.

        .. Using any key added to the locally running `ssh-agent`, if
           `ssh-agent` is True.

        .. Using `~/.ssh/id_rsa`, `~/.ssh/id_dsa` or `~/.ssh/.id_ecdsa`.

        .. Plain username/password authentication, if `password` was provided.

        :param hostname:
            Host being connected to.

        :param port:
            Port to connect to.

        :param username:
            Username to authenticate as.

        :param key_filename:
            The filename, or list of filenames of optional private key(s) to
            try for authentication

        :param password:
            Optional password. This will be used if `key_filename` is not
            passed, or if the private key is protected by a pass-phrase.

        :param look_for_keys:
            Search for discoverable private key files in `~/.ssh/`.

        :param allow_agent:
            Allow connecting to an SSH agent.

        """
        raise NotImplementedError

