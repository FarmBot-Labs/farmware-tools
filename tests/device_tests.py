#!/usr/bin/env python

'''Farmware Tools Tests: device'''

from __future__ import print_function
import time
from farmware_tools import app, device

def run_tests(TEST, app_login):
    'Run device tests.'
    COORDINATE = device.assemble_coordinate(1, 0, 1)
    OFFSET = device.assemble_coordinate(0, 0, 0)
    URL = 'https://raw.githubusercontent.com/FarmBot-Labs/farmware_manifests/' \
        'master/packages/take-photo/manifest.json'
    app.post('sequences', {'name': 'test', 'body': []}, get_info=app_login)
    SEQUENCE = app.find_sequence_by_name(name='test', get_info=app_login)
    TESTS = [
        {'command': device.log, 'kwargs': {'message': 'hi'}},
        {'command': device.log,
         'kwargs': {'message': 'hi', 'channels': ['toast']}},
        {'command': device.log,
         'kwargs': {'message': 'hi', 'rpc_id': 'abcd'}},
        {'command': device.check_updates,
         'kwargs': {'package': 'farmbot_os'}},
        {'command': device.emergency_lock, 'kwargs': {},
         'expected': {'status': [{
             'keys': ['informational_settings', 'locked'],
             'value': True}]}},
        {'command': device.emergency_unlock, 'kwargs': {},
         'expected': {'log': ['F09'], 'status': [{
             'keys': ['informational_settings', 'locked'],
             'value': False}]}},
        {'command': device.execute, 'kwargs': {'sequence_id': SEQUENCE}},
        {'command': device.execute_script,
         'kwargs': {
             'label': 'take-photo',
             'inputs': {'input_1': 1, 'take_photo_input_2': 'two'}}},
        {'command': device.run_farmware, 'kwargs': {'label': 'take-photo'}},
        {'command': device.find_home, 'kwargs': {'axis': 'y'},
         'expected': {'log': ['F12']}},
        {'command': device.home, 'kwargs': {'axis': 'z'},
         'expected': {'log': ['G00 Z0']}},
        {'command': device.install_farmware, 'kwargs': {'url': URL}},
        {'command': device.install_first_party_farmware, 'kwargs': {}},
        {'command': device.move_absolute,
         'kwargs': {'location': COORDINATE, 'speed': 100, 'offset': OFFSET},
         'expected': {'log': ['G00 X1.0 Y0.0 Z1.0']}},
        {'command': device.move_relative,
         'kwargs': {'x': -1, 'y': 0, 'z': -1, 'speed': 100},
         'expected': {'log': ['G00 X0.0 Y0.0 Z0.0']}},
        {'command': device.read_pin,
         'kwargs': {'pin_number': 1, 'label': 'label', 'pin_mode': 0},
         'expected': {'log': ['F42 P1 M0']}},
        {'command': device.read_status, 'kwargs': {}},
        {'command': device.remove_farmware,
         'kwargs': {'package': 'farmware'}},
        {'command': device.set_pin_io_mode,
         'kwargs': {'pin_io_mode': 0, 'pin_number': 47},
         'expected': {'log': ['F43 P47 M0']}},
        {'command': device.set_servo_angle,
         'kwargs': {'pin_number': 4, 'pin_value': 1},
         'expected': {'log': ['F61 P4 V1']}},
        {'command': device.set_user_env,
         'kwargs': {'key': 'test_key', 'value': 1}},
        {'command': device.sync, 'kwargs': {},
         'expected': {'status': [{
             'keys': ['informational_settings', 'sync_status'],
             'value': 'synced'}]}},
        {'command': device.take_photo, 'kwargs': {}},
        {'command': device.toggle_pin, 'kwargs': {'pin_number': 1},
         'expected': {'log': ['F41 P1 V']}},
        {'command': device.update_farmware,
         'kwargs': {'package': 'take-photo'}},
        {'command': device.wait, 'kwargs': {'milliseconds': 100}},
        {'command': device.write_pin,
         'kwargs': {'pin_number': 1, 'pin_value': 1, 'pin_mode': 0},
         'expected': {'log': ['F41 P1 V1 M0'], 'status': [{
             'keys': ['pins', '1', 'value'],
             'value': 1}]}},
        {'command': device.zero, 'kwargs': {'axis': 'y'},
         'expected': {'log': ['F84 Y1'], 'status': [
             {'keys': ['location_data', 'position', 'y'], 'value': 0},
             {'keys': ['location_data', 'scaled_encoders', 'y'], 'value': 0}
             ]}},
    ]
    TEST.setup()
    for test in TESTS:
        try:
            _rpc_id = test['kwargs'].pop('rpc_id')
        except KeyError:
            _rpc_id = None
        print()
        time.sleep(3)
        TEST.test(test['command'](**test['kwargs'])['command'],
                  rpc_id=_rpc_id, expected=test.get('expected'))
    print('=' * 20)
    TEST.print_elapsed_time()
    print()
    TEST.teardown()
    TEST.print_summary()
