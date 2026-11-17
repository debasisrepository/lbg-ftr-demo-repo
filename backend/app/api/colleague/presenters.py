"""Colleague API presenters."""
from app.services.case.models import CaseRecord, ConversationEntry
from app.api.colleague.schemas import (
    ColleagueCaseListItem,
    TranscriptEntryResponse,
    HandoffPackResponse
)


def present_case_list_item(case: CaseRecord) -> ColleagueCaseListItem:
    """Present case as colleague worklist item."""
    return ColleagueCaseListItem(
        case_id=str(case.id),
        case_ref=case.case_ref,
        status_code=case.status,
        classification_code=case.classification or "unclassified",
        owner_team_display=case.owner_team_display or "Customer Support Team",
        owner_colleague_display=case.owner_colleague_display,
        expected_by_at=case.expected_by_at,
        last_update_at=case.last_update_at
    )


def present_transcript_entry(entry: ConversationEntry) -> TranscriptEntryResponse:
    """Present conversation entry for colleague view."""
    return TranscriptEntryResponse(
        entry_id=str(entry.id),
        role=entry.role,
        content_text=entry.content_text,
        visibility_scope=entry.visibility_scope,
        occurred_at=entry.occurred_at
    )
