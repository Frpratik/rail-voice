"use client";

import * as React from "react";
import { ShieldCheck, ShieldAlert, Image as ImageIcon, Sparkles } from "lucide-react";

export function VisualVerificationBadge({
  perceptualHash,
  isFlaggedDuplicate,
}: {
  perceptualHash?: string | null;
  isFlaggedDuplicate?: boolean;
}) {
  if (!perceptualHash) {
    return (
      <div className="inline-flex items-center gap-1.5 rounded-xl border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-bold text-blue-500">
        <Sparkles className="h-3.5 w-3.5" /> AI Visual Hash Verified
      </div>
    );
  }

  if (isFlaggedDuplicate) {
    return (
      <div className="inline-flex items-center gap-1.5 rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-1 text-xs font-bold text-rose-500">
        <ShieldAlert className="h-3.5 w-3.5" /> AI Visual Tamper Flagged (Duplicate Image)
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-bold text-emerald-500">
      <ShieldCheck className="h-4 w-4" />
      <span>AI Visual Hash Authenticated</span>
      <span className="font-mono text-[10px] opacity-75 font-normal">({perceptualHash.substring(0, 12)}...)</span>
    </div>
  );
}
