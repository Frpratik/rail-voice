"use client";

import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

export default function AdminAuditPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-audit"],
    queryFn: () => api.admin.audit(),
    retry: false,
  });
  const items = data?.data.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Security"
        title="Audit log"
        description="Sign-ins and changes to user accounts. Main admins only."
      />
      {isLoading ? (
        <Skeleton className="h-48" />
      ) : error ? (
        <EmptyState title="Main admins only" description="Your account can't view the audit log." />
      ) : (
        <Card className="p-0">
          {items.length === 0 && <p className="p-4 text-sm text-muted-foreground">No events yet.</p>}
          <ul>
            {items.map((e, i) => (
              <li
                key={`${e.at}-${i}`}
                className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5 border-b border-card-border px-4 py-2.5 text-sm last:border-0"
              >
                <span className="min-w-0 font-medium">
                  {e.action}
                  {!e.success && <span className="ml-2 text-destructive">failed</span>}
                </span>
                <span className="text-muted-foreground">
                  {[e.actor, e.target && `→ ${e.target}`, e.ip, e.at && formatRelativeTime(e.at)]
                    .filter(Boolean)
                    .join(" · ")}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
