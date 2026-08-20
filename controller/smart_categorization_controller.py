import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, sanitize_string
from utils.expense_categorizer import ExpenseCategorizer
from utils.cache import cache_get_json, cache_set_json

logger = logging.getLogger(__name__)


class SmartCategorizationController(APIServiceHelper):
    def __init__(self, handler, query_params):
        super().__init__(handler, query_params)
        self.categorizer = ExpenseCategorizer()

    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            user_id = user_data['user_id']

            if self.path == '/smart-categorize':
                description = self.query_params.get('description', [''])[0]
                amount = float(self.query_params.get('amount', [0])[0])
                merchant = self.query_params.get('merchant', [''])[0]

                if not description:
                    return json_response({'message': 'Description is required'}, 400)

                result = self.categorizer.categorize_expense(
                    description, amount, merchant, user_id
                )
                return json_response(result)

            if self.path == '/category-suggestions':
                partial_text = self.query_params.get('text', [''])[0]
                if not partial_text:
                    return json_response({'message': 'Text parameter is required'}, 400)
                suggestions = self.categorizer.get_category_suggestions(partial_text, user_id)
                return json_response({'suggestions': suggestions})

            if self.path == '/spending-patterns':
                days = int(self.query_params.get('days', [30])[0])
                cache_key = f"sp:{user_id}:{days}"
                cached = cache_get_json(cache_key)
                if cached is not None:
                    return json_response(cached)
                patterns = self.categorizer.analyze_user_patterns(user_id, days)
                if 'error' not in patterns:
                    cache_set_json(cache_key, patterns, ttl_seconds=600)
                return json_response(patterns)

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in smart categorization GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path != '/learn-categorization':
                return json_response({'message': 'Not found'}, 404)

            correction_data = self.get_request_body()
            if not correction_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            required_fields = [
                'original_description',
                'original_category',
                'correct_category',
                'amount',
            ]
            is_valid, error_message = validate_required_fields(correction_data, required_fields)
            if not is_valid:
                return json_response({'message': error_message}, 400)

            self.categorizer.learn_from_correction(
                user_data['user_id'],
                sanitize_string(correction_data['original_description']),
                sanitize_string(correction_data['original_category']),
                sanitize_string(correction_data['correct_category']),
                float(correction_data['amount']),
                sanitize_string(correction_data.get('merchant', '')),
            )
            return json_response({'message': 'Learning data saved successfully'})
        except Exception as e:
            logger.error(f"Error in smart categorization POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)
