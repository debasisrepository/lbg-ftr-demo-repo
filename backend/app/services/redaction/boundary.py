from dataclasses import dataclass


@dataclass
class RedactedContext:
    """Redacted customer input safe for LLM context"""
    text: str
    redaction_applied: bool
    detections: list[str]


class RedactionBoundary:
    """Pre-LLM redaction boundary enforcing PCI/privacy controls"""
    
    def redact(self, customer_text: str) -> RedactedContext:
        """Apply redaction detectors to customer input before LLM context assembly"""
        detections = []
        text = customer_text
        redaction_applied = False
        
        # PAN detection (simplified pattern)
        if self._contains_pan(text):
            text = self._redact_pan(text)
            detections.append("pan")
            redaction_applied = True
        
        # Passcode/PIN detection
        if self._contains_passcode_reference(text):
            detections.append("passcode_reference")
        
        # Injection heuristic
        if self._contains_injection_pattern(text):
            detections.append("injection_pattern")
        
        return RedactedContext(
            text=text,
            redaction_applied=redaction_applied,
            detections=detections
        )
    
    def _contains_pan(self, text: str) -> bool:
        # Simplified: look for 16 consecutive digits
        import re
        return bool(re.search(r'\b\d{16}\b', text))
    
    def _redact_pan(self, text: str) -> str:
        import re
        return re.sub(r'\b\d{16}\b', '[CARD NUMBER REDACTED]', text)
    
    def _contains_passcode_reference(self, text: str) -> bool:
        lower = text.lower()
        keywords = ['password', 'passcode', 'pin', 'security answer']
        return any(kw in lower for kw in keywords)
    
    def _contains_injection_pattern(self, text: str) -> bool:
        # Check for common prompt injection patterns
        lower = text.lower()
        patterns = ['ignore previous', 'ignore all previous', 'new instruction:', 'system:']
        return any(pat in lower for pat in patterns)
