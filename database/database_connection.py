import mysql.connector

def create_connection():
    config = {
        'user': 'root',
        'password': '8915code',
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


# Call the create_connection function to establish a connection
connection = create_connection()

# Call the close_connection function to close the connection
if connection:
    close_connection(connection)