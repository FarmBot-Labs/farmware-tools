#!/usr/bin/env python

'''Farmware Tools: Device.'''

from __future__ import print_function
import os
import sys
from functools import wraps
import requests
from .auxiliary import Color

COLOR = Color()
ALLOWED_AXIS_VALUES = ['x', 'y', 'z', 'all']
ALLOWED_MESSAGE_TYPES = [
    'success', 'busy', 'warn', 'error', 'info', 'fun', 'debug']
ALLOWED_MESSAGE_CHANNELS = ['ticker', 'toast', 'email', 'espeak']
ALLOWED_PACKAGES = ['farmbot_os', 'arduino_firmware', 'farmware']

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
        body = command.get('body')
        if body is not None:
            if not isinstance(body, list):
                _cs_error(kind, body)
                _on_error()
        return kind, args, body

def rpc_wrapper(command, rpc_id=''):
    """Wrap a command in `rpc_request` with the given `rpc_id`."""
    return {'kind': 'rpc_request', 'args': {'label': rpc_id}, 'body': [command]}

def _device_request(method, endpoint, payload=None):
    'Make a request to the device Farmware API.'
    try:
        base_url = os.environ['FARMWARE_URL']
        token = os.environ['FARMWARE_TOKEN']
    except KeyError:
        return

    url = base_url + 'api/v1/' + endpoint
    request_kwargs = {}
    request_kwargs['headers'] = {
        'Authorization': 'Bearer ' + token,
        'content-type': 'application/json'}
    if payload is not None:
        request_kwargs['json'] = payload
    response = requests.request(method, url, **request_kwargs)
    if response.status_code != 200:
        log('Invalid {} request `{}` ({})'.format(
            endpoint, payload or '', response.status_code), 'error')
        _on_error()
    return response

def _post(endpoint, payload):
    """Post a payload to the device Farmware API.

    Since the only currently available endpoint is 'celery_script',
    use `send_celery_script(command)` instead.

    Args:
        endpoint (str): i.e., 'celery_script'
        payload (dict): i.e., {'kind': 'take_photo', 'args': {}}
    Returns:
        requests response object
    """
    return _device_request('POST', endpoint, payload)

def _get(endpoint):
    """Get info from the device Farmware API.

    Since the only currently available endpoint is 'bot/state',
    use `get_bot_state()` instead.

    Args:
        endpoint (str): i.e., 'bot/state'
    Returns:
        requests response object
    """
    return _device_request('GET', endpoint)

def get_bot_state():
    """Get the device state."""
    bot_state = _get('bot/state')
    if bot_state is None:
        _error('Device info could not be retrieved.')
        _on_error()
    else:
        return bot_state.json()

