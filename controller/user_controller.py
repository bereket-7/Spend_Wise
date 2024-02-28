import mysql
from database_connection import create_connection, close_connection
from user import User

def create_user(user):
    connection = create_connection()
    if connection is None:
        return False
    try:
        cursor = connection.cursor()

      # Insert a new user into the user table
        query = "INSERT INTO user (username, password, email, phone_number, first_name, last_name,role) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (user.username, user.password, user.email, user.phone_number, user.first_name, user.last_name, user.role)
        cursor.execute(query, values)
        connection.commit()

        return True
    except mysql.connector.Error as err:
        print(f"Error creating user: {err}")
        return False
    finally:
        close_connection(connection)

def get_user_by_id(user_id):
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor()

        # Retrieve the user from the user table based on the ID
        query = "SELECT user_id, username, password, email, phone_number, first_name, last_name,role FROM user WHERE user_id = %s"
        values = (user_id,)
        cursor.execute(query, values)
        result = cursor.fetchone()

        if result is not None:
            # Create and return a User object
            user = User(result[0], result[1], result[2], result[3], result[4], result[5], result[6])
            return user
        else:
            return None
    except mysql.connector.Error as err:
        print(f"Error retrieving user: {err}")
        return None
    finally:
        close_connection(connection)

def update_user(user):
    connection = create_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()

        # Update the user in the user table
        query = "UPDATE user SET username = %s, password = %s, email = %s, phone_number = %s, first_name = %s, last_name = %s WHERE user_id = %s"
        values = (user.username, user.password, user.email, user.phone_number, user.first_name, user.last_name, user.user_id)
        cursor.execute(query, values)
        connection.commit()

        return True
    except mysql.connector.Error as err:
        print(f"Error updating user: {err}")
        return False
    finally:
        close_connection(connection)

def delete_user(user_id):
    connection = create_connection()
    if connection is None:
        return False
    
    try:
        cursor = connection.cursor()

        # Delete the user from the user table based on the ID
        query = "DELETE FROM user WHERE user_id = %s"
        values = (user_id,)
        cursor.execute(query, values)
        connection.commit()

        return True
    except mysql.connector.Error as err:
        print(f"Error deleting user: {err}")
        return False
    finally:
        close_connection(connection)
    
def get_all_users():
    connection = create_connection()
    if connection is None:
        return None
    
    try:
        cursor = connection.cursor()

        # Retrieve all users from the user table
        query = "SELECT user_id, username, password, email, phone_number, first_name, last_name,role FROM user"
        cursor.execute(query)
        results = cursor.fetchall()

        users = []
        for result in results:
            # Create and append a User object for each row
            user = User(result[0], result[1], result[2], result[3], result[4], result[5], result[6])
            users.append(user)

        return users
    except mysql.connector.Error as err:
        print(f"Error retrieving users: {err}")
        return None
    finally:
        close_connection(connection)