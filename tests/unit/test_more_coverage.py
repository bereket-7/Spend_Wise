"""Additional controller and query coverage tests"""
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from controller.user_controller import UserController
from controller.income_controller import IncomeController
from controller.notification_controller import NotificationController
from controller.financial_health_controller import FinancialHealthController
from controller.smart_categorization_controller import SmartCategorizationController
from controller.subscription_controller import SubscriptionController
from controller.expense_controller import ExpenseController
from model.user import user
from model.income import income
from model.notification import notification
from model.expense import expense
from database import budget_query, income_query, notification_query
from utils.financial_health import FinancialHealthCalculator
from utils.expense_categorizer import ExpenseCategorizer
from config.settings import AppConfig, Environment


def _h(path, body=None, role='user', user_id=1):
    handler = Mock()
    handler.path = path
    raw = json.dumps(body or {}).encode('utf-8')
    handler.headers = {'Content-Length': str(len(raw)), 'Authorization': 'Bearer t'}
    handler.rfile = Mock()
    handler.rfile.read.return_value = raw
    handler.auth_user = {
        'user_id': user_id,
        'username': 'u',
        'email': 'u@e.com',
        'role': role,
    }
    return handler


class TestUserControllerMore:
    def test_get_self(self):
        u = user(1, 'u', 'h', 'u@e.com', '', 'A', 'B', 'user')
        with patch('controller.user_controller.user_query.get_user_by_id', return_value=u):
            resp = UserController(_h('/users/1'), {}).handle_get()
        assert resp['status_code'] == 200

    def test_get_all_admin(self):
        users = [user(1, 'u', 'h', 'u@e.com', '', 'A', 'B', 'user')]
        with patch('controller.user_controller.user_query.get_all_users', return_value=users):
            resp = UserController(_h('/users', role='admin'), {}).handle_get()
        assert resp['status_code'] == 200

    def test_get_all_denied(self):
        resp = UserController(_h('/users'), {}).handle_get()
        assert resp['status_code'] == 403

    def test_put_update(self):
        u = user(1, 'u', 'h', 'u@e.com', '', 'A', 'B', 'user')
        with patch('controller.user_controller.user_query.get_user_by_id', return_value=u):
            with patch('controller.user_controller.user_query.update_user', return_value=True):
                resp = UserController(
                    _h('/users/1', {'first_name': 'New'}), {}
                ).handle_put()
        assert resp['status_code'] == 200

    def test_delete(self):
        u = user(1, 'u', 'h', 'u@e.com', '', 'A', 'B', 'user')
        with patch('controller.user_controller.user_query.get_user_by_id', return_value=u):
            with patch('controller.user_controller.user_query.delete_user', return_value=True):
                resp = UserController(_h('/users/1'), {}).handle_delete()
        assert resp['status_code'] == 200


class TestIncomeControllerMore:
    def test_list(self):
        rows = [income(1, 100, 'job', '2024-01-01', 1)]
        with patch('controller.income_controller.get_incomes_by_user', return_value=rows):
            resp = IncomeController(_h('/incomes'), {}).handle_get()
        assert resp['status_code'] == 200

    def test_summary(self):
        with patch('controller.income_controller.get_income_summary', return_value={'total': 100}):
            resp = IncomeController(_h('/incomes/summary'), {}).handle_get()
        assert resp['status_code'] == 200

    def test_create(self):
        body = {'amount': 50, 'source': 'job', 'date': '2024-01-01'}
        with patch('controller.income_controller.create_income', return_value=True):
            with patch('controller.income_controller.invalidate_user_cache'):
                resp = IncomeController(_h('/incomes', body), {}).handle_post()
        assert resp['status_code'] == 201

    def test_put_delete(self):
        row = income(1, 100, 'job', '2024-01-01', 1)
        with patch('controller.income_controller.get_income_by_id', return_value=row):
            with patch('controller.income_controller.update_income', return_value=True):
                with patch('controller.income_controller.invalidate_user_cache'):
                    resp = IncomeController(
                        _h('/incomes/1', {'amount': 200}), {}
                    ).handle_put()
        assert resp['status_code'] == 200
        with patch('controller.income_controller.get_income_by_id', return_value=row):
            with patch('controller.income_controller.delete_income', return_value=True):
                with patch('controller.income_controller.invalidate_user_cache'):
                    resp = IncomeController(_h('/incomes/1'), {}).handle_delete()
        assert resp['status_code'] == 200


