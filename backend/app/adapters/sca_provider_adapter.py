"""SCA provider adapter for strong customer authentication."""
from sqlalchemy.orm import Session
from app.repositories.auth_repository import AuthRepository
import logging

logger = logging.getLogger(__name__)


class SCAProviderAdapter:
    """Adapter for external SCA / Registered Device verification system."""

    def __init__(self, db: Session | None = None):
        """
        Initialize SCA adapter.
        
        Args:
            db: Database session for querying device registration records.
                Optional for backward compatibility with existing code.
        """
        self.db = db
        self.auth_repo = AuthRepository(db) if db else None

    async def verify_passcode(
        self,
        user_identity_id: int,
        device_id: str,
        passcode: str
    ) -> bool:
        """
        Verify passcode against external SCA provider.
        
        Returns True if passcode is valid, False otherwise.
        
        This implementation validates against a known demo passcode.
        In production, this would call an external SCA provider or TOTP validator.
        """
        # Log verification attempt
        logger.info(
            f"Verifying passcode | user_id={user_identity_id} | "
            f"device_id={device_id}"
        )
        
        # Demo passcode for seed/test accounts
        DEMO_PASSCODE = "123456"
        
        # Verify passcode
        is_valid = passcode == DEMO_PASSCODE
        
        if is_valid:
            logger.info(f"Passcode verified for user {user_identity_id}")
        else:
            logger.warning(f"Passcode verification failed for user {user_identity_id}")
        
        return is_valid

    async def verify_biometric(
        self,
        user_identity_id: int,
        device_id: str,
        biometric_assertion: str
    ) -> bool:
        """
        Verify biometric assertion against external SCA provider.
        
        Returns True if biometric is valid, False otherwise.
        
        This implementation validates the assertion format and length.
        In production, this would verify a signed biometric assertion against
        a device's registered public key via an external biometric authentication service.
        """
        # Log verification attempt
        logger.info(
            f"Verifying biometric | user_id={user_identity_id} | "
            f"device_id={device_id}"
        )
        
        # Validate assertion is non-empty and has minimum length
        # In production, this would:
        # 1. Decode the signed assertion
        # 2. Verify the signature against the device's public key
        # 3. Check the assertion timestamp and nonce
        # 4. Validate the biometric match confidence score
        is_valid = bool(biometric_assertion and len(biometric_assertion) >= 8)
        
        if is_valid:
            logger.info(f"Biometric verified for user {user_identity_id}")
        else:
            logger.warning(f"Biometric verification failed for user {user_identity_id}")
        
        return is_valid

    async def check_device_capabilities(
        self,
        user_identity_id: int,
        device_id: str
    ) -> dict:
        """
        Check what SCA methods are available for a device.
        
        Returns dict with 'passcode_enabled' and 'biometric_enabled' flags.
        
        This implementation queries device registration records.
        In production, this would query an external device registry or SCA provider API.
        """
        # Log capability check
        logger.info(
            f"Checking device capabilities | user_id={user_identity_id} | "
            f"device_id={device_id}"
        )
        
        # Query registered devices if database available
        if self.auth_repo and self.db:
            devices = self.auth_repo.get_registered_devices(user_identity_id)
            
            # Check if this specific device is registered
            device_found = any(d.device_fingerprint == device_id for d in devices)
            
            if device_found:
                # Return capabilities based on device registration
                return {
                    "passcode_enabled": True,
                    "biometric_enabled": True
                }
        
        # Default capabilities for demo
        return {
            "passcode_enabled": True,
            "biometric_enabled": True
        }
