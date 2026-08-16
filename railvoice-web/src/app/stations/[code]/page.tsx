"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Inbox } from "lucide-react";
import { IssueCard } from "@/components/issues/issue-card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

export default function StationPage() {
  const { code } = useParams<{ code: string }>();

  const { data: stationData } = useQuery({
    queryKey: ["station", code],
    queryFn: () => api.stations.get(code),
    enabled: !!code,
  });

  const { data: issuesData, isLoading } = useQuery({
    queryKey: ["issues", "station", code],
    queryFn: () => api.issues.list({ station_code: code, limit: 30 }),
    enabled: !!code,
  });

  const station = stationData?.data;
  const issues = issuesData?.data.items ?? [];

  return (
    <div className="space-y-8">
      <Link
        href="/stations"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        All stations
      </Link>

      <PageHeader
        eyebrow={station?.code ?? code}
        title={station?.name ?? code}
        description={`${station?.open_issue_count ?? 0} open issues at this station`}
      />

      <div className="grid gap-4">
        {isLoading &&
          Array.from({ length: 3 }).map((_, i) => <IssueCardSkeleton key={i} />)}
        {!isLoading && issues.length === 0 && (
          <EmptyState
            icon={Inbox}
            title="No issues here yet"
            description="This station looks clear. Report if you spot something that needs attention."
            actionLabel="Report an issue"
            actionHref="/report"
          />
        )}
        {issues.map((issue, i) => (
          <IssueCard key={issue.id} issue={issue} index={i} />
        ))}
      </div>
    </div>
  );
}
