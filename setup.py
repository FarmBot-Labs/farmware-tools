#!/usr/bin/env python

"""Farmware Tools package setup."""

from setuptools import setup

with open('README.md') as f:
    README = f.read()

if __name__ == '__main__':
    setup(name='farmware_tools',
          version='0.2.0',
          description='Tools for use by Farmware.',
          long_description=README,
          url='https://github.com/FarmBot-Labs/farmware-tools',
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
