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
    def fbos_major():
        'Get the FarmBot OS major version integer.'
        return int(FBOS_VERSION[0])

    def farmware_api_available(self):
        'Determine if the Farmware API is available.'
        return os.getenv('FARMWARE_URL') is not None and self.token is not None
