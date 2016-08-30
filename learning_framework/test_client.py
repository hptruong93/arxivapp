import requests
import json
import argparse

import config

HOST_NAME = config.server_name
PORT_NUMBER = config.port

def do_request(data):
    x = requests.post(url, headers = headers, data = json.dumps(data))
    print x.json()

def extract_data():
    data = {
            'action' : 'extract_data',
            'args' : []
        }
    do_request(data)

def split_data():
    data = {
            'action' : 'split_data',
            'args' : []
        }
    do_request(data)

def train():
    data = {
            'action' : 'train',
            'args' : [config.CATEGORY_COUNT + config.LDA_TOPIC_COUNT, 1, 1],
            'kwargs' : {'input_load_data' : '/home/ml/arxivapp/site/arxivapp/test_data'}
        }
    do_request(data)

def predict():
    data = {
            'action' : 'predict',
            'args' : [1]
        }
    do_request(data)

def sort():
    data = {
            'action' : '{0}'.format(args.f),
            'args': [1, [u'1603.03007', u'1603.02738', u'1603.02740', u'1603.02776', u'1603.02028', u'1603.02038', u'1603.02041', u'1603.02199', u'1603.02208', u'1603.01840', u'1603.01882', u'1603.01722', u'1603.01770', u'1603.02626', u'1603.01524', u'1603.01581', u'1603.01595', u'1603.01006', u'1603.01067', u'1603.01121']],
        }
    do_request(data)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Learning interface test client')
    parser.add_argument('-f', type=str, required=False, default = 'extract_data', help='name of the function to run')
    args = parser.parse_args()

    url = 'http://{0}:{1}'.format(HOST_NAME, PORT_NUMBER)
    headers = {'Content-type': 'application/json'}

    if args.f == 'train':
        train()
    elif args.f == 'predict':
        predict()
    elif args.f == 'sort':
        sort()
    elif args.f == 'split_data':
        split_data()
    elif args.f == 'extract_data':
        extract_data()
    elif args.f == 'till_train':
        extract_data()
        split_data()
        train()
    else:
        data = {
            'action' : '{0}'.format(args.f),
            'args' : []
        }
        do_request(data)