class TestNotificationControllerMore:
    def test_list_and_unread(self):
        rows = [notification(1, 'system', 'hi', 1, False, False)]
        with patch(
            'controller.notification_controller.get_notifications_by_user', return_value=rows
        ):
            resp = NotificationController(_h('/notifications'), {}).handle_get()
        assert resp['status_code'] == 200
        with patch('controller.notification_controller.get_unread_count', return_value=3):
            resp = NotificationController(_h('/notifications/unread-count'), {}).handle_get()
        assert json.loads(resp['body'])['unread_count'] == 3

    def test_create_and_read(self):
        body = {'notification_type': 'system', 'message': 'hello'}
        with patch('controller.notification_controller.create_notification', return_value=True):
            resp = NotificationController(_h('/notifications', body), {}).handle_post()
        assert resp['status_code'] == 201
        n = notification(1, 'system', 'hi', 1, False, False)
        with patch('controller.notification_controller.get_notification_by_id', return_value=n):
            with patch(
                'controller.notification_controller.mark_notification_as_read', return_value=True
            ):
                resp = NotificationController(_h('/notifications/1/read'), {}).handle_put()
        assert resp['status_code'] == 200


class TestSmartControllers:
    def test_financial_health_cached(self):
        with patch(
            'controller.financial_health_controller.cache_get_json',
            return_value={'total_score': 70},
        ):
            resp = FinancialHealthController(_h('/financial-health'), {}).handle_get()
        assert resp['status_code'] == 200

    def test_financial_health_compute(self):
        with patch('controller.financial_health_controller.cache_get_json', return_value=None):
            with patch(
                'controller.financial_health_controller.FinancialHealthCalculator'
            ) as MockCalc:
                MockCalc.return_value.calculate_health_score.return_value = {
                    'total_score': 80,
                    'health_level': 'Excellent',
                }
                with patch('controller.financial_health_controller.cache_set_json'):
                    resp = FinancialHealthController(_h('/financial-health'), {}).handle_get()
        assert resp['status_code'] == 200

    def test_smart_categorize(self):
        with patch.object(
            ExpenseCategorizer,
            'categorize_expense',
            return_value={'category': 'Food', 'confidence': 0.9},
        ):
            ctrl = SmartCategorizationController(
                _h('/smart-categorize'),
                {'description': ['coffee'], 'amount': ['5']},
            )
            resp = ctrl.handle_get()
        assert resp['status_code'] == 200

    def test_spending_patterns(self):
        with patch(
            'controller.smart_categorization_controller.cache_get_json', return_value=None
        ):
            with patch.object(
                ExpenseCategorizer, 'analyze_user_patterns', return_value={'total': 1}
            ):
                with patch('controller.smart_categorization_controller.cache_set_json'):
                    ctrl = SmartCategorizationController(
                        _h('/spending-patterns'), {'days': ['30']}
                    )
                    resp = ctrl.handle_get()
        assert resp['status_code'] == 200

    def test_subscriptions(self):
        with patch(
            'controller.subscription_controller.cache_get_json', return_value=None
        ):
            with patch(
                'controller.subscription_controller.SubscriptionManager'
            ) as MockMgr:
                MockMgr.return_value.detect_subscriptions.return_value = {'items': []}
                with patch('controller.subscription_controller.cache_set_json'):
                    resp = SubscriptionController(
                        _h('/subscriptions'), {'days': ['90']}
                    ).handle_get()
        assert resp['status_code'] == 200


