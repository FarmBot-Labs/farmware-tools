#!/usr/bin/env python

'''Farmware Tools Tests: command error'''

from __future__ import print_function
import os
try:
    from unittest import mock
except ImportError:
    import mock
from farmware_tools import device

class MockResponse(object):
    'Mocked requests response class.'
    def __init__(self, status_code=200):
        self.status_code = status_code

CALL_UUIDS = []

def _mock_request_with(status_code):
    def _mock_request(method, url, **kwargs):
        assert method == 'POST'
        assert url == 'fake_farmware_url/api/v1/celery_script'
        uuid = kwargs['json']['args']['label']
        CALL_UUIDS.append(uuid)
        command = kwargs['json']['body'][0]
        kind = command['kind']
        args = command['args']
        print(device.COLOR.colorize_celery_script(kind, args))
        return MockResponse(status_code)
    return _mock_request

@mock.patch('requests.request', _mock_request_with(500))
def _test_500_response():
    device.log('hi')
    assert len(CALL_UUIDS) == 2
    assert CALL_UUIDS[0] != device.RESPONSE_ERROR_LOG_UUID
    assert CALL_UUIDS[1] == device.RESPONSE_ERROR_LOG_UUID

def run_command_error_tests():
    'Run command error tests.'
    os.environ['FARMWARE_URL'] = 'fake_farmware_url/'
    os.environ['FARMWARE_TOKEN'] = 'fake_farmware_token'
    _test_500_response()

if __name__ == '__main__':
    run_command_error_tests()
