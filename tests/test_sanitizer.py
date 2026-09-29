"""Unit tests for secret sanitization and display masking utilities."""

import pytest
from customer_support_agent.core.sanitizer import sanitize_obj_for_display


def test_sanitize_dict_keys_redacted():
    """Verify keys containing sensitive terms are masked."""
    payload = {
        "customer_id": 9999,
        "api_key": "secret_abc_123",
        "access_token": "token_xyz",
        "auth_header": "Bearer valid_auth_string",
        "db_password": "super_secret_pw",
        "user_credential": "user_cred_data",
        "public_data": "visible_info",
    }
    sanitized = sanitize_obj_for_display(payload)
    assert sanitized["customer_id"] == 9999
    assert sanitized["public_data"] == "visible_info"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["auth_header"] == "[REDACTED]"
    assert sanitized["db_password"] == "[REDACTED]"
    assert sanitized["user_credential"] == "[REDACTED]"


def test_sanitize_nested_structures():
    """Verify sanitization recursively traverses nested dicts and lists."""
    nested = {
        "ticket": {
            "id": 1001,
            "meta": [
                {"provider": "groq", "api_key": "gsk_test123"},
                {"provider": "openai", "token": "sk-abc456"},
            ],
        },
        "tags": ["prod", "tier-1"],
    }
    sanitized = sanitize_obj_for_display(nested)
    assert sanitized["ticket"]["id"] == 1001
    assert sanitized["ticket"]["meta"][0]["api_key"] == "[REDACTED]"
    assert sanitized["ticket"]["meta"][1]["token"] == "[REDACTED]"
    assert sanitized["tags"] == ["prod", "tier-1"]


def test_sanitize_string_secret_patterns():
    """Verify raw strings containing known token prefixes are redacted."""
    s1 = "Configuration loaded with gsk_abcdef123456789 in environment"
    assert sanitize_obj_for_display(s1) == "Configuration loaded with [REDACTED_SECRET] in environment"

    s2 = "Header sent as Bearer eyJhbGciOiJIUzI1NiJ9.test"
    assert "[REDACTED_SECRET]" in sanitize_obj_for_display(s2)

    s3 = "sk-123456789abcdef0000"
    assert sanitize_obj_for_display(s3) == "[REDACTED_SECRET]"


def test_sanitize_leaves_clean_data_untouched():
    """Verify benign strings and numeric primitives pass through without modification."""
    clean_dict = {"status": "open", "code": 200, "active": True}
    assert sanitize_obj_for_display(clean_dict) == clean_dict
