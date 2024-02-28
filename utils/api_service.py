from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from response import json_response

class APIService(BaseHTTPRequestHandler):
    def _set_response(self, response):
        self.send_response(response['status_code'])
        for header, value in response['headers'].items():
            self.send_header(header, value)
        self.end_headers()

    def do_GET(self):
        response = self.handle_get()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def do_POST(self):
        response = self.handle_post()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def do_PUT(self):
        response = self.handle_put()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def do_DELETE(self):
        response = self.handle_delete()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def handle_get(self):
        raise NotImplementedError

    def handle_post(self):
        raise NotImplementedError

    def handle_put(self):
        raise NotImplementedError

    def handle_delete(self):
        raise NotImplementedError