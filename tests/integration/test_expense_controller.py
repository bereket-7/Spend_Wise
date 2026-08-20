"""Integration-style tests for expense controller"""
import json
from unittest.mock import Mock, patch, MagicMock

from controller.expense_controller import ExpenseController
from model.expense import expense


def _handler(path='/expenses', body=None, user=None):
    handler = Mock()
    handler.path = path
    payload = body or {}
    raw = json.dumps(payload).encode('utf-8')
    handler.headers = {
        'Authorization': 'Bearer tok',
        'Content-Length': str(len(raw)),
    }
    handler.rfile = Mock()
    handler.rfile.read.return_value = raw
    handler.auth_user = user or {
        'user_id': 1,
        'username': 'u',
        'email': 'u@e.com',
        'role': 'user',
    }
    return handler


class TestExpenseController:
    def test_get_list_requires_auth(self):
        handler = _handler()
        handler.auth_user = None
        with patch.object(ExpenseController, 'get_auth_user', return_value=None):
            ctrl = ExpenseController(handler, {})
            resp = ctrl.handle_get()
        assert resp['status_code'] == 401

    def test_get_list_scoped(self):
        handler = _handler()
        records = [
            expense(1, 10.0, 'Food', '2024-01-01', 1, 'lunch'),
        ]
        with patch('controller.expense_controller.expense_query.get_expenses_by_user', return_value=records):
            ctrl = ExpenseController(handler, {})
            resp = ctrl.handle_get()
        assert resp['status_code'] == 200
        data = json.loads(resp['body'])
        assert len(data) == 1
        assert data[0]['category'] == 'Food'

    def test_post_create(self):
        body = {'amount': 20, 'category': 'Food', 'date': '2024-01-01'}
        handler = _handler(body=body)
        with patch('controller.expense_controller.expense_query.create_expense', return_value=True):
            with patch('controller.expense_controller.invalidate_user_cache'):
                ctrl = ExpenseController(handler, {})
                resp = ctrl.handle_post()
        assert resp['status_code'] == 201

    def test_get_by_id_not_found(self):
        handler = _handler(path='/expenses/99')
        with patch('controller.expense_controller.expense_query.get_expense_by_id', return_value=None):
            ctrl = ExpenseController(handler, {})
            resp = ctrl.handle_get()
        assert resp['status_code'] == 404

    def test_delete_success(self):
        handler = _handler(path='/expenses/5')
        record = expense(5, 10.0, 'Food', '2024-01-01', 1)
        with patch('controller.expense_controller.expense_query.get_expense_by_id', return_value=record):
            with patch('controller.expense_controller.expense_query.delete_expense', return_value=True):
                with patch('controller.expense_controller.invalidate_user_cache'):
                    ctrl = ExpenseController(handler, {})
                    resp = ctrl.handle_delete()
        assert resp['status_code'] == 200
