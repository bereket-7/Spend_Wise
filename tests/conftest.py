"""
Pytest configuration and shared fixtures
"""
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import pytest

# Project root on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key')
os.environ.setdefault('CACHE_ENABLED', 'false')
os.environ.setdefault('DB_PASSWORD', '')


@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    with patch('database.database_connection.get_connection') as mock_get:
        mock_cursor = MagicMock()
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.is_connected.return_value = True
        mock_get.return_value = mock_connection
        with patch('database.database_connection.release_connection'):
            yield mock_connection, mock_cursor


@pytest.fixture
def test_user_data():
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'user',
    }


@pytest.fixture
def test_expense_data():
    return {
        'amount': 25.50,
        'category': 'Food',
        'description': 'Lunch at restaurant',
        'date': '2024-01-15',
        'user_id': 1,
    }


@pytest.fixture
def auth_payload():
    return {
        'user_id': 1,
        'username': 'testuser',
        'email': 'test@example.com',
        'role': 'user',
    }


@pytest.fixture
def mock_handler(auth_payload):
    """Minimal HTTP handler mock with auth_user set."""
    handler = Mock()
    handler.path = '/expenses'
    handler.headers = {'Authorization': 'Bearer test-token', 'Content-Length': '0'}
    handler.rfile = Mock()
    handler.rfile.read.return_value = b'{}'
    handler.auth_user = auth_payload
    return handler
