import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import { CaseHero } from '../components/cases/CaseHero';
import { ThreePanel } from '../components/cases/ThreePanel';
import { ChecklistCard } from '../components/cases/ChecklistCard';
import { MyCasesList } from '../components/cases/MyCasesList';
import type { CaseListItem, CaseListResponse, CaseDetailResponse } from '../types/cases';

export function CaseConfirmationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const caseId = searchParams.get('caseId');
  const [caseDetail, setCaseDetail] = useState<CaseDetailResponse | null>(null);
  const [allCases, setAllCases] = useState<CaseListItem[]>([]);
  const [totalCases, setTotalCases] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!caseId) {
        // No case ID provided, redirect to My Cases
        navigate('/cases', { replace: true });
        return;
      }

      try {
        setLoading(true);
        
        // Fetch case detail and all cases in parallel
        const [detail, casesResponse] = await Promise.all([
          apiClient.get<CaseDetailResponse>(`/v1/cases/${caseId}`),
          apiClient.get<CaseListResponse>('/v1/cases?limit=50&offset=0')
        ]);

        setCaseDetail(detail);
        setAllCases(casesResponse.items);
        setTotalCases(casesResponse.total);
      } catch (err) {
        console.error('Failed to fetch case data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch case data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [caseId, navigate]);

  const formatExpectedBy = (isoString?: string) => {
    if (!isoString) return 'To be determined';
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
        <p className="text-muted" role="status">Loading case confirmation...</p>
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center">
        <p className="text-muted" role="alert">{error || 'Failed to fetch case'}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper">
      {/* Topbar */}
      <header className="topbar flex items-center gap-s3 p-s3 px-s4 bg-surface border-b border-line min-h-[56px]">
        <button
          type="button"
          className="icon-btn min-w-[44px] min-h-[44px] inline-flex items-center justify-center border-0 bg-transparent text-ink rounded-lg"
          aria-label="Back to the conversation"
          onClick={() => navigate(-1)}
        >
          <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m15 18-6-6 6-6"/>
          </svg>
        </button>
        <span className="title font-bold text-lg flex-1">Your case</span>
      </header>

      {/* Main content */}
      <main className="content p-s4 flex flex-col gap-s4 max-w-[375px] mx-auto" id="main">
        <CaseHero
          title="We've passed this to our team"
          message="You asked to talk to a person, so we've set up a case and sent them everything. You won't need to explain it again."
        />

        <ThreePanel
          owner={{
            team: caseDetail.owner_team_display || 'Our team',
            note: "A named colleague will pick it up and you'll see their first name here."
          }}
          nextUpdate={{
            time: formatExpectedBy(caseDetail.expected_by_at),
            note: "If anything changes before then, we'll tell you."
          }}
          whatWeKnow={{
            summary: caseDetail.problem_statement || 'Your case',
            detail: caseDetail.route_reason || 'We are looking into this for you.'
          }}
        />

        <ChecklistCard
          items={[
            { icon: 'check', label: 'What you told us, in your own words' },
            { icon: 'check', label: 'The payment you picked' },
            { icon: 'paperclip', label: 'Your screenshot (Screenshot_0912_text-message.png)' },
            { icon: 'msg', label: 'This whole conversation so far' }
          ]}
        />

        <div className="callout flex gap-s3 p-s3 px-s4 bg-info-bg text-info-ink rounded-xl text-[15px]">
          <svg className="icon w-5 h-5 flex-shrink-0" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
          </svg>
          <p>Would you rather have a call than messages? Tell the team here and they'll offer you a time. The case stays the same.</p>
        </div>

        <MyCasesList
          cases={allCases}
          total={totalCases}
          highlightCaseId={caseId || undefined}
        />

        <div className="flex flex-col gap-s2">
          <button
            className="btn btn-primary min-h-12 px-s4 rounded-3xl font-bold inline-flex items-center justify-center gap-s2 w-full cursor-pointer bg-primary text-primary-ink border-2 border-primary"
            type="button"
            onClick={() => navigate(`/cases/${caseId}`)}
          >
            <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Open the conversation
          </button>
          <button
            className="btn btn-secondary min-h-12 px-s4 rounded-3xl font-bold inline-flex items-center justify-center gap-s2 w-full cursor-pointer bg-surface text-primary border-2 border-primary"
            type="button"
          >
            <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
            I'd like a call-back
          </button>
        </div>
        
        <p className="small text-sm text-muted">We'll send you a short message when there's an update. It won't include any details. Open the app to read it.</p>
      </main>

      {/* Bottom nav */}
      <nav className="bottombar p-s2 pb-s3 bg-surface border-t border-line flex justify-around" aria-label="Main navigation">
        <button 
          className="tab min-w-[72px] min-h-12 flex flex-col items-center justify-center gap-0.5 text-xs font-semibold text-muted border-0 bg-transparent rounded-lg" 
          type="button"
          onClick={() => navigate('/')}
        >
          <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
            <polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          <span>Home</span>
        </button>
        <button 
          className="tab min-w-[72px] min-h-12 flex flex-col items-center justify-center gap-0.5 text-xs font-semibold text-primary border-0 bg-transparent rounded-lg" 
          type="button" 
          aria-current="page"
          onClick={() => navigate('/cases')}
        >
          <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
          </svg>
          <span className="underline underline-offset-[3px]">My Cases</span>
        </button>
        <button 
          className="tab min-w-[72px] min-h-12 flex flex-col items-center justify-center gap-0.5 text-xs font-semibold text-muted border-0 bg-transparent rounded-lg" 
          type="button"
          onClick={() => navigate('/resolve')}
        >
          <svg className="icon w-5 h-5" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
            <path d="M12 17h.01"/>
          </svg>
          <span>Get help</span>
        </button>
      </nav>
    </div>
  );
}
