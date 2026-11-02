"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Card } from "@/components/ui/card";
import { EmptyState, PageHeader } from "@/components/ui/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const RANGES = [30, 90, 365];

export default function TransparencyPage() {
  const [days, setDays] = useState(90);
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["transparency", days],
    queryFn: () => api.public.transparency(days),
  });
  const report = data?.data;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Open data"
        title="How stations are doing"
        description="Every number comes from public reports on RailVoice. Removed and duplicate reports aren't counted."
        action={
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
                {range === 365 ? "1 year" : `${range} days`}
              </button>
            ))}
          </div>
        }
      />

      {isLoading ? (
        <Skeleton className="h-40" />
      ) : error || !report ? (
        <EmptyState
          title="Couldn't load the numbers"
          description="Check your connection and try again."
          action={{ label: "Try again", onClick: () => refetch() }}
        />
      ) : (
        <>
          <dl className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              { label: "Reports", value: report.total_reports },
              { label: "Open", value: report.open },
              { label: "Fixed", value: report.fixed },
              { label: "Fix rate", value: report.fix_rate != null ? `${report.fix_rate}%` : "—" },
            ].map((stat) => (
              <Card key={stat.label} className="p-4">
                <dd className="font-board text-3xl">{stat.value}</dd>
                <dt className="label-caps mt-1 text-xs text-muted-foreground">{stat.label}</dt>
              </Card>
            ))}
          </dl>

          {report.stations.length === 0 ? (
            <EmptyState title="No reports yet" description="Nothing has been reported in this period." />
          ) : (
            <div className="space-y-3">
              {report.stations.map((s) => (
                <Link key={s.code} href={`/stations/${s.code}`} className="block">
                  <Card className="p-4 transition-colors hover:border-foreground/60">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <h2 className="text-display text-xl">
                        {s.name} <span className="font-board text-xs text-muted-foreground">{s.code}</span>
                      </h2>
                      <p className="font-board text-sm">{s.fix_rate ?? 0}% fixed</p>
                    </div>
                    <div
                      className="mt-2 h-2 bg-muted"
                      role="img"
                      aria-label={`${s.fix_rate ?? 0} percent of reports fixed`}
                    >
                      <div className="h-full bg-primary" style={{ width: `${s.fix_rate ?? 0}%` }} />
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {s.reports} reports · {s.open} open · {s.fixed} fixed
                      {s.avg_fix_hours != null && ` · ${s.avg_fix_hours} h average fix`}
                      {s.avg_rating != null && ` · rated ${s.avg_rating}/5`}
                    </p>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
