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
from app.models.business_profile_read_model import BusinessProfileReadModel
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.device_registration import DeviceRegistration
from app.models.material_third_party_register import MaterialThirdPartyRegister
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
    
    # Seed customers (Release 1 + Release 2)
    customers = [
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
            "customer_party_id": "CUST-SYNTH-001",
            "ciam_subject_reference": "ciam-subject-synth-001",
            "display_name": "Alex Taylor",
            "profile_type": "personal",
            "business_name": None,
            "passcode": "Pass1234",
        },
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
            "customer_party_id": "CUST-SYNTH-002",
            "ciam_subject_reference": "ciam-subject-synth-002",
            "display_name": "Jordan Smith",
            "profile_type": "personal",
            "business_name": None,
            "passcode": "Pass5678",
        },
        # Release 2: Business profile (TD-04: SP Events Ltd)
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
            "customer_party_id": "CUST-SYNTH-003",
            "ciam_subject_reference": "ciam-subject-synth-003",
            "display_name": "SP Events Ltd",
            "profile_type": "business",
            "business_name": "SP Events Ltd",
            "passcode": "Pass9999",
        },
        # Release 2: TD-09 Alex Morgan (viewer, no pay entitlement)
        {
            "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
            "customer_party_id": "CUST-SYNTH-004",
            "ciam_subject_reference": "ciam-subject-synth-004",
            "display_name": "Alex Morgan",
            "profile_type": "personal",
            "business_name": None,
            "passcode": "Pass2222",
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
                profile_type=cust_data.get("profile_type", "personal"),
                business_name=cust_data.get("business_name"),
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
    capabilities = ["accounts_overview", "saved_payees", "payments", "payment_status", "loan_view"]
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
    
    # Release 2: Seed loan account for Alex Taylor (TD-03: Personal loan)
    alex_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    loan_account = db.query(AccountReadModel).filter_by(
        customer_profile_ref_id=alex_id,
        account_type="loan"
    ).first()
    
    if not loan_account:
        now = datetime.now(UTC)
        loan_account = AccountReadModel(
            id=uuid.uuid4(),
            customer_profile_ref_id=alex_id,
            account_system_reference="LOAN-001-ALEX",
            account_type="loan",
            display_name="Personal Loan",
            masked_account_identifier="****1234",
            balance_amount_minor=1850000,  # £18,500 outstanding
            balance_currency="GBP",
            balance_availability_state="current",
            as_of_timestamp=now,
            freshness_status="within_target",
            freshness_breach_indicator=False,
            source_system_type="loan_servicing",
            provenance_reference="loan-servicing-synth-001",
            projection_updated_at=now,
            # Release 2 loan fields
            loan_outstanding_balance_minor=1850000,
            loan_next_repayment_date=now + timedelta(days=15),
            loan_next_repayment_amount_minor=45000,  # £450 per month
            loan_remaining_term_months=42,
        )
        db.add(loan_account)
        print("✓ Seeded loan account for Alex Taylor")
    
    # Release 2: Seed business account for SP Events Ltd (TD-04)
    business_id = uuid.UUID("00000000-0000-0000-0000-000000000003")
    business_account = db.query(BusinessProfileReadModel).filter_by(
        customer_profile_ref_id=business_id
    ).first()
    
    if not business_account:
        now = datetime.now(UTC)
        business_account = BusinessProfileReadModel(
            id=uuid.uuid4(),
            customer_profile_ref_id=business_id,
            business_name="SP Events Ltd",
            business_account_system_reference="BIZ-CURR-001",
            account_type="business_current",
            display_name="SP Events Ltd - Current Account",
            masked_account_identifier="****5678",
            balance_amount_minor=12450000,  # £124,500 available
            balance_currency="GBP",
            balance_availability_state="current",
            pending_outgoing_payments_count=3,
            pending_outgoing_payments_amount_minor=850000,  # £8,500 pending
            as_of_timestamp=now,
            freshness_status="within_target",
            source_system_type="business_banking",
            projection_updated_at=now,
        )
        db.add(business_account)
        print("✓ Seeded business account for SP Events Ltd")
    
    # Release 2: Seed material third-party register (TPR-01, TPR-02, TPR-03)
    third_parties = [
        {
            "name": "AWS (Cloud Infrastructure)",
            "category": "cloud",
            "description": "Cloud hosting for backend services and databases",
            "criticality": "critical",
        },
        {
            "name": "Vocalink (CoP Provider)",
            "category": "cop_provider",
            "description": "Confirmation of Payee service provider",
            "criticality": "critical",
        },
        {
            "name": "Featurespace (Fraud Engine)",
            "category": "fraud_engine",
            "description": "Real-time fraud detection and scam prevention",
            "criticality": "important",
        },
        {
            "name": "Firebase Cloud Messaging",
            "category": "push_notification",
            "description": "Push notification delivery for mobile app",
            "criticality": "important",
        },
    ]
    
    for tp in third_parties:
        existing_tp = db.query(MaterialThirdPartyRegister).filter_by(
            third_party_name=tp["name"]
        ).first()
        
        if not existing_tp:
            third_party = MaterialThirdPartyRegister(
                id=uuid.uuid4(),
                third_party_name=tp["name"],
                service_category=tp["category"],
                service_description=tp["description"],
                criticality=tp["criticality"],
                contract_start_date=datetime.now(UTC).date() - timedelta(days=365),
                contract_review_date=datetime.now(UTC).date() + timedelta(days=180),
                exit_plan_status="approved",
                exit_plan_last_tested=datetime.now(UTC).date() - timedelta(days=90),
                regulatory_reportable=True,
            )
            db.add(third_party)
    
    print("✓ Seeded material third-party register (4 entries)")
    
    db.commit()
    print("✅ Database seeding complete!")
    print("\n📋 Seed credentials:")
    print("   Customer 1: Alex Taylor (personal)   - passcode: Pass1234")
    print("              Device iOS:     device-CUST-SYNTH-001-iOS")
    print("              Device Android: device-CUST-SYNTH-001-Android")
    print("              Has loan account with £18,500 outstanding")
    print("   Customer 2: Jordan Smith (personal)  - passcode: Pass5678")
    print("              Device iOS:     device-CUST-SYNTH-002-iOS")
    print("              Device Android: device-CUST-SYNTH-002-Android")
    print("   Customer 3: SP Events Ltd (business) - passcode: Pass9999")
    print("              Device iOS:     device-CUST-SYNTH-003-iOS")
    print("              Business account with £124,500 available")
    print("   Customer 4: Alex Morgan (personal)   - passcode: Pass2222")
    print("              Device iOS:     device-CUST-SYNTH-004-iOS")
    print("              Viewer role (no pay entitlement)")


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
