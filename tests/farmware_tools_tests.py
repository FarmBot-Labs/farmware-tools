#!/usr/bin/env python

'''Farmware Tools Tests.'''

from __future__ import print_function
import uuid
import json
import time
from getpass import getpass
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import requests
from farmware_tools import device, app

try:
    INPUT = raw_input
except NameError:
    INPUT = input

def get_credentials():
    'Get device_id, token, and mqtt_host from server, email, and password.'
    use_localhost = (INPUT('Use localhost? (Y/n): ') or 'Y').decode('utf-8')
    if 'y' in use_localhost.lower():
        server = 'http://localhost:3000/'
        email = 'admin@admin.com'
        password = 'password123'
    else:
        server = (INPUT('server: ') or 'https://my.farm.bot/').decode('utf-8')
        email = INPUT('account email: ').decode('utf-8')
        password = getpass('password: ')
    token_headers = {'content-type': 'application/json'}
    user = {'user': {'email': email, 'password': password.decode('utf-8')}}
    payload = json.dumps(user)
    response = requests.post(server + 'api/tokens',
                             headers=token_headers, data=payload)
    response.raise_for_status()
    token = response.json()['token']
    return {
        'device_id': token['unencoded']['bot'],
        'token': token['encoded'],
        'mqtt_host': token['unencoded']['mqtt'],
        'url': server + '/api/'
    }

def send(celery_script, credentials, rpc_id=''):
    'Send Celery Script to a device for execution.'
    publish.single(
        'bot/{}/from_clients'.format(credentials['device_id']),
        payload=json.dumps(device.rpc_wrapper(celery_script, rpc_id)),
        hostname=credentials['mqtt_host'],
        auth={
            'username': credentials['device_id'],
            'password': credentials['token']
            }
        )

def subscribe(host, user, password, callback):
    'Subscribe to the from_device channel.'
    client = mqtt.Client()
    client.username_pw_set(user, password)
    client.on_message = callback
    client.connect(host)
    client.subscribe('bot/{}/from_device'.format(user))
    client.loop_start()
    return client

class Tester(object):
    'Test device commands.'

    def __init__(self):
        print('Input account credentials for device to run tests:')
        self.login_info = get_credentials()
        self.subscribe()
        self.outgoing = {}  # {'uuid': {'kind': 'wait', 'time': 0}}
        self.incoming = {}  # {'uuid': {'status': 'ok', 'time': 9}}
        self.elasped = []

    def test(self, command):
        'Test a command on the device.'
        if command is not None:
            kind = command['kind']
            rpc_id = str(uuid.uuid4())
            send(command, self.login_info, rpc_id)
            self.outgoing[rpc_id] = {'kind': kind, 'time': time.time()}
            self.wait_for_response(kind, rpc_id)
        else:
            print('command is {}'.format(command))

    def subscribe(self):
        'Listen for responses.'
        user = self.login_info['device_id']
        host = self.login_info['mqtt_host']
        password = self.login_info['token']
        subscribe(host, user, password, self.add_response)

    def add_response(self, _client, _userdata, message):
        'Add a response to the list.'
        if 'from_device' in message.topic:
            parsed = json.loads(message.payload)
            kind = parsed['kind']
            if kind == 'rpc_ok' or kind == 'rpc_error':
                rpc_id = parsed['args']['label']
                self.incoming[rpc_id] = {
                    'status': kind.split('_')[-1], 'time': time.time()}

    def wait_for_response(self, kind, rpc_id):
        'Wait for the device response.'
        timeout_seconds = 10
        begin = time.time()
        kind = self.outgoing[rpc_id]['kind']
        out = self.outgoing[rpc_id]['time']
        while (time.time() - begin) < timeout_seconds:
            if rpc_id in self.incoming:
                status = self.incoming[rpc_id]['status']
                _in = self.incoming[rpc_id]['time']
                time_diff = _in - out
                color = device.GREEN if status == 'ok' else device.RED
                print('{}{} {}{}{} {:.2f}s'.format(
                    device.MAGENTA, kind, color, status, device.RESET,
                    time_diff))
                break
        else:
            time_diff = time.time() - out
            print('{} {}TIMEOUT{} {:.2f}s'.format(
                kind, device.RED, device.RESET, time_diff))
        self.elasped.append(time_diff)

    def print_elapsed_time(self):
        'Calculate total test time.'
        print('Total time elapsed: {:.2f}s'.format(sum(self.elasped)))

if __name__ == '__main__':
    TEST = Tester()

    # Device tests
    COORDINATE = device.assemble_coordinate(1, 1, 1)
    OFFSET = device.assemble_coordinate(0, 0, 0)
    TESTS = [
        {'command': device.log, 'args': ['hi']},
        {'command': device.check_updates, 'args': ['farmbot_os']},
        {'command': device.emergency_lock, 'args': []},
        {'command': device.emergency_unlock, 'args': []},
        {'command': device.execute, 'args': [1]},
        {'command': device.execute_script, 'args': ['take-photo']},
        {'command': device.find_home, 'args': ['x']},
        {'command': device.home, 'args': ['z']},
        {'command': device.install_farmware, 'args': ['farmware_url']},
        {'command': device.install_first_party_farmware, 'args': []},
        {'command': device.move_absolute, 'args': [COORDINATE, 100, OFFSET]},
        {'command': device.move_relative, 'args': [0, 0, 0, 100]},
        {'command': device.read_pin, 'args': [1, 'label', 1]},
        {'command': device.read_status, 'args': []},
        {'command': device.register_gpio, 'args': [1, 1]},
        {'command': device.remove_farmware, 'args': ['farmware']},
        {'command': device.set_pin_io_mode, 'args': [0, 47]},
        {'command': device.set_servo_angle, 'args': [4, 1]},
        {'command': device.sync, 'args': []},
        {'command': device.take_photo, 'args': []},
        {'command': device.toggle_pin, 'args': [1]},
        {'command': device.unregister_gpio, 'args': [1]},
        {'command': device.update_farmware, 'args': ['take-photo']},
        {'command': device.wait, 'args': [100]},
        {'command': device.write_pin, 'args': [1, 1, 1]},
        {'command': device.zero, 'args': ['y']},
    ]

    print()
    RUN = INPUT('Run device tests? (Y/n) ') or 'y'
    if RUN.lower() == 'y':
        for test in TESTS:
            TEST.test(test['command'](*test['args']))
        print('=' * 20)
        TEST.print_elapsed_time()
        print()

    # App tests
    TIMESTAMP = str(int(time.time()))
    def app_login():
        'Return app login info.'
        mqtt_login = TEST.login_info
        return mqtt_login['token'], mqtt_login['url']
    RUN = INPUT('Run app tests? (Y/n) ') or 'y'
    if RUN.lower() == 'y':
        app.log('hi', get_info=app_login)
        app.get('sensors', get_info=app_login)
        app.post('tools', {'name': 'test_tool_' + TIMESTAMP}, get_info=app_login)
        app.download_plants(get_info=app_login)
        app.add_plant(100, 100, get_info=app_login)
