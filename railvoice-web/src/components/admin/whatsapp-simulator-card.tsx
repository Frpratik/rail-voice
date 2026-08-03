"use client";

import * as React from "react";
import { MessageSquare, Send, CheckCircle2, Phone, Sparkles } from "lucide-react";
import { toast } from "sonner";

export function WhatsAppSimulatorCard() {
  const [mobile, setMobile] = React.useState("+919876543210");
  const [message, setMessage] = React.useState("Bandra station pe platform 1 water leakage");
  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<any>(null);

  const handleSimulate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch("/api/v1/whatsapp/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from_mobile: mobile.trim(),
          body: message.trim(),
        }),
      });

      if (res.ok) {
        const json = await res.json();
        setResult(json.data);
        toast.success("WhatsApp Simulation Received Successfully!");
      } else {
        toast.error("Failed to simulate WhatsApp message");
      }
    } catch {
      toast.error("Network error during WhatsApp simulation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl border border-emerald-500/30 bg-emerald-950/10 p-5 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5 text-emerald-500">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/15">
            <MessageSquare className="h-5 w-5 text-emerald-500" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold tracking-tight text-foreground">
              WhatsApp Bot Simulator
            </h3>
            <p className="text-[11px] text-muted-foreground">
              Simulate inbound WhatsApp grievance messages and test automated AI bot responses
            </p>
          </div>
        </div>
        <span className="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[10px] font-bold text-emerald-500">
          Twilio Sandbox Live
        </span>
      </div>

      <form onSubmit={handleSimulate} className="space-y-3 text-xs">
        <div className="grid grid-cols-3 gap-2">
          <div className="col-span-1">
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
              Sender Mobile
            </label>
            <input
              type="text"
              value={mobile}
              onChange={(e) => setMobile(e.target.value)}
              className="w-full rounded-xl border border-input bg-background p-2.5 font-semibold"
            />
          </div>
          <div className="col-span-2">
            <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
              Inbound WhatsApp Message
            </label>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="e.g. Bandra platform 1 garbage"
              className="w-full rounded-xl border border-input bg-background p-2.5 font-semibold"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 font-extrabold text-white shadow-md shadow-emerald-600/25 hover:bg-emerald-700 transition-all disabled:opacity-50"
        >
          {loading ? (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
          ) : (
            <>
              <Send className="h-4 w-4" /> Simulate WhatsApp Message
            </>
          )}
        </button>
      </form>

      {result && (
        <div className="rounded-2xl border border-emerald-500/20 bg-background/90 p-3.5 space-y-2 text-xs animate-in fade-in duration-200">
          <div className="flex items-center gap-1.5 font-bold text-emerald-500">
            <CheckCircle2 className="h-4 w-4" /> Bot Response Generated
          </div>
          <div className="rounded-xl bg-muted/50 p-3 font-mono text-[11px] text-foreground whitespace-pre-wrap">
            {result.reply}
          </div>
          {result.issue_id && (
            <div className="text-[11px] text-muted-foreground font-medium">
              Registered Issue ID: <span className="font-mono font-bold text-foreground">{result.issue_id}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
