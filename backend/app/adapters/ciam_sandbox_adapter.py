"""
CIAM sandbox adapter for passcode verification in working tier.
In production, this would call the real CIAM service.
Requirement: FR-AUTH-003, FR-AUTH-006
"""

import bcrypt


class CIAMSandboxAdapter:
    """Sandbox adapter for CIAM operations using bcrypt-hashed credentials."""
    
    def verify_passcode(self, passcode: str, passcode_hash: str) -> bool:
        """
        Verify a passcode against a bcrypt hash.
        
        Args:
            passcode: Plain text passcode from user
            passcode_hash: Bcrypt hash from sandbox_credentials
        
        Returns:
            True if passcode matches, False otherwise
        """
        try:
            return bcrypt.checkpw(passcode.encode('utf-8'), passcode_hash.encode('utf-8'))
        except (ValueError, AttributeError):
            return False
    
    def create_dynamic_link_approval(
        self,
        customer_id: str,
        passcode: str,
        passcode_hash: str,
        review_fingerprint: str
    ) -> dict | None:
        """
        Create a dynamic link approval for step-up SCA.
        In working tier, this verifies passcode and returns a signed approval.
        
        Args:
            customer_id: Customer profile reference ID
            passcode: Plain text passcode from user
            passcode_hash: Bcrypt hash from sandbox_credentials
            review_fingerprint: SHA-256 fingerprint of review fields
        
        Returns:
            Approval dict if successful, None if verification fails
        """
        if not self.verify_passcode(passcode, passcode_hash):
            return None
        
        # In working tier, return a simple approval structure
        # In production, this would be a signed JWT from CIAM
        return {
            "customer_id": customer_id,
            "review_fingerprint": review_fingerprint,
            "approval_outcome": "success",
            "method": "passcode"
        }
