import logging
from typing import Dict, Any, Optional
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_email, validate_phone_number, sanitize_string
from utils.authentication import auth_manager, TokenValidationMiddleware
import user_query
from model.user import user

logger = logging.getLogger(__name__)

class UserController(APIServiceHelper):
    def handle_get(self) -> Dict[str, Any]:
        """Handle GET requests for users"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/users/'):
                # Get specific user
                user_id = int(self.path.split('/')[-1])
                user_record = user_query.get_user_by_id(user_id)
                
                if user_record and (user_record.user_id == user_data['user_id'] or user_data['role'] == 'admin'):
                    user_data_response = {
                        'user_id': user_record.user_id,
                        'username': user_record.username,
                        'email': user_record.email,
                        'phone_number': user_record.phone_number,
                        'first_name': user_record.first_name,
                        'last_name': user_record.last_name,
                        'role': user_record.role
                    }
                    return json_response(user_data_response)
                else:
                    return json_response({'message': 'User not found'}, 404)
            elif self.path == '/users':
                # Admin only: Get all users
                if user_data['role'] != 'admin':
                    return json_response({'message': 'Access denied'}, 403)
                
                users = user_query.get_all_users()
                users_data = []
                
                for user_record in users:
                    user_data_response = {
                        'user_id': user_record.user_id,
                        'username': user_record.username,
                        'email': user_record.email,
                        'phone_number': user_record.phone_number,
                        'first_name': user_record.first_name,
                        'last_name': user_record.last_name,
                        'role': user_record.role
                    }
                    users_data.append(user_data_response)
                
                return json_response(users_data)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in user GET: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_post(self) -> Dict[str, Any]:
        """Handle POST requests for users"""
        try:
            if self.path == '/users':
                user_data = self.get_request_body()
                if not user_data:
                    return json_response({'message': 'Invalid JSON data'}, 400)

                # Validate required fields
                required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
                is_valid, error_message = validate_required_fields(user_data, required_fields)
                if not is_valid:
                    return json_response({'message': error_message}, 400)

                # Validate email
                if not validate_email(user_data['email']):
                    return json_response({'message': 'Invalid email format'}, 400)

                # Validate phone number if provided
                if 'phone_number' in user_data and user_data['phone_number']:
                    if not validate_phone_number(user_data['phone_number']):
                        return json_response({'message': 'Invalid phone number format'}, 400)

                # Sanitize inputs
                sanitized_data = {
                    'username': sanitize_string(user_data['username']),
                    'password': user_data['password'],  # Will be hashed in user creation
                    'email': sanitize_string(user_data['email']),
                    'phone_number': sanitize_string(user_data.get('phone_number', '')),
                    'first_name': sanitize_string(user_data['first_name']),
                    'last_name': sanitize_string(user_data['last_name']),
                    'role': 'user'  # Default role for registration
                }

                # Hash password
                sanitized_data['password'] = auth_manager.hash_password(sanitized_data['password'])

                user_obj = user(
                    user_id=None,  # Will be set by database
                    **sanitized_data
                )

                result = user_query.create_user(user_obj)
                if result:
                    return json_response({'message': 'User created successfully'}, 201)
                else:
                    return json_response({'message': 'Failed to create user'}, 500)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in user POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_put(self) -> Dict[str, Any]:
        """Handle PUT requests for users"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/users/'):
                user_id = int(self.path.split('/')[-1])
                user_record = user_query.get_user_by_id(user_id)

                # Check if user can update this record
                if user_record and (user_record.user_id == user_data['user_id'] or user_data['role'] == 'admin'):
                    update_data = self.get_request_body()
                    if not update_data:
                        return json_response({'message': 'Invalid JSON data'}, 400)

                    # Validate email if provided
                    if 'email' in update_data and not validate_email(update_data['email']):
                        return json_response({'message': 'Invalid email format'}, 400)

                    # Validate phone number if provided
                    if 'phone_number' in update_data and update_data['phone_number']:
                        if not validate_phone_number(update_data['phone_number']):
                            return json_response({'message': 'Invalid phone number format'}, 400)

                    # Sanitize inputs
                    if 'username' in update_data:
                        update_data['username'] = sanitize_string(update_data['username'])
                    if 'email' in update_data:
                        update_data['email'] = sanitize_string(update_data['email'])
                    if 'phone_number' in update_data:
                        update_data['phone_number'] = sanitize_string(update_data['phone_number'])
                    if 'first_name' in update_data:
                        update_data['first_name'] = sanitize_string(update_data['first_name'])
                    if 'last_name' in update_data:
                        update_data['last_name'] = sanitize_string(update_data['last_name'])

                    # Hash password if provided
                    if 'password' in update_data:
                        update_data['password'] = auth_manager.hash_password(update_data['password'])

                    # Update user object properties
                    for key, value in update_data.items():
                        if hasattr(user_record, key):
                            setattr(user_record, key, value)

                    result = user_query.update_user(user_record)
                    if result:
                        return json_response({'message': 'User updated successfully'})
                    else:
                        return json_response({'message': 'Failed to update user'}, 500)
                else:
                    return json_response({'message': 'User not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in user PUT: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def handle_delete(self) -> Dict[str, Any]:
        """Handle DELETE requests for users"""
        try:
            # Validate token
            is_valid, auth_result = TokenValidationMiddleware.validate_request(self.handler)
            if not is_valid:
                return json_response(auth_result, 401)

            user_data = auth_result

            if self.path.startswith('/users/'):
                user_id = int(self.path.split('/')[-1])
                user_record = user_query.get_user_by_id(user_id)

                # Check if user can delete this record
                if user_record and (user_record.user_id == user_data['user_id'] or user_data['role'] == 'admin'):
                    result = user_query.delete_user(user_id)
                    if result:
                        return json_response({'message': 'User deleted successfully'})
                    else:
                        return json_response({'message': 'Failed to delete user'}, 500)
                else:
                    return json_response({'message': 'User not found'}, 404)
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in user DELETE: {e}")
            return json_response({'message': 'Internal server error'}, 500)