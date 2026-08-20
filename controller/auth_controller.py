import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_email, sanitize_string
from utils.authentication import auth_manager
from database import user_query
from model.user import user

logger = logging.getLogger(__name__)


class AuthController(APIServiceHelper):
    def handle_post(self) -> Dict[str, Any]:
        """Handle authentication requests"""
        try:
            if self.path == '/auth/login':
                return self._handle_login()
            if self.path == '/auth/register':
                return self._handle_register()
            return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in auth POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)

    def _handle_login(self) -> Dict[str, Any]:
        """Handle user login"""
        login_data = self.get_request_body()
        if not login_data:
            return json_response({'message': 'Invalid JSON data'}, 400)

        required_fields = ['username', 'password']
        is_valid, error_message = validate_required_fields(login_data, required_fields)
        if not is_valid:
            return json_response({'message': error_message}, 400)

        username = sanitize_string(login_data['username'])
        password = login_data['password']

        user_data = auth_manager.authenticate_user(username, password)
        if not user_data:
            return json_response({'message': 'Invalid credentials'}, 401)

        token = auth_manager.generate_token(user_data)

        return json_response({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role'],
            },
        })

    def _handle_register(self) -> Dict[str, Any]:
        """Handle user registration"""
        register_data = self.get_request_body()
        if not register_data:
            return json_response({'message': 'Invalid JSON data'}, 400)

        required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        is_valid, error_message = validate_required_fields(register_data, required_fields)
        if not is_valid:
            return json_response({'message': error_message}, 400)

        if not validate_email(register_data['email']):
            return json_response({'message': 'Invalid email format'}, 400)

        existing = user_query.get_user_by_username(sanitize_string(register_data['username']))
        if existing:
            return json_response({'message': 'Username already exists'}, 409)

        sanitized_data = {
            'username': sanitize_string(register_data['username']),
            'password': auth_manager.hash_password(register_data['password']),
            'email': sanitize_string(register_data['email']),
            'phone_number': sanitize_string(register_data.get('phone_number', '')),
            'first_name': sanitize_string(register_data['first_name']),
            'last_name': sanitize_string(register_data['last_name']),
            'role': 'user',
        }

        user_obj = user(user_id=None, **sanitized_data)
        result = user_query.create_user(user_obj)
        if result:
            return json_response({'message': 'User registered successfully'}, 201)
        return json_response({'message': 'Failed to register user'}, 500)
