import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import (
    json_response,
    validate_required_fields,
    validate_email,
    validate_phone_number,
    sanitize_string,
)
from utils.authentication import auth_manager
from database import user_query
from model.user import user

logger = logging.getLogger(__name__)


class UserController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if self.path.startswith('/users/'):
                user_id = int(self.path.split('/')[-1])
                user_record = user_query.get_user_by_id(user_id)

                if user_record and (
                    user_record.user_id == user_data['user_id'] or user_data['role'] == 'admin'
                ):
                    return json_response({
                        'user_id': user_record.user_id,
                        'username': user_record.username,
                        'email': user_record.email,
                        'phone_number': user_record.phone_number,
                        'first_name': user_record.first_name,
                        'last_name': user_record.last_name,
                        'role': user_record.role,
                    })
                return json_response({'message': 'User not found'}, 404)

            if self.path == '/users':
                if user_data['role'] != 'admin':
                    return json_response({'message': 'Access denied'}, 403)

                users = user_query.get_all_users()
                return json_response([
                    {
                        'user_id': u.user_id,
                        'username': u.username,
                        'email': u.email,
                        'phone_number': u.phone_number,
                        'first_name': u.first_name,
                        'last_name': u.last_name,
                        'role': u.role,
                    }
                    for u in users
                ])

            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in user GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if user_data['role'] != 'admin':
                return json_response({'message': 'Access denied'}, 403)

            if self.path != '/users':
                return json_response({'message': 'Not found'}, 404)

            body = self.get_request_body()
            if not body:
                return json_response({'message': 'Invalid JSON data'}, 400)

            required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
            is_valid, error_message = validate_required_fields(body, required_fields)
            if not is_valid:
                return json_response({'message': error_message}, 400)

            if not validate_email(body['email']):
                return json_response({'message': 'Invalid email format'}, 400)

            if body.get('phone_number') and not validate_phone_number(body['phone_number']):
                return json_response({'message': 'Invalid phone number format'}, 400)

            sanitized_data = {
                'username': sanitize_string(body['username']),
                'password': auth_manager.hash_password(body['password']),
                'email': sanitize_string(body['email']),
                'phone_number': sanitize_string(body.get('phone_number', '')),
                'first_name': sanitize_string(body['first_name']),
                'last_name': sanitize_string(body['last_name']),
                'role': body.get('role', 'user') if user_data['role'] == 'admin' else 'user',
            }

            user_obj = user(user_id=None, **sanitized_data)
            result = user_query.create_user(user_obj)
            if result:
                return json_response({'message': 'User created successfully'}, 201)
            return json_response({'message': 'Failed to create user'}, 500)
        except Exception as e:
            logger.error(f"Error in user POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/users/'):
                return json_response({'message': 'Not found'}, 404)

            user_id = int(self.path.split('/')[-1])
            user_record = user_query.get_user_by_id(user_id)

            if not user_record or (
                user_record.user_id != user_data['user_id'] and user_data['role'] != 'admin'
            ):
                return json_response({'message': 'User not found'}, 404)

            update_data = self.get_request_body()
            if not update_data:
                return json_response({'message': 'Invalid JSON data'}, 400)

            if 'email' in update_data and not validate_email(update_data['email']):
                return json_response({'message': 'Invalid email format'}, 400)

            if update_data.get('phone_number') and not validate_phone_number(update_data['phone_number']):
                return json_response({'message': 'Invalid phone number format'}, 400)

            for field in ['username', 'email', 'phone_number', 'first_name', 'last_name']:
                if field in update_data:
                    update_data[field] = sanitize_string(update_data[field])

            if 'password' in update_data:
                update_data['password'] = auth_manager.hash_password(update_data['password'])

            if 'role' in update_data and user_data['role'] != 'admin':
                del update_data['role']

            result = user_query.update_user(user_id, update_data)
            if result:
                return json_response({'message': 'User updated successfully'})
            return json_response({'message': 'Failed to update user'}, 500)
        except Exception as e:
            logger.error(f"Error in user PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        try:
            user_data = self.get_auth_user()
            if not user_data:
                return json_response({'message': 'Unauthorized'}, 401)

            if not self.path.startswith('/users/'):
                return json_response({'message': 'Not found'}, 404)

            user_id = int(self.path.split('/')[-1])
            user_record = user_query.get_user_by_id(user_id)

            if not user_record or (
                user_record.user_id != user_data['user_id'] and user_data['role'] != 'admin'
            ):
                return json_response({'message': 'User not found'}, 404)

            result = user_query.delete_user(user_id)
            if result:
                return json_response({'message': 'User deleted successfully'})
            return json_response({'message': 'Failed to delete user'}, 500)
        except Exception as e:
            logger.error(f"Error in user DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)
