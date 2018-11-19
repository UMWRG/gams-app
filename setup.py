#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='hydra-python',
    version='0.1',
    description='Hydra client applications and library for importing hydra network to gams-compatible input files, running gams model and importing results contained int the GDX file format.',
    packages=find_packages(),
    include_package_data=True,
    entry_points='''
    [console_scripts]
    hydra-gams=hydra_gams.cli:start_cli
    ''',
)
