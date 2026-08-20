"""
Spend Wise application entry point.
Load environment before importing modules that read configuration.
"""
from dotenv import load_dotenv

load_dotenv()

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import logging

import config.logging  # noqa: F401 — initialize logging once
from config.settings import config
from utils.response import json_response
from utils.authentication import TokenValidationMiddleware, PUBLIC_PATHS
from database.database_connection import check_database_health
from controller.user_controller import UserController
from controller.expense_controller import ExpenseController
from controller.auth_controller import AuthController
from controller.budget_controller import BudgetController
from controller.income_controller import IncomeController
from controller.notification_controller import NotificationController
from controller.financial_health_controller import FinancialHealthController
from controller.smart_categorization_controller import SmartCategorizationController
from controller.subscription_controller import SubscriptionController

logger = logging.getLogger(__name__)

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

    REQUEST_COUNT = Counter(
        'spendwise_http_requests_total',
        'Total HTTP requests',
        ['method', 'path_group'],
    )
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    REQUEST_COUNT = None


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS


def _require_auth(handler: BaseHTTPRequestHandler):
    """Return (True, user_data) or (False, error_response_dict)."""
    is_valid, auth_result = TokenValidationMiddleware.validate_request(handler)
    if not is_valid:
        return False, json_response(auth_result, 401)
    return True, auth_result


class SpendWiseRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        response = json_response({})
        self._send_response(response)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        if path == '/health':
            db_up = check_database_health()
            body = {
                'status': 'ok' if db_up else 'degraded',
                'database': 'up' if db_up else 'down',
            }
            status = 200 if db_up else 503
            self._send_response(json_response(body, status))
            return

        if path == '/metrics':
            if METRICS_AVAILABLE:
                payload = generate_latest()
                self.send_response(200)
                self.send_header('Content-Type', CONTENT_TYPE_LATEST)
                self.end_headers()
                self.wfile.write(payload)
            else:
                self._send_response(json_response({
                    'message': 'prometheus-client not installed'
                }, 501))
            return

        if not _is_public_path(path):
            ok, auth_or_err = _require_auth(self)
            if not ok:
                self._send_response(auth_or_err)
                return
            self.auth_user = auth_or_err
        else:
            self.auth_user = None

        if METRICS_AVAILABLE:
            REQUEST_COUNT.labels(method='GET', path_group=path.split('/')[1] or 'root').inc()

        if path == '/expenses' or path.startswith('/expenses/'):
            controller = ExpenseController(self, query_params)
            self._send_response(controller.handle_get())
        elif path == '/users' or path.startswith('/users/'):
            controller = UserController(self, query_params)
            self._send_response(controller.handle_get())
        elif path == '/budgets' or path.startswith('/budgets/'):
            controller = BudgetController(self, query_params)
            self._send_response(controller.handle_get())
        elif path == '/incomes' or path.startswith('/incomes/'):
            controller = IncomeController(self, query_params)
            self._send_response(controller.handle_get())
        elif path == '/notifications' or path.startswith('/notifications/'):
            controller = NotificationController(self, query_params)
            self._send_response(controller.handle_get())
        elif path == '/financial-health':
            controller = FinancialHealthController(self, query_params)
            self._send_response(controller.handle_get())
        elif path in ('/smart-categorize', '/category-suggestions', '/spending-patterns'):
            controller = SmartCategorizationController(self, query_params)
            self._send_response(controller.handle_get())
        elif path in ('/subscriptions', '/subscription-alternatives', '/subscription-changes'):
            controller = SubscriptionController(self, query_params)
            self._send_response(controller.handle_get())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Not found'}).encode('utf-8'))

    def do_POST(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        if path in ('/auth/login', '/auth/register'):
            self.auth_user = None
            controller = AuthController(self, query_params)
            self._send_response(controller.handle_post())
            return

        if not _is_public_path(path):
            ok, auth_or_err = _require_auth(self)
            if not ok:
                self._send_response(auth_or_err)
                return
            self.auth_user = auth_or_err
        else:
            self.auth_user = None

        if path == '/expenses':
            controller = ExpenseController(self, query_params)
            self._send_response(controller.handle_post())
        elif path == '/users':
            controller = UserController(self, query_params)
            self._send_response(controller.handle_post())
        elif path == '/budgets':
            controller = BudgetController(self, query_params)
            self._send_response(controller.handle_post())
        elif path == '/incomes':
            controller = IncomeController(self, query_params)
            self._send_response(controller.handle_post())
        elif path == '/notifications':
            controller = NotificationController(self, query_params)
            self._send_response(controller.handle_post())
        elif path == '/learn-categorization':
            controller = SmartCategorizationController(self, query_params)
            self._send_response(controller.handle_post())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Not found'}).encode('utf-8'))

    def do_PUT(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        ok, auth_or_err = _require_auth(self)
        if not ok:
            self._send_response(auth_or_err)
            return
        self.auth_user = auth_or_err

        if path.startswith('/expenses/'):
            controller = ExpenseController(self, query_params)
            self._send_response(controller.handle_put())
        elif path.startswith('/users/'):
            controller = UserController(self, query_params)
            self._send_response(controller.handle_put())
        elif path.startswith('/budgets/'):
            controller = BudgetController(self, query_params)
            self._send_response(controller.handle_put())
        elif path.startswith('/incomes/'):
            controller = IncomeController(self, query_params)
            self._send_response(controller.handle_put())
        elif path.startswith('/notifications/'):
            controller = NotificationController(self, query_params)
            self._send_response(controller.handle_put())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Not found'}).encode('utf-8'))

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        path = parsed_url.path

        ok, auth_or_err = _require_auth(self)
        if not ok:
            self._send_response(auth_or_err)
            return
        self.auth_user = auth_or_err

        if path.startswith('/expenses/'):
            controller = ExpenseController(self, query_params)
            self._send_response(controller.handle_delete())
        elif path.startswith('/users/'):
            controller = UserController(self, query_params)
            self._send_response(controller.handle_delete())
        elif path.startswith('/budgets/'):
            controller = BudgetController(self, query_params)
            self._send_response(controller.handle_delete())
        elif path.startswith('/incomes/'):
            controller = IncomeController(self, query_params)
            self._send_response(controller.handle_delete())
        elif path.startswith('/notifications/'):
            controller = NotificationController(self, query_params)
            self._send_response(controller.handle_delete())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Not found'}).encode('utf-8'))

    def _send_response(self, response):
        """Send response using the response dictionary"""
        status_code = response.get('status_code', 200)
        body = response.get('body', '{}')
        headers = response.get('headers', {})

        self.send_response(status_code)
        for header_name, header_value in headers.items():
            self.send_header(header_name, header_value)
        self.end_headers()
        if isinstance(body, bytes):
            self.wfile.write(body)
        else:
            self.wfile.write(body.encode('utf-8'))

    def log_message(self, format, *args):
        logger.info("%s - %s", self.address_string(), format % args)


def start_server():
    host = config.server.host
    if config.is_production() and host == 'localhost':
        host = '0.0.0.0'
    port = config.server.port
    server_address = (host, port)
    httpd = HTTPServer(server_address, SpendWiseRequestHandler)
    print(f'Server started on http://{host}:{port}')
    print('Available endpoints:')
    print('  GET  /health')
    print('  GET  /metrics')
    print('  POST /auth/login')
    print('  POST /auth/register')
    print('  CRUD /users, /expenses, /budgets, /incomes, /notifications')
    print('  GET  /financial-health, /smart-categorize, /subscriptions, ...')
    httpd.serve_forever()


if __name__ == '__main__':
    start_server()
