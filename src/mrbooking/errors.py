"""Exceptions used across the service. Every refusal carries the rule/requirement id
that caused it (F2/AC15: 'Invalid booking' alone is never an acceptable message)."""
from __future__ import annotations


class RuleViolation(Exception):
    """Raised when a request breaks a business rule or a structural requirement.

    `rule_id` is one of BR1-BR16 (business rules) or F25-F28 (structural
    input-validation requirements), matching the identifiers in the RFP.
    """

    def __init__(self, rule_id: str, message: str):
        self.rule_id = rule_id
        self.message = message
        super().__init__(f"{rule_id}: {message}")


class DataFileError(Exception):
    """Raised when the data file is missing, corrupted, or fails validation (F30/F34)."""


class NotFoundError(Exception):
    """Raised when a lookup (booking id, room name) does not resolve."""
