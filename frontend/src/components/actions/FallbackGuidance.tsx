import { Button, InlineNotification } from '@carbon/react';
import { ChevronRight } from '@carbon/icons-react';
import './FallbackGuidance.css';

interface FallbackGuidanceProps {
  fallbackText: string;
  onRetry: () => void;
  onBackToCase: () => void;
}

/**
 * Fallback guidance panel
 * Shown when SCA fails or action cannot be executed
 */
export function FallbackGuidance({ fallbackText, onRetry, onBackToCase }: FallbackGuidanceProps) {
  return (
    <div className="fallback-guidance">
      <span className="state-label">Action not completed</span>
      <h2 className="cds--productive-heading-03">Nothing was changed</h2>
      
      <InlineNotification
        kind="warning"
        title="Your action has not been completed"
        subtitle={fallbackText}
        lowContrast
      />
      
      <Button kind="primary" onClick={onRetry} renderIcon={ChevronRight}>
        Try the security check again
      </Button>
      
      <Button kind="tertiary" onClick={onBackToCase}>
        Back to Case
      </Button>
    </div>
  );
}
