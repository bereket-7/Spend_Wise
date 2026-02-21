import logging
from typing import Dict, Any, Optional
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

logger = logging.getLogger(__name__)

class APIService(BaseHTTPRequestHandler):
    """Base class for API services"""
    
    def _set_response(self, response):
        self.send_response(response['status_code'])
        for header, value in response['headers'].items():
            self.send_header(header, value)
        self.end_headers()

    def do_GET(self):
        query_params = parse_qs(urlparse(self.path).query)
        api_service = APIServiceHelper(self, query_params)
        response = api_service.handle_get()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def do_POST(self):
        query_params = parse_qs(urlparse(self.path).query)
        api_service = APIServiceHelper(self, query_params)
        response = api_service.handle_post()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def do_PUT(self):
        query_params = parse_qs(urlparse(self.path).query)
        api_service = APIServiceHelper(self, query_params)
        response = api_service.handle_put()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

    def do_DELETE(self):
        query_params = parse_qs(urlparse(self.path).query)
        api_service = APIServiceHelper(self, query_params)
        response = api_service.handle_delete()
        self._set_response(response)
        self.wfile.write(response['body'].encode('utf-8'))

class APIServiceHelper:
    """Helper class for API services"""
    
    def __init__(self, handler: BaseHTTPRequestHandler, query_params: Dict[str, Any]):
        self.handler = handler
        self.query_params = query_params
        self.path = handler.path
        
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests"""
        from utils.response import json_response
        return json_response({'message': 'GET method not implemented'}, 405)
    
    def handle_post(self) -> Dict[str, Any]:
        """Handle POST requests"""
        from utils.response import json_response
        return json_response({'message': 'POST method not implemented'}, 405)
    
    def handle_put(self) -> Dict[str, Any]:
        """Handle PUT requests"""
        from utils.response import json_response
        return json_response({'message': 'PUT method not implemented'}, 405)
    
    def handle_delete(self) -> Dict[str, Any]:
        """Handle DELETE requests"""
        from utils.response import json_response
        return json_response({'message': 'DELETE method not implemented'}, 405)
    
    def get_request_body(self) -> Optional[Dict[str, Any]]:
        """Parse JSON request body"""
        try:
            content_length = int(self.handler.headers['Content-Length'])
            body = self.handler.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error parsing request body: {e}")
            return None
    
    def send_response(self, response: Dict[str, Any]):
        """Send response using the handler"""
        status_code = response.get('status_code', 200)
        body = response.get('body', '{}')
        headers = response.get('headers', {})
        
        self.handler.send_response(status_code)
        for header_name, header_value in headers.items():
            self.handler.send_header(header_name, header_value)
        self.handler.end_headers()
        self.handler.wfile.write(body.encode('utf-8'))