"""Unit tests for expense and user query modules"""
from unittest.mock import patch, MagicMock

from database import expense_query, user_query


class TestExpenseQuery:
    def test_create_expense(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('database.expense_query.get_connection', return_value=mock_conn):
            with patch('database.expense_query.release_connection'):
                ok = expense_query.create_expense({
                    'amount': 10,
                    'category': 'Food',
                    'description': 'x',
                    'date': '2024-01-01',
                    'user_id': 1,
                })
        assert ok is True
        mock_conn.commit.assert_called()

    def test_get_expense_by_id_scoped(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'amount': 10,
            'category': 'Food',
            'date': '2024-01-01',
            'user_id': 1,
            'description': None,
        }
        with patch('database.expense_query.get_connection', return_value=mock_conn):
            with patch('database.expense_query.release_connection'):
                rec = expense_query.get_expense_by_id(1, user_id=1)
        assert rec is not None
        assert rec.category == 'Food'

    def test_get_connection_none(self):
        with patch('database.expense_query.get_connection', return_value=None):
            assert expense_query.create_expense({'amount': 1, 'category': 'a', 'date': '2024-01-01', 'user_id': 1}) is False


class TestUserQuery:
    def test_get_user_by_username(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            'user_id': 1,
            'username': 'alice',
            'password': 'hash',
            'email': 'a@e.com',
            'phone_number': '',
            'first_name': 'A',
            'last_name': 'B',
            'role': 'user',
        }
        with patch('database.user_query.get_connection', return_value=mock_conn):
            with patch('database.user_query.release_connection'):
                u = user_query.get_user_by_username('alice')
        assert u is not None
        assert u.username == 'alice'

    def test_create_user_dict(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        with patch('database.user_query.get_connection', return_value=mock_conn):
            with patch('database.user_query.release_connection'):
                ok = user_query.create_user({
                    'username': 'x',
                    'password': 'h',
                    'email': 'x@e.com',
                    'first_name': 'X',
                    'last_name': 'Y',
                })
        assert ok is True