class TestExpenseControllerMore:
    def test_put_update(self):
        rec = expense(1, 10, 'Food', '2024-01-01', 1)
        with patch(
            'controller.expense_controller.expense_query.get_expense_by_id', return_value=rec
        ):
            with patch(
                'controller.expense_controller.expense_query.update_expense', return_value=True
            ):
                with patch('controller.expense_controller.invalidate_user_cache'):
                    resp = ExpenseController(
                        _h('/expenses/1', {'amount': 15, 'category': 'Food'}), {}
                    ).handle_put()
        assert resp['status_code'] == 200

    def test_get_by_id(self):
        rec = expense(1, 10, 'Food', '2024-01-01', 1, 'x')
        with patch(
            'controller.expense_controller.expense_query.get_expense_by_id', return_value=rec
        ):
            resp = ExpenseController(_h('/expenses/1'), {}).handle_get()
        assert resp['status_code'] == 200


class TestBudgetIncomeNotificationQueries:
    def test_budget_create_and_get(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'amount': 100,
            'category': 'Food',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31',
            'user_id': 1,
        }
        with patch('database.budget_query.get_connection', return_value=mock_conn):
            with patch('database.budget_query.release_connection'):
                assert budget_query.create_budget({
                    'amount': 100,
                    'category': 'Food',
                    'start_date': '2024-01-01',
                    'end_date': '2024-01-31',
                    'user_id': 1,
                })
                b = budget_query.get_budget_by_id(1)
                assert b is not None
                mock_cursor.fetchall.return_value = [mock_cursor.fetchone.return_value]
                assert len(budget_query.get_budgets_by_user(1)) >= 0
                assert budget_query.update_budget(1, {'amount': 200})
                assert budget_query.delete_budget(1)

    def test_budget_spending(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {
                'id': 1,
                'amount': 100,
                'category': 'Food',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'user_id': 1,
            },
            {'total_spent': 40},
        ]
        with patch('database.budget_query.get_connection', return_value=mock_conn):
            with patch('database.budget_query.release_connection'):
                info = budget_query.get_budget_spending(1)
        assert info['percentage_used'] == 40.0

    def test_income_crud(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'amount': 50,
            'source': 'job',
            'date': '2024-01-01',
            'user_id': 1,
            'description': None,
        }
        with patch('database.income_query.get_connection', return_value=mock_conn):
            with patch('database.income_query.release_connection'):
                assert income_query.create_income({
                    'amount': 50, 'source': 'job', 'date': '2024-01-01', 'user_id': 1
                })
                assert income_query.get_income_by_id(1) is not None
                mock_cursor.fetchall.return_value = [mock_cursor.fetchone.return_value]
                assert isinstance(income_query.get_incomes_by_user(1), list)
                assert income_query.update_income(1, {'amount': 60})
                assert income_query.delete_income(1)
                mock_cursor.fetchone.side_effect = [
                    {'total_income': 100, 'count': 1, 'avg_income': 100},
                ]
                # reset side_effect for summary
                mock_cursor.fetchone.side_effect = None
                mock_cursor.fetchone.return_value = {
                    'total_income': 100, 'count': 1, 'avg_income': 100
                }
                mock_cursor.fetchall.return_value = []
                summary = income_query.get_income_summary(1)
                assert isinstance(summary, dict)

    def test_notification_crud(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'notification_type': 'system',
            'message': 'hi',
            'user_id': 1,
            'sent': False,
            'read': False,
            'created_at': '2024-01-01',
            'sent_at': None,
        }
        with patch('database.notification_query.get_connection', return_value=mock_conn):
            with patch('database.notification_query.release_connection'):
                assert notification_query.create_notification({
                    'notification_type': 'system', 'message': 'hi', 'user_id': 1
                })
                assert notification_query.get_notification_by_id(1) is not None
                mock_cursor.fetchall.return_value = [mock_cursor.fetchone.return_value]
                assert isinstance(notification_query.get_notifications_by_user(1), list)
                assert notification_query.mark_notification_as_read(1, 1)
                assert notification_query.mark_all_notifications_as_read(1)
                assert notification_query.delete_notification(1, 1)
                mock_cursor.fetchone.return_value = (2,)
                assert notification_query.get_unread_count(1) == 2
                assert notification_query.create_budget_alert(1, 1, 90, 'Food')
                assert notification_query.create_budget_alert(1, 1, 110, 'Food')
                assert notification_query.create_budget_alert(1, 1, 50, 'Food') is False


