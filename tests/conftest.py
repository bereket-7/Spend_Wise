"""
Comprehensive testing framework setup
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Test configuration
TEST_DATABASE_URL = "mysql://test_user:test_pass@localhost/spend_wise_test"
TEST_JWT_SECRET = "test-secret-key"

@pytest.fixture
def mock_db_connection():
    """Mock database connection for testing"""
    with patch('database.database_connection.get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_connection = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_conn.return_value = mock_connection
        yield mock_connection, mock_cursor

@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        'username': 'testuser',
        'password': 'testpass123',
        'email': 'test@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'phone_number': '1234567890',
        'role': 'user'
    }

@pytest.fixture
def test_expense_data():
    """Sample expense data for testing"""
    return {
        'amount': 25.50,
        'category': 'Food',
        'description': 'Lunch at restaurant',
        'date': '2024-01-15',
        'user_id': 1
    }

@pytest.fixture
def mock_auth_token():
    """Mock JWT token for testing"""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test"

@pytest.fixture
def sample_financial_health_data():
    """Sample financial health data for testing"""
    return {
        'total_score': 75.5,
        'health_level': 'Good',
        'components': {
            'savings_rate': {'score': 80.0, 'weight': 30},
            'budget_adherence': {'score': 70.0, 'weight': 25},
            'income_stability': {'score': 75.0, 'weight': 20},
            'expense_control': {'score': 80.0, 'weight': 15},
            'emergency_fund': {'score': 65.0, 'weight': 10}
        }
    }
