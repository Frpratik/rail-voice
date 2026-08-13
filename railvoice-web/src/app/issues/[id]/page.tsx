"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowLeft, MessageSquare, Send, Share2, Upload } from "lucide-react";
import { toast } from "sonner";
import { IssueTimeline } from "@/components/issues/issue-timeline";
import { SupportButton } from "@/components/issues/support-button";
import { Badge, StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import { IssueCardSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatRelativeTime } from "@/lib/utils";

export default function IssueDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [commentText, setCommentText] = useState("");
  const [uploading, setUploading] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["issue", id],
    queryFn: () => api.issues.get(id),
    enabled: !!id,
  });

  const supportMutation = useMutation({
    mutationFn: () => api.issues.support(id),
    onSuccess: () => {
      toast.success("Thank you for supporting this issue!");
      queryClient.invalidateQueries({ queryKey: ["issue", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const commentMutation = useMutation({
    mutationFn: (text: string) => api.comments.create(id, { body: text }),
    onSuccess: () => {
      setCommentText("");
      toast.success("Comment posted successfully");
      queryClient.invalidateQueries({ queryKey: ["issue", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  if (isLoading) return <IssueCardSkeleton />;
  if (error || !data) {
    return (
      <Card className="p-10 text-center">
        <p className="font-semibold text-destructive">Grievance not found</p>
        <p className="mt-2 text-sm text-muted-foreground">
          It may be private, removed, or the API is offline.
        </p>
        <Link href="/" className="mt-5 inline-block">
          <Button variant="outline">Back to corridor feed</Button>
        </Link>
      </Card>
    );
  }

  const { issue, timeline, comments } = data.data;
  const photos = issue.photos ?? [];

  const share = async () => {
    const url = window.location.href;
    if (navigator.share) {
      await navigator.share({ title: issue.title ?? "RailVoice Grievance", url });
    } else {
      await navigator.clipboard.writeText(url);
      toast.success("Link copied to clipboard");
    }
  };

  const onPhotoSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await api.issues.uploadPhoto(id, file);
      toast.success("Photo uploaded");
      queryClient.invalidateQueries({ queryKey: ["issue", id] });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleCommentSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    commentMutation.mutate(commentText.trim());
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-2xl space-y-6"
    >
      {/* Top Action Bar */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Corridor Feed
        </Link>
        <Button variant="ghost" size="sm" onClick={share} className="gap-1.5">
          <Share2 className="h-4 w-4" />
          Share Grievance
        </Button>
      </div>

      {/* Main Grievance Header */}
      <Card className="p-6 sm:p-8 space-y-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              {issue.issue_number}
            </p>
            <h1 className="text-display mt-1 text-2xl font-bold tracking-tight sm:text-3xl text-foreground">
              {issue.title ?? "Grievance Report"}
            </h1>
          </div>
          <StatusBadge status={issue.status} />
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Badge variant="muted">{issue.location.station.name}</Badge>
          {issue.category && <Badge variant="outline">{issue.category.name}</Badge>}
          {issue.is_emergency && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" /> Urgent Safety Hazard
            </Badge>
          )}
          {issue.location.train_number && (
            <Badge variant="muted">Train: {issue.location.train_number}</Badge>
          )}
          {issue.location.coach_number && (
            <Badge variant="muted">Platform/Coach: {issue.location.coach_number}</Badge>
          )}
        </div>

        {/* Upvote & Action row */}
        <div className="flex items-center justify-between border-t border-b border-card-border py-4">
          <div>
            <p className="text-xs text-muted-foreground">Reported by</p>
            <p className="text-sm font-medium">
              {issue.creator?.display_name ?? "Concerned Commuter"} · {formatRelativeTime(issue.created_at)}
            </p>
          </div>
          <SupportButton
            supportCount={issue.support_count}
            supported={false}
            loading={supportMutation.isPending}
            onSupport={() => supportMutation.mutate()}
          />
        </div>

        {/* Description Body */}
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            Description
          </h3>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-foreground">
            {issue.description}
          </p>
        </div>

        {/* Evidence Photos */}
        {photos.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
              Attached Evidence Photos ({photos.length})
            </h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {photos.map((photo) => (
                <div
                  key={photo.id}
                  className="group relative aspect-video overflow-hidden rounded-2xl border border-card-border bg-muted/30"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={photo.url}
                    alt="Evidence"
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Add photo if logged in */}
        {user && (
          <div className="pt-2">
            <label className="inline-flex items-center gap-2 text-xs font-semibold text-accent cursor-pointer hover:underline">
              <Upload className="h-3.5 w-3.5" />
              {uploading ? "Uploading photo..." : "Upload additional evidence photo"}
              <input
                type="file"
                accept="image/*"
                onChange={onPhotoSelected}
                disabled={uploading}
                className="hidden"
              />
            </label>
          </div>
        )}
      </Card>

      {/* Official Status Progression Timeline */}
      <Card className="p-6 sm:p-8 space-y-4">
        <h2 className="text-base font-semibold text-foreground">
          Official Action Timeline
        </h2>
        <IssueTimeline events={timeline} />
      </Card>

      {/* Community Comments Section */}
      <Card className="p-6 sm:p-8 space-y-5">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-accent" />
          <h2 className="text-base font-semibold text-foreground">
            Community Comments ({comments.length})
          </h2>
        </div>

        {comments.length === 0 ? (
          <p className="text-xs text-muted-foreground italic py-2">
            No comments yet. Have more details about this problem? Leave a note below.
          </p>
        ) : (
          <div className="space-y-3 divide-y divide-card-border">
            {comments.map((c) => (
              <div key={c.id} className="pt-3 first:pt-0 space-y-1">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-semibold text-foreground">
                    {c.author.display_name}
                  </span>
                  <span>{formatRelativeTime(c.created_at)}</span>
                </div>
                <p className="text-xs text-foreground leading-relaxed">
                  {c.body}
                </p>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleCommentSubmit} className="pt-2 space-y-2">
          <Textarea
            rows={2}
            placeholder={user ? "Write a comment or operational update..." : "Sign in to join the discussion..."}
            value={commentText}
            onChange={(e) => setCommentText(e.target.value)}
            disabled={!user || commentMutation.isPending}
            className="text-xs"
          />
          <div className="flex justify-end">
            <Button
              type="submit"
              variant="accent"
              size="sm"
              disabled={!user || !commentText.trim() || commentMutation.isPending}
              className="gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              {commentMutation.isPending ? "Posting..." : "Post Comment"}
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  );
}
