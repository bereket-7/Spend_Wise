import logging
from typing import List, Optional, Dict, Any
from database.database_connection import get_connection, release_connection
from model.income import income

logger = logging.getLogger(__name__)

def create_income(income_data: Dict[str, Any]) -> bool:
    """Create a new income record"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO income (amount, source, date, user_id)
        VALUES (%s, %s, %s, %s)
        """
        values = (
            income_data['amount'],
            income_data['source'],
            income_data['date'],
            income_data['user_id']
        )
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Income created for user {income_data['user_id']}")
        return True
    except Exception as e:
        logger.error(f"Error creating income: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def get_income_by_id(income_id: int) -> Optional[income]:
    """Get income by ID"""
    connection = get_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM income WHERE id = %s"
        cursor.execute(query, (income_id,))
        result = cursor.fetchone()
        
        if result:
            return income(
                id=result['id'],
                amount=result['amount'],
                source=result['source'],
                date=result['date'],
                user_id=result['user_id']
            )
        return None
    except Exception as e:
        logger.error(f"Error getting income: {e}")
        return None
    finally:
        cursor.close()
        release_connection(connection)

def get_incomes_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List[income]:
    """Get all incomes for a user with pagination"""
    connection = get_connection()
    if connection is None:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM income WHERE user_id = %s ORDER BY date DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (user_id, limit, offset))
        results = cursor.fetchall()
        
        incomes = []
        for result in results:
            incomes.append(income(
                id=result['id'],
                amount=result['amount'],
                source=result['source'],
                date=result['date'],
                user_id=result['user_id']
            ))
        return incomes
    except Exception as e:
        logger.error(f"Error getting incomes: {e}")
        return []
    finally:
        cursor.close()
        release_connection(connection)

def update_income(income_id: int, income_data: Dict[str, Any]) -> bool:
    """Update income"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        set_clauses = []
        values = []
        
        for field in ['amount', 'source', 'date']:
            if field in income_data:
                set_clauses.append(f"{field} = %s")
                values.append(income_data[field])
        
        if not set_clauses:
            return False
        
        query = f"UPDATE income SET {', '.join(set_clauses)} WHERE id = %s"
        values.append(income_id)
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Income {income_id} updated")
        return True
    except Exception as e:
        logger.error(f"Error updating income: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def delete_income(income_id: int) -> bool:
    """Delete income"""
    connection = get_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()
        query = "DELETE FROM income WHERE id = %s"
        cursor.execute(query, (income_id,))
        connection.commit()
        logger.info(f"Income {income_id} deleted")
        return True
    except Exception as e:
        logger.error(f"Error deleting income: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)

def get_income_summary(user_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Get income summary for a user within date range"""
    connection = get_connection()
    if connection is None:
        return {}
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if start_date and end_date:
            query = """
            SELECT 
                COALESCE(SUM(amount), 0) as total_income,
                COUNT(*) as transaction_count,
                source,
                AVG(amount) as average_income
            FROM income 
            WHERE user_id = %s AND date BETWEEN %s AND %s
            GROUP BY source
            """
            cursor.execute(query, (user_id, start_date, end_date))
        else:
            query = """
            SELECT 
                COALESCE(SUM(amount), 0) as total_income,
                COUNT(*) as transaction_count,
                source,
                AVG(amount) as average_income
            FROM income 
            WHERE user_id = %s
            GROUP BY source
            """
            cursor.execute(query, (user_id,))
        
        results = cursor.fetchall()
        
        total_income = sum(result['total_income'] for result in results)
        total_transactions = sum(result['transaction_count'] for result in results)
        
        return {
            'total_income': total_income,
            'total_transactions': total_transactions,
            'by_source': results
        }
    except Exception as e:
        logger.error(f"Error getting income summary: {e}")
        return {}
    finally:
        cursor.close()
        release_connection(connection)
