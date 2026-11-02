"use client";

import { useQuery } from "@tanstack/react-query";
import { Printer, Sparkles } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";

function Heading({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-accent" />
        <h2 className="text-display text-2xl">{title}</h2>
      </div>
      {action}
    </div>
  );
}

/** Why the same problems keep coming back, explained by AI from the reports. */
export function RecurringExplained() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["ai-recurring"],
    queryFn: () => api.ai.recurring(),
    retry: false,
    staleTime: 60 * 60 * 1000,
  });
  const items = data?.data.items ?? [];

  return (
    <Card className="space-y-4">
      <Heading title="Why problems keep coming back" />
      {isLoading ? (
        <Skeleton className="h-24" />
      ) : error ? (
        <p className="text-sm text-muted-foreground">Not available right now.</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No problem has been reported 3 or more times in 90 days.</p>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={`${item.station}-${item.category}`} className="space-y-1 border-l-4 border-primary pl-3 text-sm">
              <p className="font-semibold">
                {item.station}: {item.category} <span className="text-muted-foreground">({item.count} reports)</span>
              </p>
              <p>{item.pattern}</p>
              <p>
                <span className="label-caps text-xs text-muted-foreground">Likely cause </span>
                {item.likely_cause}
              </p>
              <p>
                <span className="label-caps text-xs text-muted-foreground">Lasting fix </span>
                {item.fix}
              </p>
              <p className="flex flex-wrap gap-x-2 text-xs">
                {item.reports.map((r) => (
                  <Link key={r.id} href={`/issues/${r.id}`} className="text-primary underline underline-offset-2">
                    {r.issue_number}
                  </Link>
                ))}
              </p>
            </div>
          ))}
          <p className="text-xs text-muted-foreground">Written by AI from the reports. Causes are guesses to check.</p>
        </div>
      )}
    </Card>
  );
}

function lastMonths(count: number) {
  const now = new Date();
  return Array.from({ length: count }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    return {
      value: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
      label: d.toLocaleString("en-IN", { month: "long", year: "numeric" }) + (i === 0 ? " (so far)" : ""),
    };
  });
}

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="label-caps mb-1 text-xs text-muted-foreground">{title}</p>
      <ul className="list-disc space-y-1 pl-5 text-sm">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

/** Monthly report for senior officials, written by AI from the month's figures. */
export function MonthlyReport() {
  const months = lastMonths(6);
  const [month, setMonth] = useState(months[1].value);
  const { data, isFetching, error } = useQuery({
    queryKey: ["ai-monthly", month],
    queryFn: () => api.ai.monthlyReport(month),
    retry: false,
    staleTime: 60 * 60 * 1000,
  });
  const report = data?.data;

  return (
    <Card className="print-area space-y-4">
      <Heading
        title="Monthly report"
        action={
          <div className="flex items-center gap-2 print:hidden">
            <select
              aria-label="Month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="h-9 border-2 border-foreground/30 bg-card px-2 text-xs"
            >
              {months.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
            <Button variant="outline" size="sm" className="gap-1.5" onClick={() => window.print()} disabled={!report}>
              <Printer className="h-3.5 w-3.5" /> Print
            </Button>
          </div>
        }
      />
      {isFetching ? (
        <Skeleton className="h-32" />
      ) : error || !report ? (
        <p className="text-sm text-muted-foreground">Not available right now.</p>
      ) : (
        <div className="space-y-4">
          <p className="text-sm font-semibold">{report.month_label}</p>
          <p className="text-sm leading-relaxed">{report.summary}</p>
          <dl className="grid grid-cols-1 gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
            {Object.entries(report.figures).map(([label, value]) => (
              <div key={label} className="flex justify-between gap-3 border-b border-card-border py-1">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="text-right font-medium">{value}</dd>
              </div>
            ))}
          </dl>
          <List title="What went well" items={report.highlights} />
          <List title="Needs attention" items={report.concerns} />
          <List title="Recommended for next month" items={report.recommendations} />
          <p className="text-xs text-muted-foreground">
            Figures are counted by RailVoice. The wording is written by AI; check it before sending.
          </p>
        </div>
      )}
    </Card>
  );
}
