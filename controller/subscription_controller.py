import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response
from utils.subscription_manager import SubscriptionManager
from utils.cache import cache_get_json, cache_set_json

logger = logging.getLogger(__name__)


class SubscriptionController(APIServiceHelper):
    def __init__(self, handler, query_params):
        super().__init__(handler, query_params)
        self.subscription_manager = SubscriptionManager()

    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            user_id = user_data['user_id']

            if self.path == '/subscriptions':
                days = int(self.query_params.get('days', [90])[0])
                cache_key = f"sub:{user_id}:{days}"
                cached = cache_get_json(cache_key)
                if cached is not None:
                    return json_response(cached)
                subscriptions = self.subscription_manager.detect_subscriptions(user_id, days)
                cache_set_json(cache_key, subscriptions, ttl_seconds=600)
                return json_response(subscriptions)

            if self.path == '/subscription-alternatives':
                service_name = self.query_params.get('service', [''])[0]
                max_cost = (
                    float(self.query_params.get('max_cost', [0])[0])
                    if self.query_params.get('max_cost')
                    else None
                )
                if not service_name:
                    return json_response({'message': 'Service name is required'}, 400)
                alternatives = self.subscription_manager.get_alternative_services(
                    service_name, max_cost
                )
                return json_response({'service': service_name, 'alternatives': alternatives})

            if self.path == '/subscription-changes':
                days = int(self.query_params.get('days', [30])[0])
                changes = self.subscription_manager.track_subscription_changes(user_id, days)
                return json_response(changes)

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in subscription GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)
