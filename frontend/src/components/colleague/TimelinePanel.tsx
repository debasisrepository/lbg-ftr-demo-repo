interface TimelineEvent {
  text: string;
  time: string;
  isHollow?: boolean;
}

interface TimelinePanelProps {
  events: TimelineEvent[];
}

export function TimelinePanel({ events }: TimelinePanelProps) {
  return (
    <section className="panel bg-surface border border-line rounded-xl p-s4 flex flex-col gap-s3" aria-labelledby="tl-title">
      <h2 id="tl-title" className="text-[15px] font-bold flex items-center gap-s2">Case history</h2>
      <ul className="tl list-none p-0 flex flex-col gap-s3">
        {events.map((event, index) => (
          <li key={index} className="flex gap-s3 text-sm">
            <span className={`dot ${event.isHollow ? 'hollow border-2 border-primary bg-surface' : 'bg-primary'} w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0`}></span>
            <div>
              {event.text}
              <time className="block text-xs text-muted">{event.time}</time>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
