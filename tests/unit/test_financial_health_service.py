"""
Unit tests for financial health calculator
"""
import pytest
from unittest.mock import Mock, patch
from src.services.financial_health_service import FinancialHealthService
from tests.conftest import sample_financial_health_data

class TestFinancialHealthService:
    """Test cases for FinancialHealthService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = FinancialHealthService()
    
    @patch('src.services.financial_health_service.get_connection')
    def test_calculate_health_score_success(self, mock_get_connection):
        """Test successful health score calculation"""
        # Mock database responses
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        
        # Mock income data
        mock_cursor.fetchone.side_effect = [
            {'total_income': 5000.0},  # Income query
            {'total_expenses': 3500.0},  # Expenses query
            {'avg_monthly_expenses': 3000.0}  # Emergency fund query
        ]
        
        # Mock budget data
        with patch('src.services.financial_health_service.get_budgets_by_user') as mock_budgets:
            mock_budgets.return_value = []
            
            result = self.service.calculate_health_score(1)
            
            assert result is not None
            assert 'total_score' in result
            assert 'health_level' in result
            assert 'components' in result
            assert isinstance(result['total_score'], (int, float))
            assert result['total_score'] >= 0
            assert result['total_score'] <= 100
    
    def test_calculate_savings_rate_positive(self):
        """Test savings rate calculation with positive savings"""
        score = self.service._calculate_savings_rate(5000, 3500)
        assert score == 100  # 30% savings rate = perfect score
    
    def test_calculate_savings_rate_zero(self):
        """Test savings rate calculation with zero savings"""
        score = self.service._calculate_savings_rate(5000, 5000)
        assert score == 50  # 0% savings = average score
    
    def test_calculate_savings_rate_negative(self):
        """Test savings rate calculation with negative savings"""
        score = self.service._calculate_savings_rate(5000, 5500)
        assert score < 50  # Negative savings = below average score
    
    def test_determine_health_level_excellent(self):
        """Test health level determination for excellent score"""
        level = self.service._determine_health_level(85)
        assert level == "Excellent"
        assert level['color'] == "#10B981"
    
    def test_determine_health_level_good(self):
        """Test health level determination for good score"""
        level = self.service._determine_health_level(70)
        assert level == "Good"
        assert level['color'] == "#3B82F6"
    
    def test_determine_health_level_fair(self):
        """Test health level determination for fair score"""
        level = self.service._determine_health_level(50)
        assert level == "Fair"
        assert level['color'] == "#F59E0B"
    
    def test_determine_health_level_poor(self):
        """Test health level determination for poor score"""
        level = self.service._determine_health_level(30)
        assert level == "Poor"
        assert level['color'] == "#EF4444"
    
    def test_generate_recommendations_low_savings(self):
        """Test recommendation generation for low savings"""
        recommendations = self.service._generate_recommendations(
            savings_score=40,
            budget_score=80,
            stability_score=75,
            expense_score=70,
            emergency_score=60
        )
        
        assert len(recommendations) > 0
        savings_rec = next((r for r in recommendations if r['type'] == 'savings'), None)
        assert savings_rec is not None
        assert savings_rec['priority'] == 'high'
        assert 'savings rate' in savings_rec['description'].lower()
    
    def test_generate_recommendations_multiple_issues(self):
        """Test recommendation generation for multiple issues"""
        recommendations = self.service._generate_recommendations(
            savings_score=30,
            budget_score=40,
            stability_score=50,
            expense_score=35,
            emergency_score=25
        )
        
        assert len(recommendations) >= 3  # Should have multiple recommendations
        
        # Check for different types of recommendations
        types = [r['type'] for r in recommendations]
        assert 'savings' in types
        assert 'budget' in types
        assert 'emergency' in types
    
    @patch('src.services.financial_health_service.get_connection')
    def test_calculate_health_score_database_error(self, mock_get_connection):
        """Test health score calculation with database error"""
        mock_get_connection.return_value = None
        
        result = self.service.calculate_health_score(1)
        
        assert 'error' in result
        assert result['error'] == 'Unable to calculate financial health score'
