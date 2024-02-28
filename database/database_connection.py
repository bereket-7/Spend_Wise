import mysql.connector

def create_connection():
    config = {
        'user': 'root',
        'password': '',
        'host': 'localhost',
        'database': 'spend_wise',
        'auth_plugin': 'mysql_native_password'
    }
    
    try:
        connection = mysql.connector.connect(**config)
        print("Database connection established!")
        return connection
    except mysql.connector.Error as err:
        print(f"Error connecting to the database: {err}")
        return None

def close_connection(connection):
    if connection.is_connected():
        connection.close()
        print("Database connection closed.")