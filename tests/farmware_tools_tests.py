#!/usr/bin/env python

'''Farmware Tools Tests.'''

from __future__ import print_function
import os
import uuid
import json
import time
from getpass import getpass
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import requests
from farmware_tools import device, app, get_config_value, aux

COLOR = aux.Color()

try:
    INPUT = raw_input
except NameError:
    INPUT = input

def _decode(_input):
    try:
        return _input.decode()
    except AttributeError:
        return _input

def get_credentials():
    'Get device_id, token, and mqtt_host from server, email, and password.'
    use_localhost = _decode(INPUT('Use localhost? (Y/n): ') or 'Y')
    if 'y' in use_localhost.lower():
        server = 'http://localhost:3000/'
        email = 'admin@admin.com'
        password = 'password123'
    else:
        server = _decode(INPUT('server: ') or 'https://my.farm.bot/')
        email = _decode(INPUT('account email: '))
        password = getpass('password: ')
    token_headers = {'content-type': 'application/json'}
    user = {'user': {'email': email, 'password': _decode(password)}}
    payload = json.dumps(user)
    response = requests.post(server + 'api/tokens',
                             headers=token_headers, data=payload)
    response.raise_for_status()
    token = response.json()['token']
    return {
        'device_id': token['unencoded']['bot'],
        'token': token['encoded'],
        'mqtt_host': token['unencoded']['mqtt'],
        'url': server + '/api/'}

def send(celery_script, credentials, rpc_id=''):
    'Send Celery Script to a device for execution.'
    publish.single(
        'bot/{}/from_clients'.format(credentials['device_id']),
        payload=json.dumps(device.rpc_wrapper(celery_script, rpc_id)),
        hostname=credentials['mqtt_host'],
        auth={
            'username': credentials['device_id'],
            'password': credentials['token']})

def subscribe(host, user, password, channel, callback):
    'Subscribe to the from_device channel.'
    client = mqtt.Client()
    client.username_pw_set(user, password)
    client.on_message = callback
    client.connect(host)
    client.subscribe(channel)
    client.loop_start()
    return client

def _new_uuid(label=''):
    return str(uuid.uuid4())[:-len(label)] + label

LOG_FW_CMD_CONFIG_KEY = 'firmware_output_log'

