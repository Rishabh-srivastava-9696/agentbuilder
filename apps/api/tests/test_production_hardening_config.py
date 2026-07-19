import pytest
from pydantic import ValidationError

from app.config import Settings


def _production_settings(**overrides):
    values = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "test-secret-key",
        "ADMIN_API_KEY": "test-admin-key",
        "SETTINGS_ENCRYPTION_KEY": "test-settings-key",
        "PII_ENCRYPTION_KEY": "test-pii-key",
        "MONGODB_URI": "mongodb://mongo.internal:27017",
        "REDIS_URL": "redis://redis.internal:6379",
        "MCP_SERVICE_AUTH_TOKEN": "test-mcp-key",
        "STRAPI_URL": "https://strapi.example.test",
        "STRAPI_API_TOKEN": "test-strapi-key",
        "VECTOR_BACKEND": "qdrant",
        "QDRANT_URL": "http://qdrant:6333",
        "QDRANT_API_KEY": "test-qdrant-key",
    }
    values.update(overrides)
    return Settings(**values)


def test_production_defaults_to_fail_closed_rate_limits_and_requires_qdrant_auth():
    settings = _production_settings()
    assert settings.RATE_LIMIT_FAIL_CLOSED is True

    with pytest.raises(ValidationError, match="QDRANT_API_KEY"):
        _production_settings(QDRANT_API_KEY="")


def test_production_rejects_fail_open_rate_limits():
    with pytest.raises(ValidationError, match="RATE_LIMIT_FAIL_CLOSED"):
        _production_settings(RATE_LIMIT_FAIL_CLOSED=False)


def test_production_requires_a_signing_secret_when_shopify_webhooks_are_enabled():
    with pytest.raises(ValidationError, match="SHOPIFY_WEBHOOK_SECRET"):
        _production_settings(SHOPIFY_WEBHOOKS_ENABLED=True, SHOPIFY_WEBHOOK_SECRET="")


def test_shopify_admin_api_release_label_is_validated():
    with pytest.raises(ValidationError, match="SHOPIFY_ADMIN_API_VERSION"):
        Settings(SECRET_KEY="test-secret", SHOPIFY_ADMIN_API_VERSION="latest")
