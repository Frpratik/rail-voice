"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { StatusBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";

/** Compact station widget for other websites to embed in an iframe. */
export default function StationEmbedPage() {
  const { code } = useParams<{ code: string }>();
  const { data: stats } = useQuery({
    queryKey: ["station-stats", code],
    queryFn: () => api.stations.stats(code),
  });
  const { data: issues } = useQuery({
    queryKey: ["embed-issues", code],
    queryFn: () => api.issues.list({ station_code: code, open_only: true, sort: "urgent", limit: 5 }),
  });
  const station = stats?.data;

  return (
    <div className="border-2 border-foreground/70 bg-card">
      <div className="bg-primary px-3 py-2 text-primary-foreground">
        <p className="text-display text-xl">{station?.name ?? code}</p>
        <p className="font-board text-xs opacity-80">
          {station ? `${station.open} open · ${station.fixed} fixed` : "Loading…"}
        </p>
      </div>
      <ul>
        {(issues?.data.items ?? []).map((issue) => (
          <li key={issue.id} className="border-t border-card-border px-3 py-2">
            <a href={`/issues/${issue.id}`} target="_blank" rel="noreferrer" className="block">
              <span className="line-clamp-1 text-sm font-medium">{issue.title ?? issue.description}</span>
              <StatusBadge status={issue.status} />
            </a>
          </li>
        ))}
      </ul>
      <a
        href={`/stations/${code}`}
        target="_blank"
        rel="noreferrer"
        className="label-caps block border-t border-card-border px-3 py-2 text-xs text-accent"
      >
        See all on RailVoice
      </a>
    </div>
  );
}
