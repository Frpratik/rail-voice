"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { StatusBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { Issue } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

const WINDOWS = [8, 12, 24];

function IssueList({ title, issues, empty }: { title: string; issues: Issue[]; empty: string }) {
  return (
    <section className="min-w-0">
      <h2 className="text-display mb-3 text-2xl">
        {title} <span className="font-board text-base text-muted-foreground">{issues.length}</span>
      </h2>
      {issues.length === 0 ? (
        <Card className="p-4 text-sm text-muted-foreground">{empty}</Card>
      ) : (
        <div className="space-y-2">
          {issues.map((issue) => (
            <Link key={issue.id} href={`/issues/${issue.id}`} className="block">
              <Card className="p-3 transition-colors hover:border-foreground/60">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-board text-xs text-muted-foreground">
                    {issue.location.station.code} · {issue.issue_number}
                  </span>
                  <StatusBadge status={issue.status} />
                </div>
                <p className="mt-1 font-medium leading-snug">{issue.title ?? issue.description}</p>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

export default function AdminHandoverPage() {
  const [hours, setHours] = useState(12);
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-handover", hours],
    queryFn: () => api.admin.handover(hours),
    retry: false,
  });
  const report = data?.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Shift handover"
        title="What the next shift needs"
        description="New reports, anything past its target time, and recent activity in your stations."
        action={
          <div className="flex gap-1">
            {WINDOWS.map((w) => (
              <button
                key={w}
                type="button"
                onClick={() => setHours(w)}
                className={cn(
                  "label-caps border-2 px-3 py-1.5 text-xs",
                  hours === w
                    ? "border-primary bg-primary text-primary-foreground"
                    : "border-foreground/30 text-muted-foreground"
                )}
              >
                {w}h
              </button>
            ))}
          </div>
        }
      />

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : error || !report ? (
        <EmptyState title="Couldn't load the handover" description="You may need a staff account." />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <IssueList title="Overdue" issues={report.overdue} empty="Nothing is past its target time." />
          <IssueList
            title={`New in ${hours}h`}
            issues={report.new_reports}
            empty="No new reports in this period."
          />
          <section className="min-w-0 lg:col-span-2">
            <h2 className="text-display mb-3 text-2xl">Recent activity</h2>
            <Card className="p-0">
              {report.activity.length === 0 && (
                <p className="p-4 text-sm text-muted-foreground">No activity in this period.</p>
              )}
              <ul>
                {report.activity.map((a, i) => (
                  <li key={i} className="border-b border-card-border px-4 py-2.5 text-sm last:border-0">
                    <span className="label-caps text-xs text-muted-foreground">
                      {a.type.replace(/_/g, " ")}
                      {a.at && ` · ${formatRelativeTime(a.at)}`}
                    </span>
                    {a.remarks && <p className="mt-0.5">{a.remarks}</p>}
                  </li>
                ))}
              </ul>
            </Card>
          </section>
        </div>
      )}
    </div>
  );
}
