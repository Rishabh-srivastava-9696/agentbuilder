"""
Authentication module for JWT and API key authentication.
"""

from .jwt import (
    create_access_token,
    create_refresh_token,
    verify_token,
    decode_token,
)
from .password import (
    hash_password,
    verify_password,
    validate_password_strength,
)
from .api_keys import (
    generate_api_key,
    hash_api_key,
    verify_api_key,
)
from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_api_key_user,
    require_role,
    require_permission,
)
from .models import (
    User,
    APIKey,
    Token,
    TokenData,
    UserRole,
)

__all__ = [
    # JWT
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "decode_token",
    # Password
    "hash_password",
    "verify_password",
    "validate_password_strength",
    # API Keys
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_api_key_user",
    "require_role",
    "require_permission",
    # Models
    "User",
    "APIKey",
    "Token",
    "TokenData",
    "UserRole",
]
