from typing import Optional


class StatusServiceClient:
    """Client for reading service status context"""
    
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or "http://status-service:8080"
    
    def get_active_incidents(self, service_codes: list[str] | None = None) -> list[dict]:
        """
        Fetch active incidents for given services
        For demo: return empty list (status service independently deployed)
        """
        return []
    
    def format_status_context(self, incidents: list[dict]) -> str | None:
        """Format incident context for customer display"""
        if not incidents:
            return None
        
        lines = ["We're aware of the following issues:"]
        for incident in incidents:
            lines.append(f"- {incident.get('title', 'Service disruption')}")
        
        return "\n".join(lines)
