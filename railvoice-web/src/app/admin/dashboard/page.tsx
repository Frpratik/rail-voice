"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  Clock3,
  FileText,
  Inbox,
  Shield,
} from "lucide-react";
import { IssueCard } from "@/components/issues/issue-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

function StatCard({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  tone?: "default" | "warn" | "ok" | "danger";
}) {
  return (
    <Card
      className={cn(
        "relative overflow-hidden p-5",
        tone === "danger" && "border-destructive/30",
        tone === "warn" && "border-warning/25",
        tone === "ok" && "border-success/25"
      )}
    >
      <div className="flex items-start justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          {label}
        </p>
        <span
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl",
            tone === "danger" && "bg-destructive/10 text-destructive",
            tone === "warn" && "bg-warning/10 text-warning",
            tone === "ok" && "bg-success/10 text-success",
            (!tone || tone === "default") && "bg-muted text-muted-foreground"
          )}
        >
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="text-display mt-4 text-3xl font-semibold tracking-tight">{value}</p>
    </Card>
  );
}

export default function AdminDashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.admin.dashboard(),
    retry: false,
  });

  if (error) {
    return (
      <Card elevated className="mx-auto max-w-lg p-10 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-muted text-muted-foreground">
          <Shield className="h-6 w-6" />
        </div>
        <p className="text-lg font-semibold tracking-tight">Official access required</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in with an authorized Station Admin or Railway Authority account.
        </p>
        <Link href="/login" className="mt-6 inline-block">
          <Button variant="accent">Sign in to console</Button>
        </Link>
      </Card>
    );
  }

  const kpis = data?.data.kpis;
  const topIssues = data?.data.top_issues ?? [];

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Station Operations"
        title="Command Dashboard"
        description="Review citizen grievances, prioritize urgent safety hazards, and escalate reports to Western Railway."
        action={
          <div className="flex items-center gap-2">
            <Link href="/admin/reports">
              <Button variant="outline" className="gap-1.5">
                <FileText className="h-4 w-4" /> Generate Report
              </Button>
            </Link>
            <Link href="/admin/issues">
              <Button variant="accent" className="gap-1.5">
                Open Triage Queue
                <ArrowUpRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))
        ) : (
          <>
            <StatCard label="Open Grievances" value={kpis?.open_issues ?? 0} icon={Inbox} />
            <StatCard
              label="Action In Progress"
              value={kpis?.in_progress ?? 0}
              icon={Clock3}
              tone="warn"
            />
            <StatCard
              label="Resolved Today"
              value={kpis?.resolved_today ?? 0}
              icon={CheckCircle2}
              tone="ok"
            />
            <StatCard
              label="Emergency Hazards"
              value={kpis?.emergency_open ?? 0}
              icon={AlertTriangle}
              tone={(kpis?.emergency_open ?? 0) > 0 ? "danger" : "default"}
            />
          </>
        )}
      </div>

      <section>
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-display text-lg font-semibold tracking-tight">
              Top Community-Supported Issues
            </h2>
            <p className="text-sm text-muted-foreground">
              Issues requiring immediate station review and operational action
            </p>
          </div>
          <Link
            href="/admin/issues"
            className="text-xs font-semibold uppercase tracking-[0.14em] text-accent transition-colors hover:underline"
          >
            View all queue →
          </Link>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-40 rounded-2xl" />
            ))}
          </div>
        ) : topIssues.length === 0 ? (
          <Card className="p-8 text-center text-muted-foreground">
            <p className="text-sm">No open issues requiring triage at your assigned station.</p>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {topIssues.map((issue, i) => (
              <motion.div
                key={issue.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: i * 0.04 }}
              >
                <IssueCard issue={issue} href={`/admin/issues?focus=${issue.id}`} />
              </motion.div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
