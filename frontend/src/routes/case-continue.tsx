import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Button, InlineNotification } from '@carbon/react';
import { ArrowLeft } from '@carbon/icons-react';
import { apiClient } from '../lib/api-client';
import { HandoffChooser } from '../components/continuity/HandoffChooser';
import { SharedFieldsPanel } from '../components/continuity/SharedFieldsPanel';
import styles from './case-continue.module.css';

interface ContinuityPackage {
  shared_field_names: string[];
  package_version: number;
  generated_at: string;
}

/**
 * Continue channel page - handoff to another channel with context
 */
export function ContinueChannelPage() {
  const { caseReference } = useParams<{ caseReference: string }>();
  const navigate = useNavigate();
  const [continuity, setContinuity] = useState<ContinuityPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedChannel, setSelectedChannel] = useState('chat');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  
  const channelOptions = [
    {
      value: 'chat',
      label: 'Chat with an adviser',
      description: 'Usually a few minutes',
    },
    {
      value: 'phone',
      label: 'Phone call',
      description: 'We call you on the number we hold',
    },
    {
      value: 'branch',
      label: 'Branch',
      description: 'Show your reference at the counter',
    },
  ];
  
  useEffect(() => {
    const loadContinuity = async () => {
      if (!caseReference) return;
      
      try {
        const data = await apiClient.get<ContinuityPackage>(
          `/cases/${caseReference}/continuity`
        );
        setContinuity(data);
      } catch (err) {
        setError('Could not load continuity information. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    
    loadContinuity();
  }, [caseReference]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!caseReference || submitting) return;
    
    setSubmitting(true);
    setError(null);
    
    try {
      await apiClient.post(`/cases/${caseReference}/handoffs`, {
        to_channel: selectedChannel,
        from_channel: 'mobile_app',
        context_presented_flag: true,
      });
      
      setSuccess(true);
      
      // Navigate back to case detail after a brief delay
      setTimeout(() => {
        navigate(`/cases/${caseReference}`);
      }, 3000);
    } catch (err) {
      setError('Could not complete handoff. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className={`cds--stack-scale-6 ${styles.container}`}>
        <p>Loading...</p>
      </div>
    );
  }
  
  if (error && !continuity) {
    return (
      <div className={`cds--stack-scale-6 ${styles.container}`}>
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          hideCloseButton
        />
        <Link to={`/cases/${caseReference}`}>Back to case</Link>
      </div>
    );
  }
  
  if (!continuity) {
    return null;
  }
  
  if (success) {
    return (
      <div className={`cds--stack-scale-6 ${styles.container}`}>
        <h1 className="cds--productive-heading-05">Your Case is ready in chat</h1>
        
        <InlineNotification
          kind="success"
          lowContrast
          hideCloseButton
          title={`Same Case: ${caseReference}`}
          subtitle="We did not open a new Case. The adviser can see the fields above, and you will not need to explain again."
        />
        
        <p>Returning to case details...</p>
      </div>
    );
  }
  
  return (
    <div className={`cds--stack-scale-6 ${styles.container}`}>
      <Link to={`/cases/${caseReference}`} className={styles.backLink}>
        <ArrowLeft size={16} />
        Case {caseReference}
      </Link>
      
      <header className="cds--stack-scale-3">
        <h1 className="cds--productive-heading-05">Get help</h1>
        <p className={styles.description}>
          Choose how you would like to carry on. You keep the same Case, so you do not have to explain again.
        </p>
      </header>
      
      <form onSubmit={handleSubmit} className="cds--stack-scale-6">
        <HandoffChooser
          value={selectedChannel}
          onChange={setSelectedChannel}
          options={channelOptions}
        />
        
        <SharedFieldsPanel
          shared_field_names={continuity.shared_field_names}
          package_version={continuity.package_version}
          generated_at={continuity.generated_at}
        />
        
        <section className="cds--stack-scale-3" aria-labelledby="never-h">
          <h2 className="cds--productive-heading-02" id="never-h">
            What is never shared
          </h2>
          <ul className={`cds--stack-scale-3 ${styles.neverList}`}>
            <li>Your full card number</li>
            <li>Passcodes and security answers</li>
            <li>A full copy of earlier conversations</li>
          </ul>
          <p className={`cds--label-01 ${styles.metaText}`}>
            Only the fields listed above are passed on, so each channel starts from the same facts.
          </p>
        </section>
        
        {error && (
          <InlineNotification
            kind="error"
            title="Error"
            subtitle={error}
            hideCloseButton
          />
        )}
        
        <Button
          type="submit"
          kind="primary"
          disabled={submitting}
          className={styles.submitButton}
        >
          {submitting ? 'Continuing...' : 'Continue in chat'}
        </Button>
        
        <Button
          as={Link}
          to={`/cases/${caseReference}`}
          kind="tertiary"
          className={styles.cancelButton}
        >
          Cancel
        </Button>
      </form>
    </div>
  );
}
