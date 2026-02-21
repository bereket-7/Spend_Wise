import json
import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_amount, sanitize_string
import expense_query
from model.expense import expense

logger = logging.getLogger(__name__)

class ExpenseController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            if self.path.startswith('/expenses/'):
                expense_id = int(self.path.split('/')[-1])
                expense_record = expense_query.get_expense_by_id(expense_id)

                if expense_record is not None:
                    expense_data = {
                        'id': expense_record.id,
                        'amount': expense_record.amount,
                        'category': expense_record.category,
                        'date': expense_record.date
                    }
                    return json_response(expense_data)
                else:
                    return json_response({'message': 'Expense not found'}, 404)
            elif self.path == '/expenses':
                expenses = expense_query.get_all_expenses()

                if expenses is not None:
                    expenses_data = []
                    for expense_record in expenses:
                        expense_data = {
                            'id': expense_record.id,
                            'amount': expense_record.amount,
                            'category': expense_record.category,
                            'date': expense_record.date
                        }
                        expenses_data.append(expense_data)

                    return json_response(expenses_data)
                else:
                    return json_response({'message': 'No expenses found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in expense GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            if self.path == '/expenses':
                expense_data = self.get_request_body()
                if not expense_data:
                    return json_response({'message': 'Invalid JSON data'}, 400)

                # Validate required fields
                required_fields = ['amount', 'category', 'date']
                is_valid, error_message = validate_required_fields(expense_data, required_fields)
                if not is_valid:
                    return json_response({'message': error_message}, 400)

                # Validate amount
                if not validate_amount(expense_data['amount']):
                    return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

                # Sanitize inputs
                expense_data['category'] = sanitize_string(expense_data['category'])
                if expense_data.get('description'):
                    expense_data['description'] = sanitize_string(expense_data['description'])

                result = expense_query.create_expense(expense_data)

                if result:
                    return json_response({'message': 'Expense created successfully'}, 201)
                else:
                    return json_response({'message': 'Failed to create expense'}, 500)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in expense POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        try:
            if self.path.startswith('/expenses/'):
                expense_id = int(self.path.split('/')[-1])
                expense_record = expense_query.get_expense_by_id(expense_id)

                if expense_record is not None:
                    expense_data = self.get_request_body()
                    if not expense_data:
                        return json_response({'message': 'Invalid JSON data'}, 400)

                    # Validate amount if provided
                    if 'amount' in expense_data and not validate_amount(expense_data['amount']):
                        return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

                    # Sanitize inputs
                    if 'category' in expense_data:
                        expense_data['category'] = sanitize_string(expense_data['category'])
                    if 'description' in expense_data:
                        expense_data['description'] = sanitize_string(expense_data['description'])

                    updated_expense = expense_query.update_expense(expense_id, expense_data)

                    if updated_expense:
                        return json_response({'message': 'Expense updated successfully'})
                    else:
                        return json_response({'message': 'Failed to update expense'}, 500)
                else:
                    return json_response({'message': 'Expense not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in expense PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        try:
            if self.path.startswith('/expenses/'):
                expense_id = int(self.path.split('/')[-1])
                expense_record = expense_query.get_expense_by_id(expense_id)

                if expense_record is not None:
                    result = expense_query.delete_expense(expense_id)

                    if result:
                        return json_response({'message': 'Expense deleted successfully'})
                    else:
                        return json_response({'message': 'Failed to delete expense'}, 500)
                else:
                    return json_response({'message': 'Expense not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in expense DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)
