"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { AlertTriangle, Flame, MessageCircle, ThumbsUp } from "lucide-react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import type { Issue } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

export function IssueCard({
  issue,
  href,
  className,
  index = 0,
}: {
  issue: Issue;
  href?: string;
  className?: string;
  index?: number;
}) {
  const targetHref = href ?? `/issues/${issue.id}`;
  const highSupport = issue.support_count >= 25;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.04, 0.24), duration: 0.35 }}
    >
      <Link href={targetHref} className="block group">
        <article
          className={cn(
            "relative overflow-hidden rounded-2xl border border-card-border bg-card p-5 transition-all duration-300",
            "hover:-translate-y-0.5 hover:border-foreground/12 hover:shadow-[0_16px_48px_rgba(10,11,13,0.08)]",
            issue.is_emergency && "border-l-[3px] border-l-destructive",
            className
          )}
        >
          <div className="mb-3 flex flex-wrap items-center gap-2">
            {highSupport && (
              <Badge variant="accent">
                <Flame className="h-3 w-3" />
                High Priority
              </Badge>
            )}
            {issue.is_emergency && (
              <Badge variant="destructive" className="flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" /> Urgent Hazard
              </Badge>
            )}
            <Badge variant="muted">
              {issue.location?.station?.code || issue.location?.station?.name || "Western Railway"}
            </Badge>
            {issue.category && (
              <Badge variant="outline">{issue.category.name}</Badge>
            )}
          </div>

          <h3 className="text-display line-clamp-2 text-[16px] font-semibold leading-snug tracking-tight transition-colors group-hover:text-accent">
            {issue.title ?? issue.description.slice(0, 90)}
          </h3>

          <p className="mt-2 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {issue.description}
          </p>

          <div className="mt-5 flex items-center justify-between gap-3 border-t border-card-border pt-4">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1.5 font-medium text-foreground/80">
                <ThumbsUp className="h-3.5 w-3.5 text-accent" />
                {issue.support_count} Upvotes
              </span>
              <span className="inline-flex items-center gap-1.5">
                <MessageCircle className="h-3.5 w-3.5" />
                {issue.comment_count}
              </span>
            </div>
            <div className="flex items-center gap-2.5">
              <StatusBadge status={issue.status} />
              <time className="hidden text-xs text-muted-foreground sm:inline">
                {formatRelativeTime(issue.created_at)}
              </time>
            </div>
          </div>
        </article>
      </Link>
    </motion.div>
  );
}
