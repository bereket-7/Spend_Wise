import logging
from typing import List, Optional, Dict, Any
from database.database_connection import get_connection, release_connection
from model.user import user

logger = logging.getLogger(__name__)


def _dict_to_user(result: Dict[str, Any]) -> user:
    return user(
        user_id=result['user_id'],
        username=result['username'],
        password=result.get('password', ''),
        email=result['email'],
        phone_number=result.get('phone_number') or '',
        first_name=result['first_name'],
        last_name=result['last_name'],
        role=result.get('role', 'user'),
    )


def create_user(user_data) -> bool:
    """Create a new user. Accepts a user model or dict."""
    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        if hasattr(user_data, 'username'):
            values = (
                user_data.username,
                user_data.password,
                user_data.email,
                user_data.phone_number,
                user_data.first_name,
                user_data.last_name,
                getattr(user_data, 'role', 'user'),
            )
        else:
            values = (
                user_data['username'],
                user_data['password'],
                user_data['email'],
                user_data.get('phone_number', ''),
                user_data['first_name'],
                user_data['last_name'],
                user_data.get('role', 'user'),
            )

        query = """
        INSERT INTO user (username, password, email, phone_number, first_name, last_name, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"User created: {values[0]}")
        return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)


def get_user_by_id(user_id: int) -> Optional[user]:
    """Get user by ID"""
    connection = get_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM user WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        if result:
            return _dict_to_user(result)
        return None
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None
    finally:
        cursor.close()
        release_connection(connection)


def get_user_by_username(username: str) -> Optional[user]:
    """Get user by username"""
    connection = get_connection()
    if connection is None:
        return None

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if result:
            return _dict_to_user(result)
        return None
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        return None
    finally:
        cursor.close()
        release_connection(connection)


def get_all_users() -> List[user]:
    """Get all users"""
    connection = get_connection()
    if connection is None:
        return []

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM user ORDER BY user_id"
        cursor.execute(query)
        results = cursor.fetchall()
        return [_dict_to_user(row) for row in results]
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []
    finally:
        cursor.close()
        release_connection(connection)


def update_user(user_id: int, user_data: Dict[str, Any] = None, user_obj=None) -> bool:
    """Update user. Accepts either (user_id, dict) or a user model via user_obj."""
    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()

        # Support legacy call: update_user(user_model)
        if user_obj is None and hasattr(user_id, 'user_id'):
            user_obj = user_id
            user_id = user_obj.user_id
            user_data = {
                'username': user_obj.username,
                'password': user_obj.password,
                'email': user_obj.email,
                'phone_number': user_obj.phone_number,
                'first_name': user_obj.first_name,
                'last_name': user_obj.last_name,
            }

        if user_data is None:
            return False

        set_clauses = []
        values = []
        for field in ['username', 'password', 'email', 'phone_number', 'first_name', 'last_name', 'role']:
            if field in user_data and user_data[field] is not None:
                set_clauses.append(f"{field} = %s")
                values.append(user_data[field])

        if not set_clauses:
            return False

        query = f"UPDATE user SET {', '.join(set_clauses)} WHERE user_id = %s"
        values.append(user_id)
        cursor.execute(query, values)
        connection.commit()
        logger.info(f"User {user_id} updated")
        return True
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)


def update_user_password(user_id: int, hashed_password: str) -> bool:
    """Update only the password hash (used for legacy hash migration)."""
    return update_user(user_id, {'password': hashed_password})


def delete_user(user_id: int) -> bool:
    """Delete user by ID"""
    connection = get_connection()
    if connection is None:
        return False

    try:
        cursor = connection.cursor()
        query = "DELETE FROM user WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        connection.commit()
        logger.info(f"User {user_id} deleted")
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        release_connection(connection)
