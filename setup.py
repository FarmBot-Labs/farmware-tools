#!/usr/bin/env python

"""Farmware Tools package setup."""

import os
from setuptools import setup

with open(os.path.join('farmware_tools', 'VERSION')) as version_file:
    VERSION = version_file.read().strip()

with open('README.md') as f:
    README = f.read()

if __name__ == '__main__':
    setup(name='farmware_tools',
          version=VERSION,
          description='Farmware convenience functions for use in FarmBot OS.',
          long_description=README,
          long_description_content_type='text/markdown',
          url='https://github.com/FarmBot-Labs/farmware-tools',
          project_urls={
              'FarmBot': 'https://farm.bot/'
          },
          author='FarmBot Inc.',
          license='MIT',
          author_email='farmware.tools@farm.bot',
          packages=['farmware_tools'],
          include_package_data=True,
          classifiers=[
              'Development Status :: 2 - Pre-Alpha',
              'License :: OSI Approved :: MIT License',
              'Programming Language :: Python',
          ],
          keywords=['farmbot', 'python'])
