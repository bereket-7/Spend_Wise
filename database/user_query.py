import database_connection
from user import user

def create_user(user):
    connection = database_connection.create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            sql = """INSERT INTO user (username, password, email, phone_number, first_name, last_name, role) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (user.username, user.password, user.email, user.phone_number, 
                                 user.first_name, user.last_name, user.role))
            connection.commit()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
        finally:
            database_connection.close_connection(connection)
    else:
        return False

def update_user(user):
    connection = database_connection.create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            sql = """UPDATE user SET username=%s, password=%s, email=%s, phone_number=%s, 
                     first_name=%s, last_name=%s WHERE user_id=%s"""
            cursor.execute(sql, (user.username, user.password, user.email, user.phone_number, 
                                 user.first_name, user.last_name, user.user_id))
            connection.commit()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False
        finally:
            database_connection.close_connection(connection)
    else:
        return False

def delete_user(user_id):
    connection = database_connection.create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            sql = "DELETE FROM user WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            connection.commit()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
        finally:
            database_connection.close_connection(connection)
    else:
        return False

def get_user_by_id(user_id):
    connection = database_connection.create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            sql = "SELECT * FROM user WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            user_record = cursor.fetchone()
            if user_record:
                user = user(*user_record)
                return user
            else:
                return None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
        finally:
            database_connection.close_connection(connection)
    else:
        return None

def get_all_users():
    connection = database_connection.create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            sql = "SELECT * FROM user"
            cursor.execute(sql)
            users_records = cursor.fetchall()
            users = [user(*user_record) for user_record in users_records]
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return None
        finally:
            database_connection.close_connection(connection)
    else:
        return None
