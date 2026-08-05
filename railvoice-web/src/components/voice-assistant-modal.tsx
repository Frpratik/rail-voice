"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Mic, Sparkles, Send, X } from "lucide-react";
import { toast } from "sonner";

interface VoiceParseResult {
  detected_language: string;
  station_code: string | null;
  station_name: string | null;
  category_code: string;
  original_transcript: string;
  translated_summary: string;
}

export function VoiceAssistantModal({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) {
  const router = useRouter();
  const [transcript, setTranscript] = React.useState("");
  const [_parsing, setParsing] = React.useState(false);
  const [parsedData, setParsedData] = React.useState<VoiceParseResult | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  if (!isOpen) return null;

  const handleParse = async (textToParse: string) => {
    if (!textToParse.trim()) return;
    setParsing(true);
    try {
      const res = await fetch("/api/v1/voice/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: textToParse }),
      });
      if (res.ok) {
        const json = await res.json();
        setParsedData(json.data);
      }
    } catch {
      toast.error("Failed to parse voice transcript");
    } finally {
      setParsing(false);
    }
  };

  const handleSubmit = async () => {
    if (!transcript.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch("/api/v1/voice/create-issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript }),
      });
      if (res.ok) {
        const json = await res.json();
        toast.success("Voice Grievance Registered Successfully!");
        onClose();
        router.push(`/issues/${json.data.issue_id}`);
      } else {
        toast.error("Failed to create issue from voice report");
      }
    } catch {
      toast.error("Network error during voice submission");
    } finally {
      setSubmitting(false);
    }
  };

  const samplePresets = [
    { label: "Hindi (हिंदी)", text: "बांद्रा स्टेशन के प्लेटफार्म 1 पर बहुत कचरा जमा है" },
    { label: "Marathi (मराठी)", text: "अंधेरी स्टेशन वर सरकता जिना बंद आहे" },
    { label: "Gujarati (ગુજરાતી)", text: "બોરીવલી સ્ટેશન પર પાણીનું લીકેજ છે" },
    { label: "Hinglish", text: "Dadar station pe ticket counter par bohot crowd hai" },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl border border-border bg-card p-6 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-accent font-bold">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15">
              <Mic className="h-5 w-5 text-accent animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold tracking-tight text-foreground">
                AI Vernacular Voice Assistant
              </h2>
              <p className="text-xs text-muted-foreground font-normal">
                Speak or type in Hindi, Marathi, Gujarati, Hinglish, or English
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

        {/* Preset Sample Quick Chips */}
        <div className="space-y-1.5">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Try Vernacular Presets:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {samplePresets.map((preset) => (
              <button
                key={preset.label}
                onClick={() => {
                  setTranscript(preset.text);
                  handleParse(preset.text);
                }}
                className="rounded-lg border border-border bg-muted/50 px-2.5 py-1 text-xs font-medium hover:border-accent/50 hover:bg-accent/10 transition-all text-left"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Input Textarea */}
        <div className="space-y-2">
          <textarea
            value={transcript}
            onChange={(e) => {
              setTranscript(e.target.value);
              if (e.target.value.length > 5) {
                handleParse(e.target.value);
              }
            }}
            placeholder="Type or paste spoken notes in any language (e.g. बांद्रा स्टेशन पर पानी का लीकेज है)..."
            rows={3}
            className="w-full rounded-2xl border border-input bg-background p-3.5 text-sm font-medium focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 transition-all"
          />
        </div>

        {/* AI Live Parse Card */}
        {parsedData && (
          <div className="rounded-2xl border border-accent/30 bg-accent/5 p-4 space-y-3 animate-in fade-in duration-300">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-xs font-bold text-accent">
                <Sparkles className="h-4 w-4" /> AI Vernacular Extraction
              </span>
              <span className="rounded-full bg-accent/20 px-2.5 py-0.5 text-[10px] font-bold uppercase text-accent">
                {parsedData.detected_language} Language
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-xl bg-background/80 p-2.5 border border-border/50">
                <div className="text-[10px] text-muted-foreground uppercase font-bold">Detected Station</div>
                <div className="font-extrabold text-foreground mt-0.5">
                  {parsedData.station_name ? `${parsedData.station_name} (${parsedData.station_code})` : "Default (Bandra)"}
                </div>
              </div>
              <div className="rounded-xl bg-background/80 p-2.5 border border-border/50">
                <div className="text-[10px] text-muted-foreground uppercase font-bold">Predicted Category</div>
                <div className="font-extrabold text-foreground mt-0.5 uppercase">
                  {parsedData.category_code.replace("_", " ")}
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-background/80 p-2.5 border border-border/50 text-xs">
              <div className="text-[10px] text-muted-foreground uppercase font-bold">Translated English Summary</div>
              <div className="font-medium text-foreground mt-0.5">{parsedData.translated_summary}</div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="rounded-xl px-4 py-2.5 text-xs font-bold text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={!transcript.trim() || submitting}
            className="flex items-center gap-2 rounded-xl bg-accent px-5 py-2.5 text-xs font-extrabold text-accent-foreground shadow-lg shadow-accent/25 hover:bg-accent/90 disabled:opacity-50 transition-all"
          >
            {submitting ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <>
                <Send className="h-4 w-4" />
                Submit Voice Report
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
