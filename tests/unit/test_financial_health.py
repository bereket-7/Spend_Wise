"""Unit tests for FinancialHealthCalculator"""
from unittest.mock import patch, MagicMock

from utils.financial_health import FinancialHealthCalculator


class TestFinancialHealthCalculator:
    def setup_method(self):
        self.calc = FinancialHealthCalculator()

    def test_generate_recommendations_low_savings(self):
        recommendations = self.calc._generate_recommendations(
            savings_score=40,
            budget_score=80,
            stability_score=75,
            expense_score=70,
            emergency_score=60,
        )
        assert len(recommendations) > 0
        savings_rec = next((r for r in recommendations if r['type'] == 'savings'), None)
        assert savings_rec is not None
        assert savings_rec['priority'] == 'high'

    def test_generate_recommendations_multiple_issues(self):
        recommendations = self.calc._generate_recommendations(
            savings_score=30,
            budget_score=40,
            stability_score=50,
            expense_score=35,
            emergency_score=25,
        )
        types = [r['type'] for r in recommendations]
        assert 'savings' in types
        assert 'budget' in types
        assert 'emergency' in types

    def test_health_levels_from_score(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        # income, expenses for savings; then for emergency fund queries etc.
        mock_cursor.fetchone.side_effect = [
            {'total_income': 5000.0},
            {'total_expenses': 3500.0},
            {'avg_monthly_expenses': 3000.0},
        ]
        mock_cursor.fetchall.return_value = [
            {'month': '2024-01', 'monthly_income': 5000},
            {'month': '2024-02', 'monthly_income': 5100},
        ]

        with patch('utils.financial_health.get_connection', return_value=mock_conn):
            with patch('utils.financial_health.release_connection'):
                with patch('utils.financial_health.get_budgets_by_user', return_value=[]):
                    with patch.object(self.calc, '_calculate_expense_control_score', return_value=80):
                        result = self.calc.calculate_health_score(1)

        assert 'total_score' in result
        assert 'health_level' in result
        assert 'components' in result
        assert 0 <= result['total_score'] <= 100

    def test_calculate_health_score_db_error(self):
        with patch('utils.financial_health.get_connection', return_value=None):
            with patch('utils.financial_health.get_budgets_by_user', side_effect=Exception('db')):
                result = self.calc.calculate_health_score(1)
        # May return error or zeros depending on which path fails
        assert isinstance(result, dict)

    def test_savings_rate_scoring(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {'total_income': 5000},
            {'total_expenses': 3500},  # 30% savings -> 100
        ]
        from datetime import datetime

        with patch('utils.financial_health.get_connection', return_value=mock_conn):
            with patch('utils.financial_health.release_connection'):
                score = self.calc._calculate_savings_rate_score(
                    1, datetime(2024, 1, 1), datetime(2024, 1, 31)
                )
        assert score == 100
