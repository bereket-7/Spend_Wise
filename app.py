from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from controller.user_controller import UserController
from controller.expense_controller import ExpenseController
from controller.auth_controller import AuthController
from controller.budget_controller import BudgetController
from controller.income_controller import IncomeController
from controller.notification_controller import NotificationController
from controller.financial_health_controller import FinancialHealthController
from controller.smart_categorization_controller import SmartCategorizationController
from controller.subscription_controller import SubscriptionController

class SpendWiseRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the request URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Extract the path from the URL
        path = parsed_url.path

        # Handle the request based on the path
        if path == '/expenses' or path.startswith('/expenses/'):
            controller = ExpenseController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/users' or path.startswith('/users/'):
            controller = UserController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/auth/login' or path == '/auth/register':
            controller = AuthController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/budgets' or path.startswith('/budgets/'):
            controller = BudgetController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/incomes' or path.startswith('/incomes/'):
            controller = IncomeController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/notifications' or path.startswith('/notifications/'):
            controller = NotificationController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/financial-health':
            controller = FinancialHealthController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/smart-categorize' or path == '/category-suggestions' or path == '/spending-patterns':
            controller = SmartCategorizationController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        elif path == '/subscriptions' or path == '/subscription-alternatives' or path == '/subscription-changes':
            controller = SubscriptionController(self, query_params)
            response = controller.handle_get()
            self._send_response(response)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def do_POST(self):
        # Parse the request URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Extract the path from the URL
        path = parsed_url.path

        # Handle the request based on the path
        if path == '/expenses':
            controller = ExpenseController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/users':
            controller = UserController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/auth/login' or path == '/auth/register':
            controller = AuthController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/budgets':
            controller = BudgetController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/incomes':
            controller = IncomeController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/notifications':
            controller = NotificationController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        elif path == '/learn-categorization':
            controller = SmartCategorizationController(self, query_params)
            response = controller.handle_post()
            self._send_response(response)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def do_PUT(self):
        # Parse the request URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Extract the path from the URL
        path = parsed_url.path

        # Handle the request based on the path
        if path.startswith('/expenses/'):
            controller = ExpenseController(self, query_params)
            response = controller.handle_put()
            self._send_response(response)
        elif path.startswith('/users/'):
            controller = UserController(self, query_params)
            response = controller.handle_put()
            self._send_response(response)
        elif path.startswith('/budgets/'):
            controller = BudgetController(self, query_params)
            response = controller.handle_put()
            self._send_response(response)
        elif path.startswith('/incomes/'):
            controller = IncomeController(self, query_params)
            response = controller.handle_put()
            self._send_response(response)
        elif path.startswith('/notifications/'):
            controller = NotificationController(self, query_params)
            response = controller.handle_put()
            self._send_response(response)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def do_DELETE(self):
        # Parse the request URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        # Extract the path from the URL
        path = parsed_url.path

        # Handle the request based on the path
        if path.startswith('/expenses/'):
            controller = ExpenseController(self, query_params)
            response = controller.handle_delete()
            self._send_response(response)
        elif path.startswith('/users/'):
            controller = UserController(self, query_params)
            response = controller.handle_delete()
            self._send_response(response)
        elif path.startswith('/budgets/'):
            controller = BudgetController(self, query_params)
            response = controller.handle_delete()
            self._send_response(response)
        elif path.startswith('/incomes/'):
            controller = IncomeController(self, query_params)
            response = controller.handle_delete()
            self._send_response(response)
        elif path.startswith('/notifications/'):
            controller = NotificationController(self, query_params)
            response = controller.handle_delete()
            self._send_response(response)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def _send_response(self, response):
        """Send response using the response dictionary"""
        status_code = response.get('status_code', 200)
        body = response.get('body', '{}')
        headers = response.get('headers', {})
        
        self.send_response(status_code)
        for header_name, header_value in headers.items():
            self.send_header(header_name, header_value)
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

def start_server():
    host = 'localhost'
    port = 8000
    server_address = (host, port)
    httpd = HTTPServer(server_address, SpendWiseRequestHandler)
    print(f'Server started on http://{host}:{port}')
    print('Available endpoints:')
    print('  Authentication:')
    print('    POST /auth/login')
    print('    POST /auth/register')
    print('  Users:')
    print('    GET /users')
    print('    GET /users/{id}')
    print('    POST /users')
    print('    PUT /users/{id}')
    print('    DELETE /users/{id}')
    print('  Expenses:')
    print('    GET /expenses')
    print('    GET /expenses/{id}')
    print('    POST /expenses')
    print('    PUT /expenses/{id}')
    print('    DELETE /expenses/{id}')
    print('  Budgets:')
    print('    GET /budgets')
    print('    GET /budgets/{id}')
    print('    GET /budgets/{id}/spending')
    print('    POST /budgets')
    print('    PUT /budgets/{id}')
    print('    DELETE /budgets/{id}')
    print('  Incomes:')
    print('    GET /incomes')
    print('    GET /incomes/{id}')
    print('    GET /incomes/summary')
    print('    POST /incomes')
    print('    PUT /incomes/{id}')
    print('    DELETE /incomes/{id}')
    print('  Notifications:')
    print('    GET /notifications')
    print('    GET /notifications/{id}')
    print('    GET /notifications/unread-count')
    print('    POST /notifications')
    print('    PUT /notifications/{id}/read')
    print('    PUT /notifications/read-all')
    print('    DELETE /notifications/{id}')
    print('  🆕 Smart Features:')
    print('    GET /financial-health')
    print('    GET /smart-categorize?description={text}&amount={num}&merchant={text}')
    print('    GET /category-suggestions?text={partial_text}')
    print('    GET /spending-patterns?days={num}')
    print('    POST /learn-categorization')
    print('    GET /subscriptions?days={num}')
    print('    GET /subscription-alternatives?service={name}&max_cost={num}')
    print('    GET /subscription-changes?days={num}')
    httpd.serve_forever()

if __name__ == '__main__':
    start_server()
