#2015
#Author: HP Truong

import BaseHTTPServer
import json
import logging
import urlparse
from pprint import pprint
import os
import sys
import traceback
from SocketServer import ThreadingMixIn
import threading
import Queue
import time

LOGGER = logging.getLogger(__name__)

CLIENT_DIR = os.path.dirname(os.path.abspath(__file__))

class NewConnectionHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Handles client HTTP requests.
    """
    MANAGER = None

    # Override __init__ to instantiate Manager, pass along parameters:
    # BaseHTTPServer.BaseHTTPRequestHandler(request, client_address, 
    #                                       server)
    def __init__(self, *args):
        """
        :param args args: Arguments to set up 
            :class:`BaseHTTPServer.BaseHTTPRequestHandler`

        """
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args)
    
    # __del__ does not override anything
    def __del__(self):
        #print "Destructing NewConnectionHandler"
        pass
        
    def do_GET(self):
        """Handles a GET request.
        """

        parsed_path = urlparse.urlparse(self.path)
        try:
            params = dict([p.split('=') for p in parsed_path[4].split('&')])
        except:
            params = {}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        
        print "Do GET"
        #Open response file
        self.wfile.write('{"value" : "Do GET"}')

    def do_POST(self):
        """Handles a POST request.
        """
        # Parse the form data posted
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        # JSONfile = json.loads(data_string)
        print "Do POST"

        # Begin the response
        self.send_response(200)
        self.end_headers()

        # function = JSONfile['function']
        # parameters = JSONfile['parameters']

    # Sends a document, unused
    def sendPage( self, type, body ):
        """Sends a page to a client.  Unused at the moment.

        :param str type: Type of data being sent ex. ``'application/json'``
        :param body: Data to send to client.

        """
        self.send_response( 200 )
        self.send_header( "Content-type", type )
        self.send_header( "Content-length", str(len(body)) )
        self.end_headers()
        self.wfile.write( body )
        

class ManagerServer(ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """Builds upon :class:`BaseHTTPServer.HTTPServer`.
    """
    def serve_forever(self):
        """Run to start the ManagerServer."""
        BaseHTTPServer.HTTPServer.serve_forever(self)
    
    def server_close(self):
        """Run to close the ManagerServer."""
        # Delete all references to manager so it destructs
        BaseHTTPServer.HTTPServer.server_close(self) 

def main():
    """An entry point for launching the server.
    """
    handler_class=NewConnectionHandler
    server_address = ('', 5554)
    try:
        msrvr = ManagerServer(server_address, handler_class)
        print "Starting server..."
        msrvr.serve_forever()
    except KeyboardInterrupt, KeyboardInterruptStopEvent:
        print "Shutting down server..."
        msrvr.server_close()
    except Exception:
        traceback.print_exc(file=sys.stdout)

if __name__ == "__main__":
    main()
