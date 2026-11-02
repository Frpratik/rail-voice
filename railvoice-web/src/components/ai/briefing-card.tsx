"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Sparkles } from "lucide-react";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

function Section({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="label-caps mb-1.5 text-xs text-muted-foreground">{title}</p>
      <ul className="space-y-1.5 text-sm">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 bg-primary" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** AI start-of-shift briefing on the control-room dashboard. */
export function BriefingCard() {
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);
  const { data, isLoading, error } = useQuery({
    queryKey: ["ai-briefing"],
    queryFn: () => api.ai.briefing(),
    retry: false,
    staleTime: 10 * 60 * 1000,
  });

  const refresh = async () => {
    setRefreshing(true);
    try {
      const res = await api.ai.briefing(true);
      queryClient.setQueryData(["ai-briefing"], res);
    } finally {
      setRefreshing(false);
    }
  };

  const brief = data?.data;

  return (
    <Card className="space-y-4 border-t-4 border-t-accent">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-accent" />
          <h2 className="text-display text-2xl">Today&apos;s briefing</h2>
        </div>
        <button
          type="button"
          onClick={() => void refresh()}
          disabled={refreshing || isLoading}
          aria-label="Refresh briefing"
          className="label-caps inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-16" />
        </div>
      ) : error || !brief ? (
        <p className="text-sm text-muted-foreground">The briefing isn&apos;t available right now.</p>
      ) : (
        <>
          <p className="text-base font-medium">{brief.headline}</p>
          <Section title="Do first" items={brief.urgent} />
          <Section title="Patterns" items={brief.patterns} />
          <Section title="Suggested next steps" items={brief.suggestions} />
          <p className="text-xs text-muted-foreground">
            Written by AI from {brief.open_count} open reports
            {brief.generated_at && `, ${formatRelativeTime(brief.generated_at)}`}. Check before acting.
          </p>
        </>
      )}
    </Card>
  );
}
