import re
from typing import Optional

def validate_phone_number(phone: str) -> Optional[str]:
    """Validate and format phone number"""
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it starts with + and has digits
    if not re.match(r'^\+\d{10,15}$', cleaned):
        return None
    
    return cleaned

def extract_country_from_phone(phone: str) -> str:
    """Extract country from phone number"""
    if phone.startswith('+234'):
        return 'Nigeria'
    elif phone.startswith('+1'):
        return 'USA/Canada'
    elif phone.startswith('+44'):
        return 'UK'
    elif phone.startswith('+91'):
        return 'India'
    else:
        return 'Unknown'

def validate_bank_details(details: str) -> bool:
    """Validate bank details format"""
    # Expected format: "9131085651 OPay Bashir Rabiu"
    parts = details.strip().split()
    if len(parts) < 3:
        return False
    
    # First part should be account number (digits)
    if not parts[0].isdigit():
        return False
    
    return True

def is_otp_message(message: str) -> bool:
    """Check if message contains OTP"""
    otp_patterns = [
        r'\b\d{5}\b',  # 5-digit code
        r'\b\d{6}\b',  # 6-digit code
        r'code.*\d{5,6}',  # "code: 12345"
        r'verification.*\d{5,6}',  # "verification code 12345"
        r'login.*\d{5,6}',  # "login code 12345"
    ]
    
    for pattern in otp_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return True
    
    return False
