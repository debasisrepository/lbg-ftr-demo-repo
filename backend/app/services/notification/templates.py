class NotificationTemplates:
    CASE_CAPTURED = "case_captured"
    CASE_STATUS_CHANGED = "case_status_changed"

    @staticmethod
    def get_template_text(template_ref: str, case_ref: str) -> str:
        if template_ref == NotificationTemplates.CASE_CAPTURED:
            return f"Your case {case_ref} has been created. View it in My Cases."
        elif template_ref == NotificationTemplates.CASE_STATUS_CHANGED:
            return f"Your case {case_ref} has been updated. View it in My Cases."
        return "You have a case update. View it in My Cases."

    @staticmethod
    def get_reentry_route(case_ref: str) -> str:
        return f"/cases/{case_ref}"
