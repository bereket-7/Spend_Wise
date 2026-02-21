import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response
from utils.authentication import auth_manager, TokenValidationMiddleware
from utils.financial_health import FinancialHealthCalculator

logger = logging.getLogger(__name__)

class FinancialHealthController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for financial health"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/financial-health':
                calculator = FinancialHealthCalculator()
                health_score = calculator.calculate_health_score(user_data['user_id'])
                
                return json_response(health_score)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in financial health GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)
