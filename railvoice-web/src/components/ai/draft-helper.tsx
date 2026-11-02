"use client";

import { Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import type { ReportDraft } from "@/lib/types";
import { VoiceInput } from "./voice-input";

/** "Write it for me": turns a rough note in any language into a filled-in report. */
export function DraftHelper({
  stationId,
  onDraft,
}: {
  stationId: string;
  onDraft: (draft: ReportDraft) => void;
}) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const write = async () => {
    setBusy(true);
    try {
      const res = await api.ai.draftReport({ note: note.trim(), station_id: stationId || undefined });
      if (!res.data.is_railway_problem) {
        toast.error("This doesn't look like a railway problem. Please describe what's wrong at the station.");
        return;
      }
      onDraft(res.data);
      toast.success("Filled in below. Please check it before you submit.");
    } catch (e) {
      toast.error(
        e instanceof ApiError && e.status === 401
          ? "Sign in, or choose to report without signing in, to use this"
          : "Couldn't write the report right now. Please fill it in yourself."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card className="space-y-3 border-2 border-dashed border-primary/50 p-4 sm:p-6">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-accent" />
        <h2 className="text-display text-xl">Describe it in your own words</h2>
      </div>
      <p className="text-sm text-muted-foreground">
        Type or speak in Hindi, Marathi, Gujarati, Hinglish or English. AI fills in the form for you to check.
      </p>
      <VoiceInput onText={setNote} />
      <Textarea
        rows={3}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="e.g. platform 3 pe escalator subah se band hai, buzurg log pareshan hai"
        className="min-h-0"
      />
      <Button
        type="button"
        variant="accent"
        size="sm"
        className="gap-1.5"
        disabled={busy || note.trim().length < 5}
        onClick={() => void write()}
      >
        <Sparkles className="h-3.5 w-3.5" />
        {busy ? "Writing…" : "Write it for me"}
      </Button>
    </Card>
  );
}
