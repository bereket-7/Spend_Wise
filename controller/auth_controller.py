import logging
from typing import Dict, Any
from utils.api_service import APIServiceHelper
from utils.response import json_response, validate_required_fields, validate_email, sanitize_string
from utils.authentication import auth_manager
import user_query
from model.user import user

logger = logging.getLogger(__name__)

class AuthController(APIServiceHelper):
    def handle_post(self) -> Dict[str, Any]:
        """Handle authentication requests"""
        try:
            if self.path == '/auth/login':
                return self._handle_login()
            elif self.path == '/auth/register':
                return self._handle_register()
            else:
                return json_response({'message': 'Not found'}, 404)
        except Exception as e:
            logger.error(f"Error in auth POST: {e}")
            return json_response({'message': 'Internal server error'}, 500)
    
    def _handle_login(self) -> Dict[str, Any]:
        """Handle user login"""
        login_data = self.get_request_body()
        if not login_data:
            return json_response({'message': 'Invalid JSON data'}, 400)

        # Validate required fields
        required_fields = ['username', 'password']
        is_valid, error_message = validate_required_fields(login_data, required_fields)
        if not is_valid:
            return json_response({'message': error_message}, 400)

        username = sanitize_string(login_data['username'])
        password = login_data['password']

        # Authenticate user
        user_data = auth_manager.authenticate_user(username, password)
        if not user_data:
            return json_response({'message': 'Invalid credentials'}, 401)

        # Generate token
        token = auth_manager.generate_token(user_data)

        return json_response({
            'message': 'Login successful',
            'token': token,
            'user': {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data['role']
            }
        })
    
    def _handle_register(self) -> Dict[str, Any]:
        """Handle user registration"""
        register_data = self.get_request_body()
        if not register_data:
            return json_response({'message': 'Invalid JSON data'}, 400)

        # Validate required fields
        required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        is_valid, error_message = validate_required_fields(register_data, required_fields)
        if not is_valid:
            return json_response({'message': error_message}, 400)

        # Validate email
        if not validate_email(register_data['email']):
            return json_response({'message': 'Invalid email format'}, 400)

        # Sanitize inputs
        sanitized_data = {
            'username': sanitize_string(register_data['username']),
            'password': register_data['password'],  # Will be hashed in user creation
            'email': sanitize_string(register_data['email']),
            'phone_number': sanitize_string(register_data.get('phone_number', '')),
            'first_name': sanitize_string(register_data['first_name']),
            'last_name': sanitize_string(register_data['last_name']),
            'role': 'user'  # Default role
        }

        # Hash password
        sanitized_data['password'] = auth_manager.hash_password(sanitized_data['password'])

        # Create user
        user_obj = user(
            user_id=None,  # Will be set by database
            **sanitized_data
        )

        result = user_query.create_user(user_obj)
        if result:
            return json_response({'message': 'User registered successfully'}, 201)
        else:
            return json_response({'message': 'Failed to register user'}, 500)

class TokenValidationMiddleware:
    """Middleware to validate JWT tokens"""
    
    @staticmethod
    def validate_request(handler) -> tuple[bool, Dict[str, Any]]:
        """Validate request token and return (is_valid, user_data)"""
        try:
            authorization_header = handler.headers.get('Authorization')
            if not authorization_header:
                return False, {'message': 'Missing Authorization header'}

            token = auth_manager.extract_token_from_header(authorization_header)
            if not token:
                return False, {'message': 'Invalid token format'}

            user_data = auth_manager.verify_token(token)
            if not user_data:
                return False, {'message': 'Invalid or expired token'}

            return True, user_data
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False, {'message': 'Token validation failed'}
