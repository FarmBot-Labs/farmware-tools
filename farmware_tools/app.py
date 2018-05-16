#!/usr/bin/env python

'''Farmware Tools: Web App.'''

from __future__ import print_function
import os
import sys
import time
import json
import base64
import requests

def _get_required_info():
    'Get the info required to send an HTTP request to the FarmBot Web App.'
    token = os.environ['API_TOKEN']
    encoded_payload = token.split('.')[1]
    encoded_payload += '=' * (4 - len(encoded_payload) % 4)
    json_payload = base64.b64decode(encoded_payload).decode('utf-8')
    server = json.loads(json_payload)['iss']
    url = 'http{}:{}/api/'.format('s' if ':443' in server else '', server)
    return token, url

def post(endpoint, payload, get_info=_get_required_info):
    'Send an POST HTTP request to the FarmBot Web App.'
    request_string = 'POST /api/{} {}'.format(endpoint, payload)
    try:
        token, url = get_info()
    except:
        print(request_string)
        return request_string
    else:
        response = requests.post(
            url + endpoint,
            headers={'Authorization': 'Bearer ' + token,
                     'content-type': 'application/json'},
            data=json.dumps(payload))
        if response.status_code != 200:
            print(response.json())
        return response.json()

def get(endpoint, get_info=_get_required_info):
    'Send an GET HTTP request to the FarmBot Web App.'
    request_string = 'GET /api/{}'.format(endpoint)
    try:
        token, url = get_info()
    except:
        print(request_string)
        return request_string
    else:
        response = requests.get(
            url + endpoint,
            headers={'Authorization': 'Bearer ' + token,
                     'content-type': 'application/json'})
        if response.status_code != 200:
            print(response.json())
        return response.json()

def log(message, message_type='info', get_info=_get_required_info):
    'POST a log message to the Web App.'
    return post('logs', {'message': message, 'type': message_type}, get_info)

def download_plants(get_info=_get_required_info):
    'Get plant data from the web app.'
    return post('points/search', {'pointer_type': 'Plant'}, get_info)

def add_plant(x, y, get_info=_get_required_info):
    'Add a plant to the garden map.'
    new_plant = {'pointer_type': 'Plant', 'x': x, 'y': y}
    return post('points', new_plant, get_info)

def find_sequence_by_name(name, get_info=_get_required_info):
    'Find the sequence_id for a given sequence name.'
    sequences = get('sequences', get_info)
    sequence_lookup = {s['name']: s['id'] for s in sequences}
    try:
        sequence_id = sequence_lookup[name]
    except KeyError:
        log('Sequence `{}` not found.'.format(name), 'error')
        sys.exit(1)
    else:
        return sequence_id

if __name__ == '__main__':
    TIMESTAMP = str(int(time.time()))
    log('Hello World!', 'success')
    get('sensors')
    post('tools', {'name': 'test_tool_' + TIMESTAMP})
    download_plants()
    add_plant(100, 100)
    find_sequence_by_name('test')
