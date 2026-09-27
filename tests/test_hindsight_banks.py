import pytest

from customer_support_agent.integrations.hindsight.banks import (
    get_company_bank_id,
    get_customer_bank_id,
    get_operations_bank_id,
    sanitize_identifier,
)


def test_sanitize_identifier_valid():
    assert sanitize_identifier("customer123") == "customer123"
    assert sanitize_identifier(42) == "42"
    assert sanitize_identifier("ALEX@ACME.IO") == "alex_acme_io"
    assert sanitize_identifier("Acme-Corp_1") == "acme-corp_1"
    assert sanitize_identifier("  spaced__name  ") == "spaced_name"


def test_sanitize_identifier_invalid():
    with pytest.raises(ValueError, match="cannot be None"):
        sanitize_identifier(None)

    with pytest.raises(ValueError, match="cannot be empty"):
        sanitize_identifier("")

    with pytest.raises(ValueError, match="cannot be empty"):
        sanitize_identifier("   ")

    with pytest.raises(ValueError, match="empty sanitized string"):
        sanitize_identifier("@@@###")


def test_customer_bank_id_formatting():
    assert get_customer_bank_id(1) == "meow_customer_1"
    assert get_customer_bank_id("42") == "meow_customer_42"
    assert get_customer_bank_id("alex@acme.io") == "meow_customer_alex_acme_io"


def test_company_bank_id_formatting():
    assert get_company_bank_id("Acme Labs") == "meow_company_acme_labs"
    assert get_company_bank_id(99) == "meow_company_99"


def test_operations_bank_id():
    assert get_operations_bank_id() == "meow_operations"


def test_bank_isolation_guarantee():
    bank_a = get_customer_bank_id("customer_a")
    bank_b = get_customer_bank_id("customer_b")
    bank_c = get_customer_bank_id(101)

    assert bank_a != bank_b
    assert bank_a != bank_c
    assert bank_b != bank_c
    assert bank_a.startswith("meow_customer_")
