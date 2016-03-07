import requests
import json
import os
import imp

config = imp.load_source('config', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'learning_framework', 'config.py'))
from main_app import models

url = 'http://{0}:{1}'.format(config.server_name, config.port)
headers = {'Content-type': 'application/json'}

def _query_result(data):
    try:
        result = requests.post(url, headers = headers, data = json.dumps(data))
    except:
        return None

    if result.status_code != 200:
        return None

    response = result.json()
    if not response['success']:
        raise Exception(response['message'])
        return None

    return response['message']

def index(user, *args, **kwargs):
    data = {
        'action' : 'predict',
        'args': [user.id]
    }

    result = _query_result(data)
    if result is None:
        return models.Paper.objects.filter(arxiv_id__in = ())

    try:
        ids = result['ids']
        assert type(ids) is list

        query_output = models.Paper.objects.filter(arxiv_id__in = ids) #E.g. ['1602.03276', '1602.03275']
        query_output = list(query_output)
        query_output.sort(key = lambda x : ids.index(x.arxiv_id))
        return query_output
    except:
        return models.Paper.objects.filter(arxiv_id__in = ())
    

def author(user, author_id, *args, **kwargs):
    return models.Paper.objects.filter(arxiv_id__in = ())

def category(user, category_code, *args, **kwargs):
    return models.Paper.objects.filter(arxiv_id__in = ())

def search(user, value, *args, **kwargs):
    return models.Paper.objects.filter(arxiv_id__in = ())