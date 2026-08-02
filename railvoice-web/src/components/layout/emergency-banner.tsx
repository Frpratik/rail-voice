"use client";

import * as React from "react";
import { AlertTriangle, Info, X, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmergencyAlert {
  id: string;
  station_id: string | null;
  station_name: string | null;
  severity: "critical" | "warning" | "info" | string;
  title: string;
  message: string;
}

export function EmergencyBanner() {
  const [alerts, setAlerts] = React.useState<EmergencyAlert[]>([]);
  const [dismissedIds, setDismissedIds] = React.useState<string[]>([]);

  React.useEffect(() => {
    let isMounted = true;
    const fetchActiveAlerts = async () => {
      try {
        const res = await fetch("/api/v1/emergency/alerts/active");
        if (res.ok) {
          const json = await res.json();
          if (isMounted && json.data) {
            setAlerts(json.data);
          }
        }
      } catch {
        // Silent catch for banner polling
      }
    };

    fetchActiveAlerts();
    const interval = setInterval(fetchActiveAlerts, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const visibleAlerts = alerts.filter((a) => !dismissedIds.includes(a.id));
  if (visibleAlerts.length === 0) return null;

  const currentAlert = visibleAlerts[0];
  const isCritical = currentAlert.severity === "critical";
  const isWarning = currentAlert.severity === "warning";

  return (
    <div
      className={cn(
        "relative z-50 w-full px-4 py-2.5 shadow-lg backdrop-blur-md transition-all animate-in slide-in-from-top duration-200 flex items-center justify-between text-xs sm:text-sm font-medium",
        isCritical && "bg-rose-600/95 text-white dark:bg-rose-700/95 shadow-rose-900/30 animate-pulse",
        isWarning && "bg-amber-600/95 text-white dark:bg-amber-700/95 shadow-amber-900/30",
        !isCritical && !isWarning && "bg-blue-600/95 text-white dark:bg-blue-700/95 shadow-blue-900/30"
      )}
    >
      <div className="mx-auto flex max-w-6xl items-center gap-3 pr-8">
        <div className="shrink-0 p-1 rounded-lg bg-white/10">
          {isCritical ? (
            <ShieldAlert className="h-4 w-4 text-white" />
          ) : isWarning ? (
            <AlertTriangle className="h-4 w-4 text-white" />
          ) : (
            <Info className="h-4 w-4 text-white" />
          )}
        </div>
        <div>
          <span className="font-bold tracking-tight uppercase px-1.5 py-0.5 rounded bg-white/20 text-[10px] mr-2">
            {currentAlert.station_name || "CORRIDOR EMERGENCY"}
          </span>
          <span className="font-bold mr-1.5">{currentAlert.title}:</span>
          <span className="opacity-95">{currentAlert.message}</span>
        </div>
      </div>

      <button
        onClick={() => setDismissedIds((prev) => [...prev, currentAlert.id])}
        className="shrink-0 rounded-lg p-1 hover:bg-white/20 transition-colors focus:outline-none"
        aria-label="Dismiss alert"
      >
        <X className="h-4 w-4 text-white" />
      </button>
    </div>
  );
}
