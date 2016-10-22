
import logging
import traceback
import json
import time
from SocketServer import ThreadingMixIn
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
            status_code = 200
        except:
            result = traceback.format_exc()
            status_code = 500

        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(result))

class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""
    pass

if __name__ == '__main__':
    logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(filename)s][%(lineno)d] - %(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        filename='/home/ml/arxivapp/site/arxivapp/learning_framework/manager.log',
                        filemode='a',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.info('Initializing manager.')

    processor.initialize()

    # server_class = BaseHTTPServer.HTTPServer
    server_class = ThreadedHTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), LearningManager)
    logger.info("Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Caught interrupt signal. Terminating...")
    httpd.server_close()
    logger.info("Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
