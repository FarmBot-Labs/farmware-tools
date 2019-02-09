#!/usr/bin/env python

'''Farmware Tools Tests: get_config_value'''

from __future__ import print_function
import os
from farmware_tools import get_config_value

def _test_get_config(farmware, config, type_, expected):
    def _get_state():
        return {'process_info': {'farmwares': {
            'Farmware Name': {'config': [{'name': 'twenty', 'value': 20}]}}}}
    if type_ is None:
        received = get_config_value(farmware, config, _get_state=_get_state)
    else:
        received = get_config_value(farmware, config, type_, _get_state=_get_state)
    assert received == expected, 'expected {}, received {}'.format(
        repr(expected), repr(received))
    print('get_config_value result {} == {}'.format(
        repr(received), repr(expected)))

def run_tests():
    'Run get_config_value tests.'
    os.environ['farmware_name_int_input'] = '10'
    os.environ['farmware_name_str_input'] = 'ten'
    _test_get_config('farmware_name', 'int_input', None, 10)
    _test_get_config('Farmware Name', 'int_input', int, 10)
    _test_get_config('farmware-name', 'int_input', str, '10')
    _test_get_config('farmware_name', 'str_input', str, 'ten')
    _test_get_config('Farmware Name', 'twenty', None, 20)  # default value
    os.environ['farmware_name_twenty'] = 'twenty'
    _test_get_config('Farmware Name', 'twenty', str, 'twenty')  # set value

if __name__ == '__main__':
    run_tests()
