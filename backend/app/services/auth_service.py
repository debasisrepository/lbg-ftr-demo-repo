"""Authentication service - sign in, proof, recovery"""
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ..adapters.ciam_adapter import CiamAdapter, get_ciam_adapter
from ..config import settings
from ..core.errors import AuthenticationError, ValidationError
from ..core.security import generate_session_token, hash_identifier, hash_token
from ..repositories.auth_attempt_repository import AuthAttemptRepository
from ..repositories.customer_repository import CustomerRepository
from ..repositories.device_repository import DeviceRepository
from ..repositories.session_repository import SessionRepository
from ..schemas.auth_schemas import (
    ProofRequest,
    ProofResponse,
    SignInRequest,
    SignInResponse,
)
from ..services.login_rate_limiter import get_rate_limiter


class AuthService:
    """Authentication and proof verification service"""

    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.device_repo = DeviceRepository(db)
        self.session_repo = SessionRepository(db)
        self.auth_attempt_repo = AuthAttemptRepository(db)
        self.ciam_adapter: CiamAdapter = get_ciam_adapter()
        self.rate_limiter = get_rate_limiter()

    def sign_in(
        self,
        request: SignInRequest,
        client_ip: str | None,
        correlation_id: str
    ) -> SignInResponse:
        """
        Sign in with username and password (FR-001).
        Returns password_only auth level requiring proof step.
        """
        # Rate limiting
        identifier_hash = hash_identifier(request.username)
        ip_hash = hash_identifier(client_ip) if client_ip else None

        try:
            self.rate_limiter.check_identifier(identifier_hash)
            if ip_hash:
                self.rate_limiter.check_ip(ip_hash)
        except Exception as e:
            # Record rate-limited attempt
            self.auth_attempt_repo.create(
                customer_id=None,
                device_id=None,
                identifier_hash=identifier_hash,
                attempt_type='password',
                outcome='rate_limited',
                client_ip_hash=ip_hash,
                correlation_id=correlation_id,
                occurred_at=datetime.now(UTC)
            )
            self.db.commit()
            raise e

        # Authenticate with CIAM
        success, external_identity_ref = self.ciam_adapter.authenticate(
            request.username,
            request.password
        )

        if not success or not external_identity_ref:
            # Record failed attempt (generic error, don't reveal which credential was wrong)
            self.auth_attempt_repo.create(
                customer_id=None,
                device_id=None,
                identifier_hash=identifier_hash,
                attempt_type='password',
                outcome='failure',
                client_ip_hash=ip_hash,
                correlation_id=correlation_id,
                occurred_at=datetime.now(UTC)
            )
            self.rate_limiter.record_attempt(identifier_hash, ip_hash)
            self.db.commit()

            # Generic error message per FR-001
            raise AuthenticationError("Invalid credentials. Please check your username and password.")

        # Get customer
        customer = self.customer_repo.get_by_external_identity_ref(external_identity_ref)
        if not customer or customer.status != 'active':
            # Record failure but don't reveal account status
            self.auth_attempt_repo.create(
                customer_id=customer.customer_id if customer else None,
                device_id=None,
                identifier_hash=identifier_hash,
                attempt_type='password',
                outcome='failure',
                client_ip_hash=ip_hash,
                correlation_id=correlation_id,
                occurred_at=datetime.now(UTC)
            )
            self.rate_limiter.record_attempt(identifier_hash, ip_hash)
            self.db.commit()
            raise AuthenticationError("Invalid credentials. Please check your username and password.")

        # Check if device is provided and trusted
        device_id_uuid = uuid.UUID(request.device_id) if request.device_id else None
        device = None
        if device_id_uuid:
            device = self.device_repo.get_customer_device(customer.customer_id, device_id_uuid)

        # Record successful password authentication
        self.auth_attempt_repo.create(
            customer_id=customer.customer_id,
            device_id=device.device_id if device else None,
            identifier_hash=identifier_hash,
            attempt_type='password',
            outcome='success',
            client_ip_hash=ip_hash,
            correlation_id=correlation_id,
            occurred_at=datetime.now(UTC)
        )

        # Create session with password_only auth level
        now = datetime.now(UTC)
        session_token = generate_session_token()
        token_hash = hash_token(session_token)

        session = self.session_repo.create(
            customer_id=customer.customer_id,
            device_id=device.device_id if device else None,
            session_token_hash=token_hash,
            auth_level='password_only',
            started_at=now,
            expires_at=now + timedelta(seconds=settings.signin_proof_window_seconds),
            inactivity_timeout_seconds=settings.session_inactivity_seconds,
            correlation_id=correlation_id
        )

        self.db.commit()

        # Determine proof methods available
        proof_methods = []
        if device and device.trust_state == 'trusted':
            if device.biometric_enabled:
                proof_methods.append('biometric')
            proof_methods.append('passcode')

        return SignInResponse(
            session_id=str(session.session_id),
            customer_id=str(customer.customer_id),
            auth_level='password_only',
            requires_proof=True,
            proof_methods=proof_methods if proof_methods else ['passcode'],
            proof_deadline=session.expires_at
        )

    def submit_proof(
        self,
        request: ProofRequest,
        correlation_id: str
    ) -> ProofResponse:
        """
        Submit second-factor proof (FR-002).
        Upgrades session from password_only to proven auth level.
        """
        session_id_uuid = uuid.UUID(request.session_id)
        session = self.session_repo.get_by_id(session_id_uuid)

        if not session:
            raise AuthenticationError("Invalid session")

        if session.ended_at is not None:
            raise AuthenticationError("Session has ended")

        if session.auth_level != 'password_only':
            raise ValidationError("Proof already submitted")

        # Check session hasn't expired
        now = datetime.now(UTC)
        # Ensure both datetimes are timezone-aware for comparison
        session_expires = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=UTC)

        if now > session_expires:
            self.session_repo.end_session(session, 'expired')
            self.db.commit()
            raise AuthenticationError("Sign-in proof window expired. Please sign in again.")

        # Get device if provided
        device = None
        if request.device_id:
            device_id_uuid = uuid.UUID(request.device_id)
            device = self.device_repo.get_customer_device(session.customer_id, device_id_uuid)

            if not device or device.trust_state != 'trusted':
                raise AuthenticationError("Device not trusted")

            # Check if passcode is paused
            now = datetime.now(UTC)
            if device.passcode_paused_until:
                pause_until = device.passcode_paused_until if device.passcode_paused_until.tzinfo else device.passcode_paused_until.replace(tzinfo=UTC)
                if now < pause_until:
                    raise AuthenticationError(
                        "Passcode entry is temporarily paused. Please use password sign-in or try again later."
                    )

        # Verify proof based on type
        proof_success = False

        if request.proof_type == 'passcode':
            if not device or not request.proof_value:
                raise ValidationError("Device ID and passcode required")

            # Verify passcode with CIAM
            proof_success = self.ciam_adapter.verify_passcode(
                session.customer_id,
                device.device_id,
                request.proof_value
            )

            if proof_success:
                # Reset failed count on success
                self.device_repo.reset_passcode_failed_count(device)
                self.device_repo.update_last_seen(device)
            else:
                # Increment failed count
                self.device_repo.increment_passcode_failed_count(device)

                # Pause after 3 failures
                if device.passcode_failed_count >= 3:
                    pause_until = datetime.now(UTC) + timedelta(minutes=15)
                    self.device_repo.pause_passcode(device, pause_until)
                    self.db.commit()
                    raise AuthenticationError(
                        "Too many incorrect passcode attempts. Passcode entry is paused. "
                        "Please use password sign-in."
                    )

            # Record attempt
            self.auth_attempt_repo.create(
                customer_id=session.customer_id,
                device_id=device.device_id,
                identifier_hash=hash_identifier(str(device.device_id)),
                attempt_type='passcode',
                outcome='success' if proof_success else 'failure',
                client_ip_hash=None,
                correlation_id=correlation_id,
                occurred_at=datetime.now(UTC)
            )

        elif request.proof_type == 'biometric':
            if not device or not request.proof_value:
                raise ValidationError("Device ID and biometric attestation required")

            if not device.biometric_enabled:
                raise ValidationError("Biometric not enabled on device")

            # Verify biometric attestation
            proof_success = self.ciam_adapter.verify_biometric(
                session.customer_id,
                device.device_id,
                request.proof_value
            )

            if proof_success:
                self.device_repo.update_last_seen(device)

            # Record attempt
            self.auth_attempt_repo.create(
                customer_id=session.customer_id,
                device_id=device.device_id,
                identifier_hash=hash_identifier(str(device.device_id)),
                attempt_type='biometric',
                outcome='success' if proof_success else 'failure',
                client_ip_hash=None,
                correlation_id=correlation_id,
                occurred_at=datetime.now(UTC)
            )
        else:
            raise ValidationError(f"Unsupported proof type: {request.proof_type}")

        if not proof_success:
            self.db.commit()
            raise AuthenticationError("Proof verification failed")

        # Upgrade session to proven
        self.session_repo.update_auth_level(session, 'proven')

        # Auto-set first active profile if none exists
        if not session.active_profile_id:
            from app.repositories.profile_repository import ProfileRepository
            profile_repo = ProfileRepository()
            profiles = profile_repo.get_by_customer_id(self.db, session.customer_id)
            if profiles:
                session.active_profile_id = profiles[0].profile_id

        # Extend session with full inactivity timeout
        now = datetime.now(UTC)
        self.session_repo.extend_session(session, settings.session_max_seconds)

        self.db.commit()

        # Generate JWT token
        from ..core.security import create_jwt_token
        access_token = create_jwt_token(
            session.customer_id,
            session.session_id,
            'proven',
            session.active_profile_id
        )

        return ProofResponse(
            session_id=str(session.session_id),
            auth_level='proven',
            access_token=access_token,
            token_type='Bearer',
            expires_in=settings.session_max_seconds,
            active_profile_id=str(session.active_profile_id) if session.active_profile_id else None
        )
