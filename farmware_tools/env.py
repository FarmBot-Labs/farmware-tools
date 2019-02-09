#!/usr/bin/env python

'''Farmware Tools: ENV vars.'''

import os

# FarmBot OS ENV variables
FARMBOT_OS_PREFIX = 'FARMBOT_OS_'
IMAGES_DIR = os.getenv('IMAGES_DIR')
FBOS_VERSION = os.getenv(FARMBOT_OS_PREFIX + 'VERSION', '0')

# FarmBot API ENV variables
TOKEN = os.getenv('API_TOKEN')

class Env(object):
    'Farmware environment variables.'

    def __init__(self):
        self.images_dir = IMAGES_DIR
        self.fbos_version = FBOS_VERSION
        self.token = TOKEN

    @staticmethod
    def get_version_parts(version_string):
        'Get major, minor, and patch ints from version string.'
        major_minor_patch = version_string.lower().strip('v').split('-')[0]
        return [int(part) for part in major_minor_patch.split('.')]

    def fbos_at_least(self, major, minor=None, patch=None):
        'Determine if the current FBOS version meets the version requirement.'
        current_version = self.get_version_parts(self.fbos_version)
        required_version = [int(p) for p in [major, minor, patch] if p is not None]
        for part, required_version_part in enumerate(required_version):
            if current_version[part] != required_version_part:
                # Versions are not equal. Check if current meets requirement.
                return current_version[part] > required_version_part
            # Versions are equal so far.
            if required_version_part == required_version[-1]:
                # No more parts to compare. Versions are equal.
                return True

    def farmware_api_available(self):
        'Determine if the Farmware API is available.'
        return os.getenv('FARMWARE_URL') is not None and self.token is not None
