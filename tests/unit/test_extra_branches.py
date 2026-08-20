"""Extra branch coverage for controllers and utilities"""
import json
from unittest.mock import Mock, patch, MagicMock

from controller.budget_controller import BudgetController
from controller.user_controller import UserController
from controller.notification_controller import NotificationController
from controller.smart_categorization_controller import SmartCategorizationController
from controller.subscription_controller import SubscriptionController
from controller.expense_controller import ExpenseController
from model.budget import budget
from model.user import user
from model.notification import notification
from utils.response import validate_phone_number, send_json_response
from database.database_connection import get_connection, release_connection, initialize_connection_pool


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
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.wfile = Mock()
    return handler


class TestBudgetBranches:
    def test_spending_and_put_delete(self):
        b = budget(1, 100, 'Food', '2024-01-01', '2024-01-31', 1)
        with patch('controller.budget_controller.get_budget_by_id', return_value=b):
            with patch(
                'controller.budget_controller.get_budget_spending',
                return_value={'percentage_used': 50},
            ):
                resp = BudgetController(_h('/budgets/1/spending'), {}).handle_get()
        assert resp['status_code'] == 200

        with patch('controller.budget_controller.get_budget_by_id', return_value=b):
            with patch('controller.budget_controller.update_budget', return_value=True):
                with patch('controller.budget_controller.invalidate_user_cache'):
                    resp = BudgetController(
                        _h('/budgets/1', {'amount': 200}), {}
                    ).handle_put()
        assert resp['status_code'] == 200

        with patch('controller.budget_controller.get_budget_by_id', return_value=b):
            with patch('controller.budget_controller.delete_budget', return_value=True):
                with patch('controller.budget_controller.invalidate_user_cache'):
                    resp = BudgetController(_h('/budgets/1'), {}).handle_delete()
        assert resp['status_code'] == 200


class TestUserPostAdmin:
    def test_admin_create_user(self):
        body = {
            'username': 'x',
            'password': 'p',
            'email': 'x@e.com',
            'first_name': 'X',
            'last_name': 'Y',
        }
        with patch('controller.user_controller.user_query.create_user', return_value=True):
            with patch(
                'controller.user_controller.auth_manager.hash_password', return_value='h'
            ):
                resp = UserController(_h('/users', body, role='admin'), {}).handle_post()
        assert resp['status_code'] == 201


class TestNotificationBranches:
    def test_get_one_delete_read_all(self):
        n = notification(1, 'system', 'hi', 1)
        with patch(
            'controller.notification_controller.get_notification_by_id', return_value=n
        ):
            resp = NotificationController(_h('/notifications/1'), {}).handle_get()
        assert resp['status_code'] == 200

        with patch(
            'controller.notification_controller.mark_all_notifications_as_read',
            return_value=True,
        ):
            resp = NotificationController(_h('/notifications/read-all'), {}).handle_put()
        assert resp['status_code'] == 200

        with patch(
            'controller.notification_controller.get_notification_by_id', return_value=n
        ):
            with patch(
                'controller.notification_controller.delete_notification', return_value=True
            ):
                resp = NotificationController(_h('/notifications/1'), {}).handle_delete()
        assert resp['status_code'] == 200


class TestSmartLearnAndSubs:
    def test_learn_and_suggestions(self):
        body = {
            'original_description': 'coffee',
            'original_category': 'Other',
            'correct_category': 'Food',
            'amount': 5,
        }
        with patch(
            'controller.smart_categorization_controller.ExpenseCategorizer.learn_from_correction'
        ):
            resp = SmartCategorizationController(
                _h('/learn-categorization', body), {}
            ).handle_post()
        assert resp['status_code'] == 200

        with patch(
            'controller.smart_categorization_controller.ExpenseCategorizer.get_category_suggestions',
            return_value=[{'category': 'Food'}],
        ):
            resp = SmartCategorizationController(
                _h('/category-suggestions'), {'text': ['food']}
            ).handle_get()
        assert resp['status_code'] == 200

    def test_subscription_alts_and_changes(self):
        with patch(
            'controller.subscription_controller.SubscriptionManager'
        ) as MockMgr:
            MockMgr.return_value.get_alternative_services.return_value = []
            resp = SubscriptionController(
                _h('/subscription-alternatives'), {'service': ['netflix']}
            ).handle_get()
        assert resp['status_code'] == 200

        with patch(
            'controller.subscription_controller.SubscriptionManager'
        ) as MockMgr:
            MockMgr.return_value.track_subscription_changes.return_value = {}
            resp = SubscriptionController(
                _h('/subscription-changes'), {'days': ['30']}
            ).handle_get()
        assert resp['status_code'] == 200


class TestExpenseValidation:
    def test_post_missing_fields(self):
        resp = ExpenseController(_h('/expenses', {'amount': 1}), {}).handle_post()
        assert resp['status_code'] == 400

    def test_post_bad_amount(self):
        resp = ExpenseController(
            _h('/expenses', {'amount': -1, 'category': 'Food', 'date': '2024-01-01'}), {}
        ).handle_post()
        assert resp['status_code'] == 400


class TestUtilsExtra:
    def test_phone_and_send_json(self):
        assert validate_phone_number('1234567890')
        assert not validate_phone_number('abc')
        handler = _h('/x')
        send_json_response(handler, {'ok': True}, 200)
        handler.send_response.assert_called()

    def test_db_pool_init_failure(self):
        with patch(
            'database.database_connection.pooling.MySQLConnectionPool',
            side_effect=Exception('fail'),
        ):
            assert initialize_connection_pool() is None

    def test_get_connection_when_pool_none(self):
        import database.database_connection as dbc

        dbc.connection_pool = None
        with patch(
            'database.database_connection.initialize_connection_pool', return_value=None
        ):
            assert get_connection() is None
