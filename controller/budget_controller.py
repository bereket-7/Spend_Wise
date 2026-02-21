import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_amount, sanitize_string
from utils.authentication import auth_manager, TokenValidationMiddleware
from database.budget_query import create_budget, get_budget_by_id, get_budgets_by_user, update_budget, delete_budget, get_budget_spending
from model.budget import budget

logger = logging.getLogger(__name__)

class BudgetController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for budgets"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/budgets/'):
                if self.path.endswith('/spending'):
                    # Get budget spending information
                    budget_id = int(self.path.split('/')[-2])
                    spending_info = get_budget_spending(budget_id)
                    if spending_info:
                        return json_response(spending_info)
                    else:
                        return json_response({'message': 'Budget not found'}, 404)
                else:
                    # Get specific budget
                    budget_id = int(self.path.split('/')[-1])
                    budget_record = get_budget_by_id(budget_id)
                    
                    if budget_record and budget_record.user_id == user_data['user_id']:
                        budget_data = {
                            'id': budget_record.id,
                            'amount': budget_record.amount,
                            'category': budget_record.category,
                            'start_date': budget_record.start_date,
                            'end_date': budget_record.end_date,
                            'user_id': budget_record.user_id
                        }
                        return json_response(budget_data)
                    else:
                        return json_response({'message': 'Budget not found'}, 404)
            elif self.path == '/budgets':
                # Get all budgets for user
                budgets = get_budgets_by_user(user_data['user_id'])
                budgets_data = []
                
                for budget_record in budgets:
                    spending_info = get_budget_spending(budget_record.id)
                    budget_data = {
                        'id': budget_record.id,
                        'amount': budget_record.amount,
                        'category': budget_record.category,
                        'start_date': budget_record.start_date,
                        'end_date': budget_record.end_date,
                        'user_id': budget_record.user_id,
                        'spending': spending_info
                    }
                    budgets_data.append(budget_data)
                
                return json_response(budgets_data)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in budget GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        """Handle POST requests for budgets"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/budgets':
                budget_data = self.get_request_body()
                if not budget_data:
                    return json_response({'message': 'Invalid JSON data'}, 400)

                # Validate required fields
                required_fields = ['amount', 'category', 'start_date', 'end_date']
                is_valid, error_message = validate_required_fields(budget_data, required_fields)
                if not is_valid:
                    return json_response({'message': error_message}, 400)

                # Validate amount
                if not validate_amount(budget_data['amount']):
                    return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

                # Sanitize inputs
                budget_data['category'] = sanitize_string(budget_data['category'])
                budget_data['user_id'] = user_data['user_id']

                result = create_budget(budget_data)
                if result:
                    return json_response({'message': 'Budget created successfully'}, 201)
                else:
                    return json_response({'message': 'Failed to create budget'}, 500)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in budget POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        """Handle PUT requests for budgets"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/budgets/'):
                budget_id = int(self.path.split('/')[-1])
                budget_record = get_budget_by_id(budget_id)

                if budget_record and budget_record.user_id == user_data['user_id']:
                    budget_data = self.get_request_body()
                    if not budget_data:
                        return json_response({'message': 'Invalid JSON data'}, 400)

                    # Validate amount if provided
                    if 'amount' in budget_data and not validate_amount(budget_data['amount']):
                        return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

                    # Sanitize inputs
                    if 'category' in budget_data:
                        budget_data['category'] = sanitize_string(budget_data['category'])

                    result = update_budget(budget_id, budget_data)
                    if result:
                        return json_response({'message': 'Budget updated successfully'})
                    else:
                        return json_response({'message': 'Failed to update budget'}, 500)
                else:
                    return json_response({'message': 'Budget not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in budget PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        """Handle DELETE requests for budgets"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/budgets/'):
                budget_id = int(self.path.split('/')[-1])
                budget_record = get_budget_by_id(budget_id)

                if budget_record and budget_record.user_id == user_data['user_id']:
                    result = delete_budget(budget_id)
                    if result:
                        return json_response({'message': 'Budget deleted successfully'})
                    else:
                        return json_response({'message': 'Failed to delete budget'}, 500)
                else:
                    return json_response({'message': 'Budget not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in budget DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)