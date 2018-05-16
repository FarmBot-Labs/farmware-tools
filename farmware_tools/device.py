#!/usr/bin/env python

'''Farmware Tools: Device.'''

from __future__ import print_function
import os
import sys
import json
from functools import wraps
import requests

def _color(string):
    lookup = {'red': 31, 'magenta': 35, 'cyan': 36, 'green': 32, 'reset': 0}
    return '\033[{}m'.format(lookup[string])

GREEN = _color('green')
MAGENTA = _color('magenta')
CYAN = _color('cyan')
RED = _color('red')
RESET = _color('reset')

def _on_error():
    sys.exit(1)
    return

def _check_celery_script(command):
    try:
        kind = command['kind']
        args = command['args']
    except (KeyError, TypeError):
        _cs_error('celery script', command)
        _on_error()
    else:
        return kind, args

def _colorize_celery_script(kind, args):
    to_print = "{{'kind': '{magenta}{kind}{reset}', " \
    "'args': {cyan}{args}{reset}}}".format(
        magenta=MAGENTA, cyan=CYAN, reset=RESET, kind=kind, args=args)
    return to_print

def rpc_wrapper(command, rpc_id=''):
    'Wrap a command in `rpc_request`.'
    return {'kind': 'rpc_request', 'args': {'label': rpc_id}, 'body': [command]}

def post(endpoint, payload):
    'Post a payload to the device Farmware API.'
    try:
        url = os.environ['FARMWARE_URL']
        token = os.environ['FARMWARE_TOKEN']
    except KeyError:
        return
    else:
        response = requests.post(
            url + 'api/v1/' + endpoint,
            headers={'Authorization': 'Bearer ' + token,
                     'content-type': 'application/json'},
            data=json.dumps(payload))
        if response.status_code != 200:
            log('Invalid {} request `{}` ({})'.format(
                endpoint, payload, response.status_code), 'error')
            _on_error()
        return response

def get(endpoint):
    'Get info from the device Farmware API.'
    try:
        url = os.environ['FARMWARE_URL']
        token = os.environ['FARMWARE_TOKEN']
    except KeyError:
        return
    else:
        response = requests.get(
            url + 'api/v1/' + endpoint,
            headers={'Authorization': 'Bearer ' + token,
                     'content-type': 'application/json'})
        if response.status_code != 200:
            log('Invalid {} request ({})'.format(
                endpoint, response.status_code), 'error')
            _on_error()
        return response

def get_bot_state():
    'Get the device state.'
    bot_state = get('bot/state')
    if bot_state is None:
        _error('Device info could not be retrieved.')
        _on_error()
    else:
        return bot_state.json()

