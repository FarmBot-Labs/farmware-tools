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
    return {'token': token, 'url': url}

def request(raw_method, endpoint, _id=None, payload=None,
            get_info=_get_required_info):
    'Send an HTTP request to the FarmBot Web App.'
    method = raw_method.upper()
    full_endpoint = endpoint
    if _id is not None:
        full_endpoint += '/{}'.format(_id)
    request_string = '{} /api/{} {}'.format(
        method, full_endpoint,
        payload if payload is not None else '')
    try:
        api = get_info()
    except:
        print(request_string)
        return request_string

    try:  # verbose output if testing
        if api['verbose']:
            verbose = True
    except KeyError:
        verbose = False

    url = api['url'] + full_endpoint
    request_kwargs = {}
    request_kwargs['headers'] = {
        'Authorization': 'Bearer ' + api['token'],
        'content-type': 'application/json'}
    if payload is not None:
        request_kwargs['json'] = payload
    response = requests.request(method, url, **request_kwargs)
    request_details = '{}: {}'.format(response.status_code, request_string)
    if verbose:
        print()
        print(request_details)
    if response.status_code != 200 and not verbose:
        print(request_details)
        print(response.json())
    return response.json()

def post(endpoint, payload, get_info=_get_required_info):
    'Send an POST HTTP request to the FarmBot Web App.'
    kwargs = {'payload': payload, 'get_info': get_info}
    return request('POST', endpoint, **kwargs)

def get(endpoint, _id=None, get_info=_get_required_info):
    'Send an GET HTTP request to the FarmBot Web App.'
    kwargs = {'_id': _id, 'get_info': get_info}
    return request('GET', endpoint, **kwargs)

def patch(endpoint, _id=None, payload=None, get_info=_get_required_info):
    'Send an PATCH HTTP request to the FarmBot Web App.'
    kwargs = {'_id': _id, 'payload': payload, 'get_info': get_info}
    return request('PATCH', endpoint, **kwargs)

def put(endpoint, _id=None, payload=None, get_info=_get_required_info):
    'Send an PUT HTTP request to the FarmBot Web App.'
    kwargs = {'_id': _id, 'payload': payload, 'get_info': get_info}
    return request('PUT', endpoint, **kwargs)

def delete(endpoint, _id=None, get_info=_get_required_info):
    'Send an DELETE HTTP request to the FarmBot Web App.'
    kwargs = {'_id': _id, 'get_info': get_info}
    return request('DELETE', endpoint, **kwargs)

def log(message, message_type='info', get_info=_get_required_info):
    'POST a log message to the Web App.'
    payload = {'message': message, 'type': message_type}
    return post('logs', payload=payload, get_info=get_info)

def search_points(search_payload, get_info=_get_required_info):
    'Use a search term to get a filtered selection of points from the web app.'
    return post('points/search', payload=search_payload, get_info=get_info)

def download_plants(get_info=_get_required_info):
    'Get plant data from the web app.'
    search_payload = {'pointer_type': 'Plant'}
    return search_points(search_payload, get_info)

def get_points(get_info=_get_required_info):
    'Get generic point data from the web app.'
    search_payload = {'pointer_type': 'GenericPointer'}
    return search_points(search_payload, get_info)

def get_plants(get_info=_get_required_info):
    'Get plant data from the web app.'
    return download_plants(get_info)

def get_toolslots(get_info=_get_required_info):
    'Get tool slot data from the web app.'
    search_payload = {'pointer_type': 'ToolSlot'}
    return search_points(search_payload, get_info)

def get_property(endpoint, field, _id=None, get_info=_get_required_info):
    'Get the value of a specific property field of a web app record.'
    record = get(endpoint, _id=_id, get_info=get_info)
    return record[field]

def add_plant(x, y, get_info=_get_required_info, **kwargs):
    'Add a plant to the garden map.'
    new_plant = {'pointer_type': 'Plant', 'x': x, 'y': y}
    for key, value in kwargs.items():
        if value is not None:
            new_plant[key] = value
    return post('points', payload=new_plant, get_info=get_info)

def find_sequence_by_name(name, get_info=_get_required_info):
    'Find the sequence_id for a given sequence name.'
    sequences = get('sequences', get_info=get_info)
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
    log('Hello World!', message_type='success')
    request('GET', 'tools')
    get('sensors')
    TOOL = post('tools', payload={'name': 'test_tool_' + TIMESTAMP})
    ID = TOOL['id']
    put('tools', ID, payload={'name': 'test_tool_edit_' + TIMESTAMP})
    delete('tools', ID)
    search_points({'pointer_type': 'Plant'})
    download_plants()
    get_points()
    get_plants()
    get_toolslots()
    get_property('device', 'name')
    add_plant(x=100, y=100)
    add_plant(x=10, y=20, z=30, radius=10, openfarm_slug='mint', name='test')
    find_sequence_by_name('test')
