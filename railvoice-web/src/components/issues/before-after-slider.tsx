"use client";

import { useState } from "react";
import { CheckCircle2, AlertTriangle, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

interface BeforeAfterSliderProps {
  beforeUrl: string;
  afterUrl: string;
  verificationScore?: number | null;
  resolutionStatus?: string | null;
}

export function BeforeAfterSlider({
  beforeUrl,
  afterUrl,
  verificationScore,
  resolutionStatus,
}: BeforeAfterSliderProps) {
  const [sliderPos, setSliderPos] = useState(50);

  const isVerified = (verificationScore ?? 0) >= 75;

  return (
    <div className="space-y-3">
      {/* AI Verification Badge */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Visual Quality Assurance
        </span>
        {verificationScore !== undefined && verificationScore !== null && (
          <div
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border shadow-sm",
              isVerified
                ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                : "bg-amber-500/10 text-amber-500 border-amber-500/30"
            )}
          >
            {isVerified ? (
              <ShieldCheck className="h-4 w-4" />
            ) : (
              <AlertTriangle className="h-4 w-4" />
            )}
            <span>
              {isVerified ? "AI Verified" : "Under Review"} ({verificationScore.toFixed(1)}% Confidence)
            </span>
          </div>
        )}
      </div>

      {/* Interactive Slider Container */}
      <div className="relative h-[320px] w-full select-none overflow-hidden rounded-2xl border border-border shadow-lg">
        {/* After Image (Full background) */}
        <img
          src={afterUrl}
          alt="Resolution After"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute top-3 right-3 rounded-lg bg-emerald-600/90 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-white backdrop-blur shadow-md">
          After (Resolution)
        </div>

        {/* Before Image (Clipped overlay) */}
        <div
          className="absolute inset-y-0 left-0 overflow-hidden border-r-2 border-white shadow-2xl"
          style={{ width: `${sliderPos}%` }}
        >
          <img
            src={beforeUrl}
            alt="Complaint Before"
            className="absolute inset-0 h-full w-full object-cover max-w-none"
            style={{ width: "100%" }}
          />
          <div className="absolute top-3 left-3 rounded-lg bg-slate-900/90 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-white backdrop-blur shadow-md">
            Before (Complaint)
          </div>
        </div>

        {/* Invisible Slider Input for Dragging */}
        <input
          type="range"
          min="0"
          max="100"
          value={sliderPos}
          onChange={(e) => setSliderPos(Number(e.target.value))}
          className="absolute inset-0 z-20 h-full w-full opacity-0 cursor-ew-resize"
        />

        {/* Divider Handle Line */}
        <div
          className="pointer-events-none absolute inset-y-0 z-10 flex items-center justify-center"
          style={{ left: `calc(${sliderPos}% - 16px)` }}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white shadow-xl ring-2 ring-indigo-500/50 text-slate-800 text-xs font-bold">
            ↔
          </div>
        </div>
      </div>
    </div>
  );
}
