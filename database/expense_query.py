import logging
from typing import List, Optional, Dict, Any
from database.database_connection import get_connection, release_connection
from model.expense import expense

logger = logging.getLogger(__name__)


def _dict_to_expense(result: Dict[str, Any]) -> expense:
    return expense(
        id=result['id'],
        amount=float(result['amount']),
        category=result['category'],
        date=str(result['date']),
        user_id=result.get('user_id'),
        description=result.get('description'),
    )


def create_expense(expense_data: Dict[str, Any]) -> bool:
    """Create a new expense"""
    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        query = """
        INSERT INTO expense (amount, category, description, date, user_id)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            expense_data['amount'],
            expense_data['category'],
            expense_data.get('description'),
            expense_data['date'],
            expense_data['user_id'],
        )
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Expense created for user {expense_data['user_id']}")
        return True
    except Exception as e:
        logger.error(f"Error creating expense: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)


def get_expense_by_id(expense_id: int, user_id: int = None) -> Optional[expense]:
    """Get expense by ID, optionally scoped to a user"""
    connection = get_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        if user_id is not None:
            query = "SELECT * FROM expense WHERE id = %s AND user_id = %s"
            cursor.execute(query, (expense_id, user_id))
        else:
            query = "SELECT * FROM expense WHERE id = %s"
            cursor.execute(query, (expense_id,))
        result = cursor.fetchone()
        if result:
            return _dict_to_expense(result)
        return None
    except Exception as e:
        logger.error(f"Error getting expense by ID: {e}")
        return None
    finally:
        cursor.close()
        release_connection(connection)


def get_expenses_by_user(user_id: int, limit: int = 100, offset: int = 0) -> List[expense]:
    """Get expenses for a specific user with pagination"""
    connection = get_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT * FROM expense
        WHERE user_id = %s
        ORDER BY date DESC, id DESC
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, limit, offset))
        results = cursor.fetchall()
        return [_dict_to_expense(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting expenses by user: {e}")
        return []
    finally:
        cursor.close()
        release_connection(connection)


def get_all_expenses(user_id: int = None) -> List[expense]:
    """Get all expenses, optionally filtered by user"""
    if user_id is not None:
        return get_expenses_by_user(user_id)

    connection = get_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM expense ORDER BY date DESC"
        cursor.execute(query)
        results = cursor.fetchall()
        return [_dict_to_expense(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting all expenses: {e}")
        return []
    finally:
        cursor.close()
        release_connection(connection)


def update_expense(expense_id: int, expense_data: Dict[str, Any], user_id: int = None) -> bool:
    """Update expense, optionally scoped to a user"""
    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        set_clauses = []
        values = []

        for field in ['amount', 'category', 'description', 'date']:
            if field in expense_data:
                set_clauses.append(f"{field} = %s")
                values.append(expense_data[field])

        if not set_clauses:
            return False

        if user_id is not None:
            query = f"UPDATE expense SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s"
            values.extend([expense_id, user_id])
        else:
            query = f"UPDATE expense SET {', '.join(set_clauses)} WHERE id = %s"
            values.append(expense_id)

        cursor.execute(query, values)
        connection.commit()
        logger.info(f"Expense {expense_id} updated")
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating expense: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)


def delete_expense(expense_id: int, user_id: int = None) -> bool:
    """Delete expense, optionally scoped to a user"""
    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        if user_id is not None:
            query = "DELETE FROM expense WHERE id = %s AND user_id = %s"
            cursor.execute(query, (expense_id, user_id))
        else:
            query = "DELETE FROM expense WHERE id = %s"
            cursor.execute(query, (expense_id,))
        connection.commit()
        logger.info(f"Expense {expense_id} deleted")
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting expense: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)
