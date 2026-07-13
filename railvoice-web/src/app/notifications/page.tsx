"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Bell } from "lucide-react";
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

  const markAll = useMutation({
    mutationFn: () => api.notifications.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      toast.success("Marked all as read");
    },
  });

  const markOne = useMutation({
    mutationFn: (id: string) => api.notifications.markRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  if (!user) {
    return (
      <div className="mx-auto max-w-lg">
        <PageHeader
          eyebrow="Alerts"
          title="Notifications"
          description="Sign in to see status updates for issues you care about."
        />
        <EmptyState
          icon={Bell}
          title="Sign in required"
          description="OTP or Google sign-in unlocks your alert feed."
          actionLabel="Sign in"
          actionHref="/login"
        />
      </div>
    );
  }

  const items = data?.data.items ?? [];
  const unread = data?.data.unread_count ?? 0;

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="flex items-end justify-between gap-3">
        <PageHeader
          eyebrow="Alerts"
          title="Notifications"
          description={unread ? `${unread} unread` : "You’re caught up."}
        />
        {unread > 0 && (
          <Button
            variant="outline"
            size="sm"
            disabled={markAll.isPending}
            onClick={() => markAll.mutate()}
          >
            Mark all read
          </Button>
        )}
      </div>

      {isLoading && (
        <Card className="p-8 text-center text-sm text-muted-foreground">Loading…</Card>
      )}

      {!isLoading && items.length === 0 && (
        <EmptyState
          icon={Bell}
          title="You’re all caught up"
          description="When an issue you created or supported moves forward, we’ll notify you here."
          actionLabel="Browse issues"
          actionHref="/"
        />
      )}

      <div className="space-y-3">
        {items.map((n) => (
          <Card
            key={n.id}
            className={`cursor-pointer p-4 transition-colors ${
              n.is_read ? "opacity-80" : "border-accent/30 bg-accent/5"
            }`}
            onClick={() => {
              if (!n.is_read) markOne.mutate(n.id);
            }}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-semibold tracking-tight">{n.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{n.body}</p>
                {n.issue_id && (
                  <Link
                    href={`/issues/${n.issue_id}`}
                    className="mt-2 inline-block text-sm font-medium text-accent hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    View issue
                  </Link>
                )}
              </div>
              <p className="shrink-0 text-xs text-muted-foreground">
                {formatRelativeTime(n.created_at)}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
