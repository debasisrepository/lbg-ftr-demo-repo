import { Checkmark, Time, Information } from '@carbon/icons-react';
import { ProtectedAction } from '../../types/api';
import './ProtectedStepPanel.css';

interface ProtectedStepPanelProps {
  action: ProtectedAction;
}

/**
 * Protected step progress indicator
 * Shows the 3-step flow: Choose → Security Check → Applied
 */
export function ProtectedStepPanel({ action }: ProtectedStepPanelProps) {
  const isPending = action.request_status === 'pending_sca';
  const isReleased = action.request_status === 'released';
  const isNotExecuted = action.request_status === 'not_executed';

  return (
    <ol className="protected-steps" aria-label="Steps to complete action">
      <li className="step-item">
        <span className="step-icon step-icon-complete">
          <Checkmark size={20} />
        </span>
        <div className="step-content">
          <p className="cds--productive-heading-01">1. Choose the change</p>
          <p className="cds--label-01 step-meta">
            {action.action_type}: done
          </p>
        </div>
      </li>

      <li className="step-item">
        <span className={`step-icon ${isPending ? 'step-icon-current' : isReleased ? 'step-icon-complete' : 'step-icon-inactive'}`}>
          {isPending ? <Time size={20} /> : isReleased ? <Checkmark size={20} /> : <Information size={20} />}
        </span>
        <div className="step-content">
          <p className="cds--productive-heading-01">
            2. Security check
            {isPending && <span className="cds--label-01 step-status"> (waiting for you)</span>}
          </p>
          <p className="cds--label-01 step-meta">
            Nothing changes until this succeeds.
          </p>
        </div>
      </li>

      <li className="step-item">
        <span className={`step-icon ${isReleased ? 'step-icon-complete' : 'step-icon-inactive'}`}>
          <Information size={20} />
        </span>
        <div className="step-content">
          <p className="cds--productive-heading-01">3. Change applied</p>
          <p className="cds--label-01 step-meta">
            {isReleased ? 'Complete' : 'Done in your banking app, not by us.'}
          </p>
        </div>
      </li>
    </ol>
  );
}
