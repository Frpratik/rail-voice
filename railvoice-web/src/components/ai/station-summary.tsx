"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

/** AI-written "how is this station right now" summary for passengers. */
export function StationSummary({ stationId }: { stationId: string }) {
  const { data: aiStatus } = useQuery({ queryKey: ["ai-status"], queryFn: () => api.ai.status() });
  const { data } = useQuery({
    queryKey: ["station-summary", stationId],
    queryFn: () => api.ai.stationSummary(stationId),
    enabled: !!aiStatus?.data.enabled,
    retry: false,
    staleTime: 30 * 60 * 1000,
  });
  const summary = data?.data;
  if (!summary) return null;

  return (
    <Card className="space-y-2 border-l-4 border-l-accent p-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-accent" />
        <h2 className="label-caps text-sm">Station right now</h2>
      </div>
      <p className="text-sm leading-relaxed">{summary.summary}</p>
      {summary.watch_out.length > 0 && (
        <ul className="space-y-1 text-sm">
          {summary.watch_out.map((item) => (
            <li key={item} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 bg-primary" />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
      <p className="text-[11px] text-muted-foreground">
        Summarised by AI from passenger reports, {formatRelativeTime(summary.generated_at)}.
      </p>
    </Card>
  );
}
