import { useState } from 'react';

interface EvidenceFile {
  name: string;
  size: number;
  state: string;
}

interface EvidenceUploadProps {
  onUpload: (file: File) => void;
  uploadedFile?: EvidenceFile;
}

export function EvidenceUpload({ onUpload, uploadedFile }: EvidenceUploadProps) {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  const formatFileSize = (bytes: number): string => {
    return `${Math.round(bytes / 1024)} KB`;
  };

  return (
    <section className="bg-white border border-[#D5CFC0] rounded-xl p-4 flex flex-col gap-3" aria-labelledby="evidence-title">
      <h2 id="evidence-title" className="text-base font-bold flex items-center gap-2">
        <svg className="w-5 h-5 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        Can you share one thing?
      </h2>
      <p className="text-[15px]">A screenshot of any message, email or text you got about this payment. If you didn't get one, just tell me.</p>
      
      {!uploadedFile && (
        <label
          className={`border-2 border-dashed ${dragActive ? 'border-[#0B5D5B] bg-[#E0EFEE]' : 'border-[#5C6B70] bg-[#FBFAF6]'} rounded-xl p-4 flex items-center gap-3 min-h-[64px] cursor-pointer`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="image/png,image/jpeg,application/pdf"
            className="sr-only"
            onChange={handleFileInput}
          />
          <svg className="w-5 h-5 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span>
            Add a photo or PDF
            <br />
            <span className="text-[14px] text-[#4A5A60]">PNG, JPG or PDF, up to 10 MB</span>
          </span>
        </label>
      )}

      {uploadedFile && (
        <div className="flex items-center gap-3 p-3 border border-[#D5CFC0] rounded-xl bg-white">
          <svg className="w-5 h-5 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7ZM14 2v4a2 2 0 0 0 2 2h4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="flex-1 flex flex-col">
            <span className="font-semibold text-[15px] break-all">{uploadedFile.name}</span>
            <span className="text-[13px] text-[#4A5A60]">{formatFileSize(uploadedFile.size)} · Added just now</span>
          </span>
          <span className={`inline-flex items-center gap-1 text-[13px] font-bold px-2 py-[2px] rounded-[10px] ${
            uploadedFile.state === 'checking' ? 'bg-[#E2EEF1] text-[#0E4A5C]' : 'bg-[#DDF1E4] text-[#0C5A30]'
          }`}>
            <svg className="w-4 h-4 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
              {uploadedFile.state === 'checking' ? (
                <>
                  <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
                  <polyline points="12 6 12 12 16 14" strokeLinecap="round" strokeLinejoin="round"/>
                </>
              ) : (
                <>
                  <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="m9 12 2 2 4-4" strokeLinecap="round" strokeLinejoin="round"/>
                </>
              )}
            </svg>
            {uploadedFile.state === 'checking' ? 'Checking' : 'Done'}
          </span>
        </div>
      )}
      
      <p className="flex gap-2 items-start text-[14px] text-[#4A5A60]">
        <svg className="w-4 h-4 flex-shrink-0 fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
          <rect width="18" height="11" x="3" y="11" rx="2" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
        <span>Only you and our colleagues can see what you share. We keep it with this issue so you won't be asked again.</span>
      </p>
    </section>
  );
}
