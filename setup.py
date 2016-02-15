#!/usr/bin/env python

from distutils.core import setup

setup(name='xrm2m',
      version='1.0',
      description='XR Machine-to-machine Python API',
      author='Matthew Earl',
      author_email='maearl@cisco.com',
      url='https://github.com/cisco/xr-telemetry-m2m-lib',
      packages=[
          'xrm2m',
          'xrm2m._shared',
          'xrm2m.tests',
          'xrm2m.tests.shared',
      ],
     )

