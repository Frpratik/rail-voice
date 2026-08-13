"use client";

import { useQuery } from "@tanstack/react-query";
import { ClipboardList } from "lucide-react";
import { IssueCard } from "@/components/issues/issue-card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

export default function MyIssuesPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["issues", "mine"],
    queryFn: () => api.issues.listMine(),
  });
  const issues = data?.data.items ?? [];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        eyebrow="Citizen Submissions"
        title="My Reported Grievances"
        description="Track the real-time lifecycle and station admin updates for issues you reported."
      />

      <div className="grid gap-4">
        {isLoading &&
          Array.from({ length: 3 }).map((_, index) => (
            <IssueCardSkeleton key={index} />
          ))}

        {error && (
          <EmptyState
            title="Could not load your issues"
            description="Please check your network connection or sign in."
            action={{ label: "Try again", onClick: () => void refetch() }}
          />
        )}

        {!isLoading && !error && issues.length === 0 && (
          <EmptyState
            title="No grievances reported yet"
            description="Problems you submit will appear here with real-time status progressions."
            action={{
              label: "Report a problem",
              onClick: () => {
                window.location.href = "/report";
              },
            }}
          />
        )}

        {issues.map((issue, index) => (
          <IssueCard key={issue.id} issue={issue} index={index} />
        ))}
      </div>
    </div>
  );
}