def _send(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        'Send Celery Script to the device.'
        return send_celery_script(function(*args, **kwargs))
    return wrapper

def send_celery_script(command):
    'Send a celery script command.'
    kind, args = _check_celery_script(command)
    response = post('celery_script', command)
    if response is None:
        print(_colorize_celery_script(kind, args))
    return command

def log(message, message_type='info'):
    'Send a send_message command to post a log to the Web App.'
    return send_message(message, message_type)

def _assemble(kind, args):
    'Assemble a celery script command.'
    return {'kind': kind, 'args': args}

def _error(error):
    try:
        os.environ['FARMWARE_URL']
    except KeyError:
        print(RED + error + RESET)
    else:
        log(error, 'error')

def _cs_error(kind, arg):
    try:
        os.environ['FARMWARE_URL']
    except KeyError:
        print('{red}Invalid input `{arg}` in `{kind}`{reset}'.format(
            red=RED, arg=arg, kind=kind, reset=RESET))
    else:
        log('Invalid arg `{}` for `{}`'.format(arg, kind), 'error')

def _check_arg(kind, arg, accepted):
    'Error and exit for invalid command arguments.'
    arg_ok = True
    if arg not in accepted:
        _cs_error(kind, arg)
        _on_error()
        arg_ok = False
    return arg_ok

def assemble_coordinate(coord_x, coord_y, coord_z):
    'Assemble a coordinate.'
    return {
        'kind': 'coordinate',
        'args': {'x': coord_x, 'y': coord_y, 'z': coord_z}}

def _check_coordinate(coordinate):
    coordinate_ok = True
    try:
        coordinate_ok = coordinate['kind'] == 'coordinate'
        coordinate_ok = sorted(coordinate['args'].keys()) == ['x', 'y', 'z']
    except (KeyError, TypeError):
        coordinate_ok = False
    if not coordinate_ok:
        _cs_error('coordinate', coordinate)
        _on_error()
    return coordinate_ok

@_send
def send_message(message, message_type):
    'Send command: send_message'
    kind = 'send_message'
    allowed_types = ['success', 'busy', 'warn', 'error', 'info', 'fun', 'debug']
    args_ok = _check_arg(kind, message_type, allowed_types)
    if args_ok:
        return _assemble(kind, {'message': message,
                                'message_type': message_type})

@_send
def calibrate(axis):
    'Send command: calibrate'
    kind = 'calibrate'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return _assemble(kind, {'axis': axis})

@_send
def check_updates(package):
    'Send command: check_updates'
    kind = 'check_updates'
    args_ok = _check_arg(kind, package,
                         ['farmbot_os', 'arduino_firmware', 'farmware'])
    if args_ok:
        return _assemble(kind, {'package': package})

@_send
def emergency_lock():
    'Send command: emergency_lock'
    kind = 'emergency_lock'
    return _assemble(kind, {})

@_send
def emergency_unlock():
    'Send command: emergency_unlock'
    kind = 'emergency_unlock'
    return _assemble(kind, {})

@_send
def execute(sequence_id):
    'Send command: execute'
    kind = 'execute'
    return _assemble(kind, {'sequence_id': sequence_id})

@_send
def execute_script(label):
    'Send command: execute_script'
    kind = 'execute_script'
    return _assemble(kind, {'label': label})

@_send
def factory_reset(package):
    'Send command: factory_reset'
    kind = 'factory_reset'
    args_ok = _check_arg(kind, package, ['farmbot_os', 'arduino_firmware'])
    if args_ok:
        return _assemble(kind, {'package': package})

@_send
def find_home(axis):
    'Send command: find_home'
    kind = 'find_home'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return _assemble(kind, {'axis': axis})

@_send
def home(axis):
    'Send command: home'
    kind = 'home'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return _assemble(kind, {'axis': axis})

@_send
def install_farmware(url):
    'Send command: install_farmware'
    kind = 'install_farmware'
    return _assemble(kind, {'url': url})

@_send
def install_first_party_farmware():
    'Send command: install_first_party_farmware'
    kind = 'install_first_party_farmware'
    return _assemble(kind, {})

@_send
def move_absolute(location, speed, offset):
    'Send command: move_absolute'
    kind = 'move_absolute'
    args_ok = _check_coordinate(location)
    args_ok = _check_coordinate(offset)
    args_ok = _check_arg(kind, speed, range(1, 101))
    if args_ok:
        return _assemble(kind, {'location': location,
                                'speed': speed,
                                'offset': offset})

@_send
def move_relative(x, y, z, speed):
    'Send command: move_relative'
    kind = 'move_relative'
    args_ok = _check_arg(kind, speed, range(1, 101))
    if args_ok:
        return _assemble(kind, {'x': x,
                                'y': y,
                                'z': z,
                                'speed': speed})

@_send
def power_off():
    'Send command: power_off'
    kind = 'power_off'
    return _assemble(kind, {})

@_send
def read_pin(pin_number, label, pin_mode):
    'Send command: read_pin'
    kind = 'read_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    args_ok = _check_arg(kind, pin_mode, [0, 1])
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number,
                                'label': label,
                                'pin_mode': pin_mode})

@_send
def read_status():
    'Send command: read_status'
    kind = 'read_status'
    return _assemble(kind, {})

@_send
def reboot():
    'Send command: reboot'
    kind = 'reboot'
    return _assemble(kind, {})

@_send
def register_gpio(sequence_id, pin_number):
    'Send command: register_gpio'
    kind = 'register_gpio'
    args_ok = _check_arg(kind, pin_number, range(1, 30))
    if args_ok:
        return _assemble(kind, {'sequence_id': sequence_id,
                                'pin_number': pin_number})

