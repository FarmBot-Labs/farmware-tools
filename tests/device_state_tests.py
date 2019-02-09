#!/usr/bin/env python

'''Farmware Tools Tests: bot state'''

from __future__ import print_function
from farmware_tools import device

def _test_get_value(func, key, expected):
    def _get_state():
        return {
            'location_data': {'position': {'y': 1, 'z': 0}},
            'pins': {'13': {'value': 1}}}
    value = func(key, _get_bot_state=_get_state)
    assert value == expected
    print('`{}` value {} == {}'.format(key, value, expected))

def run_position_tests():
    'Run get_current_position tests.'
    _test_get_value(device.get_current_position, 'all', {'y': 1, 'z': 0})
    _test_get_value(device.get_current_position, 'x', None)
    _test_get_value(device.get_current_position, 'y', 1)

def run_pin_value_tests():
    'Run get_pin_value tests.'
    _test_get_value(device.get_pin_value, 14, None)
    _test_get_value(device.get_pin_value, 13, 1)

if __name__ == '__main__':
    run_position_tests()
    run_pin_value_tests()
