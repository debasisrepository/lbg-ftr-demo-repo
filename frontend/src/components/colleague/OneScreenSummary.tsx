interface OneScreenSummaryProps {
  summary: string;
  status: string;
  expectedBy: string;
  routeReason: string;
  arrivalSource: string;
  classification: string;
  classificationConfidence: string;
  team: string;
  owner: string;
  callBack: string;
  summaryNote: string;
}

export function OneScreenSummary({ summary, status, expectedBy, routeReason, arrivalSource, classification, classificationConfidence, team, owner, callBack, summaryNote }: OneScreenSummaryProps) {
  return (
    <section className="panel summary bg-surface border-2 border-primary rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="sum-title">
      <h2 id="sum-title" className="text-[15px] font-bold flex items-center gap-s2">One-screen summary</h2>
      <p className="text text-base">{summary}</p>
      <p className="small text-[13px] text-muted">{summaryNote}</p>
      <dl className="facts grid grid-cols-[auto_1fr] gap-x-s3 gap-y-s2 text-sm">
        <dt className="text-muted">Status</dt>
        <dd className="m-0 font-semibold">{status}</dd>
        <dt className="text-muted">Expected by</dt>
        <dd className="m-0 font-semibold">{expectedBy}</dd>
        <dt className="text-muted">Why it came to us</dt>
        <dd className="m-0 font-semibold">{routeReason}</dd>
        <dt className="text-muted">How it arrived</dt>
        <dd className="m-0 font-semibold">{arrivalSource}</dd>
        <dt className="text-muted">Assistant read it as</dt>
        <dd className="m-0 font-semibold">{classification} ({classificationConfidence})</dd>
        <dt className="text-muted">Team</dt>
        <dd className="m-0 font-semibold">{team}</dd>
        <dt className="text-muted">Owner</dt>
        <dd className="m-0 font-semibold">{owner}</dd>
        <dt className="text-muted">Call-back</dt>
        <dd className="m-0 font-semibold">{callBack}</dd>
      </dl>
    </section>
  );
}
