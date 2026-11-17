import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import { OneScreenSummary } from '../components/colleague/OneScreenSummary';
import { HandlingIndicators } from '../components/colleague/HandlingIndicators';
import { ColleagueWorklist } from '../components/colleague/ColleagueWorklist';
import { TranscriptPanel } from '../components/colleague/TranscriptPanel';
import { ReplyComposer } from '../components/colleague/ReplyComposer';
import { EvidencePanel } from '../components/colleague/EvidencePanel';
import { TimelinePanel } from '../components/colleague/TimelinePanel';
import type { HandoffPackResponse, ThreadResponse, ColleagueReplyRequest, TranscriptEntryResponse } from '../types/colleague';

export function ColleagueCasePage() {
  const { caseId } = useParams<{ caseId: string }>();
  const [handoffPack, setHandoffPack] = useState<HandoffPackResponse | null>(null);
  const [thread, setThread] = useState<TranscriptEntryResponse[]>([]);
  const [threadTotal, setThreadTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!caseId) {
        setError('No case ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const [pack, threadData] = await Promise.all([
          apiClient.get<HandoffPackResponse>(`/v1/colleague/cases/${caseId}`),
          apiClient.get<ThreadResponse>(`/v1/colleague/cases/${caseId}/thread?page=1&page_size=100`)
        ]);

        setHandoffPack(pack);
        setThread(threadData.entries);
        setThreadTotal(threadData.total);
      } catch (err) {
        console.error('Failed to fetch colleague case:', err);
        setError(err instanceof Error ? err.message : 'Failed to load case');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [caseId]);

  const handleSendReply = async (text: string, visibility: 'customer_and_colleague' | 'colleague_only') => {
    if (!caseId) return;

    try {
      const payload: ColleagueReplyRequest = {
        content_text: text,
        visibility_scope: visibility
      };
      
      const newEntry = await apiClient.post<TranscriptEntryResponse>(
        `/v1/colleague/cases/${caseId}/thread/entries`,
        payload
      );
      
      setThread(prev => [...prev, newEntry]);
      setThreadTotal(prev => prev + 1);
    } catch (err) {
      console.error('Failed to send reply:', err);
      throw err;
    }
  };

  const handleRequestEvidence = async (label: string, why: string) => {
    if (!caseId) return;

    try {
      await apiClient.post(`/v1/colleague/cases/${caseId}/evidence-requests`, {
        display_label: label,
        evidence_type: 'document'
      });
    } catch (err) {
      console.error('Failed to request evidence:', err);
      throw err;
    }
  };

  const handlePickup = async () => {
    if (!caseId || !handoffPack) return;

    try {
      await apiClient.post(`/v1/colleague/cases/${caseId}/pickup`, {
        colleague_user_id: 'current-user-id' // In real app, get from auth context
      });
      
      // Refresh handoff pack
      const updatedPack = await apiClient.get<HandoffPackResponse>(`/v1/colleague/cases/${caseId}`);
      setHandoffPack(updatedPack);
    } catch (err) {
      console.error('Failed to pick up case:', err);
    }
  };

  const formatDateTime = (isoString?: string) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    const today = new Date();
    
    if (date.toDateString() === today.toDateString()) {
      return `Today, ${date.toLocaleTimeString('en-GB', { hour: 'numeric', minute: '2-digit' }).toLowerCase()}`;
    }
    return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }).toLowerCase();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <p className="text-muted">Loading case...</p>
      </div>
    );
  }

  if (error || !handoffPack) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <p className="text-muted">{error || 'Case not found'}</p>
      </div>
    );
  }

  const indicators = [
    {
      type: 'risk' as const,
      title: 'Fraud timing applies',
      description: 'Customer is waiting on a decision. The clock is shown to them in plain English.'
    },
    {
      type: 'warn' as const,
      title: 'Handling adjustments: needs time',
      description: "Customer noted they find phone calls stressful. Prefer in-app messages. Don't ask them to repeat the story."
    }
  ];

  return (
    <div className="page w-full min-w-[1440px] bg-paper">
      {/* Topbar */}
      <header className="topbar flex items-center gap-s5 p-s3 px-s5 bg-[#14343A] text-white min-h-[56px]">
        <span className="brand font-bold text-base">Colleague desktop</span>
        <nav className="crumbs flex-1 text-sm text-[#D4E4E6]" aria-label="Breadcrumb">
          <a href="#worklist" className="text-white">My team's cases</a> / Case {handoffPack.case_ref}
        </nav>
        <span className="who flex items-center gap-s2 text-sm">
          <span className="avatar w-8 h-8 rounded-2xl bg-[#E0EFEE] text-[#14343A] font-bold inline-flex items-center justify-center" aria-hidden="true">PN</span>
          Priya Nair · {handoffPack.owner_team_display || 'Card fraud team'}
        </span>
      </header>

      {/* Case head */}
      <section className="casehead flex items-center gap-s4 p-s4 px-s5 bg-surface border-b border-line" aria-label="Case header">
        <div>
          <h1 className="font-head text-[26px] leading-tight">{handoffPack.problem_statement}</h1>
          <p className="ref text-sm text-muted">
            Case {handoffPack.case_ref} · Customer: {handoffPack.customer_display_name || 'Customer'} · {handoffPack.brand || 'Lloyds'} · Opened {formatDateTime(handoffPack.opened_at)}
          </p>
        </div>
        <span className="grow flex-1"></span>
        <span className="badge b-info inline-flex items-center gap-s1 text-[13px] font-bold py-0.5 px-s3 rounded-xl whitespace-nowrap bg-info-bg text-info-ink">
          <svg className="icon-sm w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
            <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
          </svg>
          Status: {handoffPack.status_code}
        </span>
        <span className="badge b-risk inline-flex items-center gap-s1 text-[13px] font-bold py-0.5 px-s3 rounded-xl whitespace-nowrap bg-risk-bg text-risk-ink">
          <svg className="icon-sm w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/>
            <path d="M12 9v4"/>
            <path d="M12 17h.01"/>
          </svg>
          Fraud timing applies
        </span>
        <span className="badge b-warn inline-flex items-center gap-s1 text-[13px] font-bold py-0.5 px-s3 rounded-xl whitespace-nowrap bg-warn-bg text-warn-ink">
          <svg className="icon-sm w-3.5 h-3.5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
          </svg>
          Handling adjustments
        </span>
        <button
          className="btn btn-primary min-h-10 px-s4 rounded-[20px] font-bold inline-flex items-center justify-center gap-s2 cursor-pointer bg-primary text-primary-ink border-2 border-primary"
          type="button"
          onClick={handlePickup}
        >
          <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 11V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2"/>
            <path d="M14 10V4a2 2 0 0 0-2-2a2 2 0 0 0-2 2v2"/>
            <path d="M10 10.5V6a2 2 0 0 0-2-2a2 2 0 0 0-2 2v8"/>
            <path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-5.99-2.34l-3.6-3.6a2 2 0 0 1 2.83-2.82L7 15"/>
          </svg>
          Pick up this case
        </button>
      </section>

      {/* Three-column layout */}
      <main className="layout grid grid-cols-[320px_1fr_380px] gap-s5 p-s5 items-start" id="main">
        {/* Left column */}
        <div className="col flex flex-col gap-s4" aria-label="Summary">
          <OneScreenSummary
            summary={handoffPack.handoff_summary_text || handoffPack.problem_statement}
            status={handoffPack.status_code}
            expectedBy={formatDateTime(handoffPack.expected_by_at)}
            routeReason={handoffPack.route_reason || 'Customer asked for a person. A reimbursement decision needs a human.'}
            arrivalSource={handoffPack.arrival_source || 'Assistant escalation, in the app'}
            classification={handoffPack.classification_code || 'Unrecognised card payment'}
            classificationConfidence="92% sure"
            team={handoffPack.owner_team_display || 'Card fraud team'}
            owner={handoffPack.owner_colleague_display || 'Not yet picked up'}
            callBack="None requested"
            summaryNote="Summary v2 · covers messages 1 to 8 · written by the assistant at 09:41"
          />

          <HandlingIndicators indicators={indicators} />

          <ColleagueWorklist
            items={[
              { caseRef: handoffPack.case_ref, title: 'Unrecognised payment', detail: `Expected by ${formatDateTime(handoffPack.expected_by_at)} · New`, isActive: true },
              { caseRef: 'CP-20391', title: 'Card not received', detail: 'Expected by tomorrow 12:00 · Owner: Daniel' },
              { caseRef: 'CP-20366', title: 'Declined abroad', detail: 'Expected by today 5:00pm · Owner: Aisha' }
            ]}
            total={3}
          />
        </div>

        {/* Center column */}
        <div className="col flex flex-col gap-s4" aria-label="Conversation">
          <TranscriptPanel entries={thread} total={threadTotal} />
          <ReplyComposer
            onSendReply={handleSendReply}
            defaultText="Hi Sam, it's Priya from our card fraud team. I've read everything you've told us, so there's nothing to repeat. I'm checking the merchant now and I'll update you here by 3pm."
          />
        </div>

        {/* Right column */}
        <div className="col flex flex-col gap-s4" aria-label="Evidence and actions">
          <section className="panel bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="cp-title">
            <h2 id="cp-title" className="text-[15px] font-bold flex items-center gap-s2">
              <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 8V4H8"/>
                <rect width="16" height="12" x="4" y="8" rx="2"/>
                <path d="M2 14h2"/>
                <path d="M20 14h2"/>
                <path d="M15 13v2"/>
                <path d="M9 13v2"/>
              </svg>
              Suggested next step
            </h2>
            <div className="copilot bg-[#F3F8F8] border border-dashed border-primary rounded-lg p-s3 text-sm flex flex-col gap-s1">
              <span className="lab font-bold text-primary text-[13px]">Drafted by the Colleague Copilot. Assistance only; you decide.</span>
              <p>{handoffPack.copilot_note || 'Check whether the merchant has been reported before. If the text is a phishing message, record it before replying. Reimbursement is a human decision.'}</p>
            </div>
          </section>

          <EvidencePanel
            items={[
              { name: 'Screenshot_0912_text-message.png', detail: 'Customer · 412 KB · Received 09:33', status: 'checked' },
              { name: 'Bank statement, last 30 days', detail: 'Requested by you · Not yet sent', status: 'waiting' }
            ]}
            onRequestEvidence={handleRequestEvidence}
          />

          <TimelinePanel
            events={[
              { text: 'Priya Nair opened this case', time: '09:50', isHollow: true },
              { text: 'Case routed to Card fraud team', time: '09:41' },
              { text: 'Card ending 4821 frozen', time: '09:37' },
              { text: 'Screenshot received', time: '09:33' },
              { text: 'Customer described the problem', time: '09:31' }
            ]}
          />
        </div>
      </main>
    </div>
  );
}
