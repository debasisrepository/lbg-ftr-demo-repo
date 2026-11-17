from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean, CheckConstraint, Index, ForeignKey, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.clock import Clock


class CaseRecord(Base):
    __tablename__ = "case_record"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    case_ref: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    customer_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    origin_source: Mapped[str] = mapped_column(String(40), nullable=False)
    problem_statement: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str | None] = mapped_column(String(40), nullable=True)
    arrangement_reference: Mapped[str | None] = mapped_column(String(40), nullable=True)
    current_queue_ref: Mapped[str | None] = mapped_column(String(40), nullable=True)
    owner_team_display: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner_colleague_display: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    continuation_path: Mapped[str] = mapped_column(String(20), nullable=False, default='conversation')
    regulatory_clock_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    regulatory_clock_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    expected_by_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_update_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("status IN ('new', 'assigned', 'in_progress', 'awaiting_customer', 'awaiting_internal', 'resolved', 'closed', 'reopened')", name="ck_case_record_status"),
        CheckConstraint("origin_source IN ('assistant_escalation', 'colleague_desktop', 'callback_booked', 'incident_impact', 'transaction_dispute', 'direct_entry')", name="ck_case_record_origin"),
        CheckConstraint("continuation_path IN ('conversation', 'callback', 'resolved')", name="ck_case_record_continuation"),
        CheckConstraint("regulatory_clock_type IN ('complaint', 'fraud_notification', 'data_rights')", name="ck_case_record_clock_type"),
        CheckConstraint("(status IN ('new', 'assigned', 'in_progress', 'awaiting_customer', 'awaiting_internal', 'reopened') AND expected_by_at > CURRENT_TIMESTAMP) OR (status IN ('resolved', 'closed'))", name="ck_case_record_expected_by_future"),
        Index("uq_case_record_case_ref", "case_ref", unique=True),
        Index("ix_case_record_customer_status_expected", "customer_user_id", "status", "expected_by_at"),
        Index("ix_case_record_customer_last_update", "customer_user_id", "last_update_at"),
        Index("ix_case_record_queue_status", "current_queue_ref", "status"),
        Index("ix_case_record_status_heartbeat", "status", "last_heartbeat_at"),
    )


class ConversationThread(Base):
    __tablename__ = "conversation_thread"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=True)
    entry_point: Mapped[str] = mapped_column(String(40), nullable=False)
    entry_context_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entry_context_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ai_disclosure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    human_path_shown: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now)

    __table_args__ = (
        CheckConstraint("entry_point IN ('resolve_assistant', 'colleague_desktop', 'callback', 'self_service', 'transaction_detail', 'issue_card')", name="ck_conversation_thread_entry_point"),
        CheckConstraint("entry_context_type IN ('transaction', 'issue', 'card', 'none')", name="ck_conversation_thread_context_type"),
        Index("uq_conversation_thread_case_id", "case_id", unique=True),
    )


class ConversationEntry(Base):
    __tablename__ = "conversation_entry"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversation_thread.id"), nullable=False)
    thread_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    visibility_scope: Mapped[str] = mapped_column(String(20), nullable=False, default='customer_visible')
    redaction_status: Mapped[str] = mapped_column(String(20), nullable=False, default='pending')
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now, server_default=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("role IN ('customer', 'assistant', 'system', 'colleague')", name="ck_conversation_entry_role"),
        CheckConstraint("visibility_scope IN ('customer_visible', 'colleague_only')", name="ck_conversation_entry_visibility"),
        CheckConstraint("redaction_status IN ('pending', 'clean', 'redacted', 'blocked')", name="ck_conversation_entry_redaction"),
        Index("uq_conversation_entry_thread_seq", "thread_id", "thread_seq", unique=True),
    )


class ConversationSummary(Base):
    __tablename__ = "conversation_summary"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversation_thread.id"), nullable=False)
    summary_version: Mapped[int] = mapped_column(Integer, nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now)

    __table_args__ = (
        Index("ix_conversation_summary_thread_version", "thread_id", "summary_version"),
    )


class EvidenceItem(Base):
    __tablename__ = "evidence_item"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    thread_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("conversation_thread.id"), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    display_label: Mapped[str] = mapped_column(String(200), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    storage_key: Mapped[str | None] = mapped_column(String(200), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    llm_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("state IN ('requested', 'received', 'rejected')", name="ck_evidence_item_state"),
        Index("ix_evidence_item_thread_state", "thread_id", "state"),
    )


class CaseAssignment(Base):
    __tablename__ = "case_assignment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=False)
    assignment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    queue_ref: Mapped[str | None] = mapped_column(String(40), nullable=True)
    team_ref: Mapped[str | None] = mapped_column(String(40), nullable=True)
    colleague_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("app_user.id"), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now)

    __table_args__ = (
        CheckConstraint("assignment_type IN ('queue_owner', 'team_owner', 'colleague_owner')", name="ck_case_assignment_type"),
        Index("ix_case_assignment_case_assigned", "case_id", "assigned_at"),
        Index("ix_case_assignment_queue_current", "queue_ref", "is_current"),
    )


class CaseTimelineEvent(Base):
    __tablename__ = "case_timeline_event"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    case_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("case_record.id"), nullable=False)
    domain_event_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    actor_display: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=Clock.utc_now)

    __table_args__ = (
        Index("ix_case_timeline_event_case_occurred", "case_id", "occurred_at"),
    )
