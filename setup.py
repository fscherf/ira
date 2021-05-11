#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from ira import VERSION_STRING

setup(
    include_package_data=True,
    name='ira',
    version=VERSION_STRING,
    author='Florian Scherf',
    url='https://github.com/fscherf/ira',
    author_email='f.scherf@pengutronix.de',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'aiohttp>=3,<4',
        'pytest-aiohttp',
        'pytest-print',
        'jinja2',
        'requests',
    ],
    scripts=[
    ],
    entry_points={
    },
)
