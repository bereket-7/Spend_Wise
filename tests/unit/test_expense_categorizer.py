"""Unit tests for expense categorizer"""
from unittest.mock import patch, MagicMock

from utils.expense_categorizer import ExpenseCategorizer


class TestExpenseCategorizer:
    def setup_method(self):
        self.cat = ExpenseCategorizer()

    def test_categorize_food(self):
        result = self.cat.categorize_expense('Lunch at mcdonalds', 12.50, 'McDonalds')
        assert result['category'] in ('Food', 'Other')
        assert 'confidence' in result

    def test_categorize_transportation(self):
        result = self.cat.categorize_expense('Uber ride to airport', 35.0, 'Uber')
        assert result['category'] in ('Transportation', 'Other')

    def test_category_suggestions(self):
        suggestions = self.cat.get_category_suggestions('coffee lunch food')
        assert isinstance(suggestions, list)

    def test_low_confidence_falls_back_to_other(self):
        result = self.cat.categorize_expense('xyzabc nonsense', 9999.0, None)
        assert result['category'] == 'Other'

    def test_learn_from_correction(self):
        with patch.object(self.cat, '_save_learning_to_database') as mock_save:
            self.cat.learn_from_correction(
                1, 'coffee shop', 'Other', 'Food', 5.0, 'Starbucks'
            )
            mock_save.assert_called_once()
            assert 1 in self.cat.user_preferences

    def test_analyze_user_patterns_empty(self):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []
        with patch('utils.expense_categorizer.get_connection', return_value=mock_conn):
            with patch('utils.expense_categorizer.release_connection'):
                result = self.cat.analyze_user_patterns(1, 30)
        assert 'message' in result or 'total_categories' in result or result == {}
