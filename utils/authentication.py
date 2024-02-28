from database_connection import create_connection, close_connection
from user import User
import mysql

def authenticate(username, password):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor()

        # Retrieve the user from the user table based on the username and password
        query = "SELECT user_id, username, password, email, phone_number, first_name, last_name,role FROM user WHERE username = %s AND password = %s"
        values = (username, password)
        cursor.execute(query, values)
        result = cursor.fetchone()

        if result is not None:
            # Create and return a User object
            user = User(result[0], result[1], result[2], result[3], result[4], result[5], result[6])
            return user
        else:
            return None
    except mysql.connector.Error as err:
        print(f"Error authenticating user: {err}")
        return None
    finally:
        close_connection(connection)

def authorize(user):
    # Check if the user has admin privileges
    if user is not None and user.role == 'admin':
        return True
    else:
        return False