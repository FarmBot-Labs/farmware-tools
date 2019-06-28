#!/usr/bin/env python

'''Farmware Tools Tests: device requests'''

from __future__ import print_function
import os
try:
    from unittest import mock
except ImportError:
    import mock
from farmware_tools import device

class MockResponse(object):
    'Mocked requests response class.'
    def __init__(self, status_code=200, json_response=None):
        self.status_code = status_code
        self.json_response = json_response

    def json(self):
        'JSON response content.'
        return self.json_response

MOCK = {'calls': []}

def _mock_request_with(status_code, json_response=None):
    def _mock_request(method, url, **kwargs):
        try:
            uuid = kwargs['json']['args']['label']
            command = kwargs['json']['body'][0]
        except KeyError:
            MOCK['calls'].append({'method': method, 'url': url})
        else:
            MOCK['calls'].append({'method': method, 'url': url, 'uuid': uuid})
            kind = command['kind']
            args = command['args']
            print(device.COLOR.colorize_celery_script(kind, args))
        return MockResponse(status_code, json_response)
    return _mock_request

@mock.patch('requests.request', _mock_request_with(500))
def _test_500_response():
    MOCK['calls'] = []
    device.log('hi')
    print(MOCK['calls'])
    assert len(MOCK['calls']) == 2
    assert MOCK['calls'][0]['method'] == 'POST'
    assert MOCK['calls'][0]['url'] == 'fake_farmware_url/api/v1/celery_script'
    assert MOCK['calls'][0]['uuid'] != device.RESPONSE_ERROR_LOG_UUID
    assert MOCK['calls'][1]['uuid'] == device.RESPONSE_ERROR_LOG_UUID

FAKE_BOT_STATE = {'location_data': {'position': {'x': 1}}}

@mock.patch('requests.request', _mock_request_with(200, FAKE_BOT_STATE))
def _test_200_response():
    MOCK['calls'] = []
    bot_state = device.get_bot_state()
    print(MOCK['calls'])
    assert len(MOCK['calls']) == 1
    assert MOCK['calls'][0]['method'] == 'GET'
    assert MOCK['calls'][0]['url'] == 'fake_farmware_url/api/v1/bot/state'
    print(bot_state)
    assert bot_state == FAKE_BOT_STATE

def run_device_requests_tests():
    'Run command error tests.'
    os.environ['FARMWARE_URL'] = 'fake_farmware_url/'
    os.environ['FARMWARE_TOKEN'] = 'fake_farmware_token'
    _test_500_response()
    _test_200_response()

if __name__ == '__main__':
    run_device_requests_tests()
