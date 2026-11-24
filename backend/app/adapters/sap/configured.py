"""Configured SAP adapter selector."""
import os
from app.adapters.sap.stub import StubSapCustomerContextReader, StubSapReceivablesReader


def get_sap_receivables_reader():
    """Get configured SAP receivables reader.
    
    Returns the appropriate SAP reader implementation based on
    SAP_ADAPTER_MODE environment variable:
    - 'stub' (default): Returns stub implementation for development
    - 'real': Real SAP connector (not yet implemented - will raise error)
    """
    adapter_mode = os.environ.get('SAP_ADAPTER_MODE', 'stub')
    
    if adapter_mode == 'stub':
        return StubSapReceivablesReader()
    elif adapter_mode == 'real':
        raise NotImplementedError(
            "Real SAP adapter is not yet implemented. "
            "Set SAP_ADAPTER_MODE=stub or implement a real SAP connector "
            "that uses SAP RFC, OData, or other SAP integration protocol."
        )
    else:
        return StubSapReceivablesReader()


def get_sap_customer_context_reader():
    """Get configured SAP customer context reader.
    
    Returns the appropriate SAP customer context reader based on
    SAP_ADAPTER_MODE environment variable:
    - 'stub' (default): Returns stub implementation for development
    - 'real': Real SAP connector (not yet implemented - will raise error)
    """
    adapter_mode = os.environ.get('SAP_ADAPTER_MODE', 'stub')
    
    if adapter_mode == 'stub':
        return StubSapCustomerContextReader()
    elif adapter_mode == 'real':
        raise NotImplementedError(
            "Real SAP customer context adapter is not yet implemented. "
            "Set SAP_ADAPTER_MODE=stub or implement a real SAP connector "
            "that uses SAP RFC, OData, or other SAP integration protocol."
        )
    else:
        return StubSapCustomerContextReader()
