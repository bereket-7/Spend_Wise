import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, sanitize_string
from utils.authentication import auth_manager, TokenValidationMiddleware
from database.notification_query import (
    create_notification, get_notification_by_id, get_notifications_by_user, 
    mark_notification_as_read, mark_all_notifications_as_read, 
    delete_notification, get_unread_count, create_budget_alert
)
from model.notification import notification

logger = logging.getLogger(__name__)

class NotificationController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for notifications"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/notifications/'):
                if self.path.endswith('/unread-count'):
                    # Get unread count
                    count = get_unread_count(user_data['user_id'])
                    return json_response({'unread_count': count})
                else:
                    # Get specific notification
                    notification_id = int(self.path.split('/')[-1])
                    notification_record = get_notification_by_id(notification_id)
                    
                    if notification_record and notification_record.user_id == user_data['user_id']:
                        notification_data = {
                            'id': notification_record.id,
                            'notification_type': notification_record.notification_type,
                            'message': notification_record.message,
                            'user_id': notification_record.user_id,
                            'sent': notification_record.sent,
                            'read': notification_record.read,
                            'created_at': notification_record.created_at
                        }
                        return json_response(notification_data)
                    else:
                        return json_response({'message': 'Notification not found'}, 404)
            elif self.path == '/notifications':
                # Get all notifications for user with filters
                unread_only = self.query_params.get('unread_only', ['false'])[0].lower() == 'true'
                limit = int(self.query_params.get('limit', [50])[0])
                offset = int(self.query_params.get('offset', [0])[0])
                
                notifications = get_notifications_by_user(user_data['user_id'], unread_only, limit, offset)
                notifications_data = []
                
                for notification_record in notifications:
                    notification_data = {
                        'id': notification_record.id,
                        'notification_type': notification_record.notification_type,
                        'message': notification_record.message,
                        'user_id': notification_record.user_id,
                        'sent': notification_record.sent,
                        'read': notification_record.read,
                        'created_at': notification_record.created_at
                    }
                    notifications_data.append(notification_data)
                
                return json_response(notifications_data)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in notification GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        """Handle POST requests for notifications"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path == '/notifications':
                notification_data = self.get_request_body()
                if not notification_data:
                    return json_response({'message': 'Invalid JSON data'}, 400)

                # Validate required fields
                required_fields = ['notification_type', 'message']
                is_valid, error_message = validate_required_fields(notification_data, required_fields)
                if not is_valid:
                    return json_response({'message': error_message}, 400)

                # Sanitize inputs
                notification_data['notification_type'] = sanitize_string(notification_data['notification_type'])
                notification_data['message'] = sanitize_string(notification_data['message'])
                notification_data['user_id'] = user_data['user_id']

                result = create_notification(notification_data)
                if result:
                    return json_response({'message': 'Notification created successfully'}, 201)
                else:
                    return json_response({'message': 'Failed to create notification'}, 500)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in notification POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        """Handle PUT requests for notifications"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/notifications/'):
                notification_id = int(self.path.split('/')[-1])
                notification_record = get_notification_by_id(notification_id)

                if notification_record and notification_record.user_id == user_data['user_id']:
                    # Handle marking as read
                    if self.path.endswith('/read'):
                        result = mark_notification_as_read(notification_id, user_data['user_id'])
                        if result:
                            return json_response({'message': 'Notification marked as read'})
                        else:
                            return json_response({'message': 'Failed to mark notification as read'}, 500)
                    else:
                        return json_response({'message': 'Not found'}, 404)
                else:
                    return json_response({'message': 'Notification not found'}, 404)
            elif self.path == '/notifications/read-all':
                # Mark all notifications as read
                result = mark_all_notifications_as_read(user_data['user_id'])
                if result:
                    return json_response({'message': 'All notifications marked as read'})
                else:
                    return json_response({'message': 'Failed to mark all notifications as read'}, 500)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in notification PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        """Handle DELETE requests for notifications"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/notifications/'):
                notification_id = int(self.path.split('/')[-1])
                notification_record = get_notification_by_id(notification_id)

                if notification_record and notification_record.user_id == user_data['user_id']:
                    result = delete_notification(notification_id, user_data['user_id'])
                    if result:
                        return json_response({'message': 'Notification deleted successfully'})
                    else:
                        return json_response({'message': 'Failed to delete notification'}, 500)
                else:
                    return json_response({'message': 'Notification not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in notification DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)