import logging
from typing import List, Optional, Dict, Any
from database.database_connection import get_connection, release_connection
from model.budget import budget

logger = logging.getLogger(__name__)

def create_budget(budget_data: Dict[str, Any]) -> bool:
    """Create a new budget"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO budget (amount, category, start_date, end_date, user_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            budget_data['amount'],
            budget_data['category'],
            budget_data['start_date'],
            budget_data['end_date'],
            budget_data['user_id']
        )
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Budget created for user {budget_data['user_id']}")
        return True
    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def get_budget_by_id(budget_id: int) -> Optional[budget]:
    """Get budget by ID"""
    connection = get_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM budget WHERE id = %s"
        cursor.execute(query, (budget_id,))
        result = cursor.fetchone()
        
        if result:
            return budget(
                id=result['id'],
                amount=result['amount'],
                category=result['category'],
                start_date=result['start_date'],
                end_date=result['end_date'],
                user_id=result['user_id']
            )
        return None
    except Exception as e:
        logger.error(f"Error getting budget: {e}")
        return None
    finally:
        cursor.close()
        release_connection(connection)

def get_budgets_by_user(user_id: int) -> List[budget]:
    """Get all budgets for a user"""
    connection = get_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM budget WHERE user_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        budgets = []
        for result in results:
            budgets.append(budget(
                id=result['id'],
                amount=result['amount'],
                category=result['category'],
                start_date=result['start_date'],
                end_date=result['end_date'],
                user_id=result['user_id']
            ))
        return budgets
    except Exception as e:
        logger.error(f"Error getting budgets: {e}")
        return []
    finally:
        cursor.close()
        release_connection(connection)

def update_budget(budget_id: int, budget_data: Dict[str, Any]) -> bool:
    """Update budget"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        set_clauses = []
        values = []
        
        for field in ['amount', 'category', 'start_date', 'end_date']:
            if field in budget_data:
                set_clauses.append(f"{field} = %s")
                values.append(budget_data[field])
        
        if not set_clauses:
            return False
        
        query = f"UPDATE budget SET {', '.join(set_clauses)} WHERE id = %s"
        values.append(budget_id)
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Budget {budget_id} updated")
        return True
    except Exception as e:
        logger.error(f"Error updating budget: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def delete_budget(budget_id: int) -> bool:
    """Delete budget"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "DELETE FROM budget WHERE id = %s"
        cursor.execute(query, (budget_id,))
        connection.commit()
        logger.info(f"Budget {budget_id} deleted")
        return True
    except Exception as e:
        logger.error(f"Error deleting budget: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def get_budget_spending(budget_id: int) -> Dict[str, Any]:
    """Calculate current spending against budget"""
    connection = get_connection()
    if connection is None:
        return {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get budget details
        budget_query = "SELECT * FROM budget WHERE id = %s"
        cursor.execute(budget_query, (budget_id,))
        budget_result = cursor.fetchone()
        
        if not budget_result:
            return {}
        
        # Calculate total expenses for this category within budget period
        expense_query = """
        SELECT COALESCE(SUM(amount), 0) as total_spent
        FROM expense 
        WHERE category = %s 
        AND user_id = %s 
        AND date BETWEEN %s AND %s
        """
        cursor.execute(expense_query, (
            budget_result['category'],
            budget_result['user_id'],
            budget_result['start_date'],
            budget_result['end_date']
        ))
        expense_result = cursor.fetchone()
        
        total_spent = expense_result['total_spent'] or 0
        remaining = budget_result['amount'] - total_spent
        percentage_used = (total_spent / budget_result['amount']) * 100 if budget_result['amount'] > 0 else 0
        
        return {
            'budget_id': budget_id,
            'budget_amount': budget_result['amount'],
            'total_spent': total_spent,
            'remaining': remaining,
            'percentage_used': round(percentage_used, 2),
            'category': budget_result['category'],
            'start_date': budget_result['start_date'],
            'end_date': budget_result['end_date']
        }
    except Exception as e:
        logger.error(f"Error calculating budget spending: {e}")
        return {}
    finally:
        cursor.close()
        release_connection(connection)
