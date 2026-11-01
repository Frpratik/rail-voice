"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import type { FlagItem } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";

const REASON_LABEL: Record<string, string> = {
  spam: "Spam or advertising",
  abuse: "Abusive or offensive",
  false_report: "False or made up",
  duplicate: "Duplicate",
  other: "Other",
};

export default function AdminFlagsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["admin-flags"],
    queryFn: () => api.admin.flags(),
  });

  const resolve = useMutation({
    mutationFn: (vars: { id: string; action: "dismiss" | "hide" }) =>
      api.admin.resolveFlag(vars.id, { action: vars.action }),
    onSuccess: (_, vars) => {
      toast.success(vars.action === "hide" ? "Removed from public view" : "Flag dismissed");
      queryClient.invalidateQueries({ queryKey: ["admin-flags"] });
      queryClient.invalidateQueries({ queryKey: ["admin-dashboard"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  // Several passengers may flag the same thing; show it once with a count.
  const groups = new Map<string, { first: FlagItem; count: number; reasons: Set<string> }>();
  for (const flag of data?.data.items ?? []) {
    const key = `${flag.issue.id}:${flag.target}:${flag.comment_body ?? ""}`;
    const group = groups.get(key);
    if (group) {
      group.count += 1;
      group.reasons.add(flag.reason);
    } else {
      groups.set(key, { first: flag, count: 1, reasons: new Set([flag.reason]) });
    }
  }
  const rows = [...groups.values()].sort((a, b) => b.count - a.count);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Moderation"
        title="Flagged reports"
        description="Reports and comments that passengers flagged. Hide what breaks the rules, dismiss what doesn't."
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : error ? (
        <EmptyState
          title="Couldn't load flags"
          description="Check your connection and try again."
          action={{ label: "Try again", onClick: () => refetch() }}
        />
      ) : rows.length === 0 ? (
        <EmptyState title="Nothing flagged" description="No open flags in your stations." />
      ) : (
        <div className="space-y-4">
          {rows.map(({ first, count, reasons }) => (
            <Card key={first.id} className="space-y-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="label-caps text-xs text-muted-foreground">
                    {first.target === "comment" ? "Comment on" : "Report"} ·{" "}
                    <span className="font-board">{first.issue.issue_number}</span> ·{" "}
                    {first.issue.station}
                  </p>
                  <Link
                    href={`/issues/${first.issue.id}`}
                    target="_blank"
                    className="text-display text-xl hover:underline"
                  >
                    {first.issue.title ?? "Untitled report"}
                  </Link>
                </div>
                <StatusBadge status={first.issue.status} />
              </div>

              {first.comment_body && (
                <blockquote className="border-l-4 border-foreground/40 bg-muted/60 px-3 py-2 text-sm">
                  {first.comment_body}
                </blockquote>
              )}

              <p className="text-sm text-muted-foreground">
                <strong className="font-board text-foreground">{count}</strong>{" "}
                {count === 1 ? "passenger" : "passengers"} flagged this as{" "}
                {[...reasons].map((r) => REASON_LABEL[r] ?? r).join(", ").toLowerCase()} · first{" "}
                {first.created_at ? formatRelativeTime(first.created_at) : ""}
              </p>

              <div className="flex flex-wrap gap-2 border-t border-dashed border-card-border pt-3">
                <Button
                  variant="destructive"
                  size="sm"
                  disabled={resolve.isPending}
                  onClick={() => resolve.mutate({ id: first.id, action: "hide" })}
                >
                  {first.target === "comment" ? "Hide comment" : "Remove report"}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={resolve.isPending}
                  onClick={() => resolve.mutate({ id: first.id, action: "dismiss" })}
                >
                  Dismiss
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
