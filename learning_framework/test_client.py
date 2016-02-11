import requests
import json

import config

HOST_NAME = config.server_name
PORT_NUMBER = config.port

if __name__ == "__main__":
    url = 'http://{0}:{1}'.format(HOST_NAME, PORT_NUMBER)
    headers = {'Content-type': 'application/json'}
    data = {
    	'action' : 'train',
    	'args' : []
    }

    x = requests.post(url, headers = headers, data = json.dumps(data))
    print x.json()
