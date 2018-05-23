'Farmware Tools imports.'

import os

with open(os.path.join(os.path.dirname(__file__), 'VERSION')) as version_file:
    VERSION = version_file.read().strip()

__version__ = VERSION

def get_config_value(farmware_name, config_name, value_type=int):
    'Get the value of a Farmware config input.'
    farmware = farmware_name.replace(' ', '_').replace('-', '_').lower()
    return value_type(os.environ['{}_{}'.format(farmware, config_name)])
