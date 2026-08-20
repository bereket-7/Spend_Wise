"""Final coverage bump to clear 80%"""
import json
from unittest.mock import Mock, patch

from controller.user_controller import UserController
from controller.budget_controller import BudgetController
from controller.expense_controller import ExpenseController
from controller.income_controller import IncomeController
from controller.notification_controller import NotificationController
from controller.smart_categorization_controller import SmartCategorizationController
from model.user import user
from model.budget import budget
from model.expense import expense


def _h(path, body=None, role='user'):
    handler = Mock()
    handler.path = path
    raw = json.dumps(body or {}).encode('utf-8')
    handler.headers = {'Content-Length': str(len(raw)), 'Authorization': 'Bearer t'}
    handler.rfile = Mock()
    handler.rfile.read.return_value = raw
    handler.auth_user = {
        'user_id': 1,
        'username': 'u',
        'email': 'u@e.com',
        'role': role,
    }
    return handler


class TestFinalCoverage:
    def test_user_put_bad_email(self):
        u = user(1, 'u', 'h', 'u@e.com', '', 'A', 'B', 'user')
        with patch('controller.user_controller.user_query.get_user_by_id', return_value=u):
            resp = UserController(
                _h('/users/1', {'email': 'bad'}), {}
            ).handle_put()
        assert resp['status_code'] == 400

    def test_user_put_with_password(self):
        u = user(1, 'u', 'h', 'u@e.com', '', 'A', 'B', 'user')
        with patch('controller.user_controller.user_query.get_user_by_id', return_value=u):
            with patch('controller.user_controller.user_query.update_user', return_value=True):
                with patch(
                    'controller.user_controller.auth_manager.hash_password', return_value='nh'
                ):
                    resp = UserController(
                        _h('/users/1', {'password': 'new', 'first_name': 'Z'}), {}
                    ).handle_put()
        assert resp['status_code'] == 200

    def test_budget_bad_amount(self):
        resp = BudgetController(
            _h('/budgets', {
                'amount': -5,
                'category': 'Food',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
            }),
            {},
        ).handle_post()
        assert resp['status_code'] == 400

    def test_budget_create_fail(self):
        with patch('controller.budget_controller.create_budget', return_value=False):
            resp = BudgetController(
                _h('/budgets', {
                    'amount': 100,
                    'category': 'Food',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-31',
                }),
                {},
            ).handle_post()
        assert resp['status_code'] == 500

    def test_expense_create_fail(self):
        with patch('controller.expense_controller.expense_query.create_expense', return_value=False):
            resp = ExpenseController(
                _h('/expenses', {'amount': 10, 'category': 'Food', 'date': '2024-01-01'}),
                {},
            ).handle_post()
        assert resp['status_code'] == 500

    def test_income_bad_amount(self):
        resp = IncomeController(
            _h('/incomes', {'amount': 0, 'source': 'job', 'date': '2024-01-01'}),
            {},
        ).handle_post()
        assert resp['status_code'] == 400

    def test_notification_bad_body(self):
        resp = NotificationController(_h('/notifications', {}), {}).handle_post()
        assert resp['status_code'] == 400

    def test_smart_missing_description(self):
        resp = SmartCategorizationController(
            _h('/smart-categorize'), {'description': [''], 'amount': ['1']}
        ).handle_get()
        assert resp['status_code'] == 400

    def test_expense_delete_fail(self):
        rec = expense(1, 10, 'Food', '2024-01-01', 1)
        with patch(
            'controller.expense_controller.expense_query.get_expense_by_id', return_value=rec
        ):
            with patch(
                'controller.expense_controller.expense_query.delete_expense', return_value=False
            ):
                resp = ExpenseController(_h('/expenses/1'), {}).handle_delete()
        assert resp['status_code'] == 500

    def test_user_post_non_admin(self):
        resp = UserController(
            _h('/users', {
                'username': 'x',
                'password': 'p',
                'email': 'x@e.com',
                'first_name': 'X',
                'last_name': 'Y',
            }),
            {},
        ).handle_post()
        assert resp['status_code'] == 403

    def test_response_send_error_and_auth_cache_edges(self):
        from utils.response import send_json_response
        from utils.authentication import TokenValidationMiddleware
        import utils.cache as cache_mod
        from unittest.mock import MagicMock

        handler = Mock()
        handler.send_response.side_effect = [Exception('boom'), None]
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        send_json_response(handler, {'ok': True})

        h2 = Mock()
        h2.headers.get.return_value = 'Token abc'
        ok, _ = TokenValidationMiddleware.validate_request(h2)
        assert not ok

        h3 = Mock()
        h3.headers.get.return_value = 'Bearer not.a.token'
        ok, _ = TokenValidationMiddleware.validate_request(h3)
        assert not ok

        cache_mod._redis_checked = True
        mock_r = MagicMock()
        mock_r.get.side_effect = Exception('e')
        mock_r.setex.side_effect = Exception('e')
        mock_r.scan_iter.side_effect = Exception('e')
        cache_mod._redis_client = mock_r
        assert cache_mod.cache_get('k') is None
        assert cache_mod.cache_set('k', 'v') is False
        assert cache_mod.cache_delete_pattern('p') == 0