class Tester(object):
    'Test device commands.'

    def __init__(self):
        print('Input account credentials for device to run tests:')
        self.login_info = get_credentials()
        self.subscribe()
        self.outgoing = {}  # {'uuid': {'kind': 'wait', 'time': 0}}
        self.incoming = {}  # {'uuid': {'status': 'ok', 'time': 9}}
        self.all_client_comms = {}  # {'uuid': 'kind'}
        self.elapsed = []
        self.logs_string = ''
        self.verbose = True

    def setup(self):
        'Pre-test config.'
        print('-' * 50)
        print('TEST SETUP:')
        app.put('fbos_config', payload={LOG_FW_CMD_CONFIG_KEY: True},
                get_info=app_login)
        self.wait_for_log(LOG_FW_CMD_CONFIG_KEY)
        print('-' * 50)

    def tear_down(self):
        'Post-test config.'
        print('-' * 50)
        print('TEST TEAR DOWN:')
        app.put('fbos_config', payload={LOG_FW_CMD_CONFIG_KEY: False},
                get_info=app_login)
        self.wait_for_log(LOG_FW_CMD_CONFIG_KEY)
        print('-' * 50)

    def test(self, command, expected_log=None, rpc_id=None):
        'Test a command on the device.'
        if command is not None:
            kind = command['kind']
            self.logs_string = ''
            rpc_test_id = _new_uuid('test') if rpc_id is None else rpc_id
            send(command, self.login_info, rpc_test_id)
            self.outgoing[rpc_test_id] = {'kind': kind, 'time': time.time()}
            self.wait_for_response(kind, rpc_test_id)
            if expected_log is not None:
                self.wait_for_log(expected_log)
        else:
            print('command is {}'.format(command))

    def _get_channel_name(self, topic):
        return 'bot/{}/{}'.format(self.login_info['device_id'], topic)

    def subscribe(self):
        'Listen for responses.'
        user = self.login_info['device_id']
        host = self.login_info['mqtt_host']
        password = self.login_info['token']
        response_channel = self._get_channel_name('from_device')
        subscribe(host, user, password, response_channel, self.add_response)
        client_channel = self._get_channel_name('from_clients')
        subscribe(host, user, password, client_channel, self.add_client_comm)
        log_channel = self._get_channel_name('logs')
        subscribe(host, user, password, log_channel, self.add_log_message)

    def add_response(self, _client, _userdata, message):
        'Add a response to the list.'
        if 'from_device' in message.topic:
            parsed = json.loads(message.payload.decode())
            kind = parsed['kind']
            if kind == 'rpc_ok' or kind == 'rpc_error':
                rpc_id = parsed['args']['label']
                if rpc_id != 'ping':
                    self.incoming[rpc_id] = {
                        'status': kind.split('_')[-1], 'time': time.time()}

    def add_log_message(self, _client, _userdata, message):
        'Add log message string to the list.'
        if 'logs' in message.topic:
            parsed = json.loads(message.payload.decode())
            message = parsed['message']
            self.logs_string += message

    def add_client_comm(self, _client, _userdata, message):
        'Add from_clients message to the list.'
        if 'from_clients' in message.topic:
            parsed = json.loads(message.payload.decode())
            rpc_id = parsed['args']['label']
            try:
                kind = parsed['body'][0]['kind']
            except (KeyError, TypeError):
                pass
            else:
                self.all_client_comms[rpc_id] = kind

    def wait_for_log(self, string):
        'Wait for a specific log message string.'
        begin = time.time()
        while (time.time() - begin) < 10:
            if string in self.logs_string:
                print('{}`{}`{} spotted in logs.'.format(
                    COLOR.bold, string, COLOR.reset))
                break
        else:
            time_diff = time.time() - begin
            print('{}TIMEOUT{} waiting for `{}` in logs {:.2f}s'.format(
                COLOR.red, COLOR.reset, string, time_diff))
        print()

    def wait_for_response(self, kind, rpc_id):
        'Wait for the device response.'
        timeout_seconds = 10
        begin = time.time()
        kind = self.outgoing[rpc_id]['kind']
        print_kind = '' if self.verbose else COLOR.magenta + kind + ' '
        out = self.outgoing[rpc_id]['time']
        while (time.time() - begin) < timeout_seconds:
            if rpc_id in self.incoming:
                status = self.incoming[rpc_id]['status']
                _in = self.incoming[rpc_id]['time']
                time_diff = _in - out
                color = COLOR.green if status == 'ok' else COLOR.red
                print('{}{}{}{} {:.2f}s'.format(
                    print_kind, color, status, COLOR.reset, time_diff))
                if self.verbose:
                    print()
                break
        else:
            time_diff = time.time() - out
            print('{}{}TIMEOUT{} {:.2f}s'.format(
                print_kind, COLOR.red, COLOR.reset, time_diff))
            if self.verbose:
                print()
        self.elapsed.append(time_diff)

    def print_elapsed_time(self):
        'Calculate total test time.'
        print('Total time elapsed: {:.2f}s'.format(sum(self.elapsed)))

    def print_summary(self):
        'Print test summary data table.'
        table = '{:<40}{:<30}{:<10}{:>12}'
        titles = ['uuid', 'kind', 'status', 'elapsed (ms)']
        print(table.format(*titles))
        underline = table.format(*['-' * 7 for _ in titles])
        print(underline)
        summary = {}
        for rpc_uuid, in_data in self.incoming.items():
            data = {}
            data['uuid'] = rpc_uuid
            try:
                data['kind'] = self.outgoing[rpc_uuid]['kind']
                out_time = self.outgoing[rpc_uuid]['time']
            except KeyError:  # not found in outgoing RPCs
                try:  # check all client RPCs
                    data['kind'] = self.all_client_comms[rpc_uuid]
                except KeyError:
                    data['kind'] = ' '
                data['elapsed'] = ' '
            else:
                elapsed_time_float = (in_data['time'] - out_time) * 1000
                data['elapsed'] = str(int(round(elapsed_time_float)))
            data['status'] = in_data['status']
            summary[self.incoming[rpc_uuid]['time']] = data
        in_times = sorted([rpc_in['time'] for rpc_in in self.incoming.values()])
        for in_time in in_times:
            data = summary[in_time]
            print(table.format(
                data['uuid'], data['kind'], data['status'], data['elapsed']))
        print(underline)
        all_ok = all(d['status'] == 'ok' for u, d in self.incoming.items())
        print(table.format(
            'count:', len(self.incoming),
            'ok' if all_ok else 'error',
            int(round(sum(self.elapsed) * 1000))))
        print()

