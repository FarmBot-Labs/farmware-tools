#!/usr/bin/env python

'''Farmware Tools Tests: env'''

from __future__ import print_function
from farmware_tools.env import Env

def _version_compare_test(current, required, expected):
    ENV = Env()
    ENV.fbos_version = current
    result = ENV.fbos_at_least(*required)
    test_result = result == expected
    assert test_result
    test = 'pass' if test_result else 'fail'
    required_version = '.'.join([str(part) for part in required])
    print('{} >= {}: {} ({})'.format(current, required_version, result, test))

LESS = [[7, 0, 2], [8, 0, 0], [8, 0, 2], [7, 1], [7, 2], [8, 0], [8, 2], [8]]
OK = [
    [7, 0, 1],
    [7, 0, 0],
    [6, 0, 2],
    [6, 3, 1],
    [6, 0, 0],
    [7, 0], [6, 2], [6, 1], [6, 0],
    [7], [6],
    ]

def run_tests():
    'Run env tests.'
    for requirement_met in OK:
        _version_compare_test('7.0.1', requirement_met, True)
    for requirement_not_met in LESS:
        _version_compare_test('7.0.1', requirement_not_met, False)
    _version_compare_test('V7.0.11-rc1', [7, 0, 11], True)

if __name__ == '__main__':
    run_tests()
