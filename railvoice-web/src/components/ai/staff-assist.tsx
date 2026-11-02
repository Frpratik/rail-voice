"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";

const URGENCY = ["", "Cosmetic", "Minor", "Normal", "High", "Immediate danger"];

/** AI suggestion for which department should take a report and how urgent it is. Staff decide. */
export function TriageSuggestion({
  issueId,
  onUseDepartment,
}: {
  issueId: string;
  onUseDepartment: (department: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ issueId: string; department: string; urgency: number; reason: string } | null>(
    null
  );
  const current = result?.issueId === issueId ? result : null;

  const suggest = async () => {
    setBusy(true);
    try {
      const res = await api.ai.triage(issueId);
      setResult({ issueId, ...res.data });
    } catch {
      toast.error("Couldn't get a suggestion right now");
    } finally {
      setBusy(false);
    }
  };

  if (!current) {
    return (
      <button
        type="button"
        onClick={() => void suggest()}
        disabled={busy}
        className="label-caps inline-flex items-center gap-1.5 text-xs text-accent hover:underline disabled:opacity-50"
      >
        <Sparkles className="h-3.5 w-3.5" />
        {busy ? "Thinking…" : "Suggest department"}
      </button>
    );
  }
  return (
    <div className="space-y-1 border-l-4 border-accent bg-muted/50 px-2 py-1.5 text-xs">
      <p>
        <span className="font-semibold capitalize">{current.department}</span> · urgency {current.urgency}/5 (
        {URGENCY[current.urgency]})
      </p>
      <p className="text-muted-foreground">{current.reason}</p>
      <button
        type="button"
        onClick={() => onUseDepartment(current.department)}
        className="label-caps text-accent hover:underline"
      >
        Use this department
      </button>
    </div>
  );
}

/** Compare the passenger's photo with the staff proof-of-fix photo before closing a report. */
export function FixCheck({ issueId }: { issueId: string }) {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ issueId: string; same_place: boolean; looks_fixed: boolean; explanation: string } | null>(
    null
  );
  const current = result?.issueId === issueId ? result : null;

  const check = async () => {
    setBusy(true);
    try {
      const res = await api.ai.fixCheck(issueId);
      setResult({ issueId, ...res.data });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Couldn't check the photos right now");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-1">
      <button
        type="button"
        onClick={() => void check()}
        disabled={busy}
        className="label-caps inline-flex items-center gap-1.5 text-xs text-accent hover:underline disabled:opacity-50"
      >
        <Sparkles className="h-3.5 w-3.5" />
        {busy ? "Comparing photos…" : "Check fix against passenger photo"}
      </button>
      {current && (
        <div
          className={`border-l-4 px-2 py-1.5 text-xs ${
            current.looks_fixed && current.same_place ? "border-success bg-success/10" : "border-warning bg-warning/10"
          }`}
        >
          <p className="font-semibold">
            {!current.same_place
              ? "May not be the same place"
              : current.looks_fixed
                ? "Looks fixed"
                : "Doesn't look fixed yet"}
          </p>
          <p>{current.explanation}</p>
          <p className="text-muted-foreground">AI check. Look at the photos yourself before closing.</p>
        </div>
      )}
    </div>
  );
}