def _send(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        'Send Celery Script to the device.'
        try:
            rpc_id = kwargs.pop('rpc_id')
        except KeyError:
            command = function(*args, **kwargs)
        else:
            command = rpc_wrapper(function(*args, **kwargs), rpc_id=rpc_id)
        return send_celery_script(command)
    return wrapper

def send_celery_script(command):
    """Send a Celery Script command."""
    kind, args, body = _check_celery_script(command)
    response = _post('celery_script', command)
    if response is None:
        print(COLOR.colorize_celery_script(kind, args, body))
    return command

def log(message, message_type='info', channels=None):
    """Send a send_message command to post a log to the Web App.

    Args:
        message (str): log message contents
        message_type (str, optional): One of ALLOWED_MESSAGE_TYPES.
            Defaults to 'info'.
        channels (list, optional): Any of ALLOWED_MESSAGE_CHANNELS.
            Defaults to None.
    """
    return send_message(message, message_type, channels)

def _assemble(kind, args, body=None):
    'Assemble a celery script command.'
    if body is None:
        return {'kind': kind, 'args': args}
    else:
        return {'kind': kind, 'args': args, 'body': body}

def _error(error_text):
    try:
        os.environ['FARMWARE_URL']
    except KeyError:
        print(COLOR.error(error_text))
    else:
        log(error_text, 'error')

def _cs_error(kind, arg):
    try:
        os.environ['FARMWARE_URL']
    except KeyError:
        print(COLOR.error('Invalid input `{arg}` in `{kind}`'.format(
            arg=arg, kind=kind)))
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
    """Assemble a coordinate Celery Script node from x, y, and z."""
    return {
        'kind': 'coordinate',
        'args': {'x': coord_x, 'y': coord_y, 'z': coord_z}}

def _assemble_channel(name):
    'Assemble a channel body item (for `send_message`).'
    return {
        'kind': 'channel',
        'args': {'channel_name': name}}

def assemble_pair(label, value):
    """Assemble a 'pair' Celery Script node (for use as a body item)."""
    return {
        'kind': 'pair',
        'args': {'label': label, 'value': value}}

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
def send_message(message, message_type, channels=None):
    """Send command: send_message.

    Args:
        message (str): log message contents
        message_type (str, optional): One of ALLOWED_MESSAGE_TYPES.
            Defaults to 'info'.
        channels (list, optional): Any of ALLOWED_MESSAGE_CHANNELS.
            Defaults to None.
    """
    kind = 'send_message'
    args_ok = _check_arg(kind, message_type, ALLOWED_MESSAGE_TYPES)
    if channels is not None:
        for channel in channels:
            args_ok = _check_arg(kind, channel, ALLOWED_MESSAGE_CHANNELS)
    if args_ok:
        if channels is None:
            return _assemble(
                kind, {'message': message, 'message_type': message_type})
        else:
            return _assemble(
                kind,
                args={'message': message, 'message_type': message_type},
                body=[_assemble_channel(channel) for channel in channels])

@_send
def calibrate(axis):
    """Send command: calibrate.

    Args:
        axis (str): One of ALLOWED_AXIS_VALUES.
    """
    kind = 'calibrate'
    args_ok = _check_arg(kind, axis, ALLOWED_AXIS_VALUES)
    if args_ok:
        return _assemble(kind, {'axis': axis})

@_send
def check_updates(package):
    """Send command: check_updates.

    Args:
        package (str): One of ALLOWED_PACKAGES.
    """
    kind = 'check_updates'
    args_ok = _check_arg(kind, package, ALLOWED_PACKAGES)
    if args_ok:
        return _assemble(kind, {'package': package})

@_send
def emergency_lock():
    """Send command: emergency_lock."""
    kind = 'emergency_lock'
    return _assemble(kind, {})

@_send
def emergency_unlock():
    """Send command: emergency_unlock."""
    kind = 'emergency_unlock'
    return _assemble(kind, {})

@_send
def execute(sequence_id):
    """Send command: execute.

    Args:
        sequence_id (int): Web App Sequence ID.
            Sequence must be synced to FarmBot OS before execution.
    """
    kind = 'execute'
    return _assemble(kind, {'sequence_id': sequence_id})

@_send
def execute_script(label, inputs=None):
    """Send command: execute_script (Run Farmware).

    Args:
        label (str): Name of the Farmware to execute. Must be installed.
        inputs (dict, optional): Farmware configs, i.e., {'input_0': 0}.
            Defaults to None.
    """
    kind = 'execute_script'
    args = {'label': label}
    if inputs is None:
        return _assemble(kind, args)
    else:
        farmware = label.replace(' ', '_').replace('-', '_').lower()
        body = []
        for key, value in inputs.items():
            if key.startswith(farmware):
                input_name = key
            else:
                input_name = '{}_{}'.format(farmware, key)
            body.append(assemble_pair(input_name, value))
        return _assemble(kind, args, body)

@_send
def factory_reset(package):
    """Send command: factory_reset.

    Args:
        package (str): One of ALLOWED_PACKAGES.
    """
    kind = 'factory_reset'
    args_ok = _check_arg(kind, package, ALLOWED_PACKAGES)
    if args_ok:
        return _assemble(kind, {'package': package})

@_send
def find_home(axis):
    """Send command: find_home.

    Args:
        axis (str): One of ALLOWED_AXIS_VALUES.
    """
    kind = 'find_home'
    args_ok = _check_arg(kind, axis, ALLOWED_AXIS_VALUES)
    if args_ok:
        return _assemble(kind, {'axis': axis})

@_send
def home(axis):
    """Send command: home.

    Args:
        axis (str): One of ALLOWED_AXIS_VALUES.
    """
    kind = 'home'
    args_ok = _check_arg(kind, axis, ALLOWED_AXIS_VALUES)
    if args_ok:
        return _assemble(kind, {'axis': axis})

@_send
def install_farmware(url):
    """Send command: install_farmware.

    Args:
        url (str): URL for the Farmware's manifest.
    """
    kind = 'install_farmware'
    return _assemble(kind, {'url': url})

@_send
def install_first_party_farmware():
    """Send command: install_first_party_farmware."""
    kind = 'install_first_party_farmware'
    return _assemble(kind, {})

@_send
def move_absolute(location, speed, offset):
    """Send command: move_absolute.

    Celery Script 'coordinate' nodes can be assembled using
    `assemble_coordinate(coord_x, coord_y, coord_z)`.

    Args:
        location (dict): Celery Script 'coordinate' node.
        speed (int): Percent of max speed.
        offset (dict): Celery Script 'coordinate' node.
    """
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
    """Send command: move_relative.

    Args:
        x (int): Distance.
        y (int): Distance.
        z (int): Distance.
        speed (int): Percent of max speed.
    """
    kind = 'move_relative'
    args_ok = _check_arg(kind, speed, range(1, 101))
    if args_ok:
        return _assemble(kind, {'x': x,
                                'y': y,
                                'z': z,
                                'speed': speed})

@_send
def power_off():
    """Send command: power_off."""
    kind = 'power_off'
    return _assemble(kind, {})

@_send
def read_pin(pin_number, label, pin_mode):
    """Send command: read_pin.

    Args:
        pin_number (int): Arduino pin (0 through 69).
        label (str): Any string.
        pin_mode (int): 0 (digital) or 1 (analog).
    """
    kind = 'read_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    args_ok = _check_arg(kind, pin_mode, [0, 1])
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number,
                                'label': label,
                                'pin_mode': pin_mode})

