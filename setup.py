#!/usr/bin/env python
# coding: utf8

VERSION = '0.1.1'

import sys

from setuptools import setup

extra_args = {}
if (sys.version_info[0] >= 3):
    extra_args['use_2to3'] = True

setup(name='pybacktest',
      version=VERSION,
      description='pybacktest',
      author='Matvey Ezhov',
      url='https://github.com/ematvey/pybacktest',
      packages=['pybacktest'],
      install_requires=['numpy>=1.11',
                        'pandas>=0.19',
                        'pyyaml',
                        'cached_property'],
      **extra_args)
