#!/usr/bin/env python
# coding: utf8

VERSION = '0.1'

import sys
import os
from setuptools import setup, find_packages
from setuptools.extension import Extension

extra_args = {}
if (sys.version_info[0] >= 3):
    extra_args['use_2to3'] = True


setup(name='pybacktest',
      version=VERSION,
      description='pybacktest',
      author='Matvey Ezhov',
      url='https://github.com/ematvey/pybacktest',
      packages=['pybacktest'],
      install_requires=['numpy', 'pandas>=0.11', 'pyyaml'],
      **extra_args
      )
