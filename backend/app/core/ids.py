"""ID generation utilities."""
import uuid
import secrets
import string


def new_id() -> uuid.UUID:
    """Generate a new UUID for primary keys."""
    return uuid.uuid4()


class CaseReferenceGenerator:
    """Generate stable case references in format CP-XXXXXXXXXX."""
    
    # Crockford base32 alphabet (no ambiguous characters: I, L, O, U)
    ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    
    @classmethod
    def generate(cls) -> str:
        """Generate a case reference: CP- followed by 10 Crockford base-32 characters."""
        # Generate 10 random characters from the Crockford base32 alphabet
        random_part = ''.join(secrets.choice(cls.ALPHABET) for _ in range(10))
        return f"CP-{random_part}"