@_send
def remove_farmware(package):
    'Send command: remove_farmware'
    kind = 'remove_farmware'
    return _assemble(kind, {'package': package})

@_send
def set_pin_io_mode(pin_io_mode, pin_number):
    'Send command: set_pin_io_mode'
    kind = 'set_pin_io_mode'
    args_ok = _check_arg(kind, pin_io_mode, [0, 1, 2])
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return _assemble(kind, {'pin_io_mode': pin_io_mode,
                                'pin_number': pin_number})

@_send
def set_servo_angle(pin_number, pin_value):
    'Send command: set_servo_angle'
    kind = 'set_servo_angle'
    args_ok = _check_arg(kind, pin_number, range(4, 6))
    args_ok = _check_arg(kind, pin_value, range(0, 360))
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number,
                                'pin_value': pin_value})

@_send
def sync():
    'Send command: sync'
    kind = 'sync'
    return _assemble(kind, {})

@_send
def take_photo():
    'Send command: take_photo'
    kind = 'take_photo'
    return _assemble(kind, {})

@_send
def toggle_pin(pin_number):
    'Send command: toggle_pin'
    kind = 'toggle_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number})

@_send
def unregister_gpio(pin_number):
    'Send command: unregister_gpio'
    kind = 'unregister_gpio'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number})

@_send
def update_farmware(package):
    'Send command: update_farmware'
    kind = 'update_farmware'
    return _assemble(kind, {'package': package})

@_send
def wait(milliseconds):
    'Send command: wait'
    kind = 'wait'
    return _assemble(kind, {'milliseconds': milliseconds})

@_send
def write_pin(pin_number, pin_value, pin_mode):
    'Send command: write_pin'
    kind = 'write_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    args_ok = _check_arg(kind, pin_mode, [0, 1])
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number,
                                'pin_value': pin_value,
                                'pin_mode': pin_mode})

@_send
def zero(axis):
    'Send command: zero'
    kind = 'zero'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return _assemble(kind, {'axis': axis})

def get_current_position():
    'Get the current position.'
    return get_bot_state()['location_data']['position']

def get_pin_value(pin_number):
    'Get a value from a pin.'
    try:
        value = get_bot_state()['pins'][str(pin_number)]['value']
    except KeyError:
        log('Pin `{}` value unknown.'.format(pin_number), 'error')
        sys.exit(1)
    else:
        return value

if __name__ == '__main__':
    send_celery_script({'kind': 'read_status', 'args': {}})
    log('Hello World!')
    send_message('Hello World!', 'success')
    # calibrate('x')
    check_updates('farmbot_os')
    emergency_lock()
    emergency_unlock()
    execute(1)
    execute_script('take-photo')
    # factory_reset('farmbot_os')
    find_home('x')
    home('all')
    URL = 'https://raw.githubusercontent.com/FarmBot-Labs/farmware_manifests/' \
        'master/packages/take-photo/manifest.json'
    install_farmware(URL)
    install_first_party_farmware()
    COORD = assemble_coordinate(0, 0, 0)
    move_absolute(COORD, 100, COORD)
    move_relative(0, 0, 0, 100)
    # power_off()
    read_pin(1, 'label', 0)
    read_status()
    # reboot()
    register_gpio(1, 1)
    remove_farmware('farmware')
    set_pin_io_mode(0, 47)
    set_servo_angle(4, 1)
    sync()
    take_photo()
    toggle_pin(1)
    unregister_gpio(1)
    update_farmware('take-photo')
    wait(100)
    write_pin(1, 1, 0)
    zero('z')
    # preferred method for logging position
    log('At position: ({{x}}, {{y}}, {{z}})')
    # get position for calculations
    POSITION = get_current_position()
    log('At position: ({}, {}, {})'.format(
        POSITION['x'], POSITION['y'], POSITION['z']))
    # preferred method for logging pin value
    log('pin 13 value: {{pin13}}')
    # get pin value for calculations
    VALUE = get_pin_value(13)
    log('pin 13 value: {}'.format(VALUE))
