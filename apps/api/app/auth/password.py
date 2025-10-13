"""
Password hashing and validation.
"""

import re
from typing import Tuple
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("password_verification_failed", error=str(e))
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength.
    
    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    
    Args:
        password: Password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    # Check for common weak passwords
    weak_passwords = [
        "password", "12345678", "qwerty", "abc123", "password1",
        "password123", "admin", "letmein", "welcome", "monkey"
    ]
    if password.lower() in weak_passwords:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, ""


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be rehashed.
    
    Args:
        hashed_password: Hashed password
    
    Returns:
        True if rehashing is needed
    """
    return pwd_context.needs_update(hashed_password)
