import re
from typing import Tuple
from mindmate.utils.db import get_therapist_by_credentials

def validate_therapist_credentials(email: str, password: str) -> Tuple[bool, str]:
    """Validate therapist login credentials against database"""
    if not email or not password:
        return False, "Email and password are required"
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False, "Invalid email format"
        
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    # Check credentials against database
    therapist = get_therapist_by_credentials(email, password)
    if therapist:
        return True, "Login successful"
        
    return False, "Invalid credentials"
