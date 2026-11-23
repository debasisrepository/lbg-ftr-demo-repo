"""
Idempotent seed data for local development and testing.
Seeds synthetic customers, devices, credentials, entitlements, accounts, payees, and capability status.
"""
import os
from pathlib import Path

# Load environment before importing app modules
backend_dir = Path(__file__).resolve().parents[1]
dev_env_file = backend_dir / "dev.env"
if dev_env_file.exists():
    for line in dev_env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlalchemy.orm import Session

from app.models.account_read_model import AccountReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.device_registration import DeviceRegistration
from app.models.payee import Payee
from app.models.sandbox_credential import SandboxCredential
from app.models.sandbox_entitlement import SandboxEntitlement


def hash_passcode(passcode: str, cost: int = 12) -> str:
    """Hash a passcode using bcrypt."""
    return bcrypt.hashpw(passcode.encode('utf-8'), bcrypt.gensalt(rounds=cost)).decode('utf-8')


def hash_device_identifier(device_identifier: str) -> str:
    """Hash device identifier with SHA-256."""
    return hashlib.sha256(device_identifier.encode('utf-8')).hexdigest()


def seed_database(db: Session) -> None:
    """
    Seed synthetic data for development and testing.
    Idempotent: safe to run multiple times.
    """
    print("🌱 Seeding database...")
    
    # Seed customers
    customers = [
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
            "customer_party_id": "CUST-SYNTH-001",
            "ciam_subject_reference": "ciam-subject-synth-001",
            "display_name": "Alex Taylor",
            "passcode": "Pass1234",
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
            "customer_party_id": "CUST-SYNTH-002",
            "ciam_subject_reference": "ciam-subject-synth-002",
            "display_name": "Jordan Smith",
            "passcode": "Pass5678",
        },
    ]
    
    for cust_data in customers:
        # Check if customer exists
        existing = db.query(CustomerProfileRef).filter_by(id=cust_data["id"]).first()
        if not existing:
            customer = CustomerProfileRef(
                id=cust_data["id"],
                customer_party_id=cust_data["customer_party_id"],
                ciam_subject_reference=cust_data["ciam_subject_reference"],
                display_name=cust_data["display_name"],
                profile_type="personal",
                release_scope_status="in_scope",
                is_active=True,
            )
            db.add(customer)
            
            # Seed sandbox credential
            credential = SandboxCredential(
                id=uuid.uuid4(),
                customer_profile_ref_id=cust_data["id"],
                passcode_hash=hash_passcode(str(cust_data["passcode"])),
                failed_attempt_count=0,
            )
            db.add(credential)
            
            # Seed device registrations (1 iOS, 1 Android per customer)
            for idx, platform in enumerate(["iOS", "Android"]):
                # Use plain device identifier and hash it
                plain_device_id = f"device-{cust_data['customer_party_id']}-{platform}"
                device = DeviceRegistration(
                    id=uuid.uuid4(),
                    customer_profile_ref_id=cust_data["id"],
                    device_identifier_hash=hash_device_identifier(plain_device_id),
                    mobile_platform=platform,
                    registration_status="active",
                    ciam_subject_reference=cust_data["ciam_subject_reference"],
                    registered_at=datetime.now(UTC) - timedelta(days=30),
                )
                db.add(device)
            
            # Seed sandbox entitlements (allow for own accounts and payees)
            for resource_type in ["account", "payee", "payment"]:
                entitlement = SandboxEntitlement(
                    id=uuid.uuid4(),
                    customer_profile_ref_id=cust_data["id"],
                    resource_type=resource_type,
                    resource_reference="*",
                    decision="allow",
                )
                db.add(entitlement)
            
            # Commit customer and related records before adding accounts
            db.commit()
            
            # Seed 3 accounts per customer (per handoff spec)
            # Check if accounts already exist
            existing_accounts = db.query(AccountReadModel).filter_by(
                customer_profile_ref_id=cust_data["id"]
            ).count()
            
            if existing_accounts == 0:
                # Account 1: Current balance £1248.36 (current)
                account1 = AccountReadModel(
                    id=uuid.uuid4(),
                    customer_profile_ref_id=cust_data["id"],
                    account_system_reference=f"ACC-{cust_data['customer_party_id']}-001",
                    account_type="current",
                    display_name="Main Current Account",
                    masked_account_identifier="****1234",
                    balance_amount_minor=124836,  # £1248.36
                    balance_currency="GBP",
                    balance_availability_state="current",
                    as_of_timestamp=datetime.now(UTC) - timedelta(seconds=30),
                    freshness_status="within_target",
                    freshness_breach_indicator=False,
                    source_system_type="core_banking",
                    last_source_event_id=f"evt-{cust_data['customer_party_id']}-001",
                    last_source_event_at=datetime.now(UTC) - timedelta(seconds=30),
                    provenance_reference=f"seed-{cust_data['customer_party_id']}-001",
                    projection_updated_at=datetime.now(UTC)
                )
                db.add(account1)
                
                # Account 2: Savings balance £3500.00 (current)
                account2 = AccountReadModel(
                    id=uuid.uuid4(),
                    customer_profile_ref_id=cust_data["id"],
                    account_system_reference=f"ACC-{cust_data['customer_party_id']}-002",
                    account_type="savings",
                    display_name="Instant Saver",
                    masked_account_identifier="****5678",
                    balance_amount_minor=350000,  # £3500.00
                    balance_currency="GBP",
                    balance_availability_state="current",
                    as_of_timestamp=datetime.now(UTC) - timedelta(seconds=45),
                    freshness_status="within_target",
                    freshness_breach_indicator=False,
                    source_system_type="core_banking",
                    last_source_event_id=f"evt-{cust_data['customer_party_id']}-002",
                    last_source_event_at=datetime.now(UTC) - timedelta(seconds=45),
                    provenance_reference=f"seed-{cust_data['customer_party_id']}-002",
                    projection_updated_at=datetime.now(UTC)
                )
                db.add(account2)
                
                # Account 3: Stale balance £1248.36 at 08:12 (breached freshness)
                stale_time = datetime.now(UTC) - timedelta(hours=2, minutes=30)
                account3 = AccountReadModel(
                    id=uuid.uuid4(),
                    customer_profile_ref_id=cust_data["id"],
                    account_system_reference=f"ACC-{cust_data['customer_party_id']}-003",
                    account_type="current",
                    display_name="Joint Account",
                    masked_account_identifier="****9012",
                    balance_amount_minor=124836,  # £1248.36
                    balance_currency="GBP",
                    balance_availability_state="stale",
                    as_of_timestamp=stale_time,
                    freshness_status="breached",
                    freshness_breach_indicator=True,
                    source_system_type="core_banking",
                    last_source_event_id=f"evt-{cust_data['customer_party_id']}-003",
                    last_source_event_at=stale_time,
                    provenance_reference=f"seed-{cust_data['customer_party_id']}-003",
                    projection_updated_at=stale_time
                )
                db.add(account3)
                
                print(f"✓ Seeded customer: {cust_data['display_name']} (passcode: {cust_data['passcode']}) with 3 accounts")
            else:
                print(f"✓ Customer {cust_data['display_name']} already has {existing_accounts} accounts")
            
            # Seed 3 payees per customer (per handoff spec)
            # Payee 1: Jamie Clarke, sort 04-00-04, ending 3321
            # Payee 2: Priya Patel, sort 60-83-71, ending 7745
            # Payee 3: K Evans Lettings, sort 20-45-77, ending 9842
            existing_payees = db.query(Payee).filter_by(
                customer_profile_ref_id=cust_data["id"]
            ).count()
            
            if existing_payees == 0:
                payees_data = [
                    {
                        "payee_name": "Jamie Clarke",
                        "payee_account_identifier": "12345678",  # Full account never shown
                        "payee_sort_code": "04-00-04",
                        "masked_account_identifier": "****3321",
                        "cop_outcome_category": "match",
                    },
                    {
                        "payee_name": "Priya Patel",
                        "payee_account_identifier": "87654321",
                        "payee_sort_code": "60-83-71",
                        "masked_account_identifier": "****7745",
                        "cop_outcome_category": "match",
                    },
                    {
                        "payee_name": "K Evans Lettings",
                        "payee_account_identifier": "11223344",
                        "payee_sort_code": "20-45-77",
                        "masked_account_identifier": "****9842",
                        "cop_outcome_category": "close_match",
                    },
                ]
                
                for payee_data in payees_data:
                    payee = Payee(
                        id=uuid.uuid4(),
                        customer_profile_ref_id=cust_data["id"],
                        payee_name=payee_data["payee_name"],
                        payee_account_identifier=payee_data["payee_account_identifier"],
                        payee_sort_code=payee_data["payee_sort_code"],
                        masked_account_identifier=payee_data["masked_account_identifier"],
                        payee_status="saved_active",
                        activated_at=datetime.now(UTC) - timedelta(days=30),
                        cop_outcome_category=payee_data["cop_outcome_category"],
                        cop_provider_reference=f"cop-ref-{payee_data['payee_name'].replace(' ', '-').lower()}",
                        cop_checked_at=datetime.now(UTC) - timedelta(days=30),
                        correlation_id=f"seed-cop-{cust_data['customer_party_id']}"
                    )
                    db.add(payee)
                
                print(f"✓ Seeded 3 payees for {cust_data['display_name']}")
            else:
                print(f"✓ Customer {cust_data['display_name']} already has {existing_payees} payees")
    
    # Seed capability status records
    capabilities = ["accounts_overview", "saved_payees", "payments", "payment_status"]
    for cap_name in capabilities:
        existing_cap = db.query(CapabilityStatusRecord).filter_by(capability_name=cap_name).first()
        if not existing_cap:
            capability = CapabilityStatusRecord(
                id=uuid.uuid4(),
                capability_name=cap_name,
                status_value="healthy",
                cause_category="unknown",
                effective_from=datetime.now(UTC),
            )
            db.add(capability)
    
    db.commit()
    print("✅ Database seeding complete!")
    print("\n📋 Seed credentials:")
    print("   Customer 1: Alex Taylor   - passcode: Pass1234")
    print("              Device iOS:     device-CUST-SYNTH-001-iOS")
    print("              Device Android: device-CUST-SYNTH-001-Android")
    print("   Customer 2: Jordan Smith  - passcode: Pass5678")
    print("              Device iOS:     device-CUST-SYNTH-002-iOS")
    print("              Device Android: device-CUST-SYNTH-002-Android")


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