@_send
def read_status():
    """Send command: read_status."""
    kind = 'read_status'
    return _assemble(kind, {})

@_send
def reboot():
    """Send command: reboot."""
    kind = 'reboot'
    return _assemble(kind, {})

@_send
def register_gpio(sequence_id, pin_number):
    """Send command: register_gpio.

    Args:
        sequence_id (int): Web App Sequence ID.
            Sequence must be synced to FarmBot OS before registration.
        pin_number (int): Raspberry Pi GPIO BCM pin number.
    """
    kind = 'register_gpio'
    args_ok = _check_arg(kind, pin_number, range(1, 30))
    if args_ok:
        return _assemble(kind, {'sequence_id': sequence_id,
                                'pin_number': pin_number})

@_send
def remove_farmware(package):
    """Send command: remove_farmware.

    Args:
        package (str): Name of the Farmware to uninstall.
    """
    kind = 'remove_farmware'
    return _assemble(kind, {'package': package})

@_send
def set_pin_io_mode(pin_io_mode, pin_number):
    """Send command: set_pin_io_mode.

    Args:
        pin_io_mode (int): 0 (input), 1 (output), or 2 (input_pullup)
        pin_number (int): Arduino pin (0 through 69).
    """
    kind = 'set_pin_io_mode'
    args_ok = _check_arg(kind, pin_io_mode, [0, 1, 2])
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return _assemble(kind, {'pin_io_mode': pin_io_mode,
                                'pin_number': pin_number})

