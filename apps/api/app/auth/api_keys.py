"""
API key generation and validation.
"""

import secrets
import hashlib
from typing import Tuple, Optional
import structlog

logger = structlog.get_logger()

# API key configuration
API_KEY_PREFIX = "ab"  # agent-builder
API_KEY_LENGTH = 32  # Length of random part


def generate_api_key(environment: str = "live") -> Tuple[str, str, str]:
    """
    Generate a new API key.
    
    Format: ab_{environment}_{32_random_hex}
    Example: ab_live_1234567890abcdef1234567890abcdef
    
    Args:
        environment: Environment (live, test, dev)
    
    Returns:
        Tuple of (full_key, key_id, key_hash)
        - full_key: The complete API key (show once)
        - key_id: Public identifier (first 8 chars)
        - key_hash: Hashed key for storage
    """
    # Generate random hex string
    random_part = secrets.token_hex(API_KEY_LENGTH // 2)  # token_hex returns hex string
    
    # Construct full key
    full_key = f"{API_KEY_PREFIX}_{environment}_{random_part}"
    
    # Extract key ID (first 8 chars after prefix)
    key_id = f"{API_KEY_PREFIX}_{environment}_{random_part[:8]}"
    
    # Hash the full key for storage
    key_hash = hash_api_key(full_key)
    
    logger.info(
        "api_key_generated",
        key_id=key_id,
        environment=environment
    )
    
    return full_key, key_id, key_hash


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage.
    
    Args:
        api_key: Plain text API key
    
    Returns:
        Hashed API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided_key: str, stored_hash: str) -> bool:
    """
    Verify an API key against a stored hash.
    
    Args:
        provided_key: API key provided by client
        stored_hash: Stored hash from database
    
    Returns:
        True if key matches, False otherwise
    """
    provided_hash = hash_api_key(provided_key)
    return secrets.compare_digest(provided_hash, stored_hash)


def parse_api_key(api_key: str) -> Optional[dict]:
    """
    Parse an API key to extract components.
    
    Args:
        api_key: Full API key
    
    Returns:
        Dict with prefix, environment, and random parts, or None if invalid
    """
    try:
        parts = api_key.split("_")
        if len(parts) != 3:
            return None
        
        prefix, environment, random_part = parts
        
        if prefix != API_KEY_PREFIX:
            return None
        
        if environment not in ["live", "test", "dev"]:
            return None
        
        if len(random_part) != API_KEY_LENGTH:
            return None
        
        return {
            "prefix": prefix,
            "environment": environment,
            "random_part": random_part,
            "key_id": f"{prefix}_{environment}_{random_part[:8]}"
        }
        
    except Exception as e:
        logger.warning("api_key_parse_failed", error=str(e))
        return None


def is_valid_api_key_format(api_key: str) -> bool:
    """
    Check if an API key has valid format.
    
    Args:
        api_key: API key to validate
    
    Returns:
        True if format is valid
    """
    return parse_api_key(api_key) is not None


def extract_key_id(api_key: str) -> Optional[str]:
    """
    Extract the key ID from a full API key.
    
    Args:
        api_key: Full API key
    
    Returns:
        Key ID or None if invalid
    """
    parsed = parse_api_key(api_key)
    if parsed is None:
        return None
    
    return parsed["key_id"]


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key for display.
    
    Args:
        api_key: Full API key
    
    Returns:
        Masked key (e.g., ab_live_1234****...****)
    """
    parsed = parse_api_key(api_key)
    if parsed is None:
        return "****"
    
    prefix = parsed["prefix"]
    env = parsed["environment"]
    random_part = parsed["random_part"]
    
    # Show first 4 and last 4 chars of random part
    masked_random = f"{random_part[:4]}{'*' * (len(random_part) - 8)}{random_part[-4:]}"
    
    return f"{prefix}_{env}_{masked_random}"
