from __future__ import annotations

import re


def sanitize_identifier(value: int | str) -> str:
    """
    Sanitize an identifier for use in a Hindsight bank name.
    Preserves alphanumeric characters, underscores, and hyphens.
    Replaces all other characters (e.g. '@', '.', '+') with underscores.
    """
    if value is None:
        raise ValueError("Identifier cannot be None")
    raw = str(value).strip().lower()
    if not raw:
        raise ValueError("Identifier cannot be empty")
    # Replace non-alphanumeric/dash/underscore with underscore
    sanitized = re.sub(r"[^a-z0-9_-]", "_", raw)
    # Collapse multiple consecutive underscores and strip leading/trailing underscores
    collapsed = re.sub(r"_+", "_", sanitized).strip("_")
    if not collapsed:
        raise ValueError(f"Identifier '{raw}' produced an empty sanitized string")
    return collapsed


def get_customer_bank_id(customer_id: int | str) -> str:
    """
    Construct a deterministic, isolated Hindsight bank ID for a specific customer.
    Prevents cross-customer contamination by scoping each customer to their own bank.

    Example:
        get_customer_bank_id(1) -> "meow_customer_1"
        get_customer_bank_id("alex@acme.io") -> "meow_customer_alex_acme_io"
    """
    clean_id = sanitize_identifier(customer_id)
    return f"meow_customer_{clean_id}"


def get_company_bank_id(company_id: int | str) -> str:
    """
    Construct a deterministic Hindsight bank ID for company-level shared memories.

    Example:
        get_company_bank_id("Acme Corp") -> "meow_company_acme_corp"
    """
    clean_id = sanitize_identifier(company_id)
    return f"meow_company_{clean_id}"


def get_operations_bank_id() -> str:
    """
    Return the global bank ID for system-wide operational policies and directives.
    """
    return "meow_operations"
