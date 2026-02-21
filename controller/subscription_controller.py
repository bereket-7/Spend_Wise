import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields
from utils.authentication import auth_manager, TokenValidationMiddleware
from utils.subscription_manager import SubscriptionManager

logger = logging.getLogger(__name__)

class SubscriptionController(APIServiceHelper):
    def __init__(self, handler, query_params):
        super().__init__(handler, query_params)
        self.subscription_manager = SubscriptionManager()
    
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for subscription detection"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/subscriptions':
                # Detect subscriptions
                days = int(self.query_params.get('days', [90])[0])
                subscriptions = self.subscription_manager.detect_subscriptions(user_data['user_id'], days)
                
                return json_response(subscriptions)
            elif self.path == '/subscription-alternatives':
                # Get alternatives for a service
                service_name = self.query_params.get('service', [''])[0]
                max_cost = float(self.query_params.get('max_cost', [0])[0]) if self.query_params.get('max_cost') else None
                
                if not service_name:
                    return json_response({'message': 'Service name is required'}, 400)
                
                alternatives = self.subscription_manager.get_alternative_services(service_name, max_cost)
                
                return json_response({'service': service_name, 'alternatives': alternatives})
            elif self.path == '/subscription-changes':
                # Track subscription changes
                days = int(self.query_params.get('days', [30])[0])
                changes = self.subscription_manager.track_subscription_changes(user_data['user_id'], days)
                
                return json_response(changes)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in subscription GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)
