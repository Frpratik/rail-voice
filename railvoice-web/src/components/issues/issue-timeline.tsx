import { StatusBadge } from "@/components/ui/badge";
import type { TimelineEvent } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

export function IssueTimeline({ events }: { events: TimelineEvent[] }) {
  if (!events.length) {
    return (
      <p className="rounded-xl bg-muted/50 px-4 py-6 text-center text-sm text-muted-foreground">
        No timeline events yet. Updates will appear here as work progresses.
      </p>
    );
  }

  return (
    <ol className="relative space-y-0" aria-label="Issue timeline">
      {events.map((event, i) => {
        const isLatest = i === events.length - 1;
        return (
          <li key={event.id} className="relative flex gap-4 pb-8 last:pb-0">
            {i < events.length - 1 && (
              <span className="absolute left-[9px] top-5 h-[calc(100%-8px)] w-px bg-gradient-to-b from-border to-transparent" />
            )}
            <span
              className={`relative z-10 mt-1.5 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full ring-4 ring-background ${
                isLatest
                  ? "bg-accent shadow-[0_0_0_4px_var(--glow)]"
                  : "bg-muted-foreground/35"
              }`}
            >
              {isLatest && (
                <span className="h-1.5 w-1.5 rounded-full bg-accent-foreground" />
              )}
            </span>
            <div className="min-w-0 flex-1 pt-0.5">
              <div className="flex flex-wrap items-center gap-2">
                {event.to_status && <StatusBadge status={event.to_status} />}
                <time className="text-xs text-muted-foreground">
                  {formatRelativeTime(event.created_at)}
                </time>
              </div>
              {event.remarks && (
                <p className="mt-2 text-sm leading-relaxed text-foreground/90">
                  {event.remarks}
                </p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
