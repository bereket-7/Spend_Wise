import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_amount, sanitize_string
from database.budget_query import (
    create_budget,
    get_budget_by_id,
    get_budgets_by_user,
    update_budget,
    delete_budget,
    get_budget_spending,
)
from utils.cache import invalidate_user_cache

logger = logging.getLogger(__name__)


class BudgetController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path.startswith('/budgets/'):
                if self.path.endswith('/spending'):
                    budget_id = int(self.path.split('/')[-2])
                    budget_record = get_budget_by_id(budget_id)
                    if not budget_record or budget_record.user_id != user_data['user_id']:
                        return json_response({'message': 'Budget not found'}, 404)
                    spending_info = get_budget_spending(budget_id)
                    if spending_info:
                        return json_response(spending_info)
                    return json_response({'message': 'Budget not found'}, 404)

                budget_id = int(self.path.split('/')[-1])
                budget_record = get_budget_by_id(budget_id)
                if budget_record and budget_record.user_id == user_data['user_id']:
                    return json_response({
                        'id': budget_record.id,
                        'amount': budget_record.amount,
                        'category': budget_record.category,
                        'start_date': str(budget_record.start_date),
                        'end_date': str(budget_record.end_date),
                        'user_id': budget_record.user_id,
                    })
                return json_response({'message': 'Budget not found'}, 404)

            if self.path == '/budgets':
                budgets = get_budgets_by_user(user_data['user_id'])
                budgets_data = []
                for budget_record in budgets:
                    spending_info = get_budget_spending(budget_record.id)
                    budgets_data.append({
                        'id': budget_record.id,
                        'amount': budget_record.amount,
                        'category': budget_record.category,
                        'start_date': str(budget_record.start_date),
                        'end_date': str(budget_record.end_date),
                        'user_id': budget_record.user_id,
                        'spending': spending_info,
                    })
                return json_response(budgets_data)

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in budget GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path != '/budgets':
                return json_response({'message': 'Not found'}, 404)

            budget_data = self.get_request_body()
            if not budget_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            required_fields = ['amount', 'category', 'start_date', 'end_date']
            is_valid, error_message = validate_required_fields(budget_data, required_fields)
            if not is_valid:
                return json_response({'message': error_message}, 400)

            if not validate_amount(budget_data['amount']):
                return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

            budget_data['category'] = sanitize_string(budget_data['category'])
            budget_data['user_id'] = user_data['user_id']

            result = create_budget(budget_data)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Budget created successfully'}, 201)
            return json_response({'message': 'Failed to create budget'}, 500)
        except Exception as e:
            logger.error(f"Error in budget POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/budgets/'):
                return json_response({'message': 'Not found'}, 404)

            budget_id = int(self.path.split('/')[-1])
            budget_record = get_budget_by_id(budget_id)

            if not budget_record or budget_record.user_id != user_data['user_id']:
                return json_response({'message': 'Budget not found'}, 404)

            budget_data = self.get_request_body()
            if not budget_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            if 'amount' in budget_data and not validate_amount(budget_data['amount']):
                return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

            if 'category' in budget_data:
                budget_data['category'] = sanitize_string(budget_data['category'])

            result = update_budget(budget_id, budget_data)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Budget updated successfully'})
            return json_response({'message': 'Failed to update budget'}, 500)
        except Exception as e:
            logger.error(f"Error in budget PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/budgets/'):
                return json_response({'message': 'Not found'}, 404)

            budget_id = int(self.path.split('/')[-1])
            budget_record = get_budget_by_id(budget_id)

            if not budget_record or budget_record.user_id != user_data['user_id']:
                return json_response({'message': 'Budget not found'}, 404)

            result = delete_budget(budget_id)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Budget deleted successfully'})
            return json_response({'message': 'Failed to delete budget'}, 500)
        except Exception as e:
            logger.error(f"Error in budget DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)
