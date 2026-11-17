import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import type { ResolveSessionView, SendMessageRequest, ResolveTurnResponse } from '../types/resolve';
import { AiDisclosure } from '../components/resolve/AiDisclosure';
import { TranscriptEntry } from '../components/resolve/TranscriptEntry';
import { AssistantFindingsCard } from '../components/resolve/AssistantFindingsCard';
import { EvidenceUpload } from '../components/resolve/EvidenceUpload';
import { ProposalCard } from '../components/resolve/ProposalCard';

interface EvidenceFile {
  name: string;
  size: number;
  state: string;
}

interface AssistantStep {
  status: 'done' | 'waiting';
  label: string;
}

export function ResolveSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<ResolveSessionView | null>(null);
  const [replyText, setReplyText] = useState('');
  const [uploadedFile, setUploadedFile] = useState<EvidenceFile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock assistant steps and findings (in real app, would come from session state)
  const [assistantSteps] = useState<AssistantStep[]>([
    { status: 'done', label: 'Checked your recent payments' },
    { status: 'done', label: 'Looked for a known service problem. There isn\'t one for this payment.' },
    { status: 'waiting', label: 'One piece of evidence from you' },
  ]);

  const [showProposal, setShowProposal] = useState(false);

  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.get<ResolveSessionView>(`/v1/resolve/${sessionId}`);
      setSession(data);
      
      // Show proposal after initial load (simulating assistant response)
      setTimeout(() => setShowProposal(true), 500);
    } catch (err) {
      console.error('Failed to load session:', err);
      setError(err instanceof Error ? err.message : 'Failed to load session');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      loadSession();
    }
  }, [sessionId, loadSession]);

  const handleSendMessage = async () => {
    if (!sessionId || !replyText.trim()) return;

    setIsSending(true);
    setError(null);

    try {
      const payload: SendMessageRequest = {
        message_text: replyText,
      };

      const response = await apiClient.post<ResolveTurnResponse>(
        `/v1/resolve/${sessionId}/messages`,
        payload
      );

      // Update session with new entries
      if (session) {
        setSession({
          ...session,
          entries: [...session.entries, ...response.new_entries],
          state: response.state,
        });
      }

      setReplyText('');
    } catch (err) {
      console.error('Failed to send message:', err);
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!sessionId) return;

    setUploadedFile({
      name: file.name,
      size: file.size,
      state: 'checking',
    });

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('evidence_type', 'document');
      formData.append('display_label', file.name);

      await apiClient.post(
        `/v1/resolve/${sessionId}/evidence`,
        formData
      );

      setUploadedFile({
        name: file.name,
        size: file.size,
        state: 'done',
      });
    } catch (err) {
      console.error('Failed to upload evidence:', err);
      setError(err instanceof Error ? err.message : 'Failed to upload file');
      setUploadedFile(null);
    }
  };

  const handleConfirmProposal = async () => {
    if (!sessionId) return;

    try {
      await apiClient.post(
        `/v1/resolve/${sessionId}/confirmations`,
        { sca_reference: 'demo-sca-ref-123' }
      );

      alert('Action confirmed! In a real app, SCA verification would occur here.');
    } catch (err) {
      console.error('Failed to confirm action:', err);
      setError(err instanceof Error ? err.message : 'Failed to confirm action');
    }
  };

  const handleHumanRequest = async () => {
    if (!sessionId) return;

    try {
      await apiClient.post(`/v1/resolve/${sessionId}/human-request`, {});
      alert('Your request has been escalated to a colleague');
      navigate('/cases');
    } catch (err) {
      console.error('Failed to request human:', err);
      setError(err instanceof Error ? err.message : 'Failed to request human assistance');
    }
  };

  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#E5E7EB] flex justify-center items-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-[#0B5D5B] border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-[#4A5A60]">Loading session...</p>
        </div>
      </div>
    );
  }

  if (error && !session) {
    return (
      <div className="min-h-screen bg-[#E5E7EB] flex justify-center items-center p-4">
        <div className="bg-white border border-red-300 rounded-xl p-6 max-w-md">
          <h2 className="font-bold text-lg mb-2">Error Loading Session</h2>
          <p className="text-[#4A5A60] mb-4">{error}</p>
          <button 
            onClick={() => navigate('/')}
            className="min-h-[48px] px-6 rounded-full font-bold bg-[#0B5D5B] text-white border-2 border-[#0B5D5B] w-full"
          >
            Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#E5E7EB] flex justify-center items-start py-10">
      <div className="w-full max-w-[375px] min-h-[812px] flex flex-col bg-[#F6F2EA] border border-[#9CA3AF]">
        {/* Topbar */}
        <header className="flex-shrink-0 flex items-center gap-3 p-3 md:p-4 bg-white border-b border-[#D5CFC0] min-h-[56px]">
          <button 
            className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center border-0 bg-transparent text-[#1B2A2F] rounded-lg focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
            type="button" 
            aria-label="Back"
            onClick={() => navigate(-1)}
          >
            <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
              <path d="m15 18-6-6 6-6" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          <span className="font-bold text-lg flex-1">Get help</span>
          <span className="inline-flex items-center gap-1 text-[13px] font-semibold text-[#0B5D5B] bg-[#E0EFEE] px-2 py-1 rounded-xl">
            <svg className="w-4 h-4 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 8V4H8" strokeLinecap="round" strokeLinejoin="round"/>
              <rect width="16" height="12" x="4" y="8" rx="2"/>
              <path d="M2 14h2M20 14h2M15 13v2M9 13v2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            AI assistant
          </span>
        </header>

        {/* Content */}
        <main className="flex-1 p-4 flex flex-col gap-4 overflow-y-auto" id="main" aria-label="Conversation with the AI assistant">
          <AiDisclosure variant="inline" />
          
          <p className="self-center text-[13px] text-[#4A5A60]">Today, 09:31</p>

          {session?.entries.map((entry, idx) => (
            <TranscriptEntry
              key={idx}
              role={entry.role}
              content={entry.content_text}
              timestamp={formatTime(entry.occurred_at)}
            />
          ))}

          {/* Assistant response with steps */}
          <div className="flex flex-col gap-1 max-w-[92%]">
            <span className="text-[13px] font-bold text-[#4A5A60]">Assistant (AI)</span>
            <div className="p-3 md:p-4 rounded-2xl text-base bg-white border border-[#D5CFC0] rounded-bl-[4px]">
              <p className="mb-2">Thanks, I'm sorry this has happened. I'll look at it now and ask you for just one thing.</p>
              <ul className="list-none p-0 flex flex-col gap-2 mt-2" aria-label="What the assistant has done so far">
                {assistantSteps.map((step, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-[15px]">
                    <span className={`inline-flex items-center gap-1 text-[13px] font-bold px-2 py-[2px] rounded-[10px] whitespace-nowrap ${
                      step.status === 'done' ? 'bg-[#DDF1E4] text-[#0C5A30]' : 'bg-[#FFF0C7] text-[#5B3A00]'
                    }`}>
                      <svg className="w-4 h-4 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
                        {step.status === 'done' ? (
                          <>
                            <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
                            <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round"/>
                          </>
                        ) : (
                          <>
                            <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
                            <polyline points="12 6 12 12 16 14" strokeLinecap="round" strokeLinejoin="round"/>
                          </>
                        )}
                      </svg>
                      {step.status === 'done' ? 'Done' : 'Waiting'}
                    </span>
                    <span>{step.label}</span>
                  </li>
                ))}
              </ul>
            </div>
            <span className="text-[12px] text-[#4A5A60]">09:31</span>
          </div>

          <AssistantFindingsCard
            findings={[
              { label: 'Payment', value: 'TRDPLZ ONLINE 8841' },
              { label: 'Amount', value: '£89.99' },
              { label: 'When', value: 'Today, 09:14' },
              { label: 'Card', value: 'Ending 4821' },
              { label: 'Looks like', value: 'A payment you don\'t recognise' },
            ]}
            note="This payment is still pending, so the shop hasn't been paid in full yet."
          />

          <EvidenceUpload
            onUpload={handleFileUpload}
            uploadedFile={uploadedFile || undefined}
          />

          {showProposal && (
            <>
              <div className="flex flex-col gap-1 max-w-[92%]">
                <span className="text-[13px] font-bold text-[#4A5A60]">Assistant (AI)</span>
                <p className="p-3 md:p-4 rounded-2xl text-base bg-white border border-[#D5CFC0] rounded-bl-[4px]">
                  Thank you. I can freeze your card now so nothing else can be taken. You can unfreeze it any time.
                </p>
                <span className="text-[12px] text-[#4A5A60]">09:34</span>
              </div>

              <ProposalCard
                title="Freeze your card ending 4821?"
                description="Your card stops working for new payments straight away. Your salary and direct debits are not affected."
                scaNote="We'll check it's you first. Because this changes your card, you'll confirm with your fingerprint or app passcode."
                onConfirm={handleConfirmProposal}
                onDecline={() => setShowProposal(false)}
                disclaimer="Whether you get this money back is decided by a colleague, not by me. If you'd like that, I'll pass everything to the right team."
              />
            </>
          )}

          {error && (
            <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded">
              {error}
            </div>
          )}
        </main>

        {/* Bottombar */}
        <footer className="flex-shrink-0 p-3 md:p-4 pb-4 bg-white border-t border-[#D5CFC0] flex flex-col gap-2">
          <form className="flex gap-2 items-center" onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} aria-label="Reply to the assistant">
            <input
              id="reply"
              type="text"
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              aria-label="Type your reply to the assistant"
              autoComplete="off"
              className="flex-1 min-h-[48px] border-2 border-[#5C6B70] rounded-full px-4 bg-white text-[#1B2A2F] focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
              placeholder="Type a message..."
            />
            <button
              className="min-w-[48px] min-h-[48px] rounded-full border-0 bg-[#0B5D5B] text-white inline-flex items-center justify-center focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              type="submit"
              aria-label="Send reply"
              disabled={isSending || !replyText.trim()}
            >
              <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
                <path d="m22 2-7 20-4-9-9-4ZM22 2 11 13" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </form>
          <button
            className="flex items-center justify-center gap-2 min-h-[44px] font-bold text-[#0B5D5B] bg-transparent border-2 border-[#0B5D5B] rounded-full focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
            type="button"
            onClick={handleHumanRequest}
          >
            <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Talk to a person
          </button>
        </footer>
      </div>
    </div>
  );
}
