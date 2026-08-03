"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Share2 } from "lucide-react";
import { toast } from "sonner";
import { IssueTimeline } from "@/components/issues/issue-timeline";
import { CSATFeedbackModal } from "@/components/issues/csat-feedback-modal";
import { SupportButton } from "@/components/issues/support-button";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Label, Textarea } from "@/components/ui/input";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatRelativeTime } from "@/lib/utils";

export default function IssueDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { user, anonymousSessionId } = useAuthStore();
  const [comment, setComment] = useState("");
  const [uploading, setUploading] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["issue", id],
    queryFn: () => api.issues.get(id),
    enabled: !!id,
  });

  const supportMutation = useMutation({
    mutationFn: () => api.issues.support(id),
    onSuccess: () => {
      toast.success("Thank you for supporting this issue");
      queryClient.invalidateQueries({ queryKey: ["issue", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const commentMutation = useMutation({
    mutationFn: () => api.issues.addComment(id, comment),
    onSuccess: () => {
      setComment("");
      toast.success("Comment posted");
      queryClient.invalidateQueries({ queryKey: ["issue", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (isLoading) return <IssueCardSkeleton />;
  if (error || !data) {
    return (
      <Card className="p-10 text-center">
        <p className="font-semibold text-destructive">Issue not found</p>
        <p className="mt-2 text-sm text-muted-foreground">
          It may be private, removed, or the API is offline.
        </p>
        <Link href="/" className="mt-5 inline-block">
          <Button variant="outline">Back to feed</Button>
        </Link>
      </Card>
    );
  }

  const { issue, timeline, comments } = data.data;
  const photos = issue.photos ?? [];

  const share = async () => {
    const url = window.location.href;
    if (navigator.share) {
      await navigator.share({ title: issue.title ?? "RailVoice issue", url });
    } else {
      await navigator.clipboard.writeText(url);
      toast.success("Link copied");
    }
  };

  const onPhotoSelected = async (file?: File | null) => {
    if (!file) return;
    setUploading(true);
    try {
      await api.issues.uploadPhoto(id, file);
      toast.success("Photo uploaded");
      queryClient.invalidateQueries({ queryKey: ["issue", id] });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-2xl space-y-6"
    >
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Feed
        </Link>
        <Button variant="ghost" size="sm" onClick={share}>
          <Share2 className="h-4 w-4" />
          Share
        </Button>
      </div>

      <header>
        <p className="font-mono text-xs text-muted-foreground">{issue.issue_number}</p>
        <h1 className="text-display mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
          {issue.title ?? "Reported issue"}
        </h1>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Badge variant="muted">{issue.location.station.name}</Badge>
          {issue.category && <Badge variant="outline">{issue.category.name}</Badge>}
          <StatusBadge status={issue.status} />
          {issue.is_emergency && <Badge variant="emergency">Emergency</Badge>}
        </div>
      </header>

      <Card elevated className="p-6">
        <SupportButton
          supportCount={issue.support_count}
          loading={supportMutation.isPending}
          onSupport={() => {
            if (!user && !anonymousSessionId) {
              api.auth.anonymous().then((r) => {
                useAuthStore.getState().setAnonymous(r.data.anonymous_session_id);
                supportMutation.mutate();
              });
            } else {
              supportMutation.mutate();
            }
          }}
        />
      </Card>

      <Card className="p-6">
        <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Description
        </h2>
        <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-foreground/90">
          {issue.description}
        </p>
      </Card>

      <Card className="space-y-4 p-6">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Photos
          </h2>
          {(user || anonymousSessionId) && (
            <label className="cursor-pointer text-sm font-medium text-accent hover:underline">
              {uploading ? "Uploading…" : "Add photo"}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                disabled={uploading}
                onChange={(e) => onPhotoSelected(e.target.files?.[0])}
              />
            </label>
          )}
        </div>
        {photos.length === 0 ? (
          <p className="text-sm text-muted-foreground">No photos yet.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {photos.map((p) => (
              <a
                key={p.id}
                href={p.url}
                target="_blank"
                rel="noreferrer"
                className="overflow-hidden rounded-xl border border-card-border bg-muted"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={p.url} alt="" className="h-28 w-full object-cover" />
              </a>
            ))}
          </div>
        )}
      </Card>

      <Card className="space-y-4 p-6">
        <h2 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Comments ({comments?.length ?? issue.comment_count})
        </h2>
        <div className="space-y-4">
          {(comments ?? []).map((c) => (
            <div key={c.id} className="rounded-xl bg-muted/50 p-4">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-semibold tracking-tight">
                  {c.author.display_name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatRelativeTime(c.created_at)}
                </p>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-foreground/90">{c.body}</p>
            </div>
          ))}
          {(comments ?? []).length === 0 && (
            <p className="text-sm text-muted-foreground">No comments yet.</p>
          )}
        </div>
        {user && !user.is_anonymous ? (
          <div className="space-y-3 border-t border-card-border pt-4">
            <Label htmlFor="comment">Add a comment</Label>
            <Textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Share an update or more detail…"
            />
            <Button
              variant="accent"
              disabled={comment.trim().length < 1 || commentMutation.isPending}
              onClick={() => commentMutation.mutate()}
            >
              Post comment
            </Button>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            <Link href="/login" className="font-medium text-accent hover:underline">
              Sign in
            </Link>{" "}
            to join the discussion.
          </p>
        )}
      </Card>

      <CSATFeedbackModal
        issueId={issue.id}
        currentStatus={issue.status}
        onFeedbackSubmitted={() => queryClient.invalidateQueries({ queryKey: ["issue", id] })}
      />

      <Card className="p-6">
        <h2 className="mb-5 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Timeline
        </h2>
        <IssueTimeline events={timeline} />
      </Card>
    </motion.div>
  );
}
