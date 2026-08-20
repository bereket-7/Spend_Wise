import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_amount, sanitize_string
from database.income_query import (
    create_income,
    get_income_by_id,
    get_incomes_by_user,
    update_income,
    delete_income,
    get_income_summary,
)
from utils.cache import invalidate_user_cache

logger = logging.getLogger(__name__)


class IncomeController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path == '/incomes/summary' or self.path.endswith('/summary'):
                start_date = self.query_params.get('start_date', [None])[0]
                end_date = self.query_params.get('end_date', [None])[0]
                summary = get_income_summary(user_data['user_id'], start_date, end_date)
                return json_response(summary)

            if self.path.startswith('/incomes/'):
                income_id = int(self.path.split('/')[-1])
                income_record = get_income_by_id(income_id)
                if income_record and income_record.user_id == user_data['user_id']:
                    return json_response({
                        'id': income_record.id,
                        'amount': income_record.amount,
                        'source': income_record.source,
                        'date': str(income_record.date),
                        'user_id': income_record.user_id,
                    })
                return json_response({'message': 'Income not found'}, 404)

            if self.path == '/incomes':
                limit = int(self.query_params.get('limit', [100])[0])
                offset = int(self.query_params.get('offset', [0])[0])
                incomes = get_incomes_by_user(user_data['user_id'], limit, offset)
                return json_response([
                    {
                        'id': r.id,
                        'amount': r.amount,
                        'source': r.source,
                        'date': str(r.date),
                        'user_id': r.user_id,
                    }
                    for r in incomes
                ])

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in income GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path != '/incomes':
                return json_response({'message': 'Not found'}, 404)

            income_data = self.get_request_body()
            if not income_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            required_fields = ['amount', 'source', 'date']
            is_valid, error_message = validate_required_fields(income_data, required_fields)
            if not is_valid:
                return json_response({'message': error_message}, 400)

            if not validate_amount(income_data['amount']):
                return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

            income_data['source'] = sanitize_string(income_data['source'])
            income_data['user_id'] = user_data['user_id']

            result = create_income(income_data)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Income created successfully'}, 201)
            return json_response({'message': 'Failed to create income'}, 500)
        except Exception as e:
            logger.error(f"Error in income POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/incomes/'):
                return json_response({'message': 'Not found'}, 404)

            income_id = int(self.path.split('/')[-1])
            income_record = get_income_by_id(income_id)

            if not income_record or income_record.user_id != user_data['user_id']:
                return json_response({'message': 'Income not found'}, 404)

            income_data = self.get_request_body()
            if not income_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            if 'amount' in income_data and not validate_amount(income_data['amount']):
                return json_response({'message': 'Invalid amount. Must be a positive number'}, 400)

            if 'source' in income_data:
                income_data['source'] = sanitize_string(income_data['source'])

            result = update_income(income_id, income_data)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Income updated successfully'})
            return json_response({'message': 'Failed to update income'}, 500)
        except Exception as e:
            logger.error(f"Error in income PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/incomes/'):
                return json_response({'message': 'Not found'}, 404)

            income_id = int(self.path.split('/')[-1])
            income_record = get_income_by_id(income_id)

            if not income_record or income_record.user_id != user_data['user_id']:
                return json_response({'message': 'Income not found'}, 404)

            result = delete_income(income_id)
            if result:
                invalidate_user_cache(user_data['user_id'])
                return json_response({'message': 'Income deleted successfully'})
            return json_response({'message': 'Failed to delete income'}, 500)
        except Exception as e:
            logger.error(f"Error in income DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)
