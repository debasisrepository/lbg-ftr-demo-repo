"""Workspace service."""
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.core.clock import Clock
from app.core.context import RoleContext
from app.repositories.queue_repository import QueueRepository
from app.repositories.promise_repository import PromiseRepository


class WorkspaceService:
    """Service for workspace operations."""

    def __init__(self, db: Session, clock: Clock):
        self.db = db
        self.clock = clock
        self.queue_repo = QueueRepository(db)
        self.promise_repo = PromiseRepository(db)

    def build_landing_payload(
        self,
        role: RoleContext,
        available_roles: List[RoleContext],
        user_id: str,
    ) -> Dict[str, Any]:
        """Build landing workspace payload.
        
        Args:
            role: Active role context
            available_roles: All available roles
            user_id: User ID for user-specific widgets
            
        Returns:
            Landing payload dict
        """
        now = self.clock.now()

        # Build widgets based on role
        widgets = []

        if "queue_summary" in role.allowed_widgets:
            widgets.append(self._build_queue_summary_widget(role.entitled_queue_states))

        if "open_promises" in role.allowed_widgets:
            widgets.append(self._build_open_promises_widget(user_id))

        data_freshness = self.queue_repo.get_data_freshness() or now

        return {
            "active_role_code": role.role_code,
            "active_role_label": role.role_label,
            "available_roles": [
                {"role_code": r.role_code, "role_label": r.role_label}
                for r in available_roles
            ],
            "allowed_actions": role.allowed_actions,
            "widgets": widgets,
            "data_freshness": data_freshness,
            "generated_at": now,
        }

    def _build_queue_summary_widget(self, entitled_queue_states: List[str]) -> Dict[str, Any]:
        """Build queue summary widget.
        
        Args:
            entitled_queue_states: Queue states the user is entitled to see
        
        Returns:
            Queue summary widget dict
        """
        groups = self.queue_repo.get_groups()
        
        # Get top 3 items from entitled states
        top_items = []
        if entitled_queue_states:
            for queue_state in entitled_queue_states[:3]:  # Limit to first 3 states
                items, _ = self.queue_repo.list_items(
                    queue_state=queue_state,
                    limit=3,
                    offset=0,
                )
                top_items.extend([
                    {
                        "queue_item_id": str(item.id),
                        "queue_state": item.queue_state,
                        "current_rank": item.current_rank,
                        "receivable_item_id": str(item.receivable_item_id),
                    }
                    for item in items[:3]
                ])
                if len(top_items) >= 3:
                    top_items = top_items[:3]
                    break
        
        return {
            "widget_code": "queue_summary",
            "widget_label": "Queue Summary",
            "widget_data": {
                "groups": [
                    {
                        "queue_state": g["queue_state"],
                        "count": g["count"],
                        "total_amount": float(g["total_amount"]),
                    }
                    for g in groups
                ],
                "top_items": top_items,
            },
        }

    def _build_open_promises_widget(self, user_id: str) -> Dict[str, Any]:
        """Build open promises widget.
        
        Args:
            user_id: User ID to get promises for
            
        Returns:
            Open promises widget dict
        """
        import uuid
        user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        
        # Get active promises captured by user
        promises, _ = self.promise_repo.list_promises(
            captured_by_user_id=user_uuid,
            promise_status="captured",
            limit=1000,
        )
        
        # Calculate count and total
        count = len(promises)
        total_amount = sum(float(p.promised_amount) for p in promises)
        
        return {
            "widget_code": "open_promises",
            "widget_label": "Open Promises",
            "widget_data": {
                "count": count,
                "total_amount": total_amount,
            },
        }
