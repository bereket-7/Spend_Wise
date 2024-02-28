from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from controller.expense_controller import handle_expense_request
from controller.user_controller import handle_user_request

class SpendWiseRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the request URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Extract the path from the URL
        path = parsed_url.path

        # Handle the request based on the path
        if path == '/expenses':
            handle_expense_request(self, query_params)
        elif path == '/users':
            handle_user_request(self, query_params)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')

def start_server():
    host = 'localhost'
    port = 8000
    server_address = (host, port)
    httpd = HTTPServer(server_address, SpendWiseRequestHandler)
    print(f'Server started on http://{host}:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    start_server()