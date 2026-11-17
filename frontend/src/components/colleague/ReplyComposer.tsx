import { useState } from 'react';

interface ReplyComposerProps {
  onSendReply: (text: string, visibility: 'customer_and_colleague' | 'colleague_only') => Promise<void>;
  defaultText?: string;
}

export function ReplyComposer({ onSendReply, defaultText = '' }: ReplyComposerProps) {
  const [replyText, setReplyText] = useState(defaultText);
  const [visibility, setVisibility] = useState<'customer_and_colleague' | 'colleague_only'>('customer_and_colleague');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!replyText.trim() || sending) return;

    try {
      setSending(true);
      await onSendReply(replyText, visibility);
      setReplyText('');
    } catch (err) {
      console.error('Failed to send reply:', err);
    } finally {
      setSending(false);
    }
  };

  const handleSaveNote = async () => {
    if (!replyText.trim() || sending) return;

    try {
      setSending(true);
      await onSendReply(replyText, 'colleague_only');
      setReplyText('');
    } catch (err) {
      console.error('Failed to save note:', err);
    } finally {
      setSending(false);
    }
  };

  return (
    <form className="compose flex flex-col gap-s2 border-t border-line pt-s3" onSubmit={(e) => { e.preventDefault(); handleSend(); }} aria-label="Continue the conversation">
      <label htmlFor="reply" className="font-bold text-sm">
        Reply to Sam (they see this in the same conversation)
      </label>
      <textarea
        id="reply"
        name="reply"
        value={replyText}
        onChange={(e) => setReplyText(e.target.value)}
        className="w-full min-h-24 p-s3 font-[inherit] border-2 border-[#5C6B70] rounded-lg resize-none text-ink bg-surface"
        disabled={sending}
      />
      <div className="row flex gap-s3 items-center flex-wrap">
        <label htmlFor="vis" className="small text-[13px]">Who can see it</label>
        <select
          id="vis"
          name="vis"
          value={visibility}
          onChange={(e) => setVisibility(e.target.value as 'customer_and_colleague' | 'colleague_only')}
          className="min-h-10 px-s3 font-[inherit] border-2 border-[#5C6B70] rounded-lg bg-surface text-ink"
          disabled={sending}
        >
          <option value="customer_and_colleague">Customer and colleagues</option>
          <option value="colleague_only">Colleagues only (note)</option>
        </select>
        <span className="flex-1"></span>
        <button
          className="btn btn-secondary min-h-10 px-s4 rounded-[20px] font-bold inline-flex items-center justify-center gap-s2 cursor-pointer bg-surface text-primary border-2 border-primary"
          type="button"
          onClick={handleSaveNote}
          disabled={sending || !replyText.trim()}
        >
          <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect width="18" height="11" x="3" y="11" rx="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          Save as colleague-only note
        </button>
        <button
          className="btn btn-primary min-h-10 px-s4 rounded-[20px] font-bold inline-flex items-center justify-center gap-s2 cursor-pointer bg-primary text-primary-ink border-2 border-primary"
          type="submit"
          disabled={sending || !replyText.trim()}
        >
          <svg className="icon w-[18px] h-[18px]" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="m22 2-7 20-4-9-9-4Z"/>
            <path d="M22 2 11 13"/>
          </svg>
          Send reply
        </button>
      </div>
    </form>
  );
}
