"""Restricted data detection and scrubbing."""
import re


class RestrictedDataScreen:
    """Detect and remove PAN, passcodes, and security answers from text."""

    # PAN pattern: 13-19 digits
    PAN_PATTERN = re.compile(r"\b\d{13,19}\b")

    # Passcode/PIN/password phrases
    PASSCODE_PHRASES = ["passcode", "pin", "password", "security code"]

    # Security answer phrases
    SECURITY_ANSWER_PHRASES = ["mother's maiden name", "first pet", "security answer"]

    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """Validate card number using Luhn algorithm."""
        digits = [int(d) for d in card_number]
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

    @classmethod
    def contains_restricted(cls, text: str) -> bool:
        """Check if text contains restricted data."""
        if not text:
            return False

        text_lower = text.lower()

        # Check for PAN (with Luhn check)
        for match in cls.PAN_PATTERN.finditer(text):
            if cls.luhn_check(match.group()):
                return True

        # Check for passcode phrases
        for phrase in cls.PASSCODE_PHRASES:
            if phrase in text_lower:
                return True

        # Check for security answer phrases
        for phrase in cls.SECURITY_ANSWER_PHRASES:
            if phrase in text_lower:
                return True

        return False

    @classmethod
    def scrub_mapping(cls, data: dict, allow_list: list[str]) -> dict:
        """Keep only allow-listed keys and drop values with restricted data."""
        result = {}
        for key in allow_list:
            if key in data:
                value = data[key]
                # Check string values for restricted data
                if isinstance(value, str) and cls.contains_restricted(value):
                    continue  # Drop this key-value pair
                result[key] = value
        return result
