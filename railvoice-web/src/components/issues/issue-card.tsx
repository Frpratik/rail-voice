"use client";

import Link from "next/link";
import { AlertTriangle, MessageCircle, ThumbsUp } from "lucide-react";
import { Badge, StatusBadge } from "@/components/ui/badge";
import type { Issue } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

/** An issue drawn as a railway ticket: station stub, perforation, details. */
export function IssueCard({
  issue,
  href,
  className,
}: {
  issue: Issue;
  href?: string;
  className?: string;
  index?: number;
}) {
  const targetHref = href ?? `/issues/${issue.id}`;
  const highSupport = issue.support_count >= 25;
  const stationCode = issue.location?.station?.code ?? "WR";

  return (
    <Link href={targetHref} className="group block">
      <article
        style={{ "--stub": "84px" } as React.CSSProperties}
        className={cn(
          "ticket flex transition-colors group-hover:border-foreground/60",
          issue.is_emergency && "border-destructive",
          className
        )}
      >
        <div
          className={cn(
            "flex w-[84px] shrink-0 flex-col items-center justify-between px-2 py-4 text-center",
            issue.is_emergency ? "bg-destructive text-white" : "bg-primary text-primary-foreground"
          )}
        >
          <span className="label-caps text-[10px] opacity-70">Station</span>
          <span className="text-display text-3xl tracking-wide">{stationCode}</span>
          <span className="font-board text-[10px] leading-tight opacity-80">
            {issue.issue_number.replace("RV-", "")}
          </span>
        </div>

        <div className="ticket-perforation min-w-0 flex-1 p-4 pl-5">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            {issue.is_emergency && (
              <Badge variant="emergency">
                <AlertTriangle className="h-3 w-3" /> Urgent hazard
              </Badge>
            )}
            {highSupport && !issue.is_emergency && <Badge variant="accent">Many reports</Badge>}
            {issue.category && <Badge variant="outline">{issue.category.name}</Badge>}
          </div>

          <h3 className="text-display line-clamp-2 text-xl leading-snug group-hover:text-accent">
            {issue.title ?? issue.description.slice(0, 90)}
          </h3>

          <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {issue.description}
          </p>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-dashed border-card-border pt-3">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
                <ThumbsUp className="h-3.5 w-3.5" />
                <span className="font-board">{issue.support_count}</span>
              </span>
              <span className="inline-flex items-center gap-1.5">
                <MessageCircle className="h-3.5 w-3.5" />
                <span className="font-board">{issue.comment_count}</span>
              </span>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status={issue.status} />
              <time className="font-board hidden text-xs text-muted-foreground sm:inline">
                {formatRelativeTime(issue.created_at)}
              </time>
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}
