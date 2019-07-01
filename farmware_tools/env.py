#!/usr/bin/env python

'''Farmware Tools: ENV vars.'''

import os

# Farmware API ENV variables
FARMWARE_API_PREFIX = 'FARMWARE_API_V2_'
REQUEST_PIPE = os.getenv(FARMWARE_API_PREFIX + 'REQUEST_PIPE')
RESPONSE_PIPE = os.getenv(FARMWARE_API_PREFIX + 'RESPONSE_PIPE')

# FarmBot OS ENV variables
FARMBOT_OS_PREFIX = 'FARMBOT_OS_'
IMAGES_DIR = os.getenv(FARMBOT_OS_PREFIX + 'IMAGES_DIR')
LEGACY_IMAGES_DIR = os.getenv('IMAGES_DIR')
FBOS_VERSION = os.getenv(FARMBOT_OS_PREFIX + 'VERSION', '0')
BOT_STATE_DIR = os.getenv(FARMBOT_OS_PREFIX + 'STATE_DIR')

# FarmBot API ENV variables
FARMBOT_API_PREFIX = 'FARMBOT_API_'
TOKEN = os.getenv(FARMBOT_API_PREFIX + 'TOKEN')
LEGACY_TOKEN = os.getenv('API_TOKEN')

class Env(object):
    'Farmware environment variables.'

    def __init__(self):
        self.request_pipe = REQUEST_PIPE
        self.response_pipe = RESPONSE_PIPE
        self.images_dir = IMAGES_DIR or LEGACY_IMAGES_DIR
        self.fbos_version = FBOS_VERSION
        self.bot_state_dir = BOT_STATE_DIR
        self.token = TOKEN or LEGACY_TOKEN

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

    def use_v2(self):
        'Determine if the v2 API should be used.'
        return self.fbos_at_least(8)

    def farmware_api_available(self):
        'Determine if the Farmware API is available.'
        if self.use_v2():
            return self.request_pipe is not None and self.response_pipe is not None
        return os.getenv('FARMWARE_URL') is not None and self.token is not None
