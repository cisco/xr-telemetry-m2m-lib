# IOS-XR Machine-to-machine Python API

## Introduction

This project provides a Python interface for accessing and modifying
manageability data on an IOS-XR router.

## Getting going

### Dependencies

The interface has the following requirements:

  * Python 2 (>= 2.7) *or* Python 3 (>= 3.4).
  * The `trollius` and `enum34` packages if using Python 2.
  * The `paramiko` package.

### Installing xrm2m

Once the dependencies have been satisfied run `setup.py` to install the `xrm2m`
module:

    ./setup.py install

### SSH setup

In order to use the library SSH must be configured on the target router, and
SSH keys from the connecting machine installed (for this you'll need the `k9`
image):

  1. Configure an SSH server (on the router):

    `conf
    int Mgmt 0/0/CPU0/0
    no shut
    ipv4 addr dhcp
    ssh server
    commit`

  2. Generate an SSH fingerprint (on the router):

    `crypto key generate dsa`

  3. Generate a 1024-bit RSA key (on the server):

    `cd ~/.ssh
    ssh-keygen -b 1024 -t rsa -f <key-name>`

  4. Create a base64-decoded binary public key for the router (on the server):

    `cut -d" " -f2 <key-name>.pub | base64 -d > <key-name>.pub.b64`

  5. Copy the public key onto the router (on the server), e.g.

    `scp -o PreferredAuthentications=password -o PubkeyAuthentication=no ~/.ssh/<key-name>.pub.b64 <user>@<router-ip>:/disk0:`

  6. Import the public key (on the router), e.g.

    `crypto key import auth rsa disk0:/<key-name>.pub.b64`

### Using the library

You should now be able to connect to the IOS-XR router like so:

    from xrm2m import *
    conn = connect(SSHTransport("<rouer-ip>",
                                "<user>",
                                key_filename="<key-name>"))
    conn.get_version()

[Full documentation is available here.](https://rawgit.com/cisco/xr-telemetry-m2m-lib/master/doc/html/index.html)


