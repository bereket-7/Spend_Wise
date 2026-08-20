import jwt
import hashlib
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple

import bcrypt

from database.database_connection import get_connection, release_connection

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
    '/auth/login',
    '/auth/register',
    '/health',
    '/metrics',
}

BCRYPT_PREFIX = '$2'


class AuthenticationManager:
    """Handles JWT token generation and validation with bcrypt passwords."""

    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expiry_hours = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _is_bcrypt_hash(self, hashed_password: str) -> bool:
        return bool(hashed_password) and hashed_password.startswith(BCRYPT_PREFIX)

    def _sha256_hash(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt or legacy SHA-256 hash."""
        if not hashed_password:
            return False
        if self._is_bcrypt_hash(hashed_password):
            try:
                return bcrypt.checkpw(
                    password.encode('utf-8'),
                    hashed_password.encode('utf-8'),
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"bcrypt verify failed: {e}")
                return False
        # Legacy SHA-256 (64 hex chars)
        return self._sha256_hash(password) == hashed_password

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials; migrate legacy SHA-256 hashes to bcrypt."""
        connection = get_connection()
        if connection is None:
            return None

        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT user_id, username, email, phone_number, first_name, last_name, role, password
            FROM user WHERE username = %s
            """
            cursor.execute(query, (username,))
            result = cursor.fetchone()

            if not result:
                return None

            stored_hash = result['password']
            if not self.verify_password(password, stored_hash):
                return None

            # Transparent migration from SHA-256 to bcrypt
            if not self._is_bcrypt_hash(stored_hash):
                new_hash = self.hash_password(password)
                try:
                    cursor.execute(
                        "UPDATE user SET password = %s WHERE user_id = %s",
                        (new_hash, result['user_id']),
                    )
                    connection.commit()
                    logger.info(f"Migrated password hash to bcrypt for user {username}")
                except Exception as e:
                    logger.error(f"Failed to migrate password hash: {e}")
                    connection.rollback()

            return {
                'user_id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'phone_number': result['phone_number'],
                'first_name': result['first_name'],
                'last_name': result['last_name'],
                'role': result['role'],
            }
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
        finally:
            cursor.close()
            release_connection(connection)

    def generate_token(self, user_data: Dict[str, Any]) -> str:
        """Generate JWT token"""
        try:
            payload = {
                'user_id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['email'],
                'role': user_data.get('role', 'user'),
                'exp': datetime.now(timezone.utc) + timedelta(hours=self.token_expiry_hours),
                'iat': datetime.now(timezone.utc),
            }
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Token generated for user: {user_data['username']}")
            return token
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.debug(f"Token verified for user: {payload.get('username')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    def extract_token_from_header(self, authorization_header: str) -> Optional[str]:
        """Extract token from Authorization header"""
        if not authorization_header:
            return None

        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        return parts[1]

    def authorize(self, user_data: Dict[str, Any], required_role: str = 'user') -> bool:
        """Check if user has required role"""
        if not user_data:
            return False

        user_role = user_data.get('role', 'user')

        if required_role == 'admin':
            return user_role == 'admin'
        if required_role == 'user':
            return user_role in ['user', 'admin']

        return False


class TokenValidationMiddleware:
    """Middleware to validate JWT tokens"""

    @staticmethod
    def validate_request(handler) -> Tuple[bool, Dict[str, Any]]:
        """Validate request token and return (is_valid, user_data_or_error)."""
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


# Global authentication manager instance
auth_manager = AuthenticationManager()
