import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, sanitize_string
from database.notification_query import (
    create_notification,
    get_notification_by_id,
    get_notifications_by_user,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    delete_notification,
    get_unread_count,
)

logger = logging.getLogger(__name__)


class NotificationController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path.endswith('/unread-count'):
                count = get_unread_count(user_data['user_id'])
                return json_response({'unread_count': count})

            if self.path.startswith('/notifications/') and not self.path.endswith('/unread-count'):
                notification_id = int(self.path.split('/')[-1])
                notification_record = get_notification_by_id(notification_id)
                if notification_record and notification_record.user_id == user_data['user_id']:
                    return json_response({
                        'id': notification_record.id,
                        'notification_type': notification_record.notification_type,
                        'message': notification_record.message,
                        'user_id': notification_record.user_id,
                        'sent': notification_record.sent,
                        'read': notification_record.read,
                        'created_at': str(notification_record.created_at)
                        if notification_record.created_at
                        else None,
                    })
                return json_response({'message': 'Notification not found'}, 404)

            if self.path == '/notifications':
                unread_only = self.query_params.get('unread_only', ['false'])[0].lower() == 'true'
                limit = int(self.query_params.get('limit', [50])[0])
                offset = int(self.query_params.get('offset', [0])[0])
                notifications = get_notifications_by_user(
                    user_data['user_id'], unread_only, limit, offset
                )
                return json_response([
                    {
                        'id': n.id,
                        'notification_type': n.notification_type,
                        'message': n.message,
                        'user_id': n.user_id,
                        'sent': n.sent,
                        'read': n.read,
                        'created_at': str(n.created_at) if n.created_at else None,
                    }
                    for n in notifications
                ])

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in notification GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path != '/notifications':
                return json_response({'message': 'Not found'}, 404)

            notification_data = self.get_request_body()
            if not notification_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            required_fields = ['notification_type', 'message']
            is_valid, error_message = validate_required_fields(notification_data, required_fields)
            if not is_valid:
                return json_response({'message': error_message}, 400)

            notification_data['notification_type'] = sanitize_string(
                notification_data['notification_type']
            )
            notification_data['message'] = sanitize_string(notification_data['message'])
            notification_data['user_id'] = user_data['user_id']

            result = create_notification(notification_data)
            if result:
                return json_response({'message': 'Notification created successfully'}, 201)
            return json_response({'message': 'Failed to create notification'}, 500)
        except Exception as e:
            logger.error(f"Error in notification POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path == '/notifications/read-all':
                result = mark_all_notifications_as_read(user_data['user_id'])
                if result:
                    return json_response({'message': 'All notifications marked as read'})
                return json_response({'message': 'Failed to mark all notifications as read'}, 500)

            if self.path.endswith('/read') and self.path.startswith('/notifications/'):
                parts = self.path.strip('/').split('/')
                # notifications/{id}/read
                notification_id = int(parts[1])
                notification_record = get_notification_by_id(notification_id)
                if not notification_record or notification_record.user_id != user_data['user_id']:
                    return json_response({'message': 'Notification not found'}, 404)
                result = mark_notification_as_read(notification_id, user_data['user_id'])
                if result:
                    return json_response({'message': 'Notification marked as read'})
                return json_response({'message': 'Failed to mark notification as read'}, 500)

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in notification PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/notifications/'):
                return json_response({'message': 'Not found'}, 404)

            notification_id = int(self.path.split('/')[-1])
            notification_record = get_notification_by_id(notification_id)

            if not notification_record or notification_record.user_id != user_data['user_id']:
                return json_response({'message': 'Notification not found'}, 404)

            result = delete_notification(notification_id, user_data['user_id'])
            if result:
                return json_response({'message': 'Notification deleted successfully'})
            return json_response({'message': 'Failed to delete notification'}, 500)
        except Exception as e:
            logger.error(f"Error in notification DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)
