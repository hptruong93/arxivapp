import requests
import json
import argparse

import config

HOST_NAME = config.server_name
PORT_NUMBER = config.port

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Learning interface test client')
    parser.add_argument('-f', type=str, required=False, default = 'extract_data', help='name of the function to run')
    args = parser.parse_args()

    url = 'http://{0}:{1}'.format(HOST_NAME, PORT_NUMBER)
    headers = {'Content-type': 'application/json'}

    if args.f == 'train':
        data = {
            'action' : '{0}'.format(args.f),
            'args' : [168, 1, 1],
            'kwargs' : {'input_load_data' : '/home/ml/arxivapp/site/arxivapp/test_data'}
        }
    elif args.f == 'predict':
        data = {
            'action' : '{0}'.format(args.f),
            'args' : [1]
        }
    elif args.f == 'sort':
        data = {
            'action' : '{0}'.format(args.f),
            'args': [1, [u'1603.03007', u'1603.02738', u'1603.02740', u'1603.02776', u'1603.02028', u'1603.02038', u'1603.02041', u'1603.02199', u'1603.02208', u'1603.01840', u'1603.01882', u'1603.01722', u'1603.01770', u'1603.02626', u'1603.01524', u'1603.01581', u'1603.01595', u'1603.01006', u'1603.01067', u'1603.01121']],
        }
    else:
        data = {
            'action' : '{0}'.format(args.f),
            'args' : []
        }

    x = requests.post(url, headers = headers, data = json.dumps(data))
    print x.json()
