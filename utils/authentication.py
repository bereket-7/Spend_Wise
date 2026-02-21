import jwt
import hashlib
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from database.database_connection import get_connection, release_connection

logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Handles JWT token generation and validation"""
    
    def __init__(self):
        self.secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expiry_hours = int(os.getenv('TOKEN_EXPIRY_HOURS', '24'))
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        connection = get_connection()
        if connection is None:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            hashed_password = self.hash_password(password)
            
            # Secure: Verify credentials in database query
            query = "SELECT user_id, username, email, phone_number, first_name, last_name, role FROM user WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashed_password))
            result = cursor.fetchone()
            
            if result:
                return {
                    'user_id': result['user_id'],
                    'username': result['username'],
                    'email': result['email'],
                    'phone_number': result['phone_number'],
                    'first_name': result['first_name'],
                    'last_name': result['last_name'],
                    'role': result['role']
                }
            return None
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
                'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
                'iat': datetime.utcnow()
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
            logger.info(f"Token verified for user: {payload['username']}")
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
        elif required_role == 'user':
            return user_role in ['user', 'admin']
        
        return False

# Global authentication manager instance
auth_manager = AuthenticationManager()