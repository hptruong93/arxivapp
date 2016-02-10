import requests
import json

from config import CONFIG as config

HOST_NAME = config['server_name']
PORT_NUMBER = config['port']

if __name__ == "__main__":
    url = 'http://{0}:{1}'.format(HOST_NAME, PORT_NUMBER)
    headers = {'Content-type': 'application/json'}
    data = {'first_name' : 'Deepak', 'last_name' : 'Sharma', 'date_of_birth' : '1999/88/22'}

    x = requests.post(url, headers = headers, data = json.dumps(data))
    print x.json()
