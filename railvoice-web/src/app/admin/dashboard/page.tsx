"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowUpRight, FileText, Shield } from "lucide-react";
import { BriefingCard } from "@/components/ai/briefing-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { Issue } from "@/lib/types";
import { cn, formatRelativeTime } from "@/lib/utils";

/** A number shown as individual split-flap digits. */
function Flap({ value, digits = 3 }: { value: number; digits?: number }) {
  const text = String(Math.max(0, value)).padStart(digits, "0");
  return (
    <span className="inline-flex gap-1 text-[clamp(1.5rem,7vw,3rem)]" aria-label={String(value)}>
      {text.split("").map((d, i) => (
        <span key={i} className="flap" aria-hidden>
          {d}
        </span>
      ))}
    </span>
  );
}

function BoardTile({
  label,
  value,
  alert,
}: {
  label: string;
  value: number;
  alert?: boolean;
}) {
  return (
    <div className="board min-w-0 p-3 sm:p-4">
      <p className={cn("label-caps text-xs", alert ? "text-[#ff5a5a] blink" : "text-[#ffb000]/70")}>
        {label}
      </p>
      <div className="mt-3">
        <Flap value={value} />
      </div>
    </div>
  );
}

const STATUS_COLOR: Record<string, string> = {
  verified: "text-[#7dd3fc]",
  assigned: "text-[#7dd3fc]",
  action_started: "text-[#ffb000]",
  work_in_progress: "text-[#ffb000]",
  completed: "text-[#4ade80]",
  closed: "text-[#4ade80]",
  forwarded_division: "text-[#f0abfc]",
  forwarded_zone: "text-[#f0abfc]",
  forwarded_station_manager: "text-[#f0abfc]",
  rejected: "text-[#ff5a5a]",
};

function DepartureRow({ issue }: { issue: Issue }) {
  const status = issue.status.replace(/_/g, " ").toUpperCase();
  return (
    <Link
      href={`/admin/issues?focus=${issue.id}`}
      className="board-row grid grid-cols-[48px_minmax(0,1fr)] items-center gap-x-3 gap-y-1 px-3 py-3 text-sm sm:grid-cols-[70px_110px_minmax(0,1fr)_170px_60px_70px] sm:gap-x-4 sm:px-4"
    >
      <span className="font-medium">{issue.location.station.code}</span>
      <span className="hidden text-[#ffb000]/70 sm:block">
        {issue.issue_number.replace("RV-WR-", "")}
      </span>
      <span className={cn("truncate", issue.is_emergency && "text-[#ff5a5a]")}>
        {issue.is_emergency && <span className="blink mr-2">!</span>}
        {issue.title ?? issue.description.slice(0, 60)}
      </span>
      <span className={cn("col-start-2 truncate text-xs sm:col-start-auto sm:text-sm", STATUS_COLOR[issue.status] ?? "text-[#ffb000]")}>
        {status}
      </span>
      <span className="hidden text-right sm:block">{issue.support_count}</span>
      <span className="hidden text-right text-[#ffb000]/60 sm:block">
        {formatRelativeTime(issue.created_at)}
      </span>
    </Link>
  );
}

export default function AdminDashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.admin.dashboard(),
    retry: false,
  });
  const { data: aiStatus } = useQuery({ queryKey: ["ai-status"], queryFn: () => api.ai.status() });

  if (error) {
    return (
      <Card elevated className="mx-auto max-w-lg p-10 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center border-2 border-foreground/70 bg-accent text-accent-foreground">
          <Shield className="h-6 w-6" />
        </div>
        <p className="text-display text-2xl">Staff access only</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in with a station admin or main admin account to open the control room.
        </p>
        <Link href="/login" className="mt-6 inline-block">
          <Button variant="accent">Sign in</Button>
        </Link>
      </Card>
    );
  }

  const kpis = data?.data.kpis;
  const topIssues = data?.data.top_issues ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Control room"
        title="Station overview"
        description="What is open, what is being worked on, and what needs a decision today."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <Link href="/admin/reports">
              <Button variant="outline" className="gap-1.5">
                <FileText className="h-4 w-4" /> Reports
              </Button>
            </Link>
            <Link href="/admin/issues">
              <Button variant="accent" className="gap-1.5">
                Open queue
                <ArrowUpRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        }
      />

      <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)
        ) : (
          <>
            <BoardTile label="Open" value={kpis?.open_issues ?? 0} />
            <BoardTile label="In progress" value={kpis?.in_progress ?? 0} />
            <BoardTile label="Resolved today" value={kpis?.resolved_today ?? 0} />
            <BoardTile
              label="Emergency"
              value={kpis?.emergency_open ?? 0}
              alert={(kpis?.emergency_open ?? 0) > 0}
            />
          </>
        )}
      </div>

      {!isLoading && kpis && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="board flex items-center justify-between gap-3 p-3 sm:p-4">
            <span className="label-caps text-xs text-[#ffb000]/70">Avg. time to resolve</span>
            <span className="text-xl">
              {kpis.avg_resolution_hours != null ? `${kpis.avg_resolution_hours} h` : "—"}
            </span>
          </div>
          <div className="board flex items-center justify-between gap-3 p-3 sm:p-4">
            <span className="label-caps text-xs text-[#ffb000]/70">Past SLA time</span>
            <span className={cn("text-xl", kpis.sla_breaches > 0 && "text-[#ff5a5a]")}>
              {kpis.sla_breaches}
            </span>
          </div>
        </div>
      )}

      {aiStatus?.data.enabled && <BriefingCard />}

      <section>
        <div className="mb-3 flex items-end justify-between">
          <h2 className="text-display text-2xl">Most supported reports</h2>
          <Link
            href="/admin/issues"
            className="label-caps text-xs text-accent hover:underline"
          >
            Full queue →
          </Link>
        </div>

        <div className="board">
          <div className="hidden grid-cols-[70px_110px_minmax(0,1fr)_170px_60px_70px] gap-x-4 bg-[#10141d] px-4 py-2 text-xs text-[#ffb000]/60 sm:grid">
            <span>STN</span>
            <span>NO.</span>
            <span>PROBLEM</span>
            <span>STATUS</span>
            <span className="text-right">SUPP</span>
            <span className="text-right">AGE</span>
          </div>
          {isLoading ? (
            <div className="space-y-px p-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 bg-[#10141d]" />
              ))}
            </div>
          ) : topIssues.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-[#ffb000]/70">
              NO OPEN REPORTS FOR YOUR STATIONS
            </p>
          ) : (
            topIssues.map((issue) => <DepartureRow key={issue.id} issue={issue} />)
          )}
        </div>
      </section>
    </div>
  );
}
