import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response
from utils.financial_health import FinancialHealthCalculator
from utils.cache import cache_get_json, cache_set_json

logger = logging.getLogger(__name__)


class FinancialHealthController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path != '/financial-health':
                return json_response({'message': 'Not found'}, 404)

            user_id = user_data['user_id']
            cache_key = f"fh:{user_id}"
            cached = cache_get_json(cache_key)
            if cached is not None:
                return json_response(cached)

            calculator = FinancialHealthCalculator()
            health_score = calculator.calculate_health_score(user_id)
            if 'error' not in health_score:
                cache_set_json(cache_key, health_score, ttl_seconds=300)
            return json_response(health_score)
        except Exception as e:
            logger.error(f"Error in financial health GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)
