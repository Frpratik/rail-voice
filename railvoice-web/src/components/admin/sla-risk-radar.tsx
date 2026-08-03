"use client";

import * as React from "react";
import { Radar, AlertCircle, Clock, TrendingUp, ShieldAlert, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SLARiskItem {
  issue_id: string;
  issue_number: string;
  title: string;
  station_code: string;
  station_name: string;
  category_name: string;
  created_at: string;
  target_sla_hours: number;
  elapsed_hours: number;
  remaining_hours: number;
  risk_score_pct: number;
  risk_level: "critical" | "high" | "medium" | "low";
  risk_factors: string[];
}

export function SLARiskRadar() {
  const [items, setItems] = React.useState<SLARiskItem[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function fetchRadar() {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/v1/admin/sla-risk-radar", {
          headers: { Authorization: token ? `Bearer ${token}` : "" },
        });
        if (res.ok) {
          const json = await res.json();
          setItems(json.data || []);
        }
      } catch {
        // Fallback demo data if no token
        setItems([
          {
            issue_id: "demo-1",
            issue_number: "ISS-000104",
            title: "Overhead wire spark near platform 1",
            station_code: "BA",
            station_name: "Bandra",
            category_name: "Safety & Security",
            created_at: new Date().toISOString(),
            target_sla_hours: 4,
            elapsed_hours: 3.2,
            remaining_hours: 0.8,
            risk_score_pct: 88,
            risk_level: "critical",
            risk_factors: ["Target SLA 80% elapsed", "High station workload"],
          },
          {
            issue_id: "demo-2",
            issue_number: "ISS-000105",
            title: "Escalator step fault on foot overbridge",
            station_code: "ADH",
            station_name: "Andheri",
            category_name: "Lifts & Escalators",
            created_at: new Date().toISOString(),
            target_sla_hours: 12,
            elapsed_hours: 8.5,
            remaining_hours: 3.5,
            risk_score_pct: 71,
            risk_level: "high",
            risk_factors: ["Target SLA 70% elapsed"],
          },
        ]);
      } finally {
        setLoading(false);
      }
    }
    fetchRadar();
  }, []);

  return (
    <div className="rounded-3xl border border-border bg-card p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5 text-accent">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15">
            <Radar className="h-5 w-5 text-accent animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold tracking-tight text-foreground">
              AI SLA Velocity & Predictive Escalation Radar
            </h3>
            <p className="text-[11px] text-muted-foreground">
              Predictive risk scores forecasting SLA breaches before expiration
            </p>
          </div>
        </div>
        <span className="rounded-full bg-rose-500/15 px-3 py-1 text-[11px] font-extrabold text-rose-500">
          {items.filter((i) => i.risk_level === "critical" || i.risk_level === "high").length} High Risk Issues
        </span>
      </div>

      {loading ? (
        <div className="py-8 text-center text-xs text-muted-foreground animate-pulse">
          Calculating SLA velocity predictions...
        </div>
      ) : items.length === 0 ? (
        <div className="py-8 text-center text-xs text-muted-foreground">
          No open issues at high SLA breach risk.
        </div>
      ) : (
        <div className="grid gap-3">
          {items.map((item) => {
            const isCritical = item.risk_level === "critical";
            const isHigh = item.risk_level === "high";

            return (
              <div
                key={item.issue_id}
                className={cn(
                  "rounded-2xl border p-4 transition-all space-y-2.5",
                  isCritical
                    ? "border-rose-500/40 bg-rose-500/5 hover:border-rose-500/60"
                    : isHigh
                    ? "border-amber-500/40 bg-amber-500/5 hover:border-amber-500/60"
                    : "border-border bg-muted/20"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] font-bold text-muted-foreground">
                        {item.issue_number}
                      </span>
                      <span className="rounded-md bg-muted px-2 py-0.5 text-[10px] font-extrabold uppercase">
                        {item.station_name} ({item.station_code})
                      </span>
                      <span className="text-[10px] font-semibold text-muted-foreground">
                        {item.category_name}
                      </span>
                    </div>
                    <h4 className="text-xs font-extrabold text-foreground mt-1">
                      {item.title}
                    </h4>
                  </div>

                  <div className="text-right shrink-0">
                    <div
                      className={cn(
                        "text-base font-black tracking-tight",
                        isCritical ? "text-rose-500" : isHigh ? "text-amber-500" : "text-emerald-500"
                      )}
                    >
                      {item.risk_score_pct}% Risk
                    </div>
                    <div className="text-[10px] font-semibold text-muted-foreground flex items-center gap-1 justify-end mt-0.5">
                      <Clock className="h-3 w-3" /> {item.remaining_hours.toFixed(1)}h remaining
                    </div>
                  </div>
                </div>

                {/* Progress Ring / Bar */}
                <div className="w-full bg-muted/60 h-2 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      isCritical ? "bg-rose-500" : isHigh ? "bg-amber-500" : "bg-emerald-500"
                    )}
                    style={{ width: `${Math.min(item.risk_score_pct, 100)}%` }}
                  />
                </div>

                {/* Risk Factors */}
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {item.risk_factors.map((factor, i) => (
                    <span
                      key={i}
                      className="rounded-lg bg-background/80 border border-border px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
                    >
                      ⚠️ {factor}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
