import { useParams, Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Button, InlineNotification, Modal } from '@carbon/react';
import { ArrowLeft } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import { ProtectedAction } from '../types/api';
import { ProtectedStepPanel } from '../components/actions/ProtectedStepPanel';
import { ScaPrompt } from '../components/actions/ScaPrompt';
import { FallbackGuidance } from '../components/actions/FallbackGuidance';
import './case-action.css';

/**
 * Protected Action page - wireframe_06
 * Handles SCA flow for protected actions
 * Features FR-029, FR-032
 */
export function ProtectedActionPage() {
  const { caseReference, actionId } = useParams<{ caseReference: string; actionId: string }>();
  const navigate = useNavigate();
  const [action, setAction] = useState<ProtectedAction | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scaModalOpen, setScaModalOpen] = useState(false);
  const [polling, setPolling] = useState(false);

  // Load action status
  const loadAction = async () => {
    if (!caseReference || !actionId) return;
    
    try {
      const response = await apiClient.get<ProtectedAction>(
        `/cases/${caseReference}/actions/${actionId}`
      );
      setAction(response);
      setError(null);
      
      // If pending_sca and modal is open, keep polling
      if (response.request_status === 'pending_sca' && scaModalOpen) {
        setPolling(true);
      } else {
        setPolling(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load action');
      setPolling(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAction();
  }, [caseReference, actionId]);

  // Poll every 2 seconds when pending_sca and modal is open
  useEffect(() => {
    if (!polling || !scaModalOpen) return;

    const interval = setInterval(() => {
      loadAction();
    }, 2000);

    return () => clearInterval(interval);
  }, [polling, scaModalOpen]);

  const handleStartSca = () => {
    setScaModalOpen(true);
    setPolling(true);
  };

  const handleCancelSca = () => {
    setScaModalOpen(false);
    setPolling(false);
  };

  const handleBackToCase = () => {
    navigate(`/cases/${caseReference}`);
  };

  if (loading && !action) {
    return (
      <div className="case-action-page">
        <Link to={`/cases/${caseReference}`} className="back-link">
          <ArrowLeft size={16} />
          Case {caseReference}
        </Link>
        <p className="cds--body-01">Loading...</p>
      </div>
    );
  }

  if (error && !action) {
    return (
      <div className="case-action-page">
        <Link to={`/cases/${caseReference}`} className="back-link">
          <ArrowLeft size={16} />
          Case {caseReference}
        </Link>
        
        <InlineNotification
          kind="error"
          title="Failed to load action"
          subtitle={error}
          lowContrast
        />
        
        <Button kind="tertiary" onClick={handleBackToCase}>
          Back to Case
        </Button>
      </div>
    );
  }

  if (!action) {
    return null;
  }

  return (
    <div className="case-action-page">
      <Link to={`/cases/${caseReference}`} className="back-link">
        <ArrowLeft size={16} />
        Case {caseReference}
      </Link>
      
      <header className="action-header">
        <p className="case-meta">
          Case {caseReference}
        </p>
        <h1 className="cds--productive-heading-05">Protected action</h1>
        <p>This action requires security verification before it can be completed.</p>
      </header>

      <ProtectedStepPanel action={action} />

      {action.request_status === 'pending_sca' && (
        <ScaPrompt
          onStartSca={handleStartSca}
          onCancel={handleBackToCase}
        />
      )}

      {action.request_status === 'released' && action.management_api_reference && (
        <div className="outcome-section">
          <span className="state-label">Success</span>
          <h2 className="cds--productive-heading-03">Action completed</h2>
          
          <InlineNotification
            kind="success"
            title="Security check passed"
            subtitle={`Your request has been processed. Reference: ${action.management_api_reference}`}
            lowContrast
          />
          
          <Button kind="primary" onClick={handleBackToCase}>
            Back to Case
          </Button>
        </div>
      )}

      {action.request_status === 'not_executed' && (
        <FallbackGuidance
          fallbackText={action.fallback_guidance_text || 'This action could not be completed. Please contact support.'}
          onRetry={handleStartSca}
          onBackToCase={handleBackToCase}
        />
      )}

      {/* SCA Authentication Modal */}
      <Modal
        open={scaModalOpen}
        onRequestClose={handleCancelSca}
        modalHeading="Authenticating..."
        passiveModal
        size="sm"
      >
        <p className="cds--body-01">
          {polling ? 'Waiting for authentication...' : 'Processing your request...'}
        </p>
        <p className="cds--label-01 modal-secondary-text">
          This usually takes under a minute.
        </p>
      </Modal>
    </div>
  );
}
