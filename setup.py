#!/usr/bin/env python
# coding: utf8

from setuptools import setup

VERSION = '0.2'

setup(
    name='pybacktest',
    version=VERSION,
    description='pybacktest',
    author='Matvey Ezhov',
    url='https://github.com/ematvey/pybacktest',
    py_modules=['pybacktest'],
    install_requires=['numpy', 'pandas>=0.17', 'pandas-datareader>=0.2.0'],
)
