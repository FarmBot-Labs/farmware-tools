#!/usr/bin/env python

'''Farmware Tools: Farmware API utilities used by `device` for FarmBot OS v8.'''

import sys
import json
import struct
import socket
import threading
from time import sleep
from .env import Env

ENV = Env()
HEADER_FORMAT = '>HII'
TIMEOUT_SECONDS = 10


def _open_socket(address):
    opened_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    opened_socket.settimeout(TIMEOUT_SECONDS)
    try:
        opened_socket.connect(address)
    except FileNotFoundError:
        print('Could not connect to socket: address not found.')
        sys.exit(1)
    return opened_socket


class _ResponseBuffer():
    '''Collection of responses from FarmBot OS.'''

    def __init__(self):
        self.responses = {}
        self.response_socket = _open_socket(ENV.response_pipe)

    def listen(self):
        '''Collect responses from FarmBot OS.'''
        while True:
            try:
                header = self.response_socket.recv(10)
            except socket.timeout:
                continue
            if header == b'':
                continue
            (_, _, size) = struct.unpack(HEADER_FORMAT, header)
            response = json.loads(self.response_socket.recv(size).decode())
            self.responses[response['args']['label']] = response

    def pop(self, rpc_uuid):
        '''Pull a response off of the buffer by RPC UUID (label).'''
        wait_time = 0
        while wait_time < TIMEOUT_SECONDS:
            response = self.responses.pop(rpc_uuid, None)
            if response is None:
                wait_time += 0.5
                sleep(0.5)
            else:
                return response
        return 'no response'


# Listen for responses from FarmBot OS.
if ENV.use_v2() and ENV.farmware_api_available():
    RESPONSE_BUFFER = _ResponseBuffer()
    RESPONSES = threading.Thread(target=RESPONSE_BUFFER.listen, daemon=True)
    RESPONSES.start()


def _request_write(payload):
    'Make a request to FarmBot OS.'
    request_socket = _open_socket(ENV.request_pipe)
    message_bytes = bytes(json.dumps(payload), 'utf-8')
    header = struct.pack(HEADER_FORMAT, 0xFBFB, 0, len(message_bytes))
    request_socket.sendall(header + message_bytes)
    request_socket.close()


def _response_read(rpc_uuid):
    'Read a response from FarmBot OS for the provided request RPC UUID.'
    if rpc_uuid is not None:
        return RESPONSE_BUFFER.pop(rpc_uuid)
    return 'missing RPC label'
