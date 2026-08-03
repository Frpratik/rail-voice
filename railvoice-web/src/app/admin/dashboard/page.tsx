"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, ArrowUpRight, CheckCircle2, Clock3, Inbox, ShieldAlert } from "lucide-react";
import { EmergencyBroadcastModal } from "@/components/admin/emergency-broadcast-modal";
import { WhatsAppSimulatorCard } from "@/components/admin/whatsapp-simulator-card";
import { SLARiskRadar } from "@/components/admin/sla-risk-radar";
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
  const [emergencyModalOpen, setEmergencyModalOpen] = useState(false);
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: () => api.admin.dashboard(),
    retry: false,
  });

  if (error) {
    return (
      <Card elevated className="mx-auto max-w-lg p-10 text-center">
        <p className="text-lg font-semibold tracking-tight">Official access required</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in with an operations account to view this console.
        </p>
        {process.env.NEXT_PUBLIC_OTP_MOCK !== "false" && (
          <p className="mt-4 space-y-1 rounded-xl bg-muted px-3 py-2 font-mono text-xs text-muted-foreground">
            <span className="block">Passenger · +919111111111</span>
            <span className="block">Station Admin · +919888888888</span>
            <span className="block">Main Admin · +919999999999</span>
            <span className="block">OTP · 123456</span>
          </p>
        )}
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
      <EmergencyBroadcastModal
        isOpen={emergencyModalOpen}
        onClose={() => setEmergencyModalOpen(false)}
      />

      <PageHeader
        eyebrow="Operations"
        title="Overview"
        description="Live station performance and AI-ranked priority queue."
        action={
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setEmergencyModalOpen(true)}
              className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold gap-1.5 shadow-md shadow-rose-600/20"
            >
              <ShieldAlert className="h-4 w-4" /> Broadcast Emergency
            </Button>
            <Link href="/admin/issues">
              <Button variant="outline">
                Open queue
                <ArrowUpRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28 rounded-2xl" />
          ))
        ) : (
          <>
            <StatCard label="Open issues" value={kpis?.open_issues ?? 0} icon={Inbox} />
            <StatCard
              label="In progress"
              value={kpis?.in_progress ?? 0}
              icon={Clock3}
              tone="warn"
            />
            <StatCard
              label="Resolved today"
              value={kpis?.resolved_today ?? 0}
              icon={CheckCircle2}
              tone="ok"
            />
            <StatCard
              label="Avg resolution (h)"
              value={
                kpis?.avg_resolution_hours != null
                  ? Number(kpis.avg_resolution_hours).toFixed(1)
                  : "—"
              }
              icon={Clock3}
            />
            <StatCard
              label="SLA breaches"
              value={kpis?.sla_breaches ?? 0}
              icon={AlertTriangle}
              tone={(kpis?.sla_breaches ?? 0) > 0 ? "danger" : "default"}
            />
            <StatCard
              label="Emergency open"
              value={kpis?.emergency_open ?? 0}
              icon={AlertTriangle}
              tone={(kpis?.emergency_open ?? 0) > 0 ? "danger" : "default"}
            />
          </>
        )}
      </div>

      {/* AI SLA Velocity & WhatsApp Simulator Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        <SLARiskRadar />
        <WhatsAppSimulatorCard />
      </div>

      <section>
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-display text-lg font-semibold tracking-tight">
              AI priority queue
            </h2>
            <p className="text-sm text-muted-foreground">
              Highest signal issues ranked for triage
            </p>
          </div>
          <Link
            href="/admin/issues"
            className="text-sm font-medium text-accent hover:underline"
          >
            View all
          </Link>
        </div>
        <div className="grid gap-4">
          {topIssues.map((issue, i) => (
            <motion.div
              key={issue.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
            >
              <IssueCard issue={issue} index={0} />
            </motion.div>
          ))}
          {!isLoading && topIssues.length === 0 && (
            <Card className="p-8 text-center text-sm text-muted-foreground">
              Queue is clear. Nice work.
            </Card>
          )}
        </div>
      </section>
    </div>
  );
}
