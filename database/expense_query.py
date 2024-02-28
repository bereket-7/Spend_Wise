import database_connection
from expense import expense
class ExpenseQuery:
    @staticmethod
    def create_expense(expense):
        connection = database_connection.create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                sql = """INSERT INTO expense (amount, category, date) 
                         VALUES (%s, %s, %s)"""
                cursor.execute(sql, (expense.amount, expense.category, expense.date))
                connection.commit()
                return True
            except Exception as e:
                print(f"Error creating expense: {e}")
                return False
            finally:
                database_connection.close_connection(connection)
        else:
            return False

    @staticmethod
    def update_expense(expense):
        connection = database_connection.create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                sql = """UPDATE expenses SET amount=%s, category=%s, date=%s WHERE id=%s"""
                cursor.execute(sql, (expense.amount, expense.category, expense.date, expense.id))
                connection.commit()
                return True
            except Exception as e:
                print(f"Error updating expense: {e}")
                return False
            finally:
                database_connection.close_connection(connection)
        else:
            return False

    @staticmethod
    def delete_expense(expense_id):
        connection = database_connection.create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                sql = "DELETE FROM expense WHERE id = %s"
                cursor.execute(sql, (expense_id,))
                connection.commit()
                return True
            except Exception as e:
                print(f"Error deleting expense: {e}")
                return False
            finally:
                database_connection.close_connection(connection)
        else:
            return False

    @staticmethod
    def get_expense_by_id(expense_id):
        connection = database_connection.create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                sql = "SELECT * FROM expense WHERE id = %s"
                cursor.execute(sql, (expense_id,))
                expense_record = cursor.fetchone()
                if expense_record:
                    # Assuming the expense class is defined elsewhere
                    return expense(*expense_record)
                else:
                    return None
            except Exception as e:
                print(f"Error getting expense by ID: {e}")
                return None
            finally:
                database_connection.close_connection(connection)
        else:
            return None

    @staticmethod
    def get_all_expenses():
        connection = database_connection.create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                sql = "SELECT * FROM expense"
                cursor.execute(sql)
                expenses_records = cursor.fetchall()
                expenses = [expense(*expense_record) for expense_record in expenses_records]
                return expenses
            except Exception as e:
                print(f"Error getting all expenses: {e}")
                return None
            finally:
                database_connection.close_connection(connection)
        else:
            return None
