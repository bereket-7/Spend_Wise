import json
from utils import api_service
from response import json_response
import expense_query
from expense import expense

class ExpenseController(api_service.APIService):
    def handle_get(self):
        if self.path.startswith('/expenses/'):
            expense_id = int(self.path.split('/')[-1])
            expense = expense_query.get_expense_by_id(expense_id)

            if expense is not None:
                expense_data = {
                    'id': expense.id,
                    'amount': expense.amount,
                    'category': expense.category,
                    'date': expense.date
                }
                return json_response(expense_data)
            else:
                return json_response({'message': 'Expense not found'}, status_code=404)
        elif self.path == '/expenses':
            expenses = expense_query.get_all_expenses()

            if expenses is not None:
                expenses_data = []
                for expense in expenses:
                    expense_data = {
                        'id': expense.id,
                        'amount': expense.amount,
                        'category': expense.category,
                        'date': expense.date
                    }
                    expenses_data.append(expense_data)

                return json_response(expenses_data)
            else:
                return json_response({'message': 'No expenses found'}, status_code=404)
        else:
            return json_response({'message': 'Not found'}, status_code=404)

    def handle_post(self):
        if self.path == '/expenses':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            expense_data = json.loads(body)

            expense = expense_query.create_expense(expense_data)

            if expense:
                return json_response({'message': 'Expense created successfully'}, status_code=201)
            else:
                return json_response({'message': 'Failed to create expense'}, status_code=500)
        else:
            return json_response({'message': 'Not found'}, status_code=404)

    def handle_put(self):
        if self.path.startswith('/expenses/'):
            expense_id = int(self.path.split('/')[-1])
            expense = expense_query.get_expense_by_id(expense_id)

            if expense is not None:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                expense_data = json.loads(body)

                updated_expense = expense_query.update_expense(expense_id, expense_data)

                if updated_expense:
                    return json_response({'message': 'Expense updated successfully'})
                else:
                    return json_response({'message': 'Failed to update expense'}, status_code=500)
            else:
                return json_response({'message': 'Expense not found'}, status_code=404)
        else:
            return json_response({'message': 'Not found'}, status_code=404)

    def handle_delete(self):
        if self.path.startswith('/expenses/'):
            expense_id = int(self.path.split('/')[-1])
            expense = expense_query.get_expense_by_id(expense_id)

            if expense is not None:
                result = expense_query.delete_expense(expense_id)

                if result:
                    return json_response({'message': 'Expense deleted successfully'})
                else:
                    return json_response({'message': 'Failed to delete expense'}, status_code=500)
            else:
                return json_response({'message': 'Expense not found'}, status_code=404)
        else:
            return json_response({'message': 'Not found'}, status_code=404)
