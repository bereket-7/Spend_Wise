import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_amount, sanitize_string
from database import expense_query
from utils.cache import invalidate_user_cache

logger = logging.getLogger(__name__)


def _expense_to_dict(record) -> Dict[str, Any]:
    return {
        'id': record.id,
        'amount': record.amount,
        'category': record.category,
        'date': record.date,
        'user_id': record.user_id,
        'description': record.description,
    }


class ExpenseController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            user_id = user_data['user_id']

            if self.path.startswith('/expenses/'):
                expense_id = int(self.path.split('/')[-1])
                expense_record = expense_query.get_expense_by_id(expense_id, user_id)

                if expense_record is not None:
                    return json_response(_expense_to_dict(expense_record))
                return json_response({'message': 'Expense not found'}, 404)

            if self.path == '/expenses':
                limit = int(self.query_params.get('limit', [100])[0])
                offset = int(self.query_params.get('offset', [0])[0])
                expenses = expense_query.get_expenses_by_user(user_id, limit, offset)
                return json_response([_expense_to_dict(e) for e in expenses])

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in expense GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path != '/expenses':
                return json_response({'message': 'Not found'}, 404)

            expense_data = self.get_request_body()
            if not expense_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            required_fields = ['amount', 'category', 'date']
            is_valid, error_message = validate_required_fields(expense_data, required_fields)
            if not is_valid:
                return json_response({'message': error_message}, 400)

            if not validate_amount(expense_data['amount']):
                return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

            expense_data['category'] = sanitize_string(expense_data['category'])
            if expense_data.get('description'):
                expense_data['description'] = sanitize_string(expense_data['description'])
            expense_data['user_id'] = user_data['user_id']

            result = expense_query.create_expense(expense_data)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Expense created successfully'}, 201)
            return json_response({'message': 'Failed to create expense'}, 500)
        except Exception as e:
            logger.error(f"Error in expense POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/expenses/'):
                return json_response({'message': 'Not found'}, 404)

            expense_id = int(self.path.split('/')[-1])
            user_id = user_data['user_id']
            expense_record = expense_query.get_expense_by_id(expense_id, user_id)

            if expense_record is None:
                return json_response({'message': 'Expense not found'}, 404)

            expense_data = self.get_request_body()
            if not expense_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            if 'amount' in expense_data and not validate_amount(expense_data['amount']):
                return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

            if 'category' in expense_data:
                expense_data['category'] = sanitize_string(expense_data['category'])
            if 'description' in expense_data:
                expense_data['description'] = sanitize_string(expense_data['description'])

            updated = expense_query.update_expense(expense_id, expense_data, user_id)
            if updated:
                invalidate_user_cache(user_id)
                return json_response({'message': 'Expense updated successfully'})
            return json_response({'message': 'Failed to update expense'}, 500)
        except Exception as e:
            logger.error(f"Error in expense PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/expenses/'):
                return json_response({'message': 'Not found'}, 404)

            expense_id = int(self.path.split('/')[-1])
            user_id = user_data['user_id']
            expense_record = expense_query.get_expense_by_id(expense_id, user_id)

            if expense_record is None:
                return json_response({'message': 'Expense not found'}, 404)

            result = expense_query.delete_expense(expense_id, user_id)
            if result:
                invalidate_user_cache(user_id)
                return json_response({'message': 'Expense deleted successfully'})
            return json_response({'message': 'Failed to delete expense'}, 500)
        except Exception as e:
            logger.error(f"Error in expense DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)