@_send
def set_servo_angle(pin_number, pin_value):
    """Send command: set_servo_angle.

    Args:
        pin_number (int): Arduino servo pin (4 or 5).
        pin_value (int): Servo angle (0 through 359).
    """
    kind = 'set_servo_angle'
    args_ok = _check_arg(kind, pin_number, range(4, 6))
    args_ok = _check_arg(kind, pin_value, range(0, 360))
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number,
                                'pin_value': pin_value})

@_send
def set_user_env(key, value):
    """Send command: set_user_env.

    Args:
        key (str): ENV key
        value (str): ENV value
    """
    kind = 'set_user_env'
    body = [assemble_pair(key, value)]
    return _assemble(kind, {}, body)

@_send
def sync():
    """Send command: sync."""
    kind = 'sync'
    return _assemble(kind, {})

@_send
def take_photo():
    """Send command: take_photo."""
    kind = 'take_photo'
    return _assemble(kind, {})

@_send
def toggle_pin(pin_number):
    """Send command: toggle_pin.

    Args:
        pin_number (int): Arduino pin (0 through 69).
    """
    kind = 'toggle_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number})

@_send
def unregister_gpio(pin_number):
    """Send command: unregister_gpio.

    Args:
        pin_number (int): Arduino pin (0 through 69).
    """
    kind = 'unregister_gpio'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number})

@_send
def update_farmware(package):
    """Send command: update_farmware.

    Args:
        package (str): Name of the Farmware to update.
    """
    kind = 'update_farmware'
    return _assemble(kind, {'package': package})

@_send
def wait(milliseconds):
    """Send command: wait.

    Args:
        milliseconds (int): Time to wait in milliseconds.
    """
    kind = 'wait'
    return _assemble(kind, {'milliseconds': milliseconds})

@_send
def write_pin(pin_number, pin_value, pin_mode):
    """Send command: write_pin.

    Args:
        pin_number (int): Arduino pin (0 through 69).
        pin_value (int): Value to write to pin.
        pin_mode (int): 0 (digital) or 1 (analog).
    """
    kind = 'write_pin'
    args_ok = _check_arg(kind, pin_number, range(0, 70))
    args_ok = _check_arg(kind, pin_mode, [0, 1])
    if args_ok:
        return _assemble(kind, {'pin_number': pin_number,
                                'pin_value': pin_value,
                                'pin_mode': pin_mode})

@_send
def zero(axis):
    """Send command: zero.

    Args:
        axis (str): One of ALLOWED_AXIS_VALUES.
    """
    kind = 'zero'
    args_ok = _check_arg(kind, axis, ALLOWED_AXIS_VALUES)
    if args_ok:
        return _assemble(kind, {'axis': axis})

def get_current_position(axis='all', _get_bot_state=get_bot_state):
    """Get the current position.

    Args:
        axis (str, optional): One of ALLOWED_AXIS_VALUES. Defaults to 'all'.
    Returns:
        'all': FarmBot position, i.e., {'x': 0.0, 'y': 0.0, 'z': 0.0}
        'x', 'y', or 'z': FarmBot axis position, i.e., 0.0
    """
    args_ok = _check_arg('get_current_position', axis, ALLOWED_AXIS_VALUES)
    if args_ok:
        if axis in ['x', 'y', 'z']:
            try:
                return _get_bot_state()['location_data']['position'][axis]
            except KeyError:
                _error('Position `{}` value unknown.'.format(axis))
        else:
            return _get_bot_state()['location_data']['position']

def get_pin_value(pin_number, _get_bot_state=get_bot_state):
    """Get a value from a pin.

    Args:
        pin_number (int): Arduino pin (0 through 69).
    """
    try:
        value = _get_bot_state()['pins'][str(pin_number)]['value']
    except KeyError:
        _error('Pin `{}` value unknown.'.format(pin_number))
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
