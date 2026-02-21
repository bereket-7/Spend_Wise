from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from database.database_connection import get_connection, release_connection
from database.expense_query import get_all_expenses
from database.income_query import get_income_summary
from database.budget_query import get_budgets_by_user

logger = logging.getLogger(__name__)

class FinancialHealthCalculator:
    """Calculates comprehensive financial wellness score"""
    
    def __init__(self):
        self.weights = {
            'savings_rate': 0.3,      # 30% weight
            'budget_adherence': 0.25,    # 25% weight  
            'income_stability': 0.2,      # 20% weight
            'expense_control': 0.15,       # 15% weight
            'emergency_fund': 0.1          # 10% weight
        }
    
    def calculate_health_score(self, user_id: int) -> Dict[str, Any]:
        """Calculate comprehensive financial health score (0-100)"""
        try:
            # Get financial data
            current_date = datetime.now()
            start_of_month = current_date.replace(day=1)
            
            # Calculate individual components
            savings_score = self._calculate_savings_rate_score(user_id, start_of_month, current_date)
            budget_score = self._calculate_budget_adherence_score(user_id)
            stability_score = self._calculate_income_stability_score(user_id, start_of_month, current_date)
            expense_score = self._calculate_expense_control_score(user_id, start_of_month, current_date)
            emergency_score = self._calculate_emergency_fund_score(user_id)
            
            # Calculate weighted total score
            total_score = (
                savings_score * self.weights['savings_rate'] +
                budget_score * self.weights['budget_adherence'] +
                stability_score * self.weights['income_stability'] +
                expense_score * self.weights['expense_control'] +
                emergency_score * self.weights['emergency_fund']
            )
            
            # Determine health level
            if total_score >= 80:
                health_level = "Excellent"
                color = "#10B981"
            elif total_score >= 60:
                health_level = "Good"
                color = "#3B82F6"
            elif total_score >= 40:
                health_level = "Fair"
                color = "#F59E0B"
            else:
                health_level = "Poor"
                color = "#EF4444"
            
            return {
                'total_score': round(total_score, 1),
                'health_level': health_level,
                'color': color,
                'components': {
                    'savings_rate': {
                        'score': round(savings_score, 1),
                        'weight': self.weights['savings_rate'] * 100,
                        'label': 'Savings Rate'
                    },
                    'budget_adherence': {
                        'score': round(budget_score, 1),
                        'weight': self.weights['budget_adherence'] * 100,
                        'label': 'Budget Adherence'
                    },
                    'income_stability': {
                        'score': round(stability_score, 1),
                        'weight': self.weights['income_stability'] * 100,
                        'label': 'Income Stability'
                    },
                    'expense_control': {
                        'score': round(expense_score, 1),
                        'weight': self.weights['expense_control'] * 100,
                        'label': 'Expense Control'
                    },
                    'emergency_fund': {
                        'score': round(emergency_score, 1),
                        'weight': self.weights['emergency_fund'] * 100,
                        'label': 'Emergency Fund'
                    }
                },
                'recommendations': self._generate_recommendations(
                    savings_score, budget_score, stability_score, expense_score, emergency_score
                ),
                'calculated_at': current_date.isoformat()
            }
        except Exception as e:
            logger.error(f"Error calculating financial health score: {e}")
            return {'error': 'Unable to calculate financial health score'}
    
    def _calculate_savings_rate_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate savings rate score (0-100)"""
        try:
            connection = get_connection()
            if not connection:
                return 0
            
            cursor = connection.cursor(dictionary=True)
            
            # Get total income for the period
            income_query = """
            SELECT COALESCE(SUM(amount), 0) as total_income 
            FROM income 
            WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            cursor.execute(income_query, (user_id, start_date.date(), end_date.date()))
            income_result = cursor.fetchone()
            total_income = income_result['total_income'] or 0
            
            # Get total expenses for the period
            expense_query = """
            SELECT COALESCE(SUM(amount), 0) as total_expenses 
            FROM expense 
            WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            cursor.execute(expense_query, (user_id, start_date.date(), end_date.date()))
            expense_result = cursor.fetchone()
            total_expenses = expense_result['total_expenses'] or 0
            
            cursor.close()
            release_connection(connection)
            
            # Calculate savings rate
            if total_income == 0:
                return 0
            
            savings_rate = ((total_income - total_expenses) / total_income) * 100
            
            # Score: 20%+ savings = 100, 0% savings = 50, negative savings = 0
            if savings_rate >= 20:
                return 100
            elif savings_rate >= 10:
                return 75
            elif savings_rate >= 5:
                return 60
            elif savings_rate >= 0:
                return 50
            else:
                return max(0, 50 + savings_rate)  # Negative savings reduce score
                
        except Exception as e:
            logger.error(f"Error calculating savings rate: {e}")
            return 0
    
    def _calculate_budget_adherence_score(self, user_id: int) -> float:
        """Calculate budget adherence score (0-100)"""
        try:
            budgets = get_budgets_by_user(user_id)
            if not budgets:
                return 50  # Neutral score if no budgets
            
            total_budget_score = 0
            active_budgets = 0
            
            for budget in budgets:
                spending_info = get_budget_spending(budget.id)
                if spending_info and 'percentage_used' in spending_info:
                    percentage_used = spending_info['percentage_used']
                    
                    # Score based on how well they stick to budget
                    if percentage_used <= 80:
                        budget_score = 100
                    elif percentage_used <= 100:
                        budget_score = 80 - (percentage_used - 80) * 0.5  # Gradual decrease
                    else:
                        budget_score = max(0, 50 - (percentage_used - 100) * 0.3)  # Over budget penalty
                    
                    total_budget_score += budget_score
                    active_budgets += 1
            
            return total_budget_score / active_budgets if active_budgets > 0 else 50
            
        except Exception as e:
            logger.error(f"Error calculating budget adherence: {e}")
            return 0
    
    def _calculate_income_stability_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate income stability score (0-100)"""
        try:
            connection = get_connection()
            if not connection:
                return 0
            
            cursor = connection.cursor(dictionary=True)
            
            # Get income for last 6 months
            six_months_ago = start_date - timedelta(days=180)
            query = """
            SELECT DATE_FORMAT(date, '%Y-%m') as month, SUM(amount) as monthly_income
            FROM income 
            WHERE user_id = %s AND date >= %s
            GROUP BY DATE_FORMAT(date, '%Y-%m')
            ORDER BY month DESC
            LIMIT 6
            """
            cursor.execute(query, (user_id, six_months_ago.date()))
            results = cursor.fetchall()
            
            cursor.close()
            release_connection(connection)
            
            if len(results) < 2:
                return 50  # Not enough data
            
            # Calculate coefficient of variation (lower = more stable)
            incomes = [row['monthly_income'] for row in results if row['monthly_income'] > 0]
            if not incomes:
                return 0
            
            avg_income = sum(incomes) / len(incomes)
            variance = sum((x - avg_income) ** 2 for x in incomes) / len(incomes)
            std_dev = variance ** 0.5
            
            # Coefficient of variation
            cv = (std_dev / avg_income) * 100 if avg_income > 0 else 100
            
            # Score: CV < 10% = 100, CV < 20% = 80, CV < 30% = 60, CV < 50% = 40
            if cv < 10:
                return 100
            elif cv < 20:
                return 80
            elif cv < 30:
                return 60
            elif cv < 50:
                return 40
            else:
                return max(0, 20)
                
        except Exception as e:
            logger.error(f"Error calculating income stability: {e}")
            return 0
    
    def _calculate_expense_control_score(self, user_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate expense control score (0-100)"""
        try:
            connection = get_connection()
            if not connection:
                return 0
            
            cursor = connection.cursor(dictionary=True)
            
            # Get expense trends - compare to previous period
            previous_start = start_date - timedelta(days=30)
            previous_end = start_date - timedelta(days=1)
            
            # Current period expenses
            current_query = """
            SELECT COUNT(*) as transaction_count, AVG(amount) as avg_amount
            FROM expense 
            WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            cursor.execute(current_query, (user_id, start_date.date(), end_date.date()))
            current_result = cursor.fetchone()
            
            # Previous period expenses
            previous_query = """
            SELECT COUNT(*) as transaction_count, AVG(amount) as avg_amount
            FROM expense 
            WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            cursor.execute(previous_query, (user_id, previous_start.date(), previous_end.date()))
            previous_result = cursor.fetchone()
            
            cursor.close()
            release_connection(connection)
            
            if not previous_result or previous_result['avg_amount'] == 0:
                return 70  # Neutral score for new users
            
            # Calculate expense growth
            current_avg = current_result['avg_amount'] or 0
            previous_avg = previous_result['avg_amount'] or 0
            
            if previous_avg == 0:
                return 70
            
            expense_growth = ((current_avg - previous_avg) / previous_avg) * 100
            
            # Score: Negative growth (reduced expenses) = higher score
            if expense_growth <= -10:
                return 100
            elif expense_growth <= 0:
                return 85
            elif expense_growth <= 10:
                return 70
            elif expense_growth <= 20:
                return 50
            elif expense_growth <= 30:
                return 30
            else:
                return max(0, 10)
                
        except Exception as e:
            logger.error(f"Error calculating expense control: {e}")
            return 0
    
    def _calculate_emergency_fund_score(self, user_id: int) -> float:
        """Calculate emergency fund score (0-100)"""
        try:
            connection = get_connection()
            if not connection:
                return 0
            
            cursor = connection.cursor(dictionary=True)
            
            # Get last 3 months average monthly expenses
            three_months_ago = datetime.now() - timedelta(days=90)
            query = """
            SELECT AVG(monthly_total) as avg_monthly_expenses
            FROM (
                SELECT SUM(amount) as monthly_total
                FROM expense 
                WHERE user_id = %s AND date >= %s
                GROUP BY DATE_FORMAT(date, '%Y-%m')
            ) as monthly_expenses
            """
            cursor.execute(query, (user_id, three_months_ago.date()))
            result = cursor.fetchone()
            
            cursor.close()
            release_connection(connection)
            
            avg_monthly_expenses = result['avg_monthly_expenses'] or 0
            recommended_emergency_fund = avg_monthly_expenses * 6  # 6 months expenses
            
            # Get current total savings (simplified - would need actual savings tracking)
            # For now, use income - expenses from last 3 months
            current_date = datetime.now()
            start_date = current_date - timedelta(days=90)
            
            # This is simplified - in real implementation would track actual savings balance
            estimated_savings = max(0, avg_monthly_expenses * 0.2 * 3)  # Assume 20% savings rate
            
            if recommended_emergency_fund == 0:
                return 50
            
            emergency_fund_ratio = (estimated_savings / recommended_emergency_fund) * 100
            
            # Score: 6+ months expenses = 100, 3-6 months = 80, 1-3 months = 60, <1 month = 40
            if emergency_fund_ratio >= 100:
                return 100
            elif emergency_fund_ratio >= 50:
                return 80
            elif emergency_fund_ratio >= 25:
                return 60
            elif emergency_fund_ratio >= 15:
                return 40
            else:
                return max(0, 20)
                
        except Exception as e:
            logger.error(f"Error calculating emergency fund: {e}")
            return 0
    
    def _generate_recommendations(self, savings_score: float, budget_score: float, 
                             stability_score: float, expense_score: float, emergency_score: float) -> list:
        """Generate personalized recommendations based on scores"""
        recommendations = []
        
        if savings_score < 60:
            recommendations.append({
                'type': 'savings',
                'priority': 'high',
                'title': 'Increase Your Savings Rate',
                'description': 'Try to save at least 10% of your income each month',
                'action': 'Set up automatic transfers to savings account'
            })
        
        if budget_score < 70:
            recommendations.append({
                'type': 'budget',
                'priority': 'high',
                'title': 'Improve Budget Adherence',
                'description': 'You\'re consistently overspending in some categories',
                'action': 'Review and adjust your budget limits'
            })
        
        if stability_score < 60:
            recommendations.append({
                'type': 'income',
                'priority': 'medium',
                'title': 'Stabilize Your Income',
                'description': 'Your income varies significantly month to month',
                'action': 'Consider building multiple income streams or emergency savings'
            })
        
        if expense_score < 60:
            recommendations.append({
                'type': 'expenses',
                'priority': 'medium',
                'title': 'Control Your Spending',
                'description': 'Your expenses are increasing faster than income',
                'action': 'Review subscriptions and discretionary spending'
            })
        
        if emergency_score < 50:
            recommendations.append({
                'type': 'emergency',
                'priority': 'high',
                'title': 'Build Emergency Fund',
                'description': 'You should have 3-6 months of expenses saved',
                'action': 'Start with $500 and build gradually'
            })
        
        return recommendations