if __name__ == '__main__':
    TEST = Tester()
    def app_login():
        'Return app login info.'
        mqtt_login = TEST.login_info
        return {
            'token': mqtt_login['token'],
            'url': mqtt_login['url'],
            'verbose': True
        }

    # Device tests
    COORDINATE = device.assemble_coordinate(1, 1, 1)
    OFFSET = device.assemble_coordinate(0, 0, 0)
    URL = 'https://raw.githubusercontent.com/FarmBot-Labs/farmware_manifests/' \
        'master/packages/take-photo/manifest.json'
    SEQUENCE = app.find_sequence_by_name(name='test', get_info=app_login)
    TESTS = [
        {'command': device.log, 'kwargs': {'message': 'hi'}},
        {'command': device.log, 'kwargs': {'message': 'hi', 'rpc_id': 'abcd'}},
        {'command': device.check_updates, 'kwargs': {'package': 'farmbot_os'}},
        {'command': device.emergency_lock, 'kwargs': {}},
        {'command': device.emergency_unlock, 'kwargs': {},
         'expected': {'log': 'F09'}},
        {'command': device.execute, 'kwargs': {'sequence_id': SEQUENCE}},
        {'command': device.execute_script, 'kwargs': {'label': 'take-photo'}},
        {'command': device.find_home, 'kwargs': {'axis': 'x'},
         'expected': {'log': 'F11'}},
        {'command': device.home, 'kwargs': {'axis': 'z'},
         'expected': {'log': 'G00 Z0'}},
        {'command': device.install_farmware, 'kwargs': {'url': URL}},
        {'command': device.install_first_party_farmware, 'kwargs': {}},
        {'command': device.move_absolute,
         'kwargs': {'location': COORDINATE, 'speed': 100, 'offset': OFFSET},
         'expected': {'log': 'G00 X1.0 Y1.0 Z1.0'}},
        {'command': device.move_relative,
         'kwargs': {'x': 0, 'y': 0, 'z': 0, 'speed': 100},
         'expected': {'log': 'G00 X1.0 Y1.0 Z0.0'}},
        {'command': device.read_pin,
         'kwargs': {'pin_number': 1, 'label': 'label', 'pin_mode': 0},
         'expected': {'log': 'F42 P1 M0'}},
        {'command': device.read_status, 'kwargs': {}},
        {'command': device.register_gpio,
         'kwargs': {'pin_number': 1, 'sequence_id': SEQUENCE}},
        {'command': device.remove_farmware, 'kwargs': {'package': 'farmware'}},
        {'command': device.set_pin_io_mode,
         'kwargs': {'pin_io_mode': 0, 'pin_number': 47},
         'expected': {'log': 'F43 P47 M0'}},
        {'command': device.set_servo_angle,
         'kwargs': {'pin_number': 4, 'pin_value': 1},
         'expected': {'log': 'F61 P4 V1'}},
        {'command': device.sync, 'kwargs': {}},
        {'command': device.take_photo, 'kwargs': {}},
        {'command': device.toggle_pin, 'kwargs': {'pin_number': 1},
         'expected': {'log': 'F41 P1 V'}},
        {'command': device.unregister_gpio, 'kwargs': {'pin_number': 1}},
        {'command': device.update_farmware, 'kwargs': {'package': 'take-photo'}},
        {'command': device.wait, 'kwargs': {'milliseconds': 100}},
        {'command': device.write_pin,
         'kwargs': {'pin_number': 1, 'pin_value': 1, 'pin_mode': 0},
         'expected': {'log': 'F41 P1 V1 M0'}},
        {'command': device.zero, 'kwargs': {'axis': 'y'},
         'expected': {'log': 'F84 Y1'}},
    ]

    print()
    RUN = INPUT('Run device tests? (Y/n) ') or 'y'
    if RUN.lower() == 'y':
        TEST.setup()
        for test in TESTS:
            try:
                _rpc_id = test['kwargs'].pop('rpc_id')
            except KeyError:
                _rpc_id = None
            try:
                _expected_log = test['expected']['log']
            except KeyError:
                _expected_log = None
            TEST.test(test['command'](**test['kwargs']),
                      rpc_id=_rpc_id, expected_log=_expected_log)
        print('=' * 20)
        TEST.print_elapsed_time()
        print()
        TEST.tear_down()
        TEST.print_summary()

    # App tests
    TIMESTAMP = str(int(time.time()))
    RUN = INPUT('Run app tests? (Y/n) ') or 'y'
    if RUN.lower() == 'y':
        print(app.log('hi', get_info=app_login))
        print(app.request('GET', 'tools', get_info=app_login))
        print(app.get('sensors', get_info=app_login))
        TOOL = app.post('tools', payload={'name': 'test_tool_' + TIMESTAMP},
                        get_info=app_login)
        print(TOOL)
        TOOL_ID = TOOL['id']
        print(app.put('tools', TOOL_ID,
                      payload={'name': 'test_tool_edit_' + TIMESTAMP},
                      get_info=app_login))
        print(app.delete('tools', TOOL_ID, get_info=app_login))
        print(app.search_points({'pointer_type': 'Plant'}, get_info=app_login))
        print(app.get_points(get_info=app_login))
        print(app.get_plants(get_info=app_login))
        print(app.get_toolslots(get_info=app_login))
        print(app.get_property('device', 'name', get_info=app_login))
        print(app.download_plants(get_info=app_login))
        PLANT = app.add_plant(x=100, y=100, get_info=app_login)
        print(PLANT)
        PLANT_ID = PLANT['id']
        print(app.delete('points', PLANT_ID, get_info=app_login))
        PLANT2 = app.add_plant(x=10, y=20, z=30, radius=10, openfarm_slug='mint',
                               name='test', get_info=app_login)
        print(PLANT2)
        print(app.delete('points', PLANT2['id'], get_info=app_login))
        print(app.find_sequence_by_name(name='test', get_info=app_login))
        print()

    # Other tests
    def _print_header(text):
        print()
        print(text)
        print('-' * 35)
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
    os.environ['farmware_name_int_input'] = '10'
    os.environ['farmware_name_str_input'] = 'ten'
    _print_header('farmware_tools.get_config_value():')
    _test_get_config('farmware_name', 'int_input', None, 10)
    _test_get_config('Farmware Name', 'int_input', int, 10)
    _test_get_config('farmware-name', 'int_input', str, '10')
    _test_get_config('farmware_name', 'str_input', str, 'ten')
    _test_get_config('Farmware Name', 'twenty', None, 20)  # default value
    os.environ['farmware_name_twenty'] = 'twenty'
    _test_get_config('Farmware Name', 'twenty', str, 'twenty')  # set value

    def _test_get_value(func, key, expected):
        def _get_state():
            return {
                'location_data': {'position': {'y': 1, 'z': 0}},
                'pins': {'13': {'value': 1}}}
        value = func(key, _get_bot_state=_get_state)
        assert value == expected
        print('`{}` value {} == {}'.format(key, value, expected))
    _print_header('device.get_current_position():')
    _test_get_value(device.get_current_position, 'all', {'y': 1, 'z': 0})
    _test_get_value(device.get_current_position, 'x', None)
    _test_get_value(device.get_current_position, 'y', 1)
    _print_header('device.get_pin_value():')
    _test_get_value(device.get_pin_value, 14, None)
    _test_get_value(device.get_pin_value, 13, 1)
    print()
    print('tests complete.')
