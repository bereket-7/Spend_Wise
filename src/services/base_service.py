"""
Base service class for business logic layer
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class BaseService(ABC):
    """Base service with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _log_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log service operation"""
        message = f"{operation}"
        if details:
            message += f" - Details: {details}"
        self.logger.info(message)
    
    def _log_error(self, operation: str, error: Exception, details: Dict[str, Any] = None):
        """Log service error"""
        message = f"Error in {operation}: {str(error)}"
        if details:
            message += f" - Details: {details}"
        self.logger.error(message, exc_info=True)
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> tuple[bool, str]:
        """Validate required fields in data"""
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        return True, ""
    
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            return str(value)
        return value.strip()
    
    def _validate_positive_number(self, value: Any) -> tuple[bool, str]:
        """Validate positive number"""
        try:
            num_value = float(value)
            if num_value <= 0:
                return False, "Value must be positive"
            return True, ""
        except (ValueError, TypeError):
            return False, "Invalid number format"
