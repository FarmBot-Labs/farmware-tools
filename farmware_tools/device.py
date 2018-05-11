#!/usr/bin/env python

'''Farmware Tools: Device.'''

from __future__ import print_function
import os
import sys
import json
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

def _check_and_format(command):
    try:
        kind = command['kind']
        args = command['args']
    except (KeyError, TypeError):
        to_print = command
        _error('celery script', command)
        _on_error()
    else:
        to_print = "{{'kind': '{magenta}{kind}{reset}', " \
        "'args': {cyan}{args}{reset}}}".format(
            magenta=MAGENTA, cyan=CYAN, reset=RESET, kind=kind, args=args)
    return to_print

def rpc_wrapper(command, rpc_id=''):
    'Wrap a command in `rpc_request`.'
    return {'kind': 'rpc_request', 'args': {'label': rpc_id}, 'body': [command]}

def send_celery_script(command):
    'Send a celery script command.'
    to_print = _check_and_format(command)
    try:
        url = os.environ['FARMWARE_URL']
        token = os.environ['FARMWARE_TOKEN']
    except KeyError:
        print(to_print)
    else:
        response = requests.post(
            url + 'api/v1/celery_script',
            headers={'Authorization': 'Bearer ' + token,
                     'content-type': 'application/json'},
            data=json.dumps(command))
        if response.status_code != 200:
            log('Invalid celery script `{}`'.format(command), 'error')
            _on_error()
    return command

def log(message, message_type='info'):
    'Send a send_message command to post a log to the Web App.'
    return send_message(message, message_type)

def _assemble(kind, args):
    'Assemble a celery script command.'
    return {'kind': kind, 'args': args}

def _error(kind, arg):
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
        _error(kind, arg)
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
        _error('coordinate', coordinate)
        _on_error()
    return coordinate_ok

def send_message(message, message_type):
    'Send command: send_message'
    kind = 'send_message'
    allowed_types = ['success', 'busy', 'warn', 'error', 'info', 'fun', 'debug']
    args_ok = _check_arg(kind, message_type, allowed_types)
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'message': message,
                             'message_type': message_type}))

def calibrate(axis):
    'Send command: calibrate'
    kind = 'calibrate'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'axis': axis}))

def check_updates(package):
    'Send command: check_updates'
    kind = 'check_updates'
    args_ok = _check_arg(kind, package,
                         ['farmbot_os', 'arduino_firmware', 'farmware'])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'package': package}))

def emergency_lock():
    'Send command: emergency_lock'
    kind = 'emergency_lock'
    return send_celery_script(
        _assemble(kind, {}))

def emergency_unlock():
    'Send command: emergency_unlock'
    kind = 'emergency_unlock'
    return send_celery_script(
        _assemble(kind, {}))

def execute(sequence_id):
    'Send command: execute'
    kind = 'execute'
    return send_celery_script(
        _assemble(kind, {'sequence_id': sequence_id}))

def execute_script(label):
    'Send command: execute_script'
    kind = 'execute_script'
    return send_celery_script(
        _assemble(kind, {'label': label}))

def factory_reset(package):
    'Send command: factory_reset'
    kind = 'factory_reset'
    args_ok = _check_arg(kind, package, ['farmbot_os', 'arduino_firmware'])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'package': package}))

def find_home(axis):
    'Send command: find_home'
    kind = 'find_home'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'axis': axis}))

def home(axis):
    'Send command: home'
    kind = 'home'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'axis': axis}))

def install_farmware(url):
    'Send command: install_farmware'
    kind = 'install_farmware'
    return send_celery_script(
        _assemble(kind, {'url': url}))

def install_first_party_farmware():
    'Send command: install_first_party_farmware'
    kind = 'install_first_party_farmware'
    return send_celery_script(
        _assemble(kind, {}))

def move_absolute(location, speed, offset):
    'Send command: move_absolute'
    kind = 'move_absolute'
    args_ok = _check_coordinate(location)
    args_ok = _check_coordinate(offset)
    args_ok = _check_arg(kind, speed, range(1, 101))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'location': location,
                             'speed': speed,
                             'offset': offset}))

def move_relative(x, y, z, speed):
    'Send command: move_relative'
    kind = 'move_relative'
    args_ok = _check_arg(kind, speed, range(1, 101))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'x': x,
                             'y': y,
                             'z': z,
                             'speed': speed}))

def power_off():
    'Send command: power_off'
    kind = 'power_off'
    return send_celery_script(
        _assemble(kind, {}))

def read_pin(pin_number, label, pin_mode):
    'Send command: read_pin'
    kind = 'read_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    args_ok = _check_arg(kind, pin_mode, [0, 1])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'pin_number': pin_number,
                             'label': label,
                             'pin_mode': pin_mode}))

def read_status():
    'Send command: read_status'
    kind = 'read_status'
    return send_celery_script(
        _assemble(kind, {}))

def reboot():
    'Send command: reboot'
    kind = 'reboot'
    return send_celery_script(
        _assemble(kind, {}))

def register_gpio(sequence_id, pin_number):
    'Send command: register_gpio'
    kind = 'register_gpio'
    args_ok = _check_arg(kind, pin_number, range(1, 30))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'sequence_id': sequence_id,
                             'pin_number': pin_number}))

def remove_farmware(package):
    'Send command: remove_farmware'
    kind = 'remove_farmware'
    return send_celery_script(
        _assemble(kind, {'package': package}))

def set_pin_io_mode(pin_io_mode, pin_number):
    'Send command: set_pin_io_mode'
    kind = 'set_pin_io_mode'
    args_ok = _check_arg(kind, pin_io_mode, [0, 1, 2])
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'pin_io_mode': pin_io_mode,
                             'pin_number': pin_number}))

def set_servo_angle(pin_number, pin_value):
    'Send command: set_servo_angle'
    kind = 'set_servo_angle'
    args_ok = _check_arg(kind, pin_number, range(4, 6))
    args_ok = _check_arg(kind, pin_value, range(0, 360))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'pin_number': pin_number,
                             'pin_value': pin_value}))

def sync():
    'Send command: sync'
    kind = 'sync'
    return send_celery_script(
        _assemble(kind, {}))

def take_photo():
    'Send command: take_photo'
    kind = 'take_photo'
    return send_celery_script(
        _assemble(kind, {}))

def toggle_pin(pin_number):
    'Send command: toggle_pin'
    kind = 'toggle_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'pin_number': pin_number}))

def unregister_gpio(pin_number):
    'Send command: unregister_gpio'
    kind = 'unregister_gpio'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'pin_number': pin_number}))

def update_farmware(package):
    'Send command: update_farmware'
    kind = 'update_farmware'
    return send_celery_script(
        _assemble(kind, {'package': package}))

def wait(milliseconds):
    'Send command: wait'
    kind = 'wait'
    return send_celery_script(
        _assemble(kind, {'milliseconds': milliseconds}))

def write_pin(pin_number, pin_value, pin_mode):
    'Send command: write_pin'
    kind = 'write_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    args_ok = _check_arg(kind, pin_mode, [0, 1])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'pin_number': pin_number,
                             'pin_value': pin_value,
                             'pin_mode': pin_mode}))

def zero(axis):
    'Send command: zero'
    kind = 'zero'
    args_ok = _check_arg(kind, axis, ['x', 'y', 'z', 'all'])
    if args_ok:
        return send_celery_script(
            _assemble(kind, {'axis': axis}))

if __name__ == '__main__':
    send_celery_script({'kind': 'read_status', 'args': {}})
    log('Hello World!')
    send_message('Hello World!', 'success')
    calibrate('x')
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
