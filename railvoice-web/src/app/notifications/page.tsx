"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Bell, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatRelativeTime } from "@/lib/utils";

export default function NotificationsPage() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.notifications.list(),
    enabled: !!user,
    retry: false,
  });

  const markOne = useMutation({
    mutationFn: (id: string) => api.notifications.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  if (!user) {
    return (
      <div className="mx-auto max-w-lg space-y-6">
        <PageHeader
          eyebrow="Updates"
          title="Status Notifications"
          description="Sign in to see real-time updates for grievances you reported or supported."
        />
        <EmptyState
          title="Sign in required"
          description="Sign in with your mobile number to view official station notifications."
          action={{
            label: "Sign in",
            onClick: () => {
              window.location.href = "/login";
            },
          }}
        />
      </div>
    );
  }

  const items = data?.data.items ?? [];

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <PageHeader
        eyebrow="Updates"
        title="Status Notifications"
        description="Official alerts when station admins review, assign, or resolve problems."
      />

      {isLoading && (
        <Card className="p-8 text-center text-sm text-muted-foreground">
          Loading notifications…
        </Card>
      )}

      {!isLoading && items.length === 0 && (
        <EmptyState
          title="You’re all caught up"
          description="When a grievance you created or upvoted progresses, you'll receive official alerts here."
          action={{
            label: "Browse problems",
            onClick: () => {
              window.location.href = "/";
            },
          }}
        />
      )}

      <div className="space-y-3">
        {items.map((n) => (
          <Card
            key={n.id}
            onClick={() => {
              if (!n.is_read) markOne.mutate(n.id);
            }}
            className={`p-4 transition-colors ${
              n.is_read ? "opacity-75" : "border-accent/40 bg-accent/5"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-foreground">{n.title}</p>
                <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
                  {n.body}
                </p>
                {n.issue_id && (
                  <Link
                    href={`/issues/${n.issue_id}`}
                    className="mt-2 inline-block text-xs font-semibold text-accent hover:underline"
                  >
                    View Grievance Ticket →
                  </Link>
                )}
              </div>
              <span className="shrink-0 text-[10px] text-muted-foreground">
                {formatRelativeTime(n.created_at)}
              </span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
