"""Integration-style tests for budget controller"""
import json
from unittest.mock import Mock, patch

from controller.budget_controller import BudgetController
from model.budget import budget


def _handler(path='/budgets', body=None):
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
        'role': 'user',
    }
    return handler


class TestBudgetController:
    def test_list_budgets(self):
        handler = _handler()
        records = [
            budget(1, 500, 'Food', '2024-01-01', '2024-01-31', 1),
        ]
        with patch('controller.budget_controller.get_budgets_by_user', return_value=records):
            with patch('controller.budget_controller.get_budget_spending', return_value={'percentage_used': 50}):
                ctrl = BudgetController(handler, {})
                resp = ctrl.handle_get()
        assert resp['status_code'] == 200
        data = json.loads(resp['body'])
        assert len(data) == 1

    def test_get_other_users_budget_forbidden(self):
        handler = _handler(path='/budgets/9')
        other = budget(9, 100, 'Food', '2024-01-01', '2024-01-31', 99)
        with patch('controller.budget_controller.get_budget_by_id', return_value=other):
            ctrl = BudgetController(handler, {})
            resp = ctrl.handle_get()
        assert resp['status_code'] == 404

    def test_create_budget(self):
        body = {
            'amount': 300,
            'category': 'Food',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
        }
        handler = _handler(body=body)
        with patch('controller.budget_controller.create_budget', return_value=True):
            with patch('controller.budget_controller.invalidate_user_cache'):
                ctrl = BudgetController(handler, {})
                resp = ctrl.handle_post()
        assert resp['status_code'] == 201
