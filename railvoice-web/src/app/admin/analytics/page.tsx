"use client";

import { useQuery } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { MonthlyReport, RecurringExplained } from "@/components/ai/analytics-ai";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const RANGES = [7, 30, 90];

function DailyBars({
  title,
  points,
}: {
  title: string;
  points: { date: string; value: number }[];
}) {
  const max = Math.max(1, ...points.map((p) => p.value));
  const total = points.reduce((sum, p) => sum + p.value, 0);
  return (
    <Card className="min-w-0 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h2 className="text-display text-lg">{title}</h2>
        <span className="font-board text-sm">{total}</span>
      </div>
      <div className="mt-3 flex h-28 items-end gap-px border-b border-card-border">
        {points.map((p) => (
          <div
            key={p.date}
            title={`${p.date}: ${p.value}`}
            className="flex h-full min-w-0 flex-1 items-end hover:bg-muted"
          >
            <div
              className="w-full rounded-t-sm bg-primary"
              style={{ height: p.value ? `${Math.max(4, (p.value / max) * 100)}%` : 0 }}
            />
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between font-board text-[11px] text-muted-foreground">
        <span>{points[0]?.date.slice(5)}</span>
        <span>{points[points.length - 1]?.date.slice(5)}</span>
      </div>
    </Card>
  );
}

function RankedBars({
  title,
  rows,
}: {
  title: string;
  rows: { name: string; count: number; note?: string }[];
}) {
  const max = Math.max(1, ...rows.map((r) => r.count));
  return (
    <Card className="min-w-0 p-4">
      <h2 className="text-display text-lg">{title}</h2>
      {rows.length === 0 && <p className="mt-2 text-sm text-muted-foreground">No data yet.</p>}
      <ul className="mt-3 space-y-2.5">
        {rows.map((row) => (
          <li key={row.name} title={`${row.name}: ${row.count}`}>
            <div className="flex justify-between gap-3 text-sm">
              <span className="min-w-0 truncate">{row.name}</span>
              <span className="font-board shrink-0">
                {row.count}
                {row.note && <span className="text-muted-foreground"> {row.note}</span>}
              </span>
            </div>
            <div className="mt-1 h-1.5 bg-muted">
              <div className="h-full bg-primary" style={{ width: `${(row.count / max) * 100}%` }} />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}

export default function AdminAnalyticsPage() {
  const [days, setDays] = useState(30);
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-analytics", days],
    queryFn: () => api.admin.analytics(days),
    retry: false,
  });
  const report = data?.data;
  const { data: aiStatus } = useQuery({ queryKey: ["ai-status"], queryFn: () => api.ai.status() });

  const weekly = async () => {
    try {
      await api.admin.weeklyReport();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Download failed");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Analytics"
        title="Trends"
        description="Reports in your stations. Removed and duplicate reports aren't counted."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex gap-1">
              {RANGES.map((range) => (
                <button
                  key={range}
                  type="button"
                  onClick={() => setDays(range)}
                  className={cn(
                    "label-caps border-2 px-3 py-1.5 text-xs",
                    days === range
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-foreground/30 text-muted-foreground"
                  )}
                >
                  {range}d
                </button>
              ))}
            </div>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => void weekly()}>
              <Download className="h-3.5 w-3.5" /> Weekly PDF
            </Button>
          </div>
        }
      />

      {isLoading ? (
        <Skeleton className="h-48" />
      ) : error || !report ? (
        <EmptyState title="Couldn't load analytics" description="You may need a staff account." />
      ) : (
        <>
          <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              { label: "Reports", value: report.total },
              {
                label: "Avg. fix time",
                value: report.avg_resolution_hours != null ? `${report.avg_resolution_hours} h` : "—",
              },
              {
                label: "Fixed on time",
                value: report.sla_met_percent != null ? `${report.sla_met_percent}%` : "—",
              },
              { label: "Recurring", value: report.recurring.length },
            ].map((stat) => (
              <Card key={stat.label} className="p-4">
                <dd className="font-board text-2xl sm:text-3xl">{stat.value}</dd>
                <dt className="label-caps mt-1 text-xs text-muted-foreground">{stat.label}</dt>
              </Card>
            ))}
          </dl>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <DailyBars
              title="Reported per day"
              points={report.trend.map((t) => ({ date: t.date, value: t.created }))}
            />
            <DailyBars
              title="Resolved per day"
              points={report.trend.map((t) => ({ date: t.date, value: t.resolved }))}
            />
            <RankedBars
              title="By category"
              rows={report.by_category.map((c) => ({ name: c.name, count: c.count }))}
            />
            <RankedBars
              title="By station"
              rows={report.by_station.map((s) => ({
                name: s.name,
                count: s.total,
                note: s.overdue ? `(${s.overdue} overdue)` : undefined,
              }))}
            />
            <RankedBars
              title="By department"
              rows={report.by_department.map((d) => ({ name: d.name, count: d.count }))}
            />
            <RankedBars
              title="Recurring problems"
              rows={report.recurring.map((r) => ({
                name: `${r.station}: ${r.category}`,
                count: r.count,
              }))}
            />
          </div>
        </>
      )}

      {aiStatus?.data.enabled && (
        <>
          <RecurringExplained />
          <MonthlyReport />
        </>
      )}
    </div>
  );
}
