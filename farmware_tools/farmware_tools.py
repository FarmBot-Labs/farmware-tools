#!/usr/bin/env python

'''Farmware Tools.'''

import os
import json
import requests

def send_celery_script(command):
    'Send a celery script command.'
    try:
        url = os.environ['FARMWARE_URL']
        token = os.environ['FARMWARE_TOKEN']
    except KeyError:
        print(command)
    else:
        requests.post(
            url + 'api/v1/celery_script',
            headers={'Authorization': 'Bearer ' + token,
                     'content-type': 'application/json'},
            data=json.dumps(command))

def log(message, message_type='info'):
    'Send a send_message command to post a log to the Web App.'
    send_celery_script({
        'kind': 'send_message',
        'args': {
            'message': message,
            'message_type': message_type}})

if __name__ == '__main__':
    log('Hello World!', 'success')
