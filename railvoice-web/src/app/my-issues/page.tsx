"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { IssueCard } from "@/components/issues/issue-card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function MyIssuesPage() {
  const [tab, setTab] = useState<"mine" | "following">("mine");

  const mine = useQuery({
    queryKey: ["issues", "mine"],
    queryFn: () => api.issues.listMine(),
  });
  const following = useQuery({
    queryKey: ["issues", "following"],
    queryFn: () => api.me.following(),
    enabled: tab === "following",
  });

  const active = tab === "mine" ? mine : following;
  const issues = active.data?.data.items ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Your reports"
        title="My issues"
        description="Track what you reported, and the reports you follow."
      />

      <div className="flex gap-1">
        {(
          [
            { value: "mine", label: "Reported by me" },
            { value: "following", label: "Following" },
          ] as const
        ).map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => setTab(t.value)}
            className={cn(
              "label-caps border-2 px-3 py-1.5 text-xs",
              tab === t.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-foreground/30 text-muted-foreground"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid gap-4">
        {active.isLoading &&
          Array.from({ length: 3 }).map((_, index) => <IssueCardSkeleton key={index} />)}

        {active.error && (
          <EmptyState
            title="Could not load your issues"
            description="Please check your network connection or sign in."
            action={{ label: "Try again", onClick: () => void active.refetch() }}
          />
        )}

        {!active.isLoading && !active.error && issues.length === 0 && (
          <EmptyState
            title={tab === "mine" ? "Nothing reported yet" : "Not following anything yet"}
            description={
              tab === "mine"
                ? "Problems you report will appear here with their status."
                : "Follow a report to get an update whenever its status changes."
            }
            action={{ label: tab === "mine" ? "Report a problem" : "Browse reports", href: tab === "mine" ? "/report" : "/" }}
          />
        )}

        {issues.map((issue, index) => (
          <IssueCard key={issue.id} issue={issue} index={index} />
        ))}
      </div>
    </div>
  );
}
