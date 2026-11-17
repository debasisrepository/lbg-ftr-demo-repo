import { Button } from '@carbon/react';
import { ChevronRight } from '@carbon/icons-react';
import './ScaPrompt.css';

interface ScaPromptProps {
  onStartSca: () => void;
  onCancel: () => void;
}

/**
 * SCA prompt panel
 * Displays security check requirement and action buttons
 */
export function ScaPrompt({ onStartSca, onCancel }: ScaPromptProps) {
  return (
    <section className="sca-prompt" role="group" aria-labelledby="sca-heading">
      <div className="sca-prompt-header">
        <h2 className="cds--productive-heading-03" id="sca-heading">
          Security check required
        </h2>
      </div>
      <div className="sca-prompt-body">
        <p className="cds--body-01">
          Confirm in your banking app to carry on. This usually takes under a minute.
        </p>
        <Button kind="primary" onClick={onStartSca} renderIcon={ChevronRight}>
          Confirm it is me
        </Button>
        <Button kind="tertiary" onClick={onCancel}>
          Cancel, change nothing
        </Button>
      </div>
    </section>
  );
}
