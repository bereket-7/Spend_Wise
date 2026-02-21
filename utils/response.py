import logging
from typing import Dict, Any, Optional, Tuple
from http.server import BaseHTTPRequestHandler
import json

logger = logging.getLogger(__name__)

def json_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """Create JSON response dictionary"""
    return {
        'status_code': status_code,
        'body': json.dumps(data),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
    }

def send_json_response(handler: BaseHTTPRequestHandler, data: Dict[str, Any], status_code: int = 200):
    """Send JSON response via HTTP handler"""
    try:
        response_data = json.dumps(data)
        handler.send_response(status_code)
        handler.send_header('Content-type', 'application/json')
        handler.send_header('Access-Control-Allow-Origin', '*')
        handler.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        handler.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        handler.end_headers()
        handler.wfile.write(response_data.encode('utf-8'))
        logger.info(f"Response sent: {status_code} - {data}")
    except Exception as e:
        logger.error(f"Error sending response: {e}")
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(b'{"error": "Internal server error"}')

def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    import re
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def validate_amount(amount: Any) -> bool:
    """Validate amount is a positive number"""
    try:
        return float(amount) > 0
    except (ValueError, TypeError):
        return False

def sanitize_string(input_str: str) -> str:
    """Sanitize string input"""
    if not input_str:
        return ""
    # Remove potential SQL injection characters
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        input_str = input_str.replace(char, '')
    return input_str.strip()

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Tuple[bool, str]:
    """Validate that all required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, ""