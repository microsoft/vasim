#
# --------------------------------------------------------------------------
#  Licensed under the MIT License. See LICENSE file in the project root for
#  license information.
#  Copyright (c) Microsoft Corporation.
# --------------------------------------------------------------------------
#
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='VASIM',
    version='0.1',
    packages=find_packages(),
    install_requires=requirements,
    extras_require={
        'dev': ['autopep8', 'flake8', 'pytest', 'coverage']
    }
)
