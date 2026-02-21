import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, sanitize_string
from utils.authentication import auth_manager, TokenValidationMiddleware
from utils.expense_categorizer import ExpenseCategorizer

logger = logging.getLogger(__name__)

class SmartCategorizationController(APIServiceHelper):
    def __init__(self, handler, query_params):
        super().__init__(handler, query_params)
        self.categorizer = ExpenseCategorizer()
    
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for smart categorization"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/smart-categorize':
                # Get query parameters
                description = self.query_params.get('description', [''])[0]
                amount = float(self.query_params.get('amount', [0])[0])
                merchant = self.query_params.get('merchant', [''])[0]
                
                if not description:
                    return json_response({'message': 'Description is required'}, 400)
                
                # Categorize the expense
                result = self.categorizer.categorize_expense(
                    description, amount, merchant, user_data['user_id']
                )
                
                return json_response(result)
            elif self.path == '/category-suggestions':
                # Get category suggestions
                partial_text = self.query_params.get('text', [''])[0]
                
                if not partial_text:
                    return json_response({'message': 'Text parameter is required'}, 400)
                
                suggestions = self.categorizer.get_category_suggestions(
                    partial_text, user_data['user_id']
                )
                
                return json_response({'suggestions': suggestions})
            elif self.path == '/spending-patterns':
                # Analyze user spending patterns
                days = int(self.query_params.get('days', [30])[0])
                patterns = self.categorizer.analyze_user_patterns(user_data['user_id'], days)
                
                return json_response(patterns)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in smart categorization GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        """Handle POST requests for learning from corrections"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/learn-categorization':
                correction_data = self.get_request_body()
                if not correction_data:
                    return json_response({'message': 'Invalid JSON data'}, 400)

                # Validate required fields
                required_fields = ['original_description', 'original_category', 'correct_category', 'amount']
                is_valid, error_message = validate_required_fields(correction_data, required_fields)
                if not is_valid:
                    return json_response({'message': error_message}, 400)

                # Sanitize inputs
                sanitized_data = {
                    'original_description': sanitize_string(correction_data['original_description']),
                    'original_category': sanitize_string(correction_data['original_category']),
                    'correct_category': sanitize_string(correction_data['correct_category']),
                    'amount': float(correction_data['amount']),
                    'merchant': sanitize_string(correction_data.get('merchant', ''))
                }

                # Learn from user correction
                self.categorizer.learn_from_correction(
                    user_data['user_id'],
                    sanitized_data['original_description'],
                    sanitized_data['original_category'],
                    sanitized_data['correct_category'],
                    sanitized_data['amount'],
                    sanitized_data['merchant']
                )

                return json_response({'message': 'Learning data saved successfully'})
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in smart categorization POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)