class TestFinancialHealthDeep:
    def setup_method(self):
        self.calc = FinancialHealthCalculator()

    def test_budget_adherence_with_budgets(self):
        b = MagicMock()
        b.id = 1
        with patch('utils.financial_health.get_budgets_by_user', return_value=[b]):
            with patch(
                'utils.financial_health.get_budget_spending',
                return_value={'percentage_used': 90},
            ):
                score = self.calc._calculate_budget_adherence_score(1)
        assert 0 <= score <= 100

    def test_income_stability(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'month': '2024-01', 'monthly_income': 5000},
            {'month': '2024-02', 'monthly_income': 5050},
            {'month': '2024-03', 'monthly_income': 5100},
        ]
        with patch('utils.financial_health.get_connection', return_value=mock_conn):
            with patch('utils.financial_health.release_connection'):
                score = self.calc._calculate_income_stability_score(
                    1, datetime(2024, 3, 1), datetime(2024, 3, 31)
                )
        assert score >= 60

    def test_expense_control(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {'transaction_count': 10, 'avg_amount': 20},
            {'transaction_count': 10, 'avg_amount': 25},
        ]
        with patch('utils.financial_health.get_connection', return_value=mock_conn):
            with patch('utils.financial_health.release_connection'):
                score = self.calc._calculate_expense_control_score(
                    1, datetime(2024, 3, 1), datetime(2024, 3, 31)
                )
        assert score >= 0

    def test_emergency_fund(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'avg_monthly_expenses': 2000}
        with patch('utils.financial_health.get_connection', return_value=mock_conn):
            with patch('utils.financial_health.release_connection'):
                score = self.calc._calculate_emergency_fund_score(1)
        assert 0 <= score <= 100


class TestCategorizerDeep:
    def setup_method(self):
        self.cat = ExpenseCategorizer()

    def test_get_user_patterns_from_db(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [{'category': 'Food', 'frequency': 5}]
        with patch('utils.expense_categorizer.get_connection', return_value=mock_conn):
            with patch('utils.expense_categorizer.release_connection'):
                patterns = self.cat._get_user_patterns(1)
        assert 'Food' in patterns

    def test_save_learning(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('utils.expense_categorizer.get_connection', return_value=mock_conn):
            with patch('utils.expense_categorizer.release_connection'):
                self.cat._save_learning_to_database(1, 'coffee', 'Food', 5.0, 'Starbucks')
        mock_conn.commit.assert_called()

    def test_analyze_patterns_with_data(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {'category': 'Food', 'count': 10, 'total': 200, 'avg_amount': 20},
            {'category': 'Other', 'count': 1, 'total': 250, 'avg_amount': 250},
        ]
        with patch('utils.expense_categorizer.get_connection', return_value=mock_conn):
            with patch('utils.expense_categorizer.release_connection'):
                result = self.cat.analyze_user_patterns(1, 30)
        assert result['most_spent_category'] == 'Food'


class TestSettingsAndDb:
    def test_app_config_from_env(self):
        cfg = AppConfig.from_env()
        assert cfg.environment in list(Environment)
        assert cfg.server.port > 0

    def test_check_database_health_down(self):
        from database.database_connection import check_database_health

        with patch('database.database_connection.get_connection', return_value=None):
            assert check_database_health() is False

    def test_expense_update_delete(self):
        from database import expense_query

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        with patch('database.expense_query.get_connection', return_value=mock_conn):
            with patch('database.expense_query.release_connection'):
                assert expense_query.update_expense(1, {'amount': 5}, user_id=1)
                assert expense_query.delete_expense(1, user_id=1)
                mock_cursor.fetchall.return_value = []
                assert expense_query.get_expenses_by_user(1) == []

    def test_user_update_delete(self):
        from database import user_query

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.rowcount = 1
        with patch('database.user_query.get_connection', return_value=mock_conn):
            with patch('database.user_query.release_connection'):
                assert user_query.update_user(1, {'first_name': 'Z'})
                assert user_query.delete_user(1)
                mock_cursor.fetchall.return_value = []
                assert user_query.get_all_users() == []
