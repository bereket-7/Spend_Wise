"""
Request validation utilities
"""
from typing import Dict, Any, List, Optional, Union
import re
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class BaseValidator:
    """Base validator class"""
    
    @staticmethod
    def validate_required(data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
        """Validate required fields"""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        return True, ""
    
    @staticmethod
    def validate_phone_number(phone: str) -> tuple[bool, str]:
        """Validate phone number format"""
        if not phone:
            return True, ""  # Phone is optional
        
        # Remove common formatting characters
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Check if it's a reasonable length (10-15 digits)
        if len(clean_phone) < 10 or len(clean_phone) > 15:
            return False, "Invalid phone number format"
        
        return True, ""
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "Value") -> tuple[bool, str]:
        """Validate positive number"""
        try:
            num_value = float(value)
            if num_value <= 0:
                return False, f"{field_name} must be positive"
            return True, ""
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
    
    @staticmethod
    def validate_string_length(value: str, min_length: int = 1, max_length: int = 255, field_name: str = "Field") -> tuple[bool, str]:
        """Validate string length"""
        if not isinstance(value, str):
            return False, f"{field_name} must be a string"
        
        if len(value) < min_length:
            return False, f"{field_name} must be at least {min_length} characters"
        
        if len(value) > max_length:
            return False, f"{field_name} must be no more than {max_length} characters"
        
        return True, ""
    
    @staticmethod
    def validate_date_format(date_str: str, field_name: str = "Date") -> tuple[bool, str]:
        """Validate date format (YYYY-MM-DD)"""
        if not date_str:
            return False, f"{field_name} is required"
        
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, date_str):
            return False, f"{field_name} must be in YYYY-MM-DD format"
        
        try:
            from datetime import datetime
            datetime.strptime(date_str, '%Y-%m-%d')
            return True, ""
        except ValueError:
            return False, f"{field_name} is not a valid date"
    
    @staticmethod
    def validate_enum(value: str, valid_values: List[str], field_name: str = "Field") -> tuple[bool, str]:
        """Validate enum value"""
        if value not in valid_values:
            return False, f"{field_name} must be one of: {', '.join(valid_values)}"
        return True, ""

class ExpenseValidator(BaseValidator):
    """Expense-specific validator"""
    
    @staticmethod
    def validate_expense_data(data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate expense creation/update data"""
        # Required fields
        is_valid, message = BaseValidator.validate_required(
            data, ['amount', 'category', 'date', 'user_id']
        )
        if not is_valid:
            return False, message
        
        # Validate amount
        is_valid, message = BaseValidator.validate_positive_number(data['amount'], 'Amount')
        if not is_valid:
            return False, message
        
        # Validate category
        is_valid, message = BaseValidator.validate_string_length(
            data['category'], 1, 50, 'Category'
        )
        if not is_valid:
            return False, message
        
        # Validate description (optional)
        if 'description' in data and data['description']:
            is_valid, message = BaseValidator.validate_string_length(
                data['description'], 1, 500, 'Description'
            )
            if not is_valid:
                return False, message
        
        # Validate date
        is_valid, message = BaseValidator.validate_date_format(data['date'], 'Date')
        if not is_valid:
            return False, message
        
        # Validate user_id
        try:
            user_id = int(data['user_id'])
            if user_id <= 0:
                return False, "User ID must be positive"
        except (ValueError, TypeError):
            return False, "User ID must be a valid integer"
        
        return True, ""

class UserValidator(BaseValidator):
    """User-specific validator"""
    
    @staticmethod
    def validate_user_data(data: Dict[str, Any], is_update: bool = False) -> tuple[bool, str]:
        """Validate user creation/update data"""
        # Required fields for creation
        required_fields = ['username', 'password', 'email', 'first_name', 'last_name']
        if is_update:
            required_fields = ['username', 'email', 'first_name', 'last_name']
        
        is_valid, message = BaseValidator.validate_required(data, required_fields)
        if not is_valid:
            return False, message
        
        # Validate username
        is_valid, message = BaseValidator.validate_string_length(
            data['username'], 3, 50, 'Username'
        )
        if not is_valid:
            return False, message
        
        # Validate email
        is_valid, message = BaseValidator.validate_email(data['email'])
        if not is_valid:
            return False, message
        
        # Validate phone (optional)
        if 'phone_number' in data and data['phone_number']:
            is_valid, message = BaseValidator.validate_phone_number(data['phone_number'])
            if not is_valid:
                return False, message
        
        # Validate first name
        is_valid, message = BaseValidator.validate_string_length(
            data['first_name'], 1, 50, 'First name'
        )
        if not is_valid:
            return False, message
        
        # Validate last name
        is_valid, message = BaseValidator.validate_string_length(
            data['last_name'], 1, 50, 'Last name'
        )
        if not is_valid:
            return False, message
        
        # Validate role (optional)
        if 'role' in data and data['role']:
            is_valid, message = BaseValidator.validate_enum(
                data['role'], ['user', 'admin'], 'Role'
            )
            if not is_valid:
                return False, message
        
        return True, ""

def validate_request_data(data: Dict[str, Any], validator_class: type, **kwargs) -> tuple[bool, str]:
    """Generic request validation function"""
    try:
        if hasattr(validator_class, 'validate_expense_data'):
            return validator_class.validate_expense_data(data, **kwargs)
        elif hasattr(validator_class, 'validate_user_data'):
            return validator_class.validate_user_data(data, **kwargs)
        else:
            return False, "Unknown validator"
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False, "Validation failed"
