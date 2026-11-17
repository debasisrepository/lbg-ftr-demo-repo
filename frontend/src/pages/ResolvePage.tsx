import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import type { StartResolveRequest, ResolveTurnResponse } from '../types/resolve';
import { AiDisclosure } from '../components/resolve/AiDisclosure';
import { HumanPathButton } from '../components/resolve/HumanPathButton';
import { StatusContextCard } from '../components/resolve/StatusContextCard';
import { TransactionPicker } from '../components/resolve/TransactionPicker';

interface MockTransaction {
  id: string;
  merchant_name: string;
  amount: number;
  date: string;
  card_last_four: string;
  status?: string;
}

export function ResolvePage() {
  const navigate = useNavigate();
  const [messageText, setMessageText] = useState('A payment of £89.99 to a shop I don\'t recognise came out of my account this morning. I haven\'t bought anything from them and my card is still in my wallet.');
  const [selectedTxnId, setSelectedTxnId] = useState('txn-1');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock transactions for demo (would come from API in real app)
  const mockTransactions: MockTransaction[] = [
    { id: 'txn-1', merchant_name: 'TRDPLZ ONLINE 8841', amount: 89.99, date: 'Today, 09:14', card_last_four: '4821', status: 'Pending' },
    { id: 'txn-2', merchant_name: 'Corner Café, Leeds', amount: 4.20, date: 'Yesterday, 08:02', card_last_four: '4821' },
    { id: 'txn-3', merchant_name: 'British Gas, payment didn\'t go through', amount: 62.10, date: 'Yesterday, 17:45', card_last_four: '4821' },
  ];

  const selectedTransaction = mockTransactions.find(t => t.id === selectedTxnId);

  const handleSubmit = async () => {
    if (!messageText.trim() || messageText.length < 1 || messageText.length > 4000) {
      setError('Please enter a message between 1 and 4000 characters');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload: StartResolveRequest = {
        message_text: messageText,
        entry_context_type: selectedTxnId ? 'transaction' : undefined,
        entry_context_ref: selectedTxnId || undefined,
        status_context_shown: true,
      };

      const response = await apiClient.post<ResolveTurnResponse>('/v1/resolve', payload);
      
      // Navigate to session page
      navigate(`/resolve/${response.session_id}`);
    } catch (err) {
      console.error('Failed to start resolve session:', err);
      setError(err instanceof Error ? err.message : 'Failed to start session');
      setIsSubmitting(false);
    }
  };

  const handleHumanRequest = () => {
    // In real app, would navigate to colleague contact flow
    alert('Talk to a person flow would be initiated here');
  };

  const charCount = messageText.length;

  return (
    <div className="min-h-screen bg-[#E5E7EB] flex justify-center items-start py-10">
      <div className="w-full max-w-[375px] min-h-[812px] flex flex-col bg-[#F6F2EA] border border-[#9CA3AF]">
        {/* Topbar */}
        <header className="flex-shrink-0 flex items-center gap-3 p-3 md:p-4 bg-white border-b border-[#D5CFC0] min-h-[56px]">
          <button 
            className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center border-0 bg-transparent text-[#1B2A2F] rounded-lg focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
            type="button" 
            aria-label="Back to the app home"
            onClick={() => navigate('/')}
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
        <main className="flex-1 p-4 flex flex-col gap-4" id="main">
          <AiDisclosure />

          <StatusContextCard
            title="We have a problem with payments right now."
            message="Your money is safe. Salary credits are unaffected. We'll update you by 3pm."
            lastUpdated="08:42 today"
            linkText="See the latest update"
            onLinkClick={() => {}}
          />

          <section className="flex flex-col gap-2">
            <h1 className="font-serif text-[28px] leading-tight">What's gone wrong?</h1>
            <p className="text-[#4A5A60] text-base">Tell us in your own words. We'll ask for what we need once, so you won't have to repeat yourself.</p>
          </section>

          <form className="flex flex-col gap-4" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
            <TransactionPicker
              transactions={mockTransactions}
              selectedId={selectedTxnId}
              onSelect={setSelectedTxnId}
            />

            <div className="flex flex-col">
              <label htmlFor="problem" className="block font-bold mb-2">Describe the problem</label>
              <textarea
                id="problem"
                name="problem"
                maxLength={4000}
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                aria-describedby="problem-help problem-count"
                className="w-full min-h-[132px] p-3 text-[#1B2A2F] bg-white border-2 border-[#5C6B70] rounded-lg resize-none focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2"
              />
              {selectedTransaction && (
                <span className="inline-flex items-center gap-2 mt-2 px-3 py-1 bg-[#E0EFEE] text-[#083F3D] rounded-2xl text-[14px] font-semibold self-start">
                  <svg className="w-4 h-4 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
                    <rect width="20" height="14" x="2" y="5" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="2" x2="22" y1="10" y2="10" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Attached: {selectedTransaction.merchant_name}, £{selectedTransaction.amount.toFixed(2)}
                </span>
              )}
              <div className="flex justify-between gap-3 text-[14px] text-[#4A5A60] mt-1">
                <span id="problem-help">Please don't type full card numbers or passwords.</span>
                <span id="problem-count">{charCount} of 4,000</span>
              </div>
            </div>

            <section className="bg-white border border-[#D5CFC0] rounded-xl p-4 flex flex-col gap-3" aria-labelledby="next-title">
              <h2 id="next-title" className="text-base font-bold">What happens when you send this</h2>
              <ul className="p-0 m-0 list-none flex flex-col gap-2">
                <li className="flex gap-3 text-[15px]">
                  <svg className="w-5 h-5 text-[#0B5D5B] mt-[2px] flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1zM9 12l2 2 4-4" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>We check what we can see on your account and tell you what we find.</span>
                </li>
                <li className="flex gap-3 text-[15px]">
                  <svg className="w-5 h-5 text-[#0B5D5B] mt-[2px] flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <span>If we can sort it here, we'll say so. If not, a colleague gets everything you've told us.</span>
                </li>
              </ul>
            </section>

            {error && (
              <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <p className="text-[14px] text-[#4A5A60]">
              Want to report fraud or make a complaint? You can do that right here. It takes no extra steps. <a href="#talk" onClick={(e) => { e.preventDefault(); handleHumanRequest(); }} className="text-[#0B5D5B] font-semibold">Talk to a person</a>
            </p>
          </form>
        </main>

        {/* Bottombar */}
        <footer className="flex-shrink-0 p-3 md:p-4 pb-4 bg-white border-t border-[#D5CFC0] flex flex-col gap-2">
          <button 
            className="min-h-[48px] px-4 md:px-6 rounded-full font-bold inline-flex items-center justify-center gap-2 w-full bg-[#0B5D5B] text-white border-2 border-[#0B5D5B] focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#1F6FEB] focus-visible:outline-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !messageText.trim()}
          >
            <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
              <path d="m22 2-7 20-4-9-9-4ZM22 2 11 13" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            {isSubmitting ? 'Sending...' : 'Send to the assistant'}
          </button>
          <HumanPathButton onClick={handleHumanRequest} />
        </footer>
      </div>
    </div>
  );
}
