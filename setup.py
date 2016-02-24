#!/usr/bin/env python

from setuptools import setup

version = '1.0.0'

# required = open('requirements.txt').read().split('\n')

setup(
    name='ixstools',
    version=version,
    description=' ',
    author='ericdill',
    author_email='edill@bnl.gov',
    url='https://github.com/NSLS-II-IXS/ixstools',
    packages=['ixstools'],
    entry_points={
    'console_scripts': [
      'align = ixstools.align:main'
    ]},
    # install_requires=required,
    long_description='See ' + 'https://github.com/NSLS-II-IXS/ixstools',
    license='BSD'
)
