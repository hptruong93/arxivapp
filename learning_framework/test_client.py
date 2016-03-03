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
    else:
        data = {
            'action' : '{0}'.format(args.f),
            'args' : []
        }

    x = requests.post(url, headers = headers, data = json.dumps(data))
    print x.json()
