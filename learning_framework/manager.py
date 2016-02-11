
import traceback
import json
import time
import BaseHTTPServer

import config
import processor

HOST_NAME = config.server_name
PORT_NUMBER = config.port


class LearningManager(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<html><head><title>Not supported.</title></head>")
        self.wfile.write("<body><p>Not supported.</p>")

    def do_POST(self):
        """Respond to a POST request."""
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        json_payload = json.loads(data_string)
        
        try:
            result = processor.process(json_payload)
        except:
            result = traceback.format_exc()

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result))

if __name__ == '__main__':
    processor.initialize()

    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), LearningManager)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "Caught interrupt signal. Terminating..."
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
