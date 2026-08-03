"use client";

import * as React from "react";
import { ShieldAlert, AlertTriangle, Info, Send, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function EmergencyBroadcastModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const [severity, setSeverity] = React.useState<"critical" | "warning" | "info">("critical");
  const [title, setTitle] = React.useState("");
  const [message, setMessage] = React.useState("");
  const [durationHours, setDurationHours] = React.useState(4);
  const [submitting, setSubmitting] = React.useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !message.trim()) {
      toast.error("Please fill in title and message");
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/v1/emergency/alerts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          severity,
          title: title.trim(),
          message: message.trim(),
          duration_hours: durationHours,
        }),
      });

      if (res.ok) {
        toast.success("Emergency Safety Alert Broadcasted Live!");
        onClose();
        window.location.reload();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to broadcast alert");
      }
    } catch {
      toast.error("Network error during broadcast");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl border border-rose-500/30 bg-card p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-rose-500">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/15">
              <ShieldAlert className="h-5 w-5 text-rose-500 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold tracking-tight text-foreground">
                Broadcast Emergency Safety Alert
              </h2>
              <p className="text-xs text-muted-foreground">
                Trigger live top-of-screen banner notice for all active commuters
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-xl p-2 text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Severity Selector */}
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block mb-2">
              Select Severity Level
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(
                [
                  { id: "critical", label: "Critical Hazard", icon: ShieldAlert, color: "border-rose-500 bg-rose-500/10 text-rose-500" },
                  { id: "warning", label: "Warning Notice", icon: AlertTriangle, color: "border-amber-500 bg-amber-500/10 text-amber-500" },
                  { id: "info", label: "Info Announcement", icon: Info, color: "border-blue-500 bg-blue-500/10 text-blue-500" },
                ] as const
              ).map((sev) => {
                const Icon = sev.icon;
                const active = severity === sev.id;
                return (
                  <button
                    key={sev.id}
                    type="button"
                    onClick={() => setSeverity(sev.id)}
                    className={cn(
                      "flex flex-col items-center justify-center p-3 rounded-2xl border font-bold transition-all text-center gap-1.5",
                      active ? sev.color : "border-border bg-muted/40 text-muted-foreground hover:border-border/80"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{sev.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Alert Title
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Overhead Wire Hazard at Bandra Platform 2"
              className="w-full rounded-xl border border-input bg-background p-3 text-xs font-semibold focus:border-rose-500 focus:outline-none"
            />
          </div>

          {/* Message */}
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Warning Message & Action Instructions
            </label>
            <textarea
              required
              rows={3}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Detailed emergency warning instructions for commuters..."
              className="w-full rounded-xl border border-input bg-background p-3 text-xs font-medium focus:border-rose-500 focus:outline-none"
            />
          </div>

          {/* Duration */}
          <div>
            <label className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block mb-1.5">
              Alert Active Duration
            </label>
            <select
              value={durationHours}
              onChange={(e) => setDurationHours(Number(e.target.value))}
              className="w-full rounded-xl border border-input bg-background p-2.5 text-xs font-semibold focus:outline-none"
            >
              <option value={2}>2 Hours</option>
              <option value={4}>4 Hours</option>
              <option value={8}>8 Hours</option>
              <option value={24}>24 Hours</option>
            </select>
          </div>

          {/* Submit Action */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={submitting}
              className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold gap-2 shadow-lg shadow-rose-600/30"
            >
              {submitting ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  <Send className="h-4 w-4" /> Broadcast Alert
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
