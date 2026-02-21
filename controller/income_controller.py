import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_amount, sanitize_string
from utils.authentication import auth_manager, TokenValidationMiddleware
from database.income_query import create_income, get_income_by_id, get_incomes_by_user, update_income, delete_income, get_income_summary
from model.income import income

logger = logging.getLogger(__name__)

class IncomeController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for incomes"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/incomes/'):
                if self.path.endswith('/summary'):
                    # Get income summary
                    # Parse query parameters for date range
                    start_date = self.query_params.get('start_date', [None])[0]
                    end_date = self.query_params.get('end_date', [None])[0]
                    
                    summary = get_income_summary(user_data['user_id'], start_date, end_date)
                    return json_response(summary)
                else:
                    # Get specific income
                    income_id = int(self.path.split('/')[-1])
                    income_record = get_income_by_id(income_id)
                    
                    if income_record and income_record.user_id == user_data['user_id']:
                        income_data = {
                            'id': income_record.id,
                            'amount': income_record.amount,
                            'source': income_record.source,
                            'date': income_record.date,
                            'user_id': income_record.user_id
                        }
                        return json_response(income_data)
                    else:
                        return json_response({'message': 'Income not found'}, 404)
            elif self.path == '/incomes':
                # Get all incomes for user with pagination
                limit = int(self.query_params.get('limit', [100])[0])
                offset = int(self.query_params.get('offset', [0])[0])
                
                incomes = get_incomes_by_user(user_data['user_id'], limit, offset)
                incomes_data = []
                
                for income_record in incomes:
                    income_data = {
                        'id': income_record.id,
                        'amount': income_record.amount,
                        'source': income_record.source,
                        'date': income_record.date,
                        'user_id': income_record.user_id
                    }
                    incomes_data.append(income_data)
                
                return json_response(incomes_data)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in income GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        """Handle POST requests for incomes"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/incomes':
                income_data = self.get_request_body()
                if not income_data:
                    return json_response({'message': 'Invalid JSON data'}, 400)

                # Validate required fields
                required_fields = ['amount', 'source', 'date']
                is_valid, error_message = validate_required_fields(income_data, required_fields)
                if not is_valid:
                    return json_response({'message': error_message}, 400)

                # Validate amount
                if not validate_amount(income_data['amount']):
                    return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

                # Sanitize inputs
                income_data['source'] = sanitize_string(income_data['source'])
                income_data['user_id'] = user_data['user_id']

                result = create_income(income_data)
                if result:
                    return json_response({'message': 'Income created successfully'}, 201)
                else:
                    return json_response({'message': 'Failed to create income'}, 500)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in income POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        """Handle PUT requests for incomes"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/incomes/'):
                income_id = int(self.path.split('/')[-1])
                income_record = get_income_by_id(income_id)

                if income_record and income_record.user_id == user_data['user_id']:
                    income_data = self.get_request_body()
                    if not income_data:
                        return json_response({'message': 'Invalid JSON data'}, 400)

                    # Validate amount if provided
                    if 'amount' in income_data and not validate_amount(income_data['amount']):
                        return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

                    # Sanitize inputs
                    if 'source' in income_data:
                        income_data['source'] = sanitize_string(income_data['source'])

                    result = update_income(income_id, income_data)
                    if result:
                        return json_response({'message': 'Income updated successfully'})
                    else:
                        return json_response({'message': 'Failed to update income'}, 500)
                else:
                    return json_response({'message': 'Income not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in income PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        """Handle DELETE requests for incomes"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/incomes/'):
                income_id = int(self.path.split('/')[-1])
                income_record = get_income_by_id(income_id)

                if income_record and income_record.user_id == user_data['user_id']:
                    result = delete_income(income_id)
                    if result:
                        return json_response({'message': 'Income deleted successfully'})
                    else:
                        return json_response({'message': 'Failed to delete income'}, 500)
                else:
                    return json_response({'message': 'Income not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in income DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